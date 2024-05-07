"""State management routines around the lazy importing context."""
# ruff: noqa: FBT003

from __future__ import annotations

import sys
from contextlib import suppress
from importlib import import_module
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
from inspect import stack
from itertools import accumulate
from sys import _getframe as getframe
from sys import meta_path, modules
from typing import TYPE_CHECKING, cast

from lazy_importing.audits import (
    after_autobind,
    after_disable,
    after_enable,
    after_find_spec,
    after_inject_loader,
    before_autobind,
    before_disable,
    before_enable,
    before_find_spec,
    before_inject_loader,
    on_create_module,
    on_exec_module,
)
from lazy_importing.placeholder import LazyObjectPlaceholder

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from sys import _MetaPathFinder
    from types import ModuleType
    from types import ModuleType as SysBase
    from typing import Any, ClassVar

    from typing_extensions import Self, TypeAlias

    LazyObjectMapping: TypeAlias = "dict[str, LazyObjectPlaceholder]"
    MetaPath: TypeAlias = "list[_MetaPathFinder]"
else:
    SysBase = type(sys)


__all__ = (
    # Classes
    "LazyImportingContext",
    "LazyObjectLoader",
)


EXC_INFO_MISSING: tuple[None, None, None] = (None, None, None)
OBJECT_LOADER_ATTRIBUTE: str = "__builtins__"
MISSING_SENTINEL: object = object()

lazy_importing: set[str] = set()
lazy_loading: set[str] = set()


def _get_import_targets(lazy_object_name: str) -> tuple[str, str | None]:
    """Return a (module, attribute) import target names pair from a lazy object name."""
    parts = iter(lazy_object_name.rsplit(".", 1))
    return next(parts), next(parts, None)


def _cleanup_lazy_object(lazy_object: LazyObjectPlaceholder) -> None:
    parent_module_names = lazy_object.__name__.split(".")[:-1]
    for module_name in accumulate(parent_module_names, lambda *parts: ".".join(parts)):
        # Go through parents to delete references to self.
        lazy_parent = modules.get(module_name)
        if not isinstance(lazy_parent, LazyObjectPlaceholder):
            # That's an important check.
            # We don't remove modules that were (most probably)
            # eagerly imported earlier!
            continue
        try:
            del modules[module_name]
        except KeyError:
            # Assume that if it's not present, it was cleaned up correctly.
            # There is no risk of a race condition (we're inside a lock).
            continue
        # Assume a parent doesn't lie about their child
        # (would have to be set manually).
        attrs = {
            attr
            for attr, child in vars(lazy_parent).items()
            if isinstance(child, LazyObjectPlaceholder)
        }
        for attr in attrs:
            delattr(lazy_parent, attr)
    with suppress(KeyError):
        del modules[lazy_object.__name__]


def _bind_lazy_object(
    module_name: str,
    lazy_object: LazyObjectPlaceholder,
    loaded_object: Any,
    *,
    lazy_objects: dict[str, LazyObjectPlaceholder],
    local_ns: dict[str, Any],
) -> None:
    """Automatically replace all references to lazy objects with the loaded object."""
    for ref, other in lazy_objects.items():
        if other is not lazy_object:
            continue
        before_autobind(lazy_object, loaded_object, local_ns, ref)
        if module_name is not None and module_name in lazy_importing:
            # If we're inside LAZY_IMPORTING block, force the replacement.
            local_ns[ref] = loaded_object
        else:
            # We're outside LAZY_IMPORTING block.
            # Respect if the caller frame decided to define the attribute otherwise.
            local_ns.setdefault(ref, loaded_object)
        after_autobind(lazy_object, loaded_object, local_ns, ref)


