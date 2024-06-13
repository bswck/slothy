from __future__ import annotations

import runpy
import sys
import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_subtests import SubTests


def _force_reload(module_names: tuple[str, ...] = ("slothy", "slothy._impl")) -> None:
    for module_name in module_names:
        sys.modules.pop(module_name, None)


if hasattr(sys, "_getframe"):

    def test_supported_impl(subtests: SubTests) -> None:
        _force_reload()
        runpy.run_path(
            "tests/tests.py",
            run_name="tests",
            init_globals={"subtests": subtests},
        )


def test_unsupported_impl(subtests: SubTests) -> None:
    _force_reload()
    getframe = sys._getframe
    del sys._getframe
    runpy.run_path(
        "tests/tests.py",
        run_name="tests",
        init_globals={"subtests": subtests},
    )
    sys._getframe = getframe


def test_slothy_no_warn() -> None:
    _force_reload()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
