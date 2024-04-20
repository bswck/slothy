from __future__ import annotations

import sys
import types
from contextlib import suppress
from importlib import import_module
from importlib.util import find_spec
from typing import TYPE_CHECKING

import pytest

from lazy_importing import LazyImportingContextManager, supports_lazy_access
from lazy_importing.abc import LazyImportingStrategy, LazyObject
from lazy_importing.ctx import LazyObjectLoader
from tests.state import assert_importing, assert_inactive

if TYPE_CHECKING:
    from collections.abc import Iterator
    from importlib.machinery import ModuleSpec


def purge_module(module_name: str) -> None:
    """Remove a module from the module cache by name."""
    prev_ref = None
    while "." in module_name:
        removed_module = None
        with suppress(KeyError):
            removed_module = sys.modules.pop(module_name)
        if removed_module and prev_ref:
            delattr(removed_module, prev_ref)
        module_name, prev_ref = module_name.rsplit(".", 1)



@pytest.fixture(
    scope="function",
    params=(
        "lazy_namespace.inner_lazy_module",
        "lazy_namespace.inner_lazy_namespace.inner_inner_lazy_module",
        # "lazy_module",  # xxx fix this test?
    )
)
def lazy_module_name(request: pytest.FixtureRequest) -> Iterator[str]:
    """Return the name of the lazy module."""
    module_name = request.param
    yield module_name


@pytest.fixture
def strategy() -> Iterator[type[LazyImportingStrategy]]:
    """Return the name of the lazy module."""
    from lazy_importing.strategies import HalfLazyImportingStrategy
    yield HalfLazyImportingStrategy


def _validate_spec(lazy_module_name: str) -> ModuleSpec:
    """Return the name of the lazy module."""
    spec: ModuleSpec | None = find_spec(lazy_module_name, ".")
    assert spec is not None
    assert getattr(spec, "__lazy_spec__", False)
    return spec


def _validate_context_on_enter(
    context_manager: LazyImportingContextManager,
) -> None:
    """Return the name of the lazy module."""
    context = context_manager.context
    context.run(assert_importing)
    strategy = context_manager.strategy
    assert isinstance(strategy, LazyImportingStrategy)
    assert strategy.new_meta_path is sys.meta_path
    assert strategy.context is context


def _validate_context_on_exit(
    context_manager: LazyImportingContextManager,
) -> None:
    """Return the name of the lazy module."""
    context = context_manager.context
    context.run(assert_inactive)
    strategy = context_manager.strategy
    assert isinstance(strategy, LazyImportingStrategy)
    assert strategy.old_meta_path is sys.meta_path
    assert strategy.context is context

    with pytest.raises(RuntimeError):
        context_manager.__enter__()


def test_lazy_import_module(
    strategy: type[LazyImportingStrategy],
    lazy_module_name: str,
) -> None:
    """Test the lazy_importing library."""
    purge_module(lazy_module_name)

    with LazyImportingContextManager(strategy_factory=strategy) as context_manager:
        _validate_context_on_enter(context_manager)
        _validate_spec(lazy_module_name)
        exec_ns: dict[str, object] = {}
        purge_module(lazy_module_name)
        # We validated spec is found correctly, purge the module again
        # and perform full import.
        exec(f"import {lazy_module_name} as lazy_module", exec_ns)
        lazy_module = exec_ns["lazy_module"]
        assert isinstance(lazy_module, types.ModuleType)

    _validate_context_on_exit(context_manager)
    loaded_object = lazy_module.lazy_object
    purge_module(lazy_module_name)
    module = import_module(lazy_module_name)
    assert loaded_object == module.lazy_object


def test_lazy_import_module_item(
    strategy: type[LazyImportingStrategy],
    lazy_module_name: str,
) -> None:
    """Test the lazy_importing library."""
    # We're doing little gymnastics here because pytest
    # tracks assert statements in the local namespace. —_—
    local_ns = locals()
    purge_module(lazy_module_name)

    with LazyImportingContextManager(
        strategy_factory=strategy,
        local_ns=local_ns,
    ) as context_manager:
        _validate_context_on_enter(context_manager)
        _validate_spec(lazy_module_name)
        exec_ns: dict[str, object] = {}
        purge_module(lazy_module_name)
        # We validated spec is found correctly, purge the module again
        # and perform full import.
        exec(f"from {lazy_module_name} import lazy_object", exec_ns)
        lazy_object = exec_ns["lazy_object"]
        assert isinstance(lazy_object, LazyObject)
        ident_1 = "lazy_object_ref_1"
        ident_2 = "lazy_object_ref_2"
        refs = dict.fromkeys((ident_1, ident_2), lazy_object)
        local_ns.update(refs)

    _validate_context_on_exit(context_manager)
    assert ident_1 not in local_ns and ident_2 not in local_ns

    builtins = local_ns["__builtins__"]
    assert isinstance(builtins, LazyObjectLoader)
    assert builtins.lazy_objects.get(ident_1) is lazy_object
    assert builtins.lazy_objects.get(ident_2) is lazy_object

    @supports_lazy_access
    def _access_object() -> None:
        loaded_lazy_object = builtins[ident_1]
        assert ident_1 in local_ns
        assert ident_2 in local_ns  # auto binding
        purge_module(lazy_module_name)
        lazy_module = import_module(lazy_module_name)
        assert type(lazy_module) is types.ModuleType
        assert loaded_lazy_object == lazy_module.lazy_object

    _access_object()
