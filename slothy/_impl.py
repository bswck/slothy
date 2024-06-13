"""
The core implementation of slothy importing.

Inspired by https://gist.github.com/JelleZijlstra/23c01ceb35d1bc8f335128f59a32db4c.
"""

# ruff: noqa: SLF001, FBT003
from __future__ import annotations

from contextlib import contextmanager, nullcontext
from contextvars import ContextVar, copy_context
from functools import partial, reduce
from pathlib import Path
from sys import modules
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from contextlib import AbstractContextManager
    from types import FrameType, ModuleType
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
def slothy(*, prevent_eager: bool = False, stack_offset: int = 2) -> Iterator[None]:  # noqa: ARG001
    """
    Use slothy imports in a `with` statement.

    Parameters
    ----------
    prevent_eager
        If True, will raise a `RuntimeError` if slothy cannot guarantee
        to not fall back to eager imports on unsupported Python implementation.
        On supported Python implementations this parameter doesn't change the behavior.
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
            _stack_offset=stack_offset,
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


def slothy_if(
    condition: object,
    *,
    prevent_eager: bool = False,
    stack_offset: int = 3,
) -> AbstractContextManager[None]:
    """
    Use slothy imports only if condition evaluates to truth.

    Parameters
    ----------
    condition
        The condition to evaluate.
    prevent_eager
        If True, will raise a `RuntimeError` if slothy cannot guarantee
        to not fall back to eager imports on unsupported Python implementation.
        On supported Python implementations this parameter doesn't change the behavior.
    stack_offset
        The stack offset to use.

    Returns
    -------
    AbstractContextManager[None]
        The context manager.

    """
    return (
        slothy(prevent_eager=prevent_eager, stack_offset=stack_offset)
        if condition
        else nullcontext()
    )


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
        module_name = value._SlothyObject__args.module_name
        modules.pop(module_name, None)


class _ImportArgs(NamedTuple):
    """Arguments eventually passed to [`builtins.__import__`]."""

    module_name: str
    global_ns: dict[str, object]
    local_ns: dict[str, object]
    from_list: tuple[str, ...]
    level: int


def _module_get_attr_path(
    import_args: _ImportArgs,
    module: ModuleType,
    attrs: tuple[str, ...],
) -> object:
    root = attrs[0]
    attr_path = ".".join(attrs)
    try:
        obj = getattr(module, root)
    except AttributeError as err:
        spec = module.__spec__
        location = "unknown location"
        module_name = import_args.module_name
        if spec is not None:
            module_name = spec.name
            location = getattr(module, "__file__", None) or location
        suffix = " " + location.join("()")
        if root in import_args.from_list:
            msg = f"cannot import name {attr_path!r} from {module_name!r}" + suffix
            raise ImportError(msg) from err
        raise
    else:
        obj = reduce(getattr, attrs[1:], obj)
    return obj


def _get_builtin_import(builtins: dict[str, Any]) -> Callable[..., Any]:
    try:
        builtin_import: Callable[..., Any] = builtins["__import__"]
    except KeyError:
        msg = "__import__ not found"
        raise ImportError(msg) from None
    return builtin_import


class SlothyObject:
    """Slothy object."""

    _SlothyObject__args: _ImportArgs
    _SlothyObject__builtins: dict[str, Any]
    _SlothyObject__attr_path: tuple[str, ...]
    _SlothyObject__source: str | None
    _SlothyObject__refs: set[str]
    _SlothyObject__desc_ref: str | None
    _SlothyObject__import: Callable[[Callable[..., ModuleType] | None], None]

    def __init__(
        self,
        args: _ImportArgs,
        builtins: dict[str, Any],
        attr_path: tuple[str, ...] = (),
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
        attr_path
            The attributes to pull from the imported object.
        source
            The source of the import.

        """
        super().__init__()
        self.__args = args
        self.__builtins = builtins
        self.__attr_path = attr_path
        self.__source = source
        self.__refs: set[str] = set()

    def __import(
        self,
        builtin_import: Callable[..., ModuleType] | None = None,
    ) -> object:
        """Actually import the object."""
        if builtin_import is None:
            builtin_import = _get_builtin_import(self.__builtins)
        try:
            import_args = self.__args
            module = builtin_import(*import_args)
            attrs = self.__attr_path
            obj = _module_get_attr_path(import_args, module, attrs) if attrs else module
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
        builtin_import = _get_builtin_import(self.__builtins)
        if isinstance(builtin_import, _SlothyImportWrapper):
            return self
        obj = self.__import()
        if hasattr(obj, "__get__"):
            return obj.__get__(inst, owner)
        return obj

    def __set__(self, inst: object, value: object) -> None:
        """Import on-demand via descriptor protocol."""
        builtin_import = _get_builtin_import(self.__builtins)
        if isinstance(builtin_import, _SlothyImportWrapper):
            return
        obj = self.__import()
        if hasattr(obj, "__set__"):
            obj.__set__(inst, value)

    def __delete__(self, inst: object) -> None:
        """Import on-demand via descriptor protocol."""
        builtin_import = _get_builtin_import(self.__builtins)
        if isinstance(builtin_import, _SlothyImportWrapper):
            return
        obj = self.__import()
        if hasattr(obj, "__delete__"):
            obj.__delete__(inst)

    def __repr__(self) -> str:
        """Represent the slothy object using a simulated import statement."""
        source = self.__source or ""
        if source:
            source = " " + source.join("()")
        attrs = self.__attr_path
        targets = ".".join(attrs)
        attr = next(iter(attrs), None)
        module_name = self.__args.module_name
        from_list = self.__args.from_list
        if attr is None:
            return f"<import {module_name}{source}>"
        if attr in from_list:
            if from_list[0] != attr:
                targets = f"..., {targets}"
            if from_list[-1] != attr:
                targets += ", ..."
            return f"<from {module_name} import {targets}{source}>"
        return f"<import {module_name}.{targets}{source}>"

    def __getattr__(self, attr: str) -> object:
        """Allow import chains."""
        return SlothyObject(
            args=self.__args,
            builtins=self.__builtins,
            attr_path=(*self.__attr_path, attr),
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
    """Slothy key. Activates on namespace lookup."""

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
    orig_filename = frame.f_code.co_filename
    # Canonical names like "<stdin>"
    if orig_filename.startswith("<") and orig_filename.endswith(">"):
        filename = orig_filename
    else:
        filename = str(Path(frame.f_code.co_filename).resolve())
    return f'file "{filename}", line {frame.f_lineno}'


def slothy_import(
    name: str,
    global_ns: dict[str, object] | None = None,
    local_ns: dict[str, object] | None = None,
    from_list: tuple[str, ...] | None = None,
    level: int = 0,
    _stack_offset: int = 1,
) -> SlothyObject:
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
        offset = _stack_offset + 1
        return slothy_import(name, global_ns, local_ns, from_list, level, offset)
    return _builtin_import(name, global_ns, local_ns, from_list or (), level)
