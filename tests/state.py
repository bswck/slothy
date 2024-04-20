from __future__ import annotations

from lazy_importing.abc import importing, lazy_loading


def assert_lazy_loading(module_name: str | None = None) -> None:
    loading_state, importing_state = lazy_loading.get(), importing.get()
    where = f" in module {module_name}" if module_name else ""
    assert not importing_state, (
        "expected only loading, got mutually exclusive state: "
        "loading and importing at the same time" + where
    ) if loading_state else "expected loading state, got importing" + where


def assert_importing(module_name: str | None = None) -> None:
    importing_state, loading_state = importing.get(), lazy_loading.get()
    where = f" in module {module_name}" if module_name else ""
    assert not loading_state, (
        "expected only importing, got mutually exclusive state: "
        "importing and loading at the same time" + where
    ) if importing_state else "expected importing state, got loading" + where


def assert_inactive(module_name: str | None = None) -> None:
    importing_state, loading_state = importing.get(), lazy_loading.get()
    where = f" in module {module_name}" if module_name else ""
    assert not (importing_state and loading_state), (
        "expected inactive state, got mutually exclusive state: "
        "importing and loading at the same time" + where
    )
    assert not importing.get(), "expected inactive state, got importing" + where
    assert not lazy_loading.get(), "expected inactive state, got loading" + where
