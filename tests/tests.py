# ruff: noqa: FBT003, F821
from __future__ import annotations

import sys
from contextlib import nullcontext
from types import ModuleType
from typing import TYPE_CHECKING, cast

import pytest

if TYPE_CHECKING:
    from contextlib import AbstractContextManager

    from pytest_subtests import SubTests

    subtests: SubTests  # passed through runpy.run_path()

supported_implementation = hasattr(sys, "_getframe")

with cast(
    "AbstractContextManager[None]",
    nullcontext()
    if supported_implementation
    else pytest.warns(RuntimeWarning, match=r"does not support `sys._getframe\(\)`"),
):
    from slothy import slothy, slothy_if

builtin_import = __import__

with subtests.test("prevent-eager"), (
    nullcontext()
    if supported_implementation
    else pytest.raises(
        RuntimeError,
        match="cannot default to eager mode",
    )
), slothy(prevent_eager=True):
    pass

with slothy():
    with subtests.test("builtin-import-overridden"):
        if supported_implementation:
            assert __import__ is not builtin_import
        else:
            assert __import__ is builtin_import

    with subtests.test("module-importing"):
        import module1

    with subtests.test("submodule-importing"):
        import package.submodule1 as submodule1  # noqa: PLR0402
        import package.submodule2

    with subtests.test("from-import"):
        from module2 import item

    if supported_implementation:
        with subtests.test("wildcard-imports-disallowed"), pytest.raises(
            RuntimeError, match="Wildcard slothy imports are not supported"
        ):
            from module3 import *  # noqa: F403

    if supported_implementation:
        SlothyObject = builtin_import("slothy._impl")._impl.SlothyObject
        assert isinstance(module1, SlothyObject)
        assert isinstance(item, SlothyObject)
        assert isinstance(module1, SlothyObject)
        assert isinstance(submodule1, SlothyObject)
        assert isinstance(package.submodule2, SlothyObject)
    else:
        assert isinstance(module1, ModuleType)
        assert isinstance(item, int)
        assert isinstance(module1, ModuleType)
        assert isinstance(submodule1, ModuleType)
        assert isinstance(package.submodule2, ModuleType)

    module_entries = (
        "module1",
        "module2",
        "package",
        "package.submodule1",
        "package.submodule2",
    )

with subtests.test("builtin-import-unchanged"):
    assert __import__ is builtin_import

with subtests.test("modules-purged-if-slothy"):
    if supported_implementation:
        # This behavior is necessary, because we want the same imports
        # to perform actual imports in non-slothy mode.
        for module_entry in module_entries:
            assert module_entry not in sys.modules
    else:
        for module_entry in module_entries:
            assert module_entry in sys.modules

with slothy(), subtests.test("reenter-works"):
    # Should not be a problem if we re-enter.
    if supported_implementation:
        assert __import__ is not builtin_import
    else:
        assert __import__ is builtin_import

with subtests.test("builtin-import-unchanged-after-reenter"):
    assert __import__ is builtin_import

with slothy_if(True), subtests.test("slothy-if-true"):
    if supported_implementation:
        assert __import__ is not builtin_import
    else:
        assert __import__ is builtin_import

with slothy_if(False), subtests.test("slothy-if-false"):
    assert __import__ is builtin_import

with subtests.test("test-class-scope"):

    class Test:
        """Test class containing a slothy import binding an attribute."""

        with slothy():
            from module3 import a, b

            if supported_implementation:
                SlothyObject = builtin_import("slothy._impl")._impl.SlothyObject
                assert isinstance(a, SlothyObject)
            else:
                assert isinstance(a, int)

    # If it's a supported implementation, the item should be imported
    # on demand via descriptor protocol.
    assert Test.a == 1
