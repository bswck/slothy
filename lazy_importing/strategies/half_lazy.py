"""
Pure Python half-lazy importing.

Eagerly find & lazily load modules.
https://peps.python.org/pep-0690/#half-lazy-imports
"""

# ruff: noqa: FBT003
from __future__ import annotations

import sys
import types
from dataclasses import dataclass
from importlib._bootstrap import _find_spec  # type: ignore[import-not-found]
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec
from importlib.util import LazyLoader
from typing import TYPE_CHECKING, cast

from lazy_importing.abc import (
    LazyImportingStrategy,
    LazyObject,
    importing,
    lazy_loading,
)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from contextvars import Context
    from importlib.abc import Loader
    from typing import Any

    from typing_extensions import Self


__all__ = (
    "HalfLazyImportingStrategy",
    "HalfLazyObject",
    "HalfLazyModule",
    "HalfLazyLoader",
)


@dataclass(frozen=True)
class HalfLazyObject(LazyObject):
    """Tracks lazy loading."""

    module: types.ModuleType
    attribute_name: str

    def load(self) -> Any:
        """Load this item."""
        return getattr(self.module, self.attribute_name)


def _lazy_getattr(self: HalfLazyModule, attr: str) -> Any:
    if importing.get():
        return HalfLazyObject(self, attr)
    lazy_loading.set(True)
    self.__class__ = self.__lazy_module_class__  # type: ignore[assignment]
    try:
        return self.__getattribute__(attr)
    finally:
        lazy_loading.set(False)
        self.__class__ = types.ModuleType  # type: ignore[assignment]


class HalfLazyModule(types.ModuleType):
    """A subclass of the module type which triggers loading upon attribute access."""

    __context__: Context
    __lazy_module_class__: type[types.ModuleType]

    def __getattribute__(self, attr: str) -> Any:
        """Trigger the load of the module and return the attribute."""
        try:
            obj = object.__getattribute__(self, attr)
        except AttributeError:
            context = object.__getattribute__(self, "__context__")
            obj = context.run(_lazy_getattr, self, attr)
        return obj

    def __delattr__(self, attr: str) -> None:
        """Trigger the load and then perform the deletion."""
        context = object.__getattribute__(self, "__context__")
        if not context.get(importing):
            _delattr = context.run(_lazy_getattr, self, "__delattr__")
            _delattr(attr)


class HalfLazyLoader(LazyLoader):
    """
    Subclass of [`importlib.util.LazyLoader`][importlib.util.LazyLoader].

    Allows the [`LAZY_IMPORTING`][lazy_importing.LAZY_IMPORTING]
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
        self._context = context

    def exec_module(self, module: types.ModuleType) -> None:
        """
        Execute the module.

        This method is overridden to set the context of the module.
        """
        super().exec_module(module)
        lazy_module_class = object.__getattribute__(module, "__class__")
        module.__class__ = HalfLazyModule
        module = cast(HalfLazyModule, module)
        module.__context__ = self._context
        module.__lazy_module_class__ = lazy_module_class


class HalfLazyImportingStrategy(LazyImportingStrategy, MetaPathFinder):
    """A meta path finder that enables half-lazy importing."""

    def create_finder(self) -> Self:
        """Return self."""
        return self

    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None = None,
        target: types.ModuleType | None = None,
    ) -> ModuleSpec | None:
        """Find the actual spec and preserve it for loading it lazily later."""
        sys.meta_path = self.old_meta_path
        spec: ModuleSpec | None = None
        try:
            spec = _find_spec(fullname, path, target)
        finally:
            sys.meta_path = [self]
        if spec is None or (loader := spec.loader) is None:
            return None
        lazy_loader = HalfLazyLoader(loader, self.context)
        lazy_spec = ModuleSpec(fullname, None)
        vars(lazy_spec).update(vars(spec))
        lazy_spec.__lazy_spec__ = True  # type: ignore[attr-defined]  # for testing
        lazy_spec.loader = lazy_loader
        return lazy_spec
