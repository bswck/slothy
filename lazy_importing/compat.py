"""`lazy_importing.compat`: Compatibility layers for lazy_importing."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from typing_extensions import ParamSpec, TypeVar

    P = ParamSpec("P")
    R = TypeVar("R")


def accesses_lazy_objects(f: Callable[P, R]) -> Callable[P, R]:
    """
    Decorate a function for CPython 3.8 and 3.9 compatibility with lazy importing.

    Its sole purpose is to create an additional external frame before a function
    is called. That ensures the [lazy object loader](lazy_importing.cm.LazyObjectLoader)
    is requested a missing identifier after the function is.
    """

    def wrapper(*args: P.args, **kwargs: R.kwargs) -> R:
        return f(*args, **kwargs)

    return wrapper
