"""A module for the class of lazily-imported object placeholders."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slothy.audits import on_lazy_object_delattr, on_lazy_object_setattr

if TYPE_CHECKING:
    from importlib.machinery import ModuleSpec
    from typing import Any


__all__ = ("LazyObjectPlaceholder",)


class LazyObjectPlaceholder:
    """
    A placeholder for an object imported lazily.

    Capable of collecting state that normally modules would.
    """

    __name__: str
    __loader__: str
    __spec__: ModuleSpec
    __package__: str

    def __setattr__(self, attr: str, value: Any) -> None:
        """Intercept attribute assignment and raise an error if it's attempted."""
        on_lazy_object_setattr(self, attr, value)
        super().__setattr__(attr, value)

    def __delattr__(self, attr: str) -> None:
        """Intercept attribute assignment and raise an error if it's attempted."""
        on_lazy_object_delattr(self, attr)
        super().__delattr__(attr)

    @property
    def __path__(self) -> list[str]:
        """The path list necessary to allow declaring package imports."""
        return []

    if __debug__:

        def __repr__(self) -> str:
            """Return an informative representation of this lazy object."""
            # Needs decision: try to `textwrap.shorten()` on the module name?
            name = getattr(self, "__name__", None)
            state = name or ""
            if None in (
                name,
                getattr(self, "__spec__", None),
                getattr(self, "__package__", None),
            ):
                state += " (in construction)"
            return f"<lazy object {state}>"
