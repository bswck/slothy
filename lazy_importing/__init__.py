# SPDX-License-Identifier: MIT
# (C) 2024-present Bartosz Sławecki (bswck)
"""
`lazy_importing`.

Super-easy lazy importing in Python.
"""
# ruff: noqa: F403, PLE0604

from __future__ import annotations

from typing import TYPE_CHECKING

from lazy_importing import ctx, strategies
from lazy_importing.ctx import *
from lazy_importing.strategies import *

if TYPE_CHECKING:
    from collections.abc import Callable

    from typing_extensions import ParamSpec, TypeVar

    P = ParamSpec("P")
    R = TypeVar("R")


__all__ = (
    "ctx",
    "strategies",
    *ctx.__all__,
    *strategies.__all__,
)


LAZY_IMPORTING: ctx.LazyImportingContextManager


def __dir__() -> tuple[str, ...]:
    return (*__all__, "LAZY_IMPORTING")


def __getattr__(name: str) -> object:
    if name == "LAZY_IMPORTING":
        from lazy_importing.strategies.half_lazy import HalfLazyImportingStrategy

        return ctx.LazyImportingContextManager(
            strategy=HalfLazyImportingStrategy,
            stack_offset=2,
        )
    raise AttributeError


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
