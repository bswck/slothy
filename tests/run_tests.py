from __future__ import annotations

import os
import runpy
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_subtests import SubTests


def _force_reload(
    module_names: tuple[str, ...] = ("slothy", "slothy._importing"),
) -> None:
    for module_name in module_names:
        sys.modules.pop(module_name, None)


def test_unsupported_implementation(subtests: SubTests) -> None:
    _force_reload()
    os.environ["SLOTHY_DISABLE"] = "1"  # Do disable.
    ns = runpy.run_path(
        "tests/tests.py",
        run_name="tests",
        init_globals={"subtests": subtests, "supported_implementation": False},
    )
    module_entries = ns["expected_module_entries"]
    _force_reload(module_entries)


if hasattr(sys, "_getframe"):

    def test_supported_implementation(subtests: SubTests) -> None:
        _force_reload()
        os.environ["SLOTHY_DISABLE"] = ""  # Don't disable.
        ns = runpy.run_path(
            "tests/tests.py",
            run_name="tests",
            init_globals={"subtests": subtests, "supported_implementation": True},
        )
        module_entries = ns["expected_module_entries"]
        _force_reload(module_entries)
