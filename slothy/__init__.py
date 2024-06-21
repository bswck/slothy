"""Slothy's exported functionality."""

from __future__ import annotations

import sys
from os import getenv

__all__ = (
    "SLOTHY_ENABLED",
    "slothy_importing",
    "slothy_importing_if",
    "lazy_importing",
    "lazy_importing_if",
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
    from slothy._importing import slothy_importing, slothy_importing_if
else:
    from contextlib import contextmanager, nullcontext
    from typing import TYPE_CHECKING
    from warnings import warn

    if TYPE_CHECKING:
        from collections.abc import Iterator
        from contextlib import AbstractContextManager

    if not getenv("SLOTHY_NO_WARN"):
        warn(
            category=RuntimeWarning,
            message=(
                "This Python implementation does not support "
                "`sys._getframe()` and thus cannot use `slothy_importing`. "
            ),
            stacklevel=1,
        )

    EAGER_PREVENTION_MSG = (
        "Unsupported Python implementation: "
        "slothy imports cannot default to eager mode"
    )

    @contextmanager
    def slothy_importing(
        *,
        prevent_eager: bool = True,
        stack_offset: int = 1,  # noqa: ARG001
    ) -> Iterator[None]:
        """Replace slothy with a no-op on unsupported Python implementation."""
        if prevent_eager:
            raise RuntimeError(EAGER_PREVENTION_MSG)
        yield

    def slothy_importing_if(
        condition: object,
        *,
        prevent_eager: bool = True,
        stack_offset: int = 1,  # noqa: ARG001
    ) -> AbstractContextManager[None]:
        """Replace slothy with a no-op on unsupported Python implementation."""
        if condition and prevent_eager:
            raise RuntimeError(EAGER_PREVENTION_MSG)
        return nullcontext()


lazy_importing = slothy_importing
lazy_importing_if = slothy_importing_if
