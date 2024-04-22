from __future__ import annotations

import runpy

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_subtests import SubTests


def test_main(subtests: SubTests) -> None:
    runpy.run_path("tests/tests.py", init_globals={"subtests": subtests})
