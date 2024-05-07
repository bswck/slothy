from slothy.api import slothy, lazy_loading

assert "tests" not in slothy
assert "tests" in lazy_loading
member = __name__
