"""
Out of the box lazy importing strategies.

The subpackage includes:
- [`ast`](lazy_importing.strategies.ast).
  AST-based declarations with zero runtime overhead.
- [`half`](lazy_importing.strategies.half).
  Half-lazy importing (resolving module finders, but loading lazily).

"""
# ruff: noqa: F403, PLE0604

from __future__ import annotations

from lazy_importing.strategies import ast, half_lazy
from lazy_importing.strategies.ast import *
from lazy_importing.strategies.half_lazy import *

__all__ = (
    *ast.__all__,
    *half_lazy.__all__,
)
