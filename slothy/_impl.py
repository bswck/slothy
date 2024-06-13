"""
The core implementation of slothy importing.

Inspired by https://gist.github.com/JelleZijlstra/23c01ceb35d1bc8f335128f59a32db4c.
"""

# ruff: noqa: SLF001, FBT003
from __future__ import annotations

from contextlib import contextmanager, nullcontext
from contextvars import ContextVar, copy_context
from functools import partial
from sys import modules
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from contextlib import AbstractContextManager
    from types import FrameType
    from typing import Any

try:
    from sys import _getframe as get_frame
except AttributeError as err:
    msg = (
        "This Python implementation does not support `sys._getframe()` "
        "and thus cannot use `slothy`; do not import `slothy` from "
        f"`{__name__}`, import from the public interface instead"
    )
    raise RuntimeError(msg) from err

__all__ = ("slothy",)


@contextmanager
def slothy(stack_offset: int = 2) -> Iterator[None]:
    """
    Use slothy imports in a `with` statement.

    Parameters
    ----------
    stack_offset
        The stack offset to use.

    Returns
    -------
    Iterator[None]
        Context manager's underlying generator.

    """
    frame = get_frame(stack_offset)
    try:
        builtin_import = frame.f_builtins["__import__"]
    except KeyError:
        msg = "__import__ not found"
        raise ImportError(msg) from None
    frame.f_builtins["__import__"] = _SlothyImportWrapper(
        partial(
            _slothy_import_locally,
            frame.f_globals["__name__"],
            builtin_import,
            _stack_offset=2,
        )
    )
    try:
        yield
    finally:
        _process_slothy_objects(frame.f_locals)
        # Important note: we assume that the built-in `__import__` was not
        # patched before.
        frame.f_builtins["__import__"] = builtin_import


class _SlothyImportWrapper(NamedTuple):
    """Internal slothy import wrapper."""

    import_: Callable[..., object]

    def __call__(self, *args: object, **kwds: object) -> object:
        return self.import_(*args, **kwds)


def slothy_if(condition: object, stack_offset: int = 3) -> AbstractContextManager[None]:
    """
    Use slothy imports only if condition is true.

    Parameters
    ----------
    condition
        The condition to evaluate.
    stack_offset
        The stack offset to use.

    Returns
    -------
    AbstractContextManager[None]
        The context manager.

    """
    return slothy(stack_offset) if condition else nullcontext()


def _process_slothy_objects(local_ns: dict[str, object]) -> None:
    """
    Bind slothy objects and their aliases to special keys triggering on lookup.

    This function has a side effect of cleaning up [`sys.modules`][]
    from slothily-imported modules.

    Parameters
    ----------
    local_ns
        The local namespace where the slothy objects are stored.

    """
    for ref, value in local_ns.copy().items():
        if not isinstance(value, SlothyObject):
            continue
        if isinstance(ref, SlothyKey):
            ref.obj = value
            continue
        local_ns[SlothyKey(ref, value)] = value  # type: ignore[index]
        modules.pop(value._SlothyObject__args.module_name, None)


class _ImportArgs(NamedTuple):
    """Arguments eventually passed to [`builtins.__import__`]."""

    module_name: str
    global_ns: dict[str, object]
    local_ns: dict[str, object]
    from_list: tuple[str, ...]
    level: int


class SlothyObject:
    """Slothy object."""

    _SlothyObject__args: _ImportArgs
    _SlothyObject__builtins: dict[str, Any]
    _SlothyObject__attr: str | None
    _SlothyObject__source: str | None
    _SlothyObject__refs: set[str]
    _SlothyObject__import: Callable[[Callable[..., object] | None], None]

    def __init__(
        self,
        args: _ImportArgs,
        builtins: dict[str, Any],
        attr: str | None = None,
        source: str | None = None,
    ) -> None:
        """
        Create a new slothy object.

        Parameters
        ----------
        args
            The arguments to pass to [`builtins.__import__`].
        builtins
            The builtins namespace.
        attr
            The attribute to import.
        source
            The source of the import.

        """
        super().__init__()
        self.__args = args
        self.__builtins = builtins
        self.__attr = attr
        self.__source = source
        self.__refs: set[str] = set()

    def __import(self, builtin_import: Callable[..., object] | None = None) -> object:
        """Actually import the object."""
        if builtin_import is None:
            try:
                builtin_import = self.__builtins["__import__"]
            except KeyError:
                msg = "__import__ not found"
                raise ImportError(msg) from None
        try:
            module = builtin_import(*self.__args)
            obj = getattr(module, self.__attr) if self.__attr is not None else module
        except BaseException as exc:  # noqa: BLE001
            args = exc.args
            if self.__source:
                args = (
                    (args[0] if args else "")
                    + f" (caught on slothy import from {self.__source})",
                    *args[1:],
                )
            exc = type(exc)(*args).with_traceback(exc.__traceback__)
            raise exc from None
        local_ns = self.__args.local_ns
        ctx = copy_context()
        ctx.run(binding.set, True)
        for ref in self.__refs:
            existing_value = ctx.run(local_ns.get, ref)
            if isinstance(existing_value, SlothyObject):
                ctx.run(local_ns.__setitem__, ref, obj)
        return obj

    def __set_name__(self, owner: object, name: str) -> None:
        """Set the name of the object."""
        self.__refs.add(name)

    def __get__(self, inst: object, owner: type[object] | None = None) -> object:
        """Import on-demand via descriptor protocol."""
        obj = self.__import()
        if hasattr(obj, "__get__"):
            return obj.__get__(inst, owner)
        return obj

    def __set__(self, inst: object, value: object) -> None:
        """Import on-demand via descriptor protocol."""
        obj = self.__import()
        if hasattr(obj, "__set__"):
            obj.__set__(inst, value)

    def __delete__(self, inst: object) -> None:
        """Import on-demand via descriptor protocol."""
        obj = self.__import()
        if hasattr(obj, "__delete__"):
            obj.__delete__(inst)

    def __repr__(self) -> str:
        """Represent the slothy object using a simulated import statement."""
        source = self.__source or ""
        if source:
            source = " " + source.join("()")
        attr = self.__attr
        if attr is None:
            return f"<import {self.__args.module_name}{source}>"
        if attr in self.__args.from_list:
            return f"<from {self.__args.module_name} import {attr}{source}>"
        return f"<import {self.__args.module_name}.{attr}{source}>"

    def __getattr__(self, attr: str) -> object:
        """Allow import chains."""
        return SlothyObject(
            args=self.__args,
            builtins=self.__builtins,
            attr=attr,
            source=self.__source,
        )


