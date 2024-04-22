import sys
from types import ModuleType

import pytest
from lazy_importing import LAZY_IMPORTING, LazyObject, supports_lazy_access

from tests.context_utils import (
    assert_inactive,
    assert_lazy_importing,
)

with LAZY_IMPORTING:
    assert_lazy_importing()
    import package
    from package.eager_submodule import member
    from package import lazy_submodule

    assert isinstance(sys.modules["package"], LazyObject)
    assert isinstance(member, LazyObject)

assert_inactive()

with pytest.raises(NameError):
    package

with pytest.raises(NameError):
    member

with pytest.raises(NameError):
    lazy_submodule

with pytest.raises(RuntimeError, match="Cannot enter .+ twice"):
    with LAZY_IMPORTING:
        pass

@supports_lazy_access
def test_objects() -> None:
    assert isinstance(package, ModuleType)
    assert member == "package.eager_submodule"
    assert isinstance(lazy_submodule, ModuleType)
    assert lazy_submodule.member == "package.lazy_submodule"

test_objects()
