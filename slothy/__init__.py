"""Slothy's exported functionality."""

from __future__ import annotations

import sys
from os import getenv

__all__ = ("SLOTHY_ENABLED", "slothy", "slothy_if", "lazy_importing")

SLOTHY_ENABLED: bool
"""Whether slothy is enabled."""

try:
    sys._getframe  # noqa: B018, SLF001
except AttributeError:
    SLOTHY_ENABLED = False
else:
    SLOTHY_ENABLED = not getenv("SLOTHY_DISABLE")

if SLOTHY_ENABLED:
    from slothy._impl import slothy, slothy_if

    lazy_importing = slothy  # Readability alias.
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
                "`sys._getframe()` and thus cannot use `slothy`. "
            ),
            stacklevel=1,
        )

    EAGER_PREVENTION_MSG = (
        "Unsupported Python implementation: "
        "slothy imports cannot default to eager mode"
    )

    @contextmanager
    def slothy(
        *,
        prevent_eager: bool = False,
        stack_offset: int = 2,  # noqa: ARG001
    ) -> Iterator[None]:
        """Replace slothy with a no-op on unsupported Python implementation."""
        if prevent_eager:
            raise RuntimeError(EAGER_PREVENTION_MSG)
        yield

    def slothy_if(
        condition: object,  # noqa: ARG001
        *,
        prevent_eager: bool = False,
        stack_offset: int = 3,  # noqa: ARG001
    ) -> AbstractContextManager[None]:
        """Replace slothy with a no-op on unsupported Python implementation."""
        if prevent_eager:
            raise RuntimeError(EAGER_PREVENTION_MSG)
        return nullcontext()

    lazy_importing = slothy
