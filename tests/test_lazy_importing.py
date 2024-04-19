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
from lazy_importing.importer import lazy_loading, lazy_objects

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
        identifier = lazy_object.identifier
        lazy_objects_reg = context.get(lazy_objects) or {}
        assert identifier in lazy_objects_reg
        assert identifier == "lazy_object"
        local_ns[identifier] = lazy_object  # again, pytest.

    assert not context.get(lazy_loading)
    assert context.get(lazy_objects) is lazy_objects_reg
    assert identifier in lazy_objects_reg

    builtins = local_ns["__builtins__"]

    @supports_lazy_access
    def _access_object() -> None:
        loaded_lazy_object = builtins["lazy_object"]
        _purge_module(lazy_module_name)
        lazy_module = _import_lazy_module(lazy_module_name)
        assert type(lazy_module) is types.ModuleType
        assert loaded_lazy_object == lazy_module.lazy_object

    _access_object()
