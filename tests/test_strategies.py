from __future__ import annotations

import sys
import types
from contextlib import suppress
from functools import reduce
from importlib.util import find_spec
from typing import TYPE_CHECKING

import pytest

from lazy_importing import LazyImportingContextManager, supports_lazy_access
from lazy_importing.abc import LazyImportingStrategy, LazyObject, lazy_loading
from lazy_importing.ctx import LazyObjectLoader

if TYPE_CHECKING:
    from collections.abc import Iterator
    from importlib.machinery import ModuleSpec

    from lazy_importing.abc import MetaPath


def purge_module(module_name: str) -> None:
    """Remove a module from the module cache by name."""
    with suppress(KeyError):
        del sys.modules[module_name]


@pytest.fixture
def lazy_module_name() -> Iterator[str]:
    """Return the name of the lazy module."""
    yield "tests._lazy_module"


@pytest.fixture
def strategy() -> Iterator[type[LazyImportingStrategy]]:
    """Return the name of the lazy module."""
    from lazy_importing.strategies import HalfLazyImportingStrategy
    yield HalfLazyImportingStrategy


@pytest.fixture(autouse=True)
def purge_lazy_module(lazy_module_name: str) -> None:
    """Remove the lazy module from the module cache."""
    purge_module(lazy_module_name)


def _validate_spec(lazy_module_name: str) -> ModuleSpec:
    """Return the name of the lazy module."""
    spec: ModuleSpec | None = find_spec(lazy_module_name, ".")
    assert spec is not None
    assert getattr(spec, "__lazy_spec__", False)
    return spec


def _validate_context_on_enter(
    context_manager: LazyImportingContextManager,
    meta_path: MetaPath,
) -> None:
    """Return the name of the lazy module."""
    context = context_manager.context
    assert context.get(lazy_loading)
    strategy = context_manager._strategy  # instance, not type
    assert isinstance(strategy, LazyImportingStrategy)
    assert strategy.new_meta_path is sys.meta_path
    assert strategy.old_meta_path is not sys.meta_path
    assert strategy.context is context


def _validate_context_on_exit(
    context_manager: LazyImportingContextManager,
    meta_path: MetaPath,
) -> None:
    """Return the name of the lazy module."""
    context = context_manager.context
    assert not context.get(lazy_loading)
    strategy = context_manager._strategy  # instance, not type
    assert isinstance(strategy, LazyImportingStrategy)
    assert strategy.new_meta_path is not meta_path
    assert strategy.old_meta_path is meta_path
    assert strategy.context is context

    with pytest.raises(RuntimeError):
        context_manager.__enter__()


def _import_module(module_name: str) -> types.ModuleType:
    """Return the name of the lazy module."""
    attrs = module_name.split(".")[1:]
    return reduce(getattr, attrs, __import__(module_name))


def test_lazy_import_module(
    strategy: type[LazyImportingStrategy],
    lazy_module_name: str,
) -> None:
    """Test the lazy_importing library."""
    meta_path = sys.meta_path

    with LazyImportingContextManager(strategy=strategy) as context_manager:
        _validate_context_on_enter(context_manager, meta_path)
        _validate_spec(lazy_module_name)
        lazy_module = _import_module(lazy_module_name)
        assert isinstance(lazy_module, types.ModuleType)

    _validate_context_on_exit(context_manager, meta_path)


def test_lazy_import_module_item(
    strategy: type[LazyImportingStrategy],
    lazy_module_name: str,
) -> None:
    """Test the lazy_importing library."""
    # We're doing little gymnastics here because pytest
    # tracks assert statements in the local namespace. —_—
    local_ns = locals()
    meta_path = sys.meta_path

    with LazyImportingContextManager(
        strategy=strategy,
        local_ns=local_ns,
    ) as context_manager:
        _validate_context_on_enter(context_manager, meta_path)
        _validate_spec(lazy_module_name)
        lazy_module = _import_module(lazy_module_name)
        lazy_object = lazy_module.lazy_object
        assert isinstance(lazy_object, LazyObject)
        ident_1 = "lazy_object_ref_1"
        ident_2 = "lazy_object_ref_2"
        refs = dict.fromkeys((ident_1, ident_2), lazy_object)
        local_ns.update(refs)

    _validate_context_on_exit(context_manager, meta_path)
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
        lazy_module = _import_module(lazy_module_name)
        assert type(lazy_module) is types.ModuleType
        assert loaded_lazy_object == lazy_module.lazy_object

    _access_object()
