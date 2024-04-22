import sys
import pytest
from lazy_importing import LAZY_IMPORTING, LazyObject, supports_lazy_access
from tests.context_utils import (
    assert_inactive,
    assert_lazy_importing,
)

with LAZY_IMPORTING:
    assert_lazy_importing()
    from module import member

    assert isinstance(sys.modules["module"], LazyObject)
    assert isinstance(member, LazyObject)

assert_inactive()

with pytest.raises(NameError):
    member

@supports_lazy_access
def get_member() -> str:
    return member

assert get_member() == "module"
