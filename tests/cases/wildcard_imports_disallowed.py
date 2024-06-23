from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from slothy import lazy_importing

if TYPE_CHECKING:
    from pytest_subtests import SubTests

    subtests: SubTests


with lazy_importing(prevent_eager=False), subtests.test(
    "wildcard-imports-disallowed"
), pytest.raises(RuntimeError, match="Wildcard slothy imports are not supported"):
    from whatever import *  # type: ignore[import-not-found]  # noqa: F403
