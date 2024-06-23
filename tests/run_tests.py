from __future__ import annotations

import gc
import os
import platform
import re
import runpy
import sys
from collections import defaultdict
from contextlib import contextmanager
from contextvars import Context, copy_context
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple
from weakref import WeakSet

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pytest_subtests import SubTests

CASES_DIR: Path = Path("tests/cases/")

# If that fails, something's wrong in test collection stage.
# Ensure that pytest collection doesn't trigger importing slothy.
assert not any(map(re.compile("slothy").search, sys.modules))

initial_modules = sys.modules.copy()


def purge_modules() -> None:
    sys.modules.clear()
    sys.modules.update(initial_modules)


@pytest.fixture()
def case(request: pytest.FixtureRequest) -> object:
    return request.param


@contextmanager
def reference_tracking(
    *,
    context: Context,
    supported: bool,
    tracking: tuple[str, ...],
    subtests: SubTests,
) -> Iterator[None]:
    if supported:
        # We're using slothy's internal system for tracking whether
        # slothy objects are properly garbage collected. :-)
        from slothy._importing import SlothyObject, _SlothyKey, tracker_var

        tracking_map = {
            "object": SlothyObject,
            "key": _SlothyKey,
        }

        tracked = {tracking_map[tracked_type] for tracked_type in tracking}
        untracked = set(tracking_map.values()) - tracked

        tracker: defaultdict[type, WeakSet[object]] = defaultdict(WeakSet)
        context.run(tracker_var.set, tracker)
    try:
        yield
    finally:
        if supported:
            with subtests.test("tracked-intended-types"):
                for intended_type in tracked:
                    assert intended_type in tracker
                for unintended_type in untracked:
                    assert unintended_type not in tracker

            with subtests.test("slothy-objects-freed"):
                if platform.python_implementation() == "PyPy":
                    # https://doc.pypy.org/en/latest/cpython_differences.html#differences-related-to-garbage-collection-strategies
                    gc.collect()

                for intended_type in tracked:
                    assert not tracker[intended_type]


class Case(NamedTuple):
    test_file: Path
    supported: bool
    tracking: tuple[str, ...] = ("object", "key")


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
@pytest.mark.parametrize(
    ("test_file", "supported", "tracking"),
    [
        Case(
            CASES_DIR / "import_bound_descriptors_disallowed.py",
            supported=True,
            tracking=("object",),
        ),
        Case(CASES_DIR / "imports_lazily.py", supported=True),
        Case(CASES_DIR / "imports_lazily.py", supported=False),
        Case(CASES_DIR / "type_importing.py", supported=True),
        Case(CASES_DIR / "prevents_eager.py", supported=True, tracking=()),
        Case(CASES_DIR / "prevents_eager.py", supported=False, tracking=()),
        Case(CASES_DIR / "raises_warnings.py", supported=False, tracking=()),
        Case(
            CASES_DIR / "wildcard_imports_disallowed.py",
            supported=True,
            tracking=(),
        ),
    ],
)
def test_file(
    *,
    test_file: Path,
    supported: bool,
    tracking: tuple[str, ...],
    subtests: SubTests,
) -> None:
    os.environ["SLOTHY_DISABLE"] = "" if supported else "1"
    context = copy_context()
    with reference_tracking(
        context=context,
        supported=supported,
        tracking=tracking,
        subtests=subtests,
    ):
        context.run(
            runpy.run_path,
            str(test_file),
            run_name="tests",
            init_globals={"subtests": subtests, "supported": supported},
        )
    purge_modules()
