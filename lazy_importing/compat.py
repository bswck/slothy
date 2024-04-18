"""`lazy_importing.compat`: Compatibility layers for lazy_importing."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from typing_extensions import ParamSpec, TypeVar

    P = ParamSpec("P")
    R = TypeVar("R")


__all__ = ("supports_lazy_access",)


def supports_lazy_access(f: Callable[P, R]) -> Callable[P, R]:
    """
    Decorate a function for CPython 3.8 and 3.9 compatibility with lazy importing.

    The sole purpose of this function is to create an additional external frame
    before the decorated function `f` is called. This ensures that
    the [lazy object loader](lazy_importing.cm.LazyObjectLoader)
    is requested a missing identifier during the function being called.
    """

    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return f(*args, **kwargs)

    return wrapper
