# core tests
from __future__ import annotations

import re
import sys
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

import pytest

from slothy import lazy_importing, lazy_importing_if

if TYPE_CHECKING:
    from pytest_subtests import SubTests

    from slothy._importing import SlothyObject

    subtests: SubTests
    supported: bool

builtin_import = __import__

with lazy_importing(prevent_eager=False):
    if supported:
        with subtests.test("wildcard-imports-disallowed"), pytest.raises(
            RuntimeError, match="Wildcard slothy imports are not supported"
        ):
            from whatever import *  # type: ignore[import-not-found]  # noqa: F403

    with subtests.test("builtin-import-overridden"):
        if supported:
            assert __import__ is not builtin_import
        else:
            assert __import__ is builtin_import

    with subtests.test("perform-lazy-imports"):
        import module
        import package1 as pkg
        import package2.submodule
        from module import attr

        if supported:
            # This should fail later.
            from package1 import delusion  # type: ignore[attr-defined]
        else:
            with pytest.raises(ImportError):
                from package1 import delusion  # type: ignore[attr-defined]

        from package1 import subpackage  # noqa: I001
        from package1.submodule1 import member1 as m1_1
        from package1.submodule2 import member1 as m2_1, member2 as m2_2
        from package1.submodule3 import (
            member1 as m3_1,
            member2 as m3_2,
            member3 as m3_3,
        )

        with pytest.raises(AttributeError):
            # Expected in both implementations.
            # We can identify whether a member should be available
            # using either (1) the `fromlist` or (2) the submodule
            # (from the `__import__` 1st arg, i.e. the module name).
            subpackage.subsubmodule

        if supported:
            # `package2.__getattr__()` should simply return itself;
            # it already holds the info about the targeted module.
            # As a side effect, it is possible to get away
            # with `package2.submodule.submodule` at runtime,
            # but that's where mypy comes in.
            assert package2.submodule is package2

        from package1.subpackage import subsubmodule

        if supported:
            # We'll make it work later.
            from package1 import fake as package1_fake  # type: ignore[attr-defined]

    if supported:
        PATH_HERE = str(Path(__file__).resolve())
        SRC_REF = rf'"{re.escape(PATH_HERE)}", line \d+'

        with subtests.test("slothy-object-repr"):
            from slothy._importing import SlothyObject

            assert isinstance(module, SlothyObject)
            assert re.fullmatch(rf"<import module \({SRC_REF}\)>", repr(module))

            assert isinstance(pkg, SlothyObject)
            assert re.fullmatch(rf"<import package1 \({SRC_REF}\)>", repr(pkg))

            assert isinstance(attr, SlothyObject)
            assert re.fullmatch(rf"<from module import attr \({SRC_REF}\)>", repr(attr))

            assert isinstance(subpackage, SlothyObject)
            assert re.fullmatch(
                rf"<from package1 import subpackage \({SRC_REF}\)>",
                repr(subpackage),
            )

            with subtests.test("representing-neighboring-fromlist-members"):
                assert isinstance(m1_1, SlothyObject)
                assert re.fullmatch(
                    rf"<from package1.submodule1 import member1 \({SRC_REF}\)>",
                    repr(m1_1),
                )

                assert isinstance(m2_1, SlothyObject)
                assert re.fullmatch(
                    rf"<from package1.submodule2 import member1, ... \({SRC_REF}\)>",
                    repr(m2_1),
                )

                assert isinstance(m2_2, SlothyObject)
                assert re.fullmatch(
                    rf"<from package1.submodule2 import ..., member2 \({SRC_REF}\)>",
                    repr(m2_2),
                )

                assert isinstance(m3_1, SlothyObject)
                assert re.fullmatch(
                    rf"<from package1.submodule3 import member1, ... \({SRC_REF}\)>",
                    repr(m3_1),
                )

                assert isinstance(m3_2, SlothyObject)
                assert re.fullmatch(
                    (
                        r"<from package1.submodule3 import ..., member2, "
                        rf"... \({SRC_REF}\)>"
                    ),
                    repr(m3_2),
                )

                assert isinstance(m3_3, SlothyObject)
                assert re.fullmatch(
                    rf"<from package1.submodule3 import ..., member3 \({SRC_REF}\)>",
                    repr(m3_3),
                )

    expected_module_entries: tuple[str, ...] = (
        "module",
        "package1",
        "package1.submodule1",
        "package1.submodule2",
        "package1.submodule3",
        # ↓ Because of `from package1.subpackage import subsubmodule`,
        #   NOT because of `from package1 import subpackage`.
        "package1.subpackage",
        "package2.submodule",
    )
    modules_in_from_imports = ("package1.subpackage.subsubmodule",)
    if not supported:
        expected_module_entries += modules_in_from_imports

    unwanted_module_entries: tuple[str, ...] = (
        # `from X import Y` can't register X.Y in sys.modules
        # if Y isn't a module.
        # We want to expose `fromlist` members as non-modules
        # and let the final resolution handle it correctly.
        # In `supported=False` case this will also not be bound
        # because `module.attr` in fact isn't a module.
        "module.attr",
        "package.submodule.member",  # ↑
    )
    if supported:
        unwanted_module_entries += modules_in_from_imports

    def test_all_imported() -> None:
        assert isinstance(module, ModuleType)
        assert isinstance(pkg, ModuleType)
        assert isinstance(attr, int)
        assert isinstance(subpackage, ModuleType)
        assert isinstance(subsubmodule, ModuleType)
        assert isinstance(package2.submodule, ModuleType)
        assert isinstance(m1_1, int)
        assert isinstance(m2_1, int)
        assert isinstance(m2_2, int)
        assert isinstance(m3_1, int)
        assert isinstance(m3_2, int)
        assert isinstance(m3_3, int)

        if supported:
            with pytest.raises(
                ImportError,
                match=rf"\(caused by delayed execution of {SRC_REF}\)",
            ):
                delusion

            import fake

            sys.modules["package1.fake"] = fake
            pkg.fake = fake  # type: ignore[attr-defined]
            assert package1_fake is fake

    if not supported:
        test_all_imported()

with subtests.test("builtin-import-unchanged"):
    assert __import__ is builtin_import

with subtests.test("module-registry-purged"):
    if supported:
        # This behavior is necessary, because we want the same imports
        # to perform actual imports in non-slothy mode.
        for module_entry in expected_module_entries:
            assert module_entry not in sys.modules
    else:
        for module_entry in expected_module_entries:
            assert module_entry in sys.modules
    for module_entry in unwanted_module_entries:
        assert module_entry not in sys.modules

with lazy_importing(prevent_eager=False), subtests.test("reenter-works"):
    # Should not be a problem if we re-enter.
    if supported:
        assert __import__ is not builtin_import
    else:
        assert __import__ is builtin_import

with subtests.test("builtin-import-unchanged-after-reenter"):
    assert __import__ is builtin_import

with subtests.test("imported-on-reference"):
    test_all_imported()

with lazy_importing_if(True, prevent_eager=False), subtests.test("slothy-if-true"):
    if supported:
        assert __import__ is not builtin_import
    else:
        assert __import__ is builtin_import

with lazy_importing_if(False, prevent_eager=False), subtests.test("slothy-if-false"):
    assert __import__ is builtin_import
