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

from slothy.audits import (
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
from slothy.object import SlothyObject

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from sys import _MetaPathFinder
    from types import ModuleType
    from types import ModuleType as SysBase
    from typing import Any, ClassVar

    from typing_extensions import Self, TypeAlias

    SlothyObjectMapping: TypeAlias = "dict[str, SlothyObject]"
    MetaPath: TypeAlias = "list[_MetaPathFinder]"
else:
    SysBase = type(sys)


__all__ = (
    # Classes
    "SlothyContext",
    "SlothyLoader",
)


EXC_INFO_MISSING: tuple[None, None, None] = (None, None, None)
OBJECT_LOADER_ATTRIBUTE: str = "__builtins__"
MISSING_SENTINEL: object = object()

slothy_importing: set[str] = set()
slothy_loading: set[str] = set()


def _get_import_targets(slothy_object_name: str) -> tuple[str, str | None]:
    """Return a (module, attribute) import target names pair from a lazy object name."""
    parts = iter(slothy_object_name.rsplit(".", 1))
    return next(parts), next(parts, None)


def _cleanup_slothy_object(slothy_object: SlothyObject) -> None:
    parent_module_names = slothy_object.__name__.split(".")[:-1]
    for module_name in accumulate(parent_module_names, lambda *parts: ".".join(parts)):
        # Go through parents to delete references to self.
        slothy_parent = modules.get(module_name)
        if not isinstance(slothy_parent, SlothyObject):
            # That's an important check.
            # We don't remove modules that were (most probably)
            # eagerly imported earlier!
            continue
        try:
            del modules[module_name]
        except KeyError:
            # Assume that if it's not present, it was cleaned up correctly.
            # Food for thought: Is there a risk of a race condition?
            continue
        # Assume a parent doesn't lie about their child
        # (would have to be set manually).
        attrs = {
            attr
            for attr, child in vars(slothy_parent).items()
            if isinstance(child, SlothyObject)
        }
        for attr in attrs:
            delattr(slothy_parent, attr)
    with suppress(KeyError):
        del modules[slothy_object.__name__]


def _bind_slothy_object(
    module_name: str,
    slothy_object: SlothyObject,
    loaded_object: Any,
    *,
    slothy_objects: dict[str, SlothyObject],
    local_ns: dict[str, Any],
) -> None:
    """Automatically replace all references to lazy objects with the loaded object."""
    for ref, other in slothy_objects.items():
        if other is not slothy_object:
            continue
        before_autobind(slothy_object, loaded_object, local_ns, ref)
        if module_name is not None and module_name in slothy_importing:
            # If we're inside SLOTHY block, force the replacement.
            local_ns[ref] = loaded_object
        else:
            # We're outside SLOTHY block.
            # Respect if the caller frame decided to define the attribute otherwise.
            local_ns.setdefault(ref, loaded_object)
        after_autobind(slothy_object, loaded_object, local_ns, ref)


def _load_slothy_object(
    module_name: str,
    slothy_object: SlothyObject,
    global_ns: dict[str, Any],
    local_ns: dict[str, Any],
) -> Any:
    """Perform an actual import of a lazy object."""
    slothy_loading.add(module_name)
    try:
        if module_name is not None and module_name in slothy_importing:
            # If we're inside SLOTHY block, raise a RuntimeError.
            msg = "Cannot load objects inside SLOTHY blocks"
            raise RuntimeError(msg)
        package = local_ns.get("__package__") or global_ns.get("__package__")
        target_name = slothy_object.__name__
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
        slothy_loading.discard(module_name)


class SlothyLoader(dict):  # type: ignore[type-arg]
    """New [`__builtins__`][builtins] to provide lazy objects on first reference."""

    __slots__ = ("slothy_objects", "global_ns", "local_ns", "module_name")

    module_name: str
    global_ns: dict[str, object]
    local_ns: dict[str, object]
    slothy_objects: SlothyObjectMapping

    def __getitem__(self, key: Any) -> Any:
        """Intercept undefined name lookup and load a lazy object if applicable."""
        with suppress(KeyError):
            return super().__getitem__(key)
        try:
            slothy_object = (slothy_objects := self.slothy_objects)[key]
        except KeyError:
            raise NameError(key) from None
        final_object = _load_slothy_object(
            module_name := self.module_name,
            slothy_object,
            global_ns=self.global_ns,
            local_ns=(local_ns := self.local_ns),
        )
        _bind_slothy_object(
            module_name,
            slothy_object,
            loaded_object=final_object,
            local_ns=local_ns,
            slothy_objects=slothy_objects,
        )
        return final_object


class SlothyContext:
    """A context manager that enables lazy importing."""

    slothy_objects: SlothyObjectMapping
    _slothy_loader_class: type[SlothyLoader]

    def __init__(  # noqa: PLR0913
        self,
        *,
        importer_factory: Callable[..., SlothyImporter] | None = None,
        local_ns: dict[str, Any] | None = None,
        global_ns: dict[str, Any] | None = None,
        object_loader_class: type[SlothyLoader] | None = None,
        stack_offset: int = 1,
    ) -> None:
        """
        Initialize self.

        Parameters
        ----------
        importer_factory
            The importer to use.
            Defaults to [`SlothyImporter`][slothy.api.SlothyImporter].
        local_ns
            The local namespace to use. Defaults to the local namespace of the caller.
        global_ns
            The global namespace to use. Defaults to the global namespace of the caller.
        object_loader_class
            The loader factory to use.
            Defaults to [`SlothyLoader`][slothy.SlothyLoader].
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
        self._slothy_loader_class = object_loader_class or SlothyLoader
        self._importer_factory = importer_factory or SlothyImporter
        module_name = self._global_ns["__name__"]
        self.module_name = module_name
        self.importer = self._importer_factory(module_name)
        self.slothy_objects = {}

    def load_slothy_object(self, slothy_object: Any) -> Any:
        """Perform an actual import of a lazy object."""
        return _load_slothy_object(
            self.module_name,
            slothy_object,
            global_ns=self._global_ns,
            local_ns=self._local_ns,
        )

    def bind_slothy_object(
        self,
        slothy_object: Any,
        loaded_object: Any,
        *references: str,
    ) -> Any:
        """Perform an actual import of a lazy object."""
        new_slothy_objects = self.slothy_objects.copy()
        new_slothy_objects.update(dict.fromkeys(references, slothy_object))
        _bind_slothy_object(
            self.module_name,
            slothy_object,
            loaded_object,
            slothy_objects=new_slothy_objects,
            local_ns=self._local_ns,
        )

    def __enter__(self) -> Self:
        """Enable lazy importing mode."""
        if self._exited:
            msg = "Cannot enter the same lazy importing context twice."
            raise RuntimeError(msg)
        __slothy_skip_frame__ = True  # noqa: F841
        self.importer.enable()
        return self

    def _cleanup_objects(self) -> None:
        for identifier, slothy_object in self._local_ns.copy().items():
            if not isinstance(slothy_object, SlothyObject):
                continue
            with suppress(KeyError):
                del self._local_ns[identifier]
                self.slothy_objects[identifier] = slothy_object
            _cleanup_slothy_object(slothy_object=slothy_object)

    def _inject_loader(self) -> None:
        builtins = self._local_ns.get(OBJECT_LOADER_ATTRIBUTE)
        if builtins is None:
            builtins = self._global_ns[OBJECT_LOADER_ATTRIBUTE]
        if not isinstance(builtins, dict):
            builtins = vars(builtins)
        slothy_loader = self._slothy_loader_class(builtins)
        slothy_loader.module_name = self.module_name
        slothy_loader.global_ns = self._global_ns
        slothy_loader.local_ns = self._local_ns
        slothy_loader.slothy_objects = self.slothy_objects
        before_inject_loader(self, slothy_loader)
        self._local_ns[OBJECT_LOADER_ATTRIBUTE] = slothy_loader
        after_inject_loader(self, slothy_loader)

    def __exit__(self, *exc_info: object) -> None:
        """Disable lazy importing mode."""
        self._exited = True
        self.importer.disable()
        self._cleanup_objects()
        # Treat exc_info==() as manual calls with assumed success.
        if not exc_info or exc_info == EXC_INFO_MISSING:
            self._inject_loader()


_OLD_META_PATH: MetaPath = None  # type: ignore[assignment]


class _SlothySys(SysBase):
    # This is hell ;)
    __meta_path__: MetaPath = meta_path
    _slothy_metapaths: ClassVar[dict[str, MetaPath]] = {}

    @property
    def meta_path(self) -> MetaPath:
        module_name = None
        for frame_info in stack()[1:]:
            if frame_info.code_context is None:
                continue
            frame_locals = frame_info.frame.f_locals
            module_name = frame_locals.get("__name__")
            if not frame_locals.get("__slothy_skip_frame__"):
                break
            if module_name is not None and module_name in slothy_importing:
                break
        if module_name is None or module_name not in slothy_importing:
            return self.__meta_path__
        return self._slothy_metapaths.get(module_name, self.__meta_path__)

    @meta_path.setter
    def meta_path(self, value: MetaPath) -> None:
        module_name = None
        for frame_info in stack()[1:]:
            if frame_info.code_context is None:
                continue
            frame_locals = frame_info.frame.f_locals
            module_name = frame_locals.get("__name__")
            if not frame_locals.get("__slothy_skip_frame__"):
                break
            if module_name is not None and module_name in slothy_importing:
                break
        if value is _OLD_META_PATH:
            if module_name is not None:
                self._slothy_metapaths.pop(module_name, None)
                return
            value = self.__meta_path__
        if module_name is None or module_name not in slothy_importing:
            self.__meta_path__ = value
            return
        self._slothy_metapaths[module_name] = value


sys.__class__ = _SlothySys


class SlothyImporter(Loader, MetaPathFinder):
    """An importer used by the [slothy context manager][slothy.api.SlothyContext]."""

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
        # (`sys.meta_path`) is a dynamic property that examines `slothy_module`.
        if not isinstance(sys, _SlothySys) or self._enabled:
            return
        self._enabled = True
        before_enable(self)
        slothy_importing.add(self.module_name)
        __slothy_skip_frame__ = True  # noqa: F841
        sys.meta_path = [self]
        after_enable(self)

    def disable(self) -> None:
        """Remove lazy importer from meta path."""
        # Bring back the same instance of sys.meta_path.
        if not (isinstance(sys, _SlothySys) and self._enabled):
            return
        before_disable(self)
        sys.meta_path = _OLD_META_PATH
        slothy_importing.discard(self.module_name)
        after_disable(self)

    def create_module(self, spec: ModuleSpec) -> ModuleType:
        """Create a module."""
        slothy_object = SlothyObject()
        on_create_module(self, spec, slothy_object)
        return cast("ModuleType", slothy_object)

    def exec_module(self, module: Any) -> None:
        """Raise an auditing event and return immediately."""
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
