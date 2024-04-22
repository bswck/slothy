"""The API for entering lazy importing context."""
# ruff: noqa: FBT003

from __future__ import annotations

import sys
from contextlib import suppress
from contextvars import ContextVar, copy_context
from importlib import import_module
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
from itertools import accumulate
from sys import _getframe as getframe
from threading import RLock
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from contextvars import Context
    from sys import _MetaPathFinder
    from types import ModuleType
    from typing import Any

    from typing_extensions import Self, TypeAlias

    LazyObjectMapping: TypeAlias = "dict[str, LazyObject]"
    MetaPath: TypeAlias = "list[_MetaPathFinder]"


__all__ = (
    # Classes
    "LazyImportingContext",
    "LazyObject",
    "LazyObjectLoader",
    "LazyImporter",
    # Functions
    "bind_lazy_object",
    "load_lazy_object",
    # Local state
    "lazy_importing",
    "lazy_loading",
    "old_meta_path",
)


EXC_INFO_MISSING: tuple[None, None, None] = (None, None, None)
OBJECT_LOADER_ATTRIBUTE: str = "__builtins__"
lazy_importing: ContextVar[bool] = ContextVar("lazy_importing", default=False)
lazy_loading: ContextVar[bool] = ContextVar("lazy_loading", default=False)
old_meta_path: ContextVar[MetaPath] = ContextVar("old_meta_path")


def _get_import_targets(lazy_object_name: str) -> tuple[str, str | None]:
    """Return a (module, attribute) import target names pair from a lazy object name."""
    parts = iter(lazy_object_name.rsplit(".", 1))
    return next(parts), next(parts, None)


def _cleanup_lazy_object(lazy_object: LazyObject) -> None:
    parent_module_names = lazy_object.__name__.split(".")[:-1]
    for module_name in accumulate(parent_module_names, lambda *parts: ".".join(parts)):
        # Go through parents to delete references to self.
        lazy_parent = sys.modules.get(module_name)
        if not isinstance(lazy_parent, LazyObject):
            # That's an important check.
            # We don't remove modules that were (most probably)
            # eagerly imported earlier!
            continue
        try:
            del sys.modules[module_name]
        except KeyError:
            # Assume that if it's not present, it was cleaned up correctly.
            # There is no risk of a race condition (we're inside a lock).
            continue
        attrs = set()
        for attr, child in vars(lazy_parent).items():
            if not isinstance(child, LazyObject):
                continue
            # Assume a parent doesn't lie about their child
            # (would have to be set manually).
            attrs.add(attr)
        for attr in attrs:
            delattr(lazy_parent, attr)
    with suppress(KeyError):
        del sys.modules[lazy_object.__name__]


def bind_lazy_object(  # noqa: PLR0913
    lazy_object: LazyObject,
    loaded_object: Any,
    *,
    lazy_objects: dict[str, LazyObject],
    global_ns: dict[str, Any] | None = None,
    local_ns: dict[str, Any] | None = None,
    stack_offset: int = 1,
) -> None:
    """Automatically replace all references to lazy objects with the loaded object."""
    if local_ns is None:
        local_ns = getframe(stack_offset).f_locals
    if global_ns is None:
        global_ns = getframe(stack_offset).f_globals
    for ref, other in lazy_objects.items():
        if other is not lazy_object:
            continue
        if lazy_importing.get():
            # If we're inside LAZY_IMPORTING block, force the replacement.
            local_ns[ref] = loaded_object
        else:
            # We're outside LAZY_IMPORTING block.
            # Respect if the caller frame decided to define the attribute otherwise.
            local_ns.setdefault(ref, loaded_object)


