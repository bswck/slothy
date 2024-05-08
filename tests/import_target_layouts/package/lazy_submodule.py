from slothy.api import slothy_importing, slothy_loading

assert "tests" not in slothy_importing
assert "tests" in slothy_loading
member = __name__
