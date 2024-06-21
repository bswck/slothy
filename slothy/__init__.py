"""Slothy's exported functionality."""

from __future__ import annotations

import sys
from os import getenv
from typing import TYPE_CHECKING, Any
from warnings import warn

__all__ = (
    "SLOTHY_ENABLED",
    "lazy_importing",
    "lazy_importing_if",
    "type_importing",
)

SLOTHY_ENABLED: bool
"""Whether slothy is enabled."""

try:
    sys._getframe  # noqa: B018, SLF001
except AttributeError:  # pragma: no cover
    SLOTHY_ENABLED = False
else:
    SLOTHY_ENABLED = not getenv("SLOTHY_DISABLE")

if SLOTHY_ENABLED:
    from slothy._importing import lazy_importing, lazy_importing_if, type_importing
else:
    from contextlib import contextmanager, nullcontext

    if TYPE_CHECKING:
        from collections.abc import Iterator
        from contextlib import AbstractContextManager

    if not getenv("SLOTHY_NO_WARN"):
        warn(
            category=RuntimeWarning,
            message=(
                "This Python implementation does not support "
                "`sys._getframe()` and thus cannot use `lazy_importing`. "
            ),
            stacklevel=1,
        )

    EAGER_PREVENTION_MSG = (
        "Unsupported Python implementation: "
        "slothy imports cannot default to eager mode"
    )

    @contextmanager
    def lazy_importing(
        *,
        prevent_eager: bool = True,
        stack_offset: int = 1,  # noqa: ARG001
    ) -> Iterator[None]:
        """Replace slothy with a no-op on unsupported Python implementation."""
        if prevent_eager:
            raise RuntimeError(EAGER_PREVENTION_MSG)
        yield

    @contextmanager
    def type_importing(
        *,
        default_type: object = Any,  # noqa: ARG001
        stack_offset: int = 1,  # noqa: ARG001
    ) -> Iterator[None]:
        """Fail immediately on unsupported Python implementation."""
        raise RuntimeError(EAGER_PREVENTION_MSG)
        yield

    def lazy_importing_if(
        condition: object,
        *,
        prevent_eager: bool = True,
        stack_offset: int = 1,  # noqa: ARG001
    ) -> AbstractContextManager[None]:
        """Replace slothy with a no-op on unsupported Python implementation."""
        if condition and prevent_eager:
            raise RuntimeError(EAGER_PREVENTION_MSG)
        return nullcontext()


_SI_MSG = "Use `lazy_importing` instead"
_SII_MSG = "Use `lazy_importing_if` instead"


def __getattr__(attr: str) -> object:
    if attr == "slothy_importing":
        warn(_SI_MSG, category=DeprecationWarning, stacklevel=2)
        return lazy_importing

    if attr == "slothy_importing_if":
        warn(_SII_MSG, category=DeprecationWarning, stacklevel=2)
        return lazy_importing_if

    raise AttributeError(attr)


if TYPE_CHECKING:
    from typing_extensions import deprecated

    @deprecated(_SI_MSG)
    def slothy_importing(*args: Any, **kwargs: Any) -> Any:
        return lazy_importing(*args, **kwargs)

    @deprecated(_SII_MSG)
    def slothy_importing_if(*args: Any, **kwargs: Any) -> Any:
        return lazy_importing_if(*args, **kwargs)
