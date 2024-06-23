# type_importing() tests

from __future__ import annotations

from typing import TYPE_CHECKING

from slothy import type_importing

if TYPE_CHECKING:
    from pytest_subtests import SubTests

    subtests: SubTests

with subtests.test("type-importing"):
    from typing import Any

    with type_importing():
        from module import attr

    assert attr is not Any
    assert attr == 1

with subtests.test("type-importing-falls-back"):
    from typing import Any

    with type_importing():
        from _typeshed import StrPath

    assert StrPath is Any
    del StrPath

    with type_importing(default_type=object):
        from _typeshed import StrPath

    assert StrPath is object  # type: ignore[comparison-overlap]
