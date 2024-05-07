from __future__ import annotations
import sys
from collections import defaultdict
from importlib.machinery import ModuleSpec
from types import ModuleType
from typing import TYPE_CHECKING

import pytest
from lazy_importing import (
    LAZY_IMPORTING,
    ALL_AUDITING_EVENTS,
    LazyObjectPlaceholder,
    supports_lazy_access,
    audits,
)
from lazy_importing.api import lazy_importing, lazy_loading

if TYPE_CHECKING:
    from typing import Any

    from pytest_subtests import SubTests

    subtests: SubTests  # passed through runpy.run_path()

# Dict to keep track of audits and arguments passed.
audits_done: dict[str, list[tuple[Any, ...]]] = defaultdict(list)

@sys.addaudithook
def audit_hook(ev: str, args: tuple[Any, ...]) -> None:
    if ev in ALL_AUDITING_EVENTS:
        audits_done[ev].append(args)

importer = LAZY_IMPORTING.importer
old_meta_path = sys.meta_path

with subtests.test("state-before-enter"):
    assert __name__ not in {*lazy_importing, *lazy_loading}

with LAZY_IMPORTING:
    with subtests.test("state-after-enter"):
        assert __name__ in lazy_importing
        assert __name__ not in lazy_loading

    assert sys.meta_path == [importer]
    assert old_meta_path is not sys.meta_path
    new_meta_path = sys.meta_path
    assert new_meta_path is not old_meta_path
    assert new_meta_path == [importer]

    with subtests.test("audits-after-enter"):
        assert audits_done[audits.BEFORE_ENABLE] == [(importer,)]
        assert audits_done[audits.AFTER_ENABLE] == [(importer,)]

    # All the imports below only "emulate" real importing.
    # We return lazy objects that keep track of what will really be imported.

    import package

    with subtests.test("after-import-audits"):
        assert audits_done[audits.BEFORE_FIND_SPEC] == [(
            importer, "package", None, None,
        )]
        after_find_spec_args = audits_done[audits.AFTER_FIND_SPEC][-1]
        assert after_find_spec_args[0] is importer
        assert isinstance(after_find_spec_args[1], ModuleSpec)
        package_spec = after_find_spec_args[1]
        assert audits_done[audits.CREATE_MODULE] == [(
            importer, package_spec, package,
        )]
        assert audits_done[audits.EXEC_MODULE] == [(importer, package)]
        setattr_arg_tuples = audits_done[audits.LAZY_OBJECT_SETATTR]
        names_set = set()
        for setattr_args in setattr_arg_tuples:
            assert isinstance(setattr_args[0], LazyObjectPlaceholder)
            names_set.add(setattr_args[1])
        expected_names_set = {"__name__", "__spec__", "__package__"}
        # https://docs.python.org/3/reference/import.html#loader__
        if sys.version_info < (3, 14):
            expected_names_set.add("__loader__")
        assert names_set == expected_names_set

    import module
    import try_optout_module
    from module import member
    # Support aliases.
    from package.eager_submodule import member as eager_submodule_member
    from package import lazy_submodule, lazy_submodule as lazy_submodule_alias

    module_alias = module_alias_dont_overwrite = module

    with subtests.test("placeholders-created"):
        assert isinstance(sys.modules["module"], LazyObjectPlaceholder)
        assert isinstance(sys.modules["try_optout_module"], LazyObjectPlaceholder)
        assert isinstance(sys.modules["package"], LazyObjectPlaceholder)
        assert isinstance(sys.modules["package.eager_submodule"], LazyObjectPlaceholder)
        assert isinstance(sys.modules["package.lazy_submodule"], LazyObjectPlaceholder)
        assert isinstance(member, LazyObjectPlaceholder)

    with subtests.test("cant-opt-out"), pytest.raises(RuntimeError):
        LAZY_IMPORTING.load_lazy_object(try_optout_module)

with subtests.test("state-after-exit"):
    assert __name__ not in lazy_importing
    assert __name__ not in lazy_loading

with subtests.test("audits-after-exit"):
    assert audits_done[audits.BEFORE_DISABLE] == [(importer,)]
    assert audits_done[audits.AFTER_DISABLE] == [(importer,)]

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
    with pytest.raises(NameError):
        try_optout_module
    with pytest.raises(NameError):
        member
    with pytest.raises(NameError):
        eager_submodule_member
    with pytest.raises(NameError):
        lazy_submodule
    with pytest.raises(NameError):
        lazy_submodule_alias

# We now define this to test if lazy_importing overwrites it
module_alias_dont_overwrite = None  # type: ignore[assignment, unused-ignore]

with subtests.test("single-use-cm"), \
    pytest.raises(RuntimeError, match="Cannot enter .+ twice"), \
    LAZY_IMPORTING:
    pass

@supports_lazy_access
def test_access() -> None:
    # assert_inactive()
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
