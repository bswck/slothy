from __future__ import annotations

import os
import re
import runpy
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_subtests import SubTests

# If that fails, something's wrong in test collection stage.
# Ensure that pytest collection doesn't trigger importing slothy.
assert not any(map(re.compile("slothy").search, sys.modules))

initial_modules = sys.modules.copy()


def purge_modules() -> None:
    sys.modules.clear()
    sys.modules.update(initial_modules)


def test_unsupported_implementation(subtests: SubTests) -> None:
    os.environ["SLOTHY_DISABLE"] = "1"  # Do disable.
    runpy.run_path(
        "tests/tests.py",
        run_name="tests",
        init_globals={"subtests": subtests, "supported_implementation": False},
    )
    purge_modules()


if hasattr(sys, "_getframe"):

    def test_supported_implementation(subtests: SubTests) -> None:
        os.environ["SLOTHY_DISABLE"] = ""  # Don't disable.
        runpy.run_path(
            "tests/tests.py",
            run_name="tests",
            init_globals={"subtests": subtests, "supported_implementation": True},
        )
        purge_modules()
