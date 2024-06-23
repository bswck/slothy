# tests for eager importing prevention
from __future__ import annotations

from contextlib import nullcontext
from typing import TYPE_CHECKING

import pytest

from slothy import lazy_importing, lazy_importing_if, type_importing

if TYPE_CHECKING:
    from pytest_subtests import SubTests

    supported: bool
    subtests: SubTests

for cm in (
    lambda: lazy_importing(prevent_eager=True),
    lambda: lazy_importing_if(True, prevent_eager=True),
    lambda: type_importing(),
):
    with subtests.test("prevents-eager"), (
        nullcontext()
        if supported
        else pytest.raises(
            RuntimeError,
            match="cannot default to eager mode",
        )
    ), cm():  # type: ignore[no-untyped-call]
        pass

for cm in (
    lambda: lazy_importing(prevent_eager=False),
    lambda: lazy_importing_if(False, prevent_eager=True),
    lambda: lazy_importing_if(True, prevent_eager=False),
):
    with subtests.test("no-prevent-eager"), cm():  # type: ignore[no-untyped-call]
        # Should never fail.
        pass
