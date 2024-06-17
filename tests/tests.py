# ruff: noqa: B018, FBT003, F401, F821, PLR2004
from __future__ import annotations

import re
import sys
from contextlib import nullcontext
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, cast

import pytest

if TYPE_CHECKING:
    from contextlib import AbstractContextManager

    from pytest_subtests import SubTests

    subtests: SubTests  # defined via runpy
    supported_implementation: bool  # defined via runpy

with cast(
    "AbstractContextManager[None]",
    nullcontext()
    if supported_implementation
    else pytest.warns(RuntimeWarning, match=r"does not support `sys._getframe\(\)`"),
):
    from slothy import slothy_importing, slothy_importing_if

if supported_implementation:
    from slothy._importing import SlothyObject

builtin_import = __import__

with subtests.test("prevent-eager"), (
    nullcontext()
    if supported_implementation
    else pytest.raises(
        RuntimeError,
        match="cannot default to eager mode",
    )
), slothy_importing(prevent_eager=True):
    pass

with subtests.test("no-prevent-eager"), slothy_importing(prevent_eager=False):
    # Should never fail.
    pass

with slothy_importing():
    if supported_implementation:
        with subtests.test("wildcard-imports-disallowed"), pytest.raises(
            RuntimeError, match="Wildcard slothy imports are not supported"
        ):
            from whatever import *  # type: ignore[import-not-found]  # noqa: F403

    with subtests.test("builtin-import-overridden"):
        if supported_implementation:
            assert __import__ is not builtin_import
        else:
            assert __import__ is builtin_import

    with subtests.test("perform-slothy-imports"):
        import module
        import package as pkg
        from module import attr

        if supported_implementation:
            # This should fail later.
            from package import delusion  # type: ignore[attr-defined]
        else:
            with pytest.raises(ImportError):
                from package import delusion  # type: ignore[attr-defined]

        from package import subpackage  # noqa: I001
        from package.submodule1 import member1 as m1_1
        from package.submodule2 import member1 as m2_1, member2 as m2_2
        from package.submodule3 import member1 as m3_1, member2 as m3_2, member3 as m3_3

        with pytest.raises(AttributeError):
            # Expected in both implementations.
            # We can identify whether a member should be available not
            # using either (1) the fromlist or (2) the submodule
            # (from __import__ 1st arg, modulename).
            subpackage.subsubmodule

        from package.subpackage import subsubmodule

    if supported_implementation:
        PATH_HERE = str(Path(__file__).resolve())
        REFERENCE = rf'\("{re.escape(PATH_HERE)}", line \d+\)'

        with subtests.test("import-outputs"):
            assert isinstance(module, SlothyObject)
            assert re.fullmatch(rf"<import module {REFERENCE}>", repr(module))

            assert isinstance(pkg, SlothyObject)
            assert re.fullmatch(rf"<import package {REFERENCE}>", repr(pkg))

            assert isinstance(attr, SlothyObject)
            assert re.fullmatch(rf"<from module import attr {REFERENCE}>", repr(attr))

            assert isinstance(subpackage, SlothyObject)
            assert re.fullmatch(
                rf"<from package import subpackage {REFERENCE}>",
                repr(subpackage),
            )

            with subtests.test("representing-neighboring-fromlist-members"):
                assert isinstance(m1_1, SlothyObject)
                assert re.fullmatch(
                    rf"<from package.submodule1 import member1 {REFERENCE}>",
                    repr(m1_1),
                )

                assert isinstance(m2_1, SlothyObject)
                assert re.fullmatch(
                    rf"<from package.submodule2 import member1, ... {REFERENCE}>",
                    repr(m2_1),
                )

                assert isinstance(m2_2, SlothyObject)
                assert re.fullmatch(
                    rf"<from package.submodule2 import ..., member2 {REFERENCE}>",
                    repr(m2_2),
                )

                assert isinstance(m3_1, SlothyObject)
                assert re.fullmatch(
                    rf"<from package.submodule3 import member1, ... {REFERENCE}>",
                    repr(m3_1),
                )

                assert isinstance(m3_2, SlothyObject)
                assert re.fullmatch(
                    rf"<from package.submodule3 import ..., member2, ... {REFERENCE}>",
                    repr(m3_2),
                )

                assert isinstance(m3_3, SlothyObject)
                assert re.fullmatch(
                    rf"<from package.submodule3 import ..., member3 {REFERENCE}>",
                    repr(m3_3),
                )

    expected_module_entries: tuple[str, ...] = (
        "module",
        "package",
        "package.submodule1",
        "package.submodule2",
        "package.submodule3",
        # Because of `from package.subpackage import subsubmodule`,
        # NOT because of `from package import subpackage`
        "package.subpackage",
    )
    if not supported_implementation:
        expected_module_entries += (
            "package.subpackage.subsubmodule",  # ↑
        )

    unwanted_module_entries: tuple[str, ...] = (
        # `from X import Y` can't register X.Y in sys.modules
        # if Y isn't a module.
        # We want to expose fromlist members as non-modules
        # and let the final resolution handle it correctly.
        # In `supported_implementation=False` case this will also not be bound
        # because `module.attr` in fact isn't a module.
        "module.attr",
        "package.submodule.member",  # ↑
    )
    if supported_implementation:
        unwanted_module_entries += (
            "package.subpackage.subsubmodule",  # ↑
        )

    def test_all_imported() -> None:
        assert isinstance(module, ModuleType)
        assert isinstance(attr, int)

    if not supported_implementation:
        test_all_imported()

