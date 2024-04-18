# SPDX-License-Identifier: MIT
# (C) 2024-present Bartosz Sławecki (bswck)
"""
`lazy_importing`.

Super-easy lazy importing in Python.
"""
# ruff: noqa: F403, PLE0604

from __future__ import annotations

from lazy_importing import cm, compat, importer
from lazy_importing.cm import *
from lazy_importing.compat import *
from lazy_importing.importer import *

__all__ = (
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
