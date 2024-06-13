"""Slothy's exported functionality."""

from __future__ import annotations

import sys
from os import getenv

__all__ = ("SLOTHY_ENABLED", "slothy", "slothy_if")

try:
    sys._getframe  # noqa: B018, SLF001
except AttributeError:
    SLOTHY_ENABLED = False
    """Whether slothy is enabled."""
else:
    SLOTHY_ENABLED = not getenv("SLOTHY_DISABLE")

if SLOTHY_ENABLED:
    from slothy._impl import slothy, slothy_if
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

    @contextmanager
    def slothy(stack_offset: int = 2) -> Iterator[None]:  # noqa: ARG001
        """Replace slothy with a no-op on unsupported platforms."""
        yield

    def slothy_if(
        condition: object,  # noqa: ARG001
        stack_offset: int = 3,  # noqa: ARG001
    ) -> AbstractContextManager[None]:
        """Replace slothy with a no-op on unsupported platforms."""
        return nullcontext()
