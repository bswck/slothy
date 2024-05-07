# SPDX-License-Identifier: MIT
# (C) 2024-present Bartosz Sławecki (bswck)
"""Super-easy lazy importing in Python."""
# ruff: noqa: F403, PLE0604

from __future__ import annotations

from functools import wraps
from sys import version_info
from typing import TYPE_CHECKING

from slothy import api, audits, placeholder
from slothy.api import *
from slothy.audits import *
from slothy.placeholder import *

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from typing_extensions import ParamSpec, TypeVar

    P = ParamSpec("P")
    R = TypeVar("R")


__all__ = (
    "api",
    *api.__all__,
    *audits.__all__,
    *placeholder.__all__,
)

SLOTHY: api.SlothyContext


def __dir__() -> tuple[str, ...]:
    return ("SLOTHY", *__all__)


def __getattr__(name: str) -> Any:
    if name == "SLOTHY":
        return api.SlothyContext(stack_offset=2)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


def supports_slothy(f: Callable[P, R]) -> Callable[P, R]:
    """
    Decorate a function for CPython 3.8 and 3.9 compatibility with lazy importing.

    The sole purpose of this function is to create an additional external frame
    before the decorated function `f` is called. This ensures that
    the [lazy object loader][slothy.api.LazyObjectLoader]
    is requested a missing identifier during the function being called.
    """
    if version_info < (3, 10):

        @wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            __tracebackhide__ = True
            return f(*args, **kwargs)

        return wrapper

    return f
