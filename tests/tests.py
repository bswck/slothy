import sys
from types import ModuleType
from typing import TYPE_CHECKING

import pytest
from lazy_importing import (
    LAZY_IMPORTING,
    LazyObject,
    supports_lazy_access
)

from tests.context_utils import (
    assert_inactive,
    assert_lazy_importing,
)

if TYPE_CHECKING:
    from pytest_subtests import SubTests

    subtests: SubTests  # passed through runpy.run_path()

with LAZY_IMPORTING:
    with subtests.test("state after enter"):
        assert_lazy_importing()

    import package
    import module
    from module import member
    from package.eager_submodule import member as eager_submodule_member
    from package import lazy_submodule, lazy_submodule as lazy_submodule_alias

    module_alias = module

    with subtests.test("lazy object creation"):
        assert isinstance(sys.modules["module"], LazyObject)
        assert isinstance(sys.modules["package"], LazyObject)
        assert isinstance(sys.modules["package.eager_submodule"], LazyObject)
        assert isinstance(sys.modules["package.lazy_submodule"], LazyObject)
        assert isinstance(member, LazyObject)


with subtests.test("state after exit"):
    assert_inactive()

with subtests.test("frame cleanup"):
    with pytest.raises(NameError):
        package

    with pytest.raises(NameError):
        member

    with pytest.raises(NameError):
        lazy_submodule


with subtests.test("un-re-entrant context management"):
    with pytest.raises(RuntimeError, match="Cannot enter .+ twice"):
        with LAZY_IMPORTING:
            pass


@supports_lazy_access
def test_access() -> None:
    assert_inactive()
    assert eager_submodule_member == "package.eager_submodule"
    assert isinstance(package, ModuleType)

    with subtests.test("auto-binding aliases"):
        assert isinstance(lazy_submodule, ModuleType)
        assert lazy_submodule.member == "package.lazy_submodule"

    with subtests.test("auto-binding aliases"):
        assert "lazy_submodule_alias" in globals()
        assert lazy_submodule_alias is lazy_submodule


test_access()
