"""
Abstract base classes & type aliases for implementing lazy importing strategies.

Provides a modest framework that facilitates communication with the core
[lazy importing context manager][lazy_importing.ctx.LazyImportingContextManager].
"""

from __future__ import annotations

import sys
from abc import ABCMeta, abstractmethod
from contextvars import ContextVar
from threading import RLock
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contextvars import Context
    from sys import _MetaPathFinder
    from typing import Any

    from typing_extensions import TypeAlias

    LazyObjectMapping: TypeAlias = "dict[str, LazyObject]"
    MetaPath: TypeAlias = "list[_MetaPathFinder]"


importing: ContextVar[bool] = ContextVar("is_importing", default=False)
lazy_loading: ContextVar[bool] = ContextVar("is_loading", default=False)
old_meta_path: ContextVar[MetaPath] = ContextVar("old_meta_path")


class LazyObject(metaclass=ABCMeta):
    """An object imported lazily."""

    def bind(
        self,
        final: Any,
        local_ns: dict[str, object],
        lazy_objects: dict[str, LazyObject],
    ) -> None:
        """Automatically replace all references to lazy objects with self."""
        for ref, other in lazy_objects.items():
            if other is self:
                local_ns[ref] = final

    @abstractmethod
    def load(self) -> Any:
        """Load the object."""


class LazyImportingStrategy(metaclass=ABCMeta):
    """A strategy for lazy importing."""

    context: Context
    _lock = RLock()
    old_meta_path: MetaPath

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
        self.old_meta_path = meta_path
        self.finder = self.create_finder()
        self.new_meta_path = [self.finder]
        context.run(old_meta_path.set, self.old_meta_path)

    def enable(self) -> None:
        """Delegate processing all import finder requests into the lazy importer."""
        self._lock.acquire()
        # Important:
        # We don't clear the original list not to break imports based on
        # the old sys.meta_path object. Instead, we overwrite with a new list.
        sys.meta_path = self.new_meta_path

    def disable(self) -> None:
        """Remove lazy importer from meta path."""
        # Bring back the same instance of sys.meta_path.
        sys.meta_path = self.old_meta_path
        self._lock.release()

    def create_finder(self) -> _MetaPathFinder:
        """Create a meta path finder for this strategy."""
        raise NotImplementedError
