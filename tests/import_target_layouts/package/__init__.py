from lazy_importing.api import lazy_importing, lazy_loading

assert "tests" not in lazy_importing
assert "tests" in lazy_loading
from . import eager_submodule