def load_lazy_object(
    lazy_object: LazyObject,
    global_ns: dict[str, Any] | None = None,
    local_ns: dict[str, Any] | None = None,
    *,
    stack_offset: int = 1,
) -> Any:
    """Perform an actual import of a lazy object."""
    optout = lazy_importing.get()
    if optout:
        # If we're inside LAZY_IMPORTING block, clean the lazy object before loading.
        _cleanup_lazy_object(lazy_object)
    if local_ns is None:
        local_ns = getframe(stack_offset).f_locals
    if global_ns is None:
        global_ns = getframe(stack_offset).f_globals
    package = local_ns.get("__package__") or global_ns.get("__package__")
    target_name = lazy_object.__name__
    module_name, attribute_name = _get_import_targets(target_name)
    meta_path = sys.meta_path
    if optout:
        sys.meta_path = old_meta_path.get()
    missing = object()
    ret = missing
    if attribute_name:
        base_module = import_module(module_name, package=package)
        with suppress(AttributeError):
            ret = getattr(base_module, attribute_name)
    if ret is missing:
        ret = import_module(target_name, package=package)
    if optout:
        sys.meta_path = meta_path
    return ret


class LazyObject:
    """An object imported lazily. Collects state that normal modules do."""

    __name__: str
    __loader__: str
    __spec__: ModuleSpec
    __package__: str

    @property
    def __path__(self) -> list[str]:
        """Return the path. Necessary to allow declaring package imports."""
        return []

    if __debug__:

        def __repr__(self) -> str:
            """Return a representation of self."""
            # Needs decision: try to `textwrap.shorten()` on the module name?
            return f"<lazy object {self.__name__!r}>"


class LazyObjectLoader(dict):  # type: ignore[type-arg]
    """Substitute for `__builtins__` to provide lazy objects on first reference."""

    __slots__ = ("lazy_objects", "global_ns", "local_ns")

    global_ns: dict[str, object]
    local_ns: dict[str, object]
    lazy_objects: LazyObjectMapping

    def __getitem__(self, key: Any) -> Any:
        """Intercept undefined name lookup and load a lazy object if applicable."""
        with suppress(KeyError):
            return super().__getitem__(key)
        try:
            lazy_object = self.lazy_objects[key]
        except KeyError:
            raise NameError(key) from None
        final_object = load_lazy_object(
            lazy_object,
            global_ns=self.global_ns,
            local_ns=self.local_ns,
        )
        bind_lazy_object(
            lazy_object=lazy_object,
            loaded_object=final_object,
            global_ns=self.global_ns,
            local_ns=self.local_ns,
            lazy_objects=self.lazy_objects,
        )
        return final_object


