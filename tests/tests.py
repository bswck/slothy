from __future__ import annotations
import sys
from collections import defaultdict
from types import ModuleType
from typing import TYPE_CHECKING

import pytest
from lazy_importing import (
    LAZY_IMPORTING,
    ALL_AUDITING_EVENTS,
    LazyObject,
    supports_lazy_access,
)

from tests.context_utils import (
    assert_inactive,
    assert_lazy_importing,
)

if TYPE_CHECKING:
    from typing import Any

    from pytest_subtests import SubTests

    subtests: SubTests  # passed through runpy.run_path()

else:
    # Workarounds for pytest side effects whilst running the test.
    __import__("pygments.formatters.terminal")
    __import__("pygments.lexers.python")
    __import__("pygments.lexers.diff")
    __import__("pygments.formatters.terminal")
    __import__("pygments.util")

# Dict to keep track of audits and arguments passed.
audits_done: dict[str, list[tuple[Any, ...]]] = defaultdict(list)

@sys.addaudithook
def audit_hook(ev: str, args: tuple[Any, ...]) -> None:
    if ev in ALL_AUDITING_EVENTS:
        audits_done[ev].append(args)

importer = LAZY_IMPORTING.importer

with LAZY_IMPORTING:
    with subtests.test("state-after-enter"):
        # Checks if lazy_importing.get() is True.
        assert_lazy_importing()

    # All the imports below only "emulate" real importing.
    # We return lazy objects that keep track of what will really be imported.
    import package
    import module
    import optout_module
    from module import member
    # Support aliases.
    from package.eager_submodule import member as eager_submodule_member
    from package import lazy_submodule, lazy_submodule as lazy_submodule_alias

    module_alias = module_alias_dont_overwrite = module

    with subtests.test("lazy-object-creation"):
        assert isinstance(sys.modules["module"], LazyObject)
        assert isinstance(sys.modules["optout_module"], LazyObject)
        assert isinstance(sys.modules["package"], LazyObject)
        assert isinstance(sys.modules["package.eager_submodule"], LazyObject)
        assert isinstance(sys.modules["package.lazy_submodule"], LazyObject)
        assert isinstance(member, LazyObject)

    with subtests.test("opt-out"):
        loaded_optout_module = LAZY_IMPORTING.load_lazy_object(optout_module)
        assert sys.modules["optout_module"] is loaded_optout_module
        LAZY_IMPORTING.bind_lazy_object(
            optout_module,
            loaded_optout_module,
            "optout_module",
        )
        assert optout_module is loaded_optout_module

with subtests.test("state-after-exit"):
    assert_inactive()

with subtests.test("frame-cleanup"):
    # Check if locals defined before entering the context manager
    # are the same after we exit.
    with pytest.raises(NameError):
        package
    with pytest.raises(NameError):
        module
    with pytest.raises(NameError):
        module_alias
    with pytest.raises(NameError):
        module_alias_dont_overwrite
    optout_module  # Shouldn't raise.
    loaded_optout_module  # Shouldn't raise.
    with pytest.raises(NameError):
        member
    with pytest.raises(NameError):
        eager_submodule_member
    with pytest.raises(NameError):
        lazy_submodule
    with pytest.raises(NameError):
        lazy_submodule_alias

with subtests.test("lazy-objects-unavailable-same-frame"):
    with pytest.raises(NameError):
        # Make sure we can't access it from the same frame.
        package

# We now define this to test if lazy_importing overwrites it
module_alias_dont_overwrite = None  # type: ignore[assignment, unused-ignore]

with subtests.test("single-use-cm"):
    with pytest.raises(RuntimeError, match="Cannot enter .+ twice"):
        with LAZY_IMPORTING:
            pass

@supports_lazy_access
def test_access() -> None:
    assert_inactive()
    with subtests.test("import-on-access"):
        assert isinstance(package, ModuleType)
        assert "package" in sys.modules
        assert "package.eager_submodule" in sys.modules  # it's eager!
        assert eager_submodule_member == "package.eager_submodule"

    with pytest.raises(NameError):
        undefined  # type: ignore[name-defined]

    assert isinstance(lazy_submodule, ModuleType)
    assert lazy_submodule.member == "package.lazy_submodule"

    with subtests.test("auto-binding-aliases"):
        assert "lazy_submodule_alias" in globals()
        assert lazy_submodule_alias is lazy_submodule
        assert module_alias_dont_overwrite is None

test_access()

with subtests.test("all-audits-covered"):
    assert set(audits_done) == ALL_AUDITING_EVENTS
