from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.tests import Test

__all__ = ("a_int", "b_int")

a_int = 1
b_int = 2


@property  # type: ignore[misc]
def c_property(self: object) -> object:
    return self


@c_property.setter
def c_property(self: Test, value: object) -> None:
    self.desc_set_called = True


@c_property.deleter
def c_property(self: Test) -> None:
    self.desc_delete_called = True
