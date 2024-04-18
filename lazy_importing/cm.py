"""`lazy_importing.cm`: A context manager that enables lazy importing."""
# ruff: noqa: FBT003

from __future__ import annotations

from contextvars import copy_context
from sys import _getframe as getframe
from typing import TYPE_CHECKING

from lazy_importing.importer import LazyImporter, lazy_loading, lazy_objects

if TYPE_CHECKING:
    from contextvars import Context
    from typing import Any

    from typing_extensions import Self

    from lazy_importing.importer import MetaPath


__all__ = ("LazyImporting",)

_MISSING_EXC_INFO = (None, None, None)


class LazyObjectLoader(dict):  # type: ignore[type-arg]
    __slots__ = ("__context__",)
    __context__: Context

    def __getitem__(self, key: Any) -> Any:
        try:
            return super().__getitem__(key)
        except KeyError:
            objects = self.__context__.run(lazy_objects.get)
            try:
                lazy_obj = objects[key]
            except KeyError:
                raise NameError(key) from None
            else:
                return lazy_obj.load()


class LazyImporting:
    """A context manager that enables lazy importing."""

    def __init__(
        self,
        *,
        meta_path: MetaPath | None = None,
        namespace: dict[str, object] | None = None,
        stack_offset: int = 1,
    ) -> None:
        """Initialize a new LazyImporting instance."""
        self._context = copy_context()
        self._namespace = namespace or getframe(stack_offset).f_locals
        self._lazy_importer = self._context.run(LazyImporter, self._context, meta_path)

    def _cleanup_identifiers(self) -> None:
        try:
            objects = self._context.run(lazy_objects.get)
        except LookupError:
            return
        for identifier in objects.copy():
            try:
                del self._namespace[identifier]
            except KeyError:  # noqa: PERF203
                # Don't provide this object since it was deleted.
                del objects[identifier]

    def _inject_loader(self) -> None:
        builtins = self._namespace["__builtins__"]
        provider = LazyObjectLoader(vars(builtins))
        provider.__context__ = self._context
        self._namespace["__builtins__"] = provider

    def __enter__(self) -> Self:
        """Enable lazy importing mode."""
        self._context.run(lazy_loading.set, True)
        self._lazy_importer.acquire_meta_path()
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Disable lazy importing mode."""
        self._lazy_importer.release_meta_path()
        self._context.run(lazy_loading.set, False)
        self._cleanup_identifiers()
        if exc_info == _MISSING_EXC_INFO:
            self._inject_loader()
