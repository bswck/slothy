from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from slothy import lazy_importing

if TYPE_CHECKING:
    from pytest_subtests import SubTests

    subtests: SubTests


with subtests.test("test-class-scope"), pytest.raises(
    RuntimeError,
    match="__set_name__",
), lazy_importing():

    class _ClassScope:
        from whatever_else import anything  # type: ignore[import-not-found]
