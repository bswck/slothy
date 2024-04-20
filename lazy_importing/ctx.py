"""
Context & state management.

Temporarily enable a preferred lazy importing mode.
"""
# ruff: noqa: FBT003

from __future__ import annotations

from contextlib import suppress
from contextvars import copy_context
from sys import _getframe as getframe
from typing import TYPE_CHECKING

from lazy_importing.abc import LazyObject, importing

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, ClassVar

    from typing_extensions import Self

    from lazy_importing.abc import LazyImportingStrategy, LazyObjectMapping, MetaPath


__all__ = ("LazyImportingContextManager",)

_MISSING_EXC_INFO = (None, None, None)


class LazyObjectLoader(dict):  # type: ignore[type-arg]
    """Substitute for `__builtins__` to provide lazy objects on first reference."""

    __slots__ = ("lazy_objects", "local_ns")

    attribute: ClassVar[str] = "__builtins__"
    local_ns: dict[str, object]
    lazy_objects: LazyObjectMapping

    def __getitem__(self, key: Any) -> Any:
        try:
            return super().__getitem__(key)
        except KeyError:
            try:
                lazy_object = self.lazy_objects[key]
            except KeyError:
                raise NameError(key) from None
            final_object = lazy_object.load()
            lazy_object.bind(final_object, self.local_ns, self.lazy_objects)
            return final_object


class LazyImportingContextManager:
    """A context manager that enables lazy importing."""

    _lazy_objects: LazyObjectMapping
    _object_loader_class: type[LazyObjectLoader]

    def __init__(  # noqa: PLR0913
        self,
        *,
        strategy_factory: Callable[..., LazyImportingStrategy],
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
        strategy_factory
            The strategy to use.
        meta_path
            The meta path to use.
        local_ns
            The local namespace to use.
        global_ns
            The global namespace to use.
        object_loader_class
            The loader factory to use.
        stack_offset
            The stack offset to use.

        """
        if object_loader_class is None:
            object_loader_class = LazyObjectLoader
        self._object_loader_class = object_loader_class
        self._lazy_objects = {}
        self.context = copy_context()
        frame = getframe(stack_offset)
        self._local_ns = local_ns or frame.f_locals
        self._global_ns = global_ns or frame.f_globals
        self._initial_locals = set(self._local_ns)
        self.strategy = strategy_factory(self.context, meta_path)
        self._exited = False

    def __enter__(self) -> Self:
        """Enable lazy importing mode."""
        if self._exited:
            msg = "Cannot enter the same lazy importing context twice."
            raise RuntimeError(msg)
        self.context.run(importing.set, True)
        self.strategy.enable()
        return self

    def _cleanup_identifiers(self) -> None:
        for identifier, lazy_object in self._local_ns.copy().items():
            if not isinstance(lazy_object, LazyObject):
                continue
            with suppress(KeyError):
                del self._local_ns[identifier]
                self._lazy_objects[identifier] = lazy_object

    def _inject_loader(self) -> None:
        loader_attribute = self._object_loader_class.attribute
        builtins = self._local_ns.get(loader_attribute)
        if builtins is None:
            builtins = self._global_ns[loader_attribute]
        if not isinstance(builtins, dict):
            builtins = vars(builtins)
        lazy_object_loader = self._object_loader_class(builtins)
        lazy_object_loader.local_ns = self._local_ns
        lazy_object_loader.lazy_objects = self._lazy_objects
        self._local_ns[loader_attribute] = lazy_object_loader

    def __exit__(self, *exc_info: object) -> None:
        """Disable lazy importing mode."""
        self._exited = True
        self.strategy.disable()
        self.context.run(importing.set, False)
        self._cleanup_identifiers()
        if exc_info == _MISSING_EXC_INFO:
            self._inject_loader()
