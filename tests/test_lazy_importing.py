from __future__ import annotations

import sys
import types
from contextlib import suppress
from functools import reduce
from importlib.util import find_spec
from typing import TYPE_CHECKING

import pytest

from lazy_importing import (
    LazyImporting,
    LazilyLoadedObject,
    LazyModuleWrapper,
    supports_lazy_access
)
from lazy_importing.cm import LazyObjectLoader
from lazy_importing.importer import lazy_loading

if TYPE_CHECKING:
    from collections.abc import Iterator

    from importlib.machinery import ModuleSpec


@pytest.fixture
def lazy_module_name() -> Iterator[str]:
    """Return the name of the lazy module."""
    yield "tests._lazy_module"


def _purge_module(module_name: str) -> None:
    """Remove a module from the module cache by name."""
    with suppress(KeyError):
        del sys.modules[module_name]


@pytest.fixture(autouse=True)
def purge_lazy_module(lazy_module_name: str) -> None:
    """Remove the lazy module from the module cache."""
    _purge_module(lazy_module_name)


def _validate_spec(lazy_module_name: str) -> ModuleSpec:
    """Return the name of the lazy module."""
    spec: ModuleSpec | None = find_spec(lazy_module_name, ".")
    assert spec is not None
    assert getattr(spec, "__lazy_spec__", False)
    return spec


def _import_lazy_module(lazy_module_name: str) -> types.ModuleType:
    """Return the name of the lazy module."""
    attrs = lazy_module_name.split(".")[1:]
    return reduce(getattr, attrs, __import__(lazy_module_name))


def test_lazy_import_module(lazy_module_name: str) -> None:
    """Test the lazy_importing library."""
    with LazyImporting() as LAZY_IMPORTING:
        assert sys.meta_path == [LAZY_IMPORTING._lazy_importer]
        _validate_spec(lazy_module_name)
        lazy_module = _import_lazy_module(lazy_module_name)
        assert isinstance(lazy_module, LazyModuleWrapper)


def test_lazy_import_module_item(lazy_module_name: str) -> None:
    """Test the lazy_importing library."""
    # We're doing little gymnastics here because pytest
    # tracks assert statements in the local namespace. —_—
    local_ns = locals()

    with LazyImporting(local_ns=local_ns) as LAZY_IMPORTING:
        context = LAZY_IMPORTING._context
        assert context.get(lazy_loading)
        importer = LAZY_IMPORTING._lazy_importer
        assert sys.meta_path == [importer]
        assert importer._context is context
        _validate_spec(lazy_module_name)
        lazy_module = _import_lazy_module(lazy_module_name)
        lazy_object = lazy_module.lazy_object
        assert isinstance(lazy_object, LazilyLoadedObject)
        ident_1 = "lazy_object_ref_1"
        ident_2 = "lazy_object_ref_2"
        refs = dict.fromkeys((ident_1, ident_2), lazy_object)
        local_ns.update(refs)

    assert not context.get(lazy_loading)
    assert ident_1 not in local_ns and ident_2 not in local_ns

    builtins = local_ns["__builtins__"]
    assert isinstance(builtins, LazyObjectLoader)
    assert builtins.__lazy_objects__.get(ident_1) is lazy_object
    assert builtins.__lazy_objects__.get(ident_2) is lazy_object

    @supports_lazy_access
    def _access_object() -> None:
        loaded_lazy_object = builtins[ident_1]
        assert ident_1 in local_ns
        assert ident_2 in local_ns  # auto binding
        _purge_module(lazy_module_name)
        lazy_module = _import_lazy_module(lazy_module_name)
        assert type(lazy_module) is types.ModuleType
        assert loaded_lazy_object == lazy_module.lazy_object

    _access_object()
