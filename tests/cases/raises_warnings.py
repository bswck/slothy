# tests for everything warning-related
from __future__ import annotations

import pytest

with pytest.warns(RuntimeWarning, match=r"does not support `sys._getframe\(\)`"):
    from slothy import lazy_importing, lazy_importing_if
with pytest.warns(DeprecationWarning):
    from slothy import slothy_importing, slothy_importing_if
