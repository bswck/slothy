from slothy.api import slothy, lazy_loading

assert "tests" not in slothy
assert "tests" in lazy_loading
from . import eager_submodule
