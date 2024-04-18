# SPDX-License-Identifier: MIT
# (C) 2024-present Bartosz Sławecki (bswck)
"""
`lazy_importing`.

Convenient lazy importing in Python.
"""

from __future__ import annotations

from lazy_importing import cm, compat, importer

__all__ = (  # noqa: PLE0604
    *cm.__all__,
    *compat.__all__,
    *importer.__all__,
)


LAZY_IMPORTING: cm.LazyImporting


def __dir__() -> tuple[str, ...]:
    return (*__all__, "LAZY_IMPORTING")


def __getattr__(name: str) -> object:
    if name == "LAZY_IMPORTING":
        return cm.LazyImporting(stack_offset=2)
    raise AttributeError
