from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.tests import Test

__all__ = ("a", "b")

a = 1
b = 2


@property  # type: ignore[misc]
def c(self: object) -> object:
    return self


@c.setter
def c(self: Test, value: object) -> None:
    self.desc_set_called = True


@c.deleter
def c(self: Test) -> None:
    self.desc_delete_called = True
