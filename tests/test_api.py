from __future__ import annotations

import sys
from importlib import import_module
from itertools import accumulate
from typing import TYPE_CHECKING

import pytest

from lazy_importing import (
    LazyObject,
    LazyObjectLoader,
    LazyImportingContext,
    supports_lazy_access
)
from tests.state import assert_importing, assert_inactive

if TYPE_CHECKING:
    from collections.abc import Iterator


LAZY_ATTRIBUTE_NAME: str = "lazy_object"


@pytest.fixture(
    scope="function",
    params=(
        "lazy_module",
        "lazy_namespace.inner_lazy_module",
        "lazy_namespace.inner_lazy_namespace.inner_inner_lazy_module",
    )
)
def module_name(request: pytest.FixtureRequest) -> Iterator[str]:
    """Return the name of the lazy module."""
    yield request.param


@pytest.fixture
def ident() -> Iterator[str]:
    """Return the name of the lazy module."""
    yield "foo"


def _test_on_enter(context_manager: LazyImportingContext) -> None:
    """Return the name of the lazy module."""
    context = context_manager.context
    context.run(assert_importing)
    importer = context_manager.importer
    assert importer.meta_path is not sys.meta_path
    assert importer.context is context


def _test_on_exit(context_manager: LazyImportingContext) -> None:
    """Return the name of the lazy module."""
    context = context_manager.context
    context.run(assert_inactive)
    importer = context_manager.importer
    assert importer.meta_path is sys.meta_path
    assert importer.context is context

    with pytest.raises(RuntimeError, match="Cannot enter .+ twice."):
        context_manager.__enter__()


def test_lazy_import_module(module_name: str, ident: str) -> None:
    """Test importing an entire module lazily, i.e. `import X` statements."""
    local_ns: dict[str, object] = {}

    with LazyImportingContext(local_ns=local_ns) as context_manager:
        _test_on_enter(context_manager)

        module = import_module(module_name)
        assert isinstance(module, LazyObject)
        local_ns[ident] = module

    assert ident not in local_ns

    parts = module_name.split(".")
    for consecutive_name in accumulate(parts, lambda *parts: ".".join(parts)):
        assert consecutive_name not in sys.modules

    _test_on_exit(context_manager)


def test_lazy_import_module_item(module_name: str, ident: str) -> None:
    """Test importing an entire module lazily, i.e. `from X import Y` statements."""
    module_name += "." + LAZY_ATTRIBUTE_NAME
    local_ns: dict[str, object] = {}

    with LazyImportingContext(local_ns=local_ns) as context_manager:
        _test_on_enter(context_manager)

        item = import_module(module_name)
        assert isinstance(item, LazyObject)
        local_ns[ident] = item

    assert ident not in local_ns

    parts = module_name.split(".")
    for consecutive_name in accumulate(parts, lambda *parts: ".".join(parts)):
        assert consecutive_name not in sys.modules

    _test_on_exit(context_manager)
