"""`lazy_importing.importer`: An importer that carries out lazy importing globally."""

from __future__ import annotations

import sys
import types
from contextvars import Context, ContextVar
from dataclasses import dataclass, field
from importlib._bootstrap import _find_spec  # type: ignore[import-not-found]
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec
from importlib.util import LazyLoader
from threading import RLock
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from collections.abc import Sequence
    from importlib.abc import Loader
    from sys import _MetaPathFinder
    from typing import Any

    from typing_extensions import TypeAlias

    MetaPath: TypeAlias = "list[_MetaPathFinder]"

__all__ = ("LazyImporter",)


old_meta_path: ContextVar[MetaPath | None] = ContextVar("old_meta_path", default=None)
lazy_loading: ContextVar[bool] = ContextVar("lazy_loading", default=False)
lazy_objects: ContextVar[dict[str, LazilyLoadedObject]] = ContextVar("lazy_objects")


@dataclass(frozen=True)
class LazilyLoadedObject:
    """Tracks lazy loading."""

    module: types.ModuleType = field(hash=False, repr=False)
    identifier: str
    context: Context = field(hash=False, repr=False)

    def __post_init__(self) -> None:
        """Attach self to the registry of objects watched by the context manager."""
        try:
            objects = self.context.run(lazy_objects.get)
        except LookupError:
            self.context.run(lazy_objects.set, objects := {})
        objects.update({self.identifier: self})

    def load(self) -> Any:
        """Load this item."""
        return getattr(self.module, self.identifier)


class LazyModuleWrapper(types.ModuleType):
    """A subclass of the module type which triggers loading upon attribute access."""

    __context__: Context
    __lazy_module_class__: type[types.ModuleType]

    def __getattribute__(self, attr: str) -> Any:
        """Trigger the load of the module and return the attribute."""
        try:
            return object.__getattribute__(self, attr)
        except AttributeError:
            context = self.__context__
            if context.get(lazy_loading):
                return LazilyLoadedObject(self, attr, context)
            self.__class__ = self.__lazy_module_class__  # type: ignore[assignment]
            try:
                return self.__getattribute__(attr)
            finally:
                self.__class__ = LazyModuleWrapper

    def __delattr__(self, attr: str) -> None:
        """Trigger the load and then perform the deletion."""
        self.__lazy_module_class__.__delattr__(self, attr)


class LazyLoaderWrapper(LazyLoader):
    """
    Subclass of [`importlib.util.LazyLoader`](importlib.util.LazyLoader).

    Allows the [`LAZY_IMPORTING`](lazy_importing.LAZY_IMPORTING)
    context manager to resolve the objects to load lazily.
    """

    def __init__(self, loader: Loader, context: Context) -> None:
        """
        Create a lazy loader.

        Parameters
        ----------
        loader
            The loader to wrap.

        context
            The context in which the loader should operate.

        """
        super().__init__(loader)
        self.context = context

    def exec_module(self, module: types.ModuleType) -> None:
        """
        Execute the module.

        This method is overridden to set the context of the module.
        """
        super().exec_module(module)
        lazy_module_class = object.__getattribute__(module, "__class__")
        module.__class__ = LazyModuleWrapper
        module = cast(LazyModuleWrapper, module)
        module.__context__ = self.context
        module.__lazy_module_class__ = lazy_module_class


class LazyImporter(MetaPathFinder):
    """Importer that carries out lazy importing globally."""

    _context: Context
    _lock = RLock()

    def __init__(
        self,
        context: Context,
        meta_path: MetaPath | None = None,
    ) -> None:
        """
        Create a lazy importer.

        Parameters
        ----------
        context
            The context in which the importer should operate.

        meta_path : optional
            The meta path to use for lazy importing. Defaults to the meta path
            known to the least recently created
            [`LazyImporting`](lazy_importing.cm.LazyImporting) context manager
            that initiated the call chain of consecutive imports.

        """
        self._context = context
        self._old_meta_path = (
            meta_path or context.get(old_meta_path) or sys.meta_path.copy()
        )
        old_meta_path.set(self._old_meta_path)

    def acquire_meta_path(self) -> None:
        """Delegate processing all import finder requests into the lazy importer."""
        self._lock.acquire()
        sys.meta_path = [self]

    def release_meta_path(self) -> None:
        """Remove lazy importer from meta path."""
        sys.meta_path = self._old_meta_path
        self._lock.release()

    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None = None,
        target: types.ModuleType | None = None,
    ) -> ModuleSpec | None:
        """Find the actual spec and preserve it for loading it lazily later."""
        sys.meta_path = self._old_meta_path
        spec: ModuleSpec | None = None
        try:
            spec = _find_spec(fullname, path, target)
        finally:
            sys.meta_path = [self]
        if spec is None or (loader := spec.loader) is None:
            return None
        lazy_loader = LazyLoaderWrapper(loader, self._context)
        lazy_spec = ModuleSpec(fullname, None)
        vars(lazy_spec).update(vars(spec))
        lazy_spec.loader = lazy_loader
        return lazy_spec
