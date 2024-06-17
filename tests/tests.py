# ruff: noqa: B018, FBT003, F401, F821, PLR2004
from __future__ import annotations

import gc
import platform
import re
import sys
from contextlib import nullcontext
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, cast
from weakref import WeakSet

import pytest

if TYPE_CHECKING:
    from contextlib import AbstractContextManager

    from pytest_subtests import SubTests

    from slothy._importing import SlothyObject

    # Global variables passed through runpy.
    subtests: SubTests
    supported_implementation: bool

with cast(
    "AbstractContextManager[None]",
    nullcontext()
    if supported_implementation
    else pytest.warns(RuntimeWarning, match=r"does not support `sys._getframe\(\)`"),
):
    from slothy import slothy_importing, slothy_importing_if

if supported_implementation:
    # We're using slothy's internal system for tracking whether
    # slothy objects are properly garbage collected. :-)
    from slothy._importing import SlothyObject, _SlothyKey

    SlothyKey_objects: WeakSet[_SlothyKey] = WeakSet()
    SlothyObject_objects: WeakSet[SlothyObject] = WeakSet()

    SlothyObject.__slothy_tracker__ = SlothyObject_objects
    _SlothyKey.__slothy_tracker__ = SlothyKey_objects

    assert not SlothyObject_objects
    assert not SlothyKey_objects

builtin_import = __import__

for cm in (
    lambda: slothy_importing(prevent_eager=True),
    lambda: slothy_importing_if(True, prevent_eager=True),
):
    with subtests.test("prevent-eager"), (
        nullcontext()
        if supported_implementation
        else pytest.raises(
            RuntimeError,
            match="cannot default to eager mode",
        )
    ), cm():  # type: ignore[no-untyped-call]
        pass

for cm in (
    lambda: slothy_importing(prevent_eager=False),
    lambda: slothy_importing_if(False, prevent_eager=True),
    lambda: slothy_importing_if(True, prevent_eager=False),
):
    with subtests.test("no-prevent-eager"), cm():  # type: ignore[no-untyped-call]
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
        import package1 as pkg
        import package2.submodule
        from module import attr

        if supported_implementation:
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

        if supported_implementation:
            # `package2.__getattr__()` should simply return itself;
            # it already holds the info about the targeted module.
            # As a side effect, it is possible to get away
            # with `package2.submodule.submodule` at runtime,
            # but that's where MyPy comes in.
            assert package2.submodule is package2

        from package1.subpackage import subsubmodule

        if supported_implementation:
            # We'll make it work later.
            from package1 import fake as package1_fake  # type: ignore[attr-defined]

    if supported_implementation:
        PATH_HERE = str(Path(__file__).resolve())
        SRC_REF = rf'"{re.escape(PATH_HERE)}", line \d+'

        with subtests.test("import-outputs"):
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
    if not supported_implementation:
        expected_module_entries += modules_in_from_imports

    unwanted_module_entries: tuple[str, ...] = (
        # `from X import Y` can't register X.Y in sys.modules
        # if Y isn't a module.
        # We want to expose `fromlist` members as non-modules
        # and let the final resolution handle it correctly.
        # In `supported_implementation=False` case this will also not be bound
        # because `module.attr` in fact isn't a module.
        "module.attr",
        "package.submodule.member",  # ↑
    )
    if supported_implementation:
        unwanted_module_entries += modules_in_from_imports

    def test_all_imported() -> None:
        if supported_implementation:
            with subtests.test("garbage-collection-trackers-full"):
                assert SlothyObject_objects
                assert SlothyKey_objects

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

        if supported_implementation:
            with pytest.raises(
                ImportError,
                match=rf"\(caused by delayed execution of {SRC_REF}\)",
            ):
                delusion

            import fake

            sys.modules["package1.fake"] = fake
            pkg.fake = fake  # type: ignore[attr-defined]
            assert package1_fake is fake

            with subtests.test("garbage-collection-trackers-clear"):
                if platform.python_implementation() == "PyPy":
                    # https://doc.pypy.org/en/latest/cpython_differences.html#differences-related-to-garbage-collection-strategies
                    gc.collect()
                assert not SlothyObject_objects
                assert not SlothyKey_objects

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

if supported_implementation:
    with subtests.test("test-class-scope"), pytest.raises(
        RuntimeError,
        match="__set_name__",
    ), slothy_importing():

        class _ClassScope:
            from whatever_else import anything  # type: ignore[import-not-found]