with subtests.test("builtin-import-unchanged"):
    assert __import__ is builtin_import

with subtests.test("module-registry-purged"):
    if supported_implementation:
        # This behavior is necessary, because we want the same imports
        # to perform actual imports in non-slothy mode.
        for module_entry in expected_module_entries:
            assert module_entry not in sys.modules
    else:
        for module_entry in expected_module_entries:
            assert module_entry in sys.modules
    for module_entry in unwanted_module_entries:
        assert module_entry not in sys.modules

with slothy_importing(), subtests.test("reenter-works"):
    # Should not be a problem if we re-enter.
    if supported_implementation:
        assert __import__ is not builtin_import
    else:
        assert __import__ is builtin_import

with subtests.test("builtin-import-unchanged-after-reenter"):
    assert __import__ is builtin_import

with subtests.test("imported-on-reference"):
    test_all_imported()

with slothy_importing_if(True), subtests.test("slothy-if-true"):
    if supported_implementation:
        assert __import__ is not builtin_import
    else:
        assert __import__ is builtin_import

with slothy_importing_if(False), subtests.test("slothy-if-false"):
    assert __import__ is builtin_import

with subtests.test("test-class-scope"):

    class Test:
        """Test class containing slothy imports binding attributes."""

        desc_set_called = False
        desc_delete_called = False

        with slothy_importing():
            # Curio: mypy doesn't support from-imports with multiple items.
            from class_imported_module import a, b, c  # type: ignore[misc]

            if supported_implementation:
                assert isinstance(a, SlothyObject)
                assert isinstance(b, SlothyObject)
                assert isinstance(c, SlothyObject)
            else:
                assert isinstance(a, int)
                assert isinstance(b, int)
                assert isinstance(c, property)

    # If it's a supported implementation, the item should be imported
    # on demand via descriptor protocol.
    assert Test.a == 1

    test = Test()

    with subtests.test("reenter-slothy-descriptor-no-import"), slothy_importing():
        if supported_implementation:
            assert isinstance(test.b, SlothyObject)
            assert isinstance(test.c, SlothyObject)
        else:
            assert isinstance(test.b, int)

    assert test.b == 2
    with subtests.test("descriptor-get-called"):
        assert test.c is test  # That property returns self.

    with subtests.test("descriptor-set-called"):
        test.c = None
        assert test.desc_set_called

    with subtests.test("descriptor-delete-called"):
        del test.c
        assert test.desc_delete_called
