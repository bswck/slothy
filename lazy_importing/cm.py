"""`lazy_importing.cm`: A context manager that enables lazy importing."""
# ruff: noqa: FBT003

from __future__ import annotations

from contextvars import copy_context
from sys import _getframe as getframe
from typing import TYPE_CHECKING

from lazy_importing.importer import (
    LazilyLoadedObject,
    LazyImporter,
    lazy_loading,
)

if TYPE_CHECKING:
    from typing import Any

    from typing_extensions import Self, TypeAlias

    from lazy_importing.importer import MetaPath

    LazyObjectMapping: TypeAlias = "dict[str, LazilyLoadedObject]"


__all__ = ("LazyImporting",)

_MISSING_EXC_INFO = (None, None, None)


class LazyObjectLoader(dict):  # type: ignore[type-arg]
    __slots__ = ("__lazy_objects__", "__local_ns__")
    __local_ns__: dict[str, object]
    __lazy_objects__: LazyObjectMapping

    def __getitem__(self, key: Any) -> Any:
        try:
            return super().__getitem__(key)
        except KeyError:
            try:
                lazy_obj = self.__lazy_objects__[key]
            except KeyError:
                raise NameError(key) from None
            all_refs = {
                ref
                for ref, other_lazy_obj in self.__lazy_objects__.items()
                if other_lazy_obj is lazy_obj
            }
            obj = lazy_obj.load()
            for ref in all_refs:
                self.__local_ns__[ref] = obj  # auto binding
            return obj


class LazyImporting:
    """A context manager that enables lazy importing."""

    _lazy_objects: LazyObjectMapping

    def __init__(
        self,
        *,
        meta_path: MetaPath | None = None,
        local_ns: dict[str, object] | None = None,
        global_ns: dict[str, object] | None = None,
        stack_offset: int = 1,
    ) -> None:
        """Initialize a new LazyImporting instance."""
        self._context = copy_context()
        self._local_ns = local_ns or getframe(stack_offset).f_locals
        self._global_ns = global_ns or getframe(stack_offset).f_globals
        self._entrance_locals = set(self._local_ns)
        self._lazy_objects = {}
        self._lazy_importer = self._context.run(LazyImporter, self._context, meta_path)
        self._exited = False

    def _cleanup_identifiers(self) -> None:
        for identifier, lazy_object in self._local_ns.copy().items():
            if identifier in self._entrance_locals or not isinstance(
                lazy_object, LazilyLoadedObject
            ):
                continue
            try:
                del self._local_ns[identifier]
            except KeyError:
                # Don't provide this object since it was deleted
                # from the user's namespace.
                pass
            else:
                self._lazy_objects[identifier] = lazy_object

    def _inject_loader(self) -> None:
        builtins = self._local_ns.get("__builtins__")
        if builtins is None:
            builtins = self._global_ns.get("__builtins__")
        if not isinstance(builtins, dict):
            builtins = vars(builtins)
        lazy_object_loader = LazyObjectLoader(builtins)
        lazy_object_loader.__local_ns__ = self._local_ns
        lazy_object_loader.__lazy_objects__ = self._lazy_objects
        self._local_ns["__builtins__"] = lazy_object_loader

    def __enter__(self) -> Self:
        """Enable lazy importing mode."""
        if self._exited:
            msg = "Cannot enter LazyImporting context twice"
            raise RuntimeError(msg)
        self._context.run(lazy_loading.set, True)
        self._lazy_importer.acquire_meta_path()
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Disable lazy importing mode."""
        self._exited = True
        self._lazy_importer.release_meta_path()
        self._context.run(lazy_loading.set, False)
        self._cleanup_identifiers()
        if exc_info == _MISSING_EXC_INFO:
            self._inject_loader()