class SlothyObjectWithList(SlothyObject):
    """Slothy object used in `from ... import ...` imports."""

    def __getattr__(self, attr: str) -> object:
        if attr not in self._SlothyObject__args.from_list:
            raise AttributeError(attr)
        return super().__getattr__(attr)


binding: ContextVar[bool] = ContextVar("binding", default=False)


class SlothyKey:
    """Slothy key. Activates on identifier lookup."""

    def __init__(self, key: str, obj: SlothyObject) -> None:
        """
        Create a new slothy key.

        Parameters
        ----------
        key
            The key to use.
        obj
            The object to use.

        """
        obj._SlothyObject__refs.add(key)
        self.key = key
        self.obj = obj
        self._hash = hash(key)
        self._import = obj._SlothyObject__import
        self._do_refresh = True

    def __eq__(self, key: object) -> bool:
        """
        Check if the key is equal to another key.

        This method is called when other modules using slothy request
        slothily-imported identifiers.

        Parameters
        ----------
        key
            The key to check.

        Returns
        -------
        bool
            Whether the keys are equal.

        """
        if not isinstance(key, str):
            return NotImplemented
        elif key != self.key:  # noqa: RET505, for microoptimization
            return False
        elif binding.get():
            return True
        their_import = self.obj._SlothyObject__builtins.get("__import__")
        if not isinstance(their_import, _SlothyImportWrapper):
            self._import(their_import)
            return True
        local_ns = self.obj._SlothyObject__args.local_ns
        if self._do_refresh:
            del local_ns[key]
            local_ns[self] = self.obj  # type: ignore[index]
            self._do_refresh = False
        return True

    def __hash__(self) -> int:
        """Get the hash of the key."""
        return self._hash


def _format_source(frame: FrameType) -> str:
    """Refer to an import in the `<file name>:<line number>` format."""
    return f"{frame.f_code.co_filename}:{frame.f_lineno}"


def slothy_import(
    name: str,
    global_ns: dict[str, object] | None = None,
    local_ns: dict[str, object] | None = None,
    from_list: tuple[str, ...] | None = None,
    level: int = 0,
    _stack_offset: int = 1,
) -> object:
    """
    Slothy import.

    Equivalent to [`builtins.__import__`]. The difference is that
    the returned object will be a `SlothyObject` instead of the actual object.
    """
    if from_list is None:
        from_list = ()
    if "*" in from_list:
        msg = "Wildcard slothy imports are not supported"
        raise RuntimeError(msg)
    frame = get_frame(_stack_offset)
    if global_ns is None:
        global_ns = frame.f_globals
    if local_ns is None:
        local_ns = frame.f_locals
    args = _ImportArgs(name, global_ns, local_ns, from_list, level)
    source = _format_source(frame)
    if from_list:
        return SlothyObjectWithList(args=args, builtins=frame.f_builtins, source=source)
    return SlothyObject(args=args, builtins=frame.f_builtins, source=source)


def _slothy_import_locally(
    _target: str,
    _builtin_import: Callable[..., object],
    name: str,
    global_ns: dict[str, object] | None = None,
    local_ns: dict[str, object] | None = None,
    from_list: tuple[str, ...] | None = None,
    level: int = 0,
    _stack_offset: int = 1,
) -> object:
    """Slothily import an object only if requested in a `with slothy():` statement."""
    frame = get_frame(_stack_offset)
    if frame.f_globals["__name__"] == _target:
        return slothy_import(name, global_ns, local_ns, from_list, level)
    return _builtin_import(name, global_ns, local_ns, from_list or (), level)