class LazyImportingContext:
    """A context manager that enables lazy importing."""

    lazy_objects: LazyObjectMapping
    _object_loader_class: type[LazyObjectLoader]

    def __init__(  # noqa: PLR0913
        self,
        *,
        importer_factory: Callable[..., LazyImporter] | None = None,
        meta_path: MetaPath | None = None,
        local_ns: dict[str, object] | None = None,
        global_ns: dict[str, object] | None = None,
        object_loader_class: type[LazyObjectLoader] | None = None,
        stack_offset: int = 1,
    ) -> None:
        """
        Initialize self.

        Parameters
        ----------
        importer_factory
            The importer to use.
            Defaults to [`LazyImporter`][lazy_importing.LazyImporter].
        meta_path
            The meta path to remember. Defaults to [`sys.meta_path`][sys.meta_path].
        local_ns
            The local namespace to use. Defaults to the local namespace of the caller.
        global_ns
            The global namespace to use. Defaults to the global namespace of the caller.
        object_loader_class
            The loader factory to use.
            Defaults to [`LazyObjectLoader`][lazy_importing.LazyObjectLoader].
        stack_offset
            The stack offset to use.

        """
        self._exited = False
        if local_ns is None:
            local_ns = getframe(stack_offset).f_locals
        self._local_ns = local_ns
        if global_ns is None:
            global_ns = getframe(stack_offset).f_globals
        self._global_ns = global_ns
        self._object_loader_class = object_loader_class or LazyObjectLoader
        self._importer_factory = importer_factory or LazyImporter
        self.lazy_objects = {}
        self.context = copy_context()
        self.importer = self._importer_factory(self.context, meta_path)

    def load_lazy_object(self, lazy_object: LazyObject) -> Any:
        """Perform an actual import of a lazy object."""
        return self.context.run(
            load_lazy_object,
            lazy_object,
            global_ns=self._global_ns,
            local_ns=self._local_ns,
        )

    def bind_lazy_object(
        self,
        lazy_object: LazyObject,
        loaded_object: Any,
        *references: str,
    ) -> Any:
        """Perform an actual import of a lazy object."""
        lazy_objects = self.lazy_objects.copy()
        lazy_objects.update(dict.fromkeys(references, lazy_object))
        return self.context.run(
            bind_lazy_object,
            lazy_object,
            loaded_object,
            lazy_objects=lazy_objects,
            global_ns=self._global_ns,
            local_ns=self._local_ns,
        )

    def __enter__(self) -> Self:
        """Enable lazy importing mode."""
        if self._exited:
            msg = "Cannot enter the same lazy importing context twice."
            raise RuntimeError(msg)
        self.context.run(lazy_importing.set, True)
        self.importer.enable()
        return self

    def _cleanup_objects(self) -> None:
        for identifier, lazy_object in self._local_ns.copy().items():
            if not isinstance(lazy_object, LazyObject):
                continue
            with suppress(KeyError):
                del self._local_ns[identifier]
                self.lazy_objects[identifier] = lazy_object
            _cleanup_lazy_object(lazy_object=lazy_object)

    def _inject_loader(self) -> None:
        builtins = self._local_ns.get(OBJECT_LOADER_ATTRIBUTE)
        if builtins is None:
            builtins = self._global_ns[OBJECT_LOADER_ATTRIBUTE]
        if not isinstance(builtins, dict):
            builtins = vars(builtins)
        lazy_object_loader = self._object_loader_class(builtins)
        lazy_object_loader.global_ns = self._global_ns
        lazy_object_loader.local_ns = self._local_ns
        lazy_object_loader.lazy_objects = self.lazy_objects
        self._local_ns[OBJECT_LOADER_ATTRIBUTE] = lazy_object_loader

    def __exit__(self, *exc_info: object) -> None:
        """Disable lazy importing mode."""
        self._exited = True
        self.importer.disable()
        self.context.run(lazy_importing.set, False)
        self._cleanup_objects()
        if exc_info == EXC_INFO_MISSING:
            self._inject_loader()


class LazyImporter(Loader, MetaPathFinder):
    """A strategy for lazy importing."""

    _lock = RLock()
    context: Context
    meta_path: MetaPath

    def __init__(
        self,
        context: Context,
        meta_path: MetaPath | None = None,
    ) -> None:
        """
        Create a lazy importing strategy.

        Parameters
        ----------
        context
            The context in which the importing strategy should operate.

        meta_path
            The meta path to use for lazy importing. Defaults to the meta path
            known to the least recently created lazy importing context manager.

        """
        self.context = context
        if meta_path is None:
            meta_path = context.get(old_meta_path) or sys.meta_path
        self.meta_path = meta_path
        context.run(old_meta_path.set, self.meta_path)

    def enable(self) -> None:
        """Delegate processing all import finder requests into the lazy importer."""
        self._lock.acquire()
        # Important:
        # We don't clear the original list not to break imports based on
        # the old sys.meta_path object. Instead, we overwrite with a new list.
        sys.meta_path = [self]

    def disable(self) -> None:
        """Remove lazy importer from meta path."""
        # Bring back the same instance of sys.meta_path.
        sys.meta_path = self.meta_path
        self._lock.release()

    def create_module(self, spec: ModuleSpec) -> ModuleType:  # noqa: ARG002
        """Create a module."""
        return cast("ModuleType", LazyObject())

    def exec_module(self, module: Any) -> None:
        """Do nothing."""

    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None = None,  # noqa: ARG002
        target: ModuleType | None = None,  # noqa: ARG002
    ) -> ModuleSpec | None:
        """Find the actual spec and preserve it for loading it lazily later."""
        return ModuleSpec(fullname, self)