def _load_lazy_object(
    module_name: str,
    lazy_object: LazyObjectPlaceholder,
    global_ns: dict[str, Any],
    local_ns: dict[str, Any],
) -> Any:
    """Perform an actual import of a lazy object."""
    lazy_loading.add(module_name)
    try:
        if module_name is not None and module_name in lazy_importing:
            # If we're inside LAZY_IMPORTING block, raise a RuntimeError.
            msg = "Cannot load objects inside LAZY_IMPORTING blocks"
            raise RuntimeError(msg)
        package = local_ns.get("__package__") or global_ns.get("__package__")
        target_name = lazy_object.__name__
        target_module_name, attribute_name = _get_import_targets(target_name)
        obj = MISSING_SENTINEL
        if attribute_name:
            base_module = import_module(target_module_name, package=package)
            with suppress(AttributeError):
                obj = getattr(base_module, attribute_name)
        if obj is MISSING_SENTINEL:
            obj = import_module(target_name, package=package)
        return obj
    finally:
        lazy_loading.discard(module_name)


class LazyObjectLoader(dict):  # type: ignore[type-arg]
    """New [`__builtins__`][builtins] to provide lazy objects on first reference."""

    __slots__ = ("lazy_objects", "global_ns", "local_ns", "module_name")

    module_name: str
    global_ns: dict[str, object]
    local_ns: dict[str, object]
    lazy_objects: LazyObjectMapping

    def __getitem__(self, key: Any) -> Any:
        """Intercept undefined name lookup and load a lazy object if applicable."""
        with suppress(KeyError):
            return super().__getitem__(key)
        try:
            lazy_object = (lazy_objects := self.lazy_objects)[key]
        except KeyError:
            raise NameError(key) from None
        final_object = _load_lazy_object(
            module_name := self.module_name,
            lazy_object,
            global_ns=self.global_ns,
            local_ns=(local_ns := self.local_ns),
        )
        _bind_lazy_object(
            module_name,
            lazy_object,
            loaded_object=final_object,
            local_ns=local_ns,
            lazy_objects=lazy_objects,
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
        local_ns: dict[str, Any] | None = None,
        global_ns: dict[str, Any] | None = None,
        object_loader_class: type[LazyObjectLoader] | None = None,
        stack_offset: int = 1,
    ) -> None:
        """
        Initialize self.

        Parameters
        ----------
        importer_factory
            The importer to use.
            Defaults to [`LazyImporter`][lazy_importing.api.LazyImporter].
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
        module_name = self._global_ns["__name__"]
        self.module_name = module_name
        self.importer = self._importer_factory(module_name)
        self.lazy_objects = {}

    def load_lazy_object(self, lazy_object: Any) -> Any:
        """Perform an actual import of a lazy object."""
        return _load_lazy_object(
            self.module_name,
            lazy_object,
            global_ns=self._global_ns,
            local_ns=self._local_ns,
        )

    def bind_lazy_object(
        self,
        lazy_object: Any,
        loaded_object: Any,
        *references: str,
    ) -> Any:
        """Perform an actual import of a lazy object."""
        new_lazy_objects = self.lazy_objects.copy()
        new_lazy_objects.update(dict.fromkeys(references, lazy_object))
        _bind_lazy_object(
            self.module_name,
            lazy_object,
            loaded_object,
            lazy_objects=new_lazy_objects,
            local_ns=self._local_ns,
        )

    def __enter__(self) -> Self:
        """Enable lazy importing mode."""
        if self._exited:
            msg = "Cannot enter the same lazy importing context twice."
            raise RuntimeError(msg)
        __lazy_importing_skip_frame__ = True  # noqa: F841
        self.importer.enable()
        return self

    def _cleanup_objects(self) -> None:
        for identifier, lazy_object in self._local_ns.copy().items():
            if not isinstance(lazy_object, LazyObjectPlaceholder):
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
        object_loader = self._object_loader_class(builtins)
        object_loader.module_name = self.module_name
        object_loader.global_ns = self._global_ns
        object_loader.local_ns = self._local_ns
        object_loader.lazy_objects = self.lazy_objects
        before_inject_loader(self, object_loader)
        self._local_ns[OBJECT_LOADER_ATTRIBUTE] = object_loader
        after_inject_loader(self, object_loader)

    def __exit__(self, *exc_info: object) -> None:
        """Disable lazy importing mode."""
        self._exited = True
        self.importer.disable()
        self._cleanup_objects()
        # Treat exc_info==() as manual calls with assumed success.
        if not exc_info or exc_info == EXC_INFO_MISSING:
            self._inject_loader()


_OLD_META_PATH: MetaPath = None  # type: ignore[assignment]


class _LazyImportingSys(SysBase):
    # This is hell...
    __meta_path__: MetaPath = meta_path
    _lazy_importing_metapaths: ClassVar[dict[str, MetaPath]] = {}

    @property
    def meta_path(self) -> MetaPath:
        module_name = None
        for frame_info in stack()[1:]:
            if frame_info.code_context is None:
                continue
            frame_locals = frame_info.frame.f_locals
            module_name = frame_locals.get("__name__")
            if not frame_locals.get("__lazy_importing_skip_frame__"):
                break
            if module_name is not None and module_name in lazy_importing:
                break
        if module_name is None or module_name not in lazy_importing:
            return self.__meta_path__
        return self._lazy_importing_metapaths.get(module_name, self.__meta_path__)

    @meta_path.setter
    def meta_path(self, value: MetaPath) -> None:
        module_name = None
        for frame_info in stack()[1:]:
            if frame_info.code_context is None:
                continue
            frame_locals = frame_info.frame.f_locals
            module_name = frame_locals.get("__name__")
            if not frame_locals.get("__lazy_importing_skip_frame__"):
                break
            if module_name is not None and module_name in lazy_importing:
                break
        if value is _OLD_META_PATH:
            if module_name is not None:
                self._lazy_importing_metapaths.pop(module_name, None)
                return
            value = self.__meta_path__
        if module_name is None or module_name not in lazy_importing:
            self.__meta_path__ = value
            return
        self._lazy_importing_metapaths[module_name] = value


sys.__class__ = _LazyImportingSys


class LazyImporter(Loader, MetaPathFinder):
    """A context-local importer (finder & loader) to perform lazy importing."""

    _initialized: bool = False
    _importers: ClassVar[dict[str, Self]] = {}

    def __new__(cls, module_name: str) -> Self:
        try:
            return cast("Self", cls._importers[module_name])
        except KeyError:
            self = super().__new__(cls)
            cls._importers[module_name] = self
            return self

    def __init__(self, module_name: str) -> None:
        """
        Create a lazy importer.

        Parameters
        ----------
        module_name
            The targeted module name.

        """
        if not self._initialized:
            self.module_name = module_name
            self._enabled = False
            self._initialized = True

    def enable(self) -> None:
        """Delegate processing all import finder requests into the lazy importer."""
        # Important:
        # We don't re-initialize the original list not to break imports based on
        # the old `sys.meta_path`. Instead, we overwrite the attribute with a new list
        # which will only be available to the module of name `module_name`;
        # (`sys.meta_path`) is a dynamic property that examines `lazy_importing_module`.
        if not isinstance(sys, _LazyImportingSys) or self._enabled:
            return
        self._enabled = True
        before_enable(self)
        lazy_importing.add(self.module_name)
        __lazy_importing_skip_frame__ = True  # noqa: F841
        sys.meta_path = [self]
        after_enable(self)

    def disable(self) -> None:
        """Remove lazy importer from meta path."""
        # Bring back the same instance of sys.meta_path.
        if not (isinstance(sys, _LazyImportingSys) and self._enabled):
            return
        before_disable(self)
        sys.meta_path = _OLD_META_PATH
        lazy_importing.discard(self.module_name)
        after_disable(self)

    def create_module(self, spec: ModuleSpec) -> ModuleType:
        """Create a module."""
        lazy_object = LazyObjectPlaceholder()
        on_create_module(self, spec, lazy_object)
        return cast("ModuleType", lazy_object)

    def exec_module(self, module: Any) -> None:
        """Raise an auditing event. Do nothing meaningful."""
        on_exec_module(self, module)

    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None = None,
        target: ModuleType | None = None,
    ) -> ModuleSpec | None:
        """Find the actual spec and preserve it for loading it lazily later."""
        before_find_spec(self, fullname, path, target)
        spec = ModuleSpec(fullname, self)
        after_find_spec(self, spec)
        return spec
