"""
The core implementation of slothy importing.

Inspired by https://gist.github.com/JelleZijlstra/23c01ceb35d1bc8f335128f59a32db4c.
"""

# ruff: noqa: SLF001, FBT003, PLR0913
from __future__ import annotations

from contextlib import contextmanager, nullcontext
from contextvars import ContextVar, copy_context
from functools import partial
from pathlib import Path
from sys import modules
from typing import TYPE_CHECKING, Any, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from contextlib import AbstractContextManager
    from types import FrameType, ModuleType
    from typing import Final
    from weakref import WeakSet

    from typing_extensions import Self

try:
    from sys import _getframe as get_frame
except AttributeError as err:  # pragma: no cover
    msg = (
        "This Python implementation does not support `sys._getframe()` "
        "and thus cannot use `slothy_importing`; do not import `slothy_importing` from "
        f"`{__name__}`, import from the public interface instead"
    )
    raise RuntimeError(msg) from err


__all__ = ("slothy_importing", "slothy_importing_if", "type_importing")


FALLBACK_MISSING: Final = object()


@contextmanager
def slothy_importing(
    *,
    prevent_eager: bool = True,  # noqa: ARG001
    stack_offset: int = 1,
    _fallback: object = FALLBACK_MISSING,
) -> Iterator[None]:
    """
    Use slothy imports in a `with` statement.

    Parameters
    ----------
    prevent_eager
        If True, will raise a `RuntimeError` if slothy cannot guarantee
        to not fall back to eager imports on unsupported Python implementation.
        On supported Python implementations this parameter doesn't change the behavior.
        A general recommendation is to set this to `True` in applications
        and `False` in libraries.
    stack_offset
        The stack offset to use.

    Returns
    -------
    Iterator[None]
        Context manager's underlying generator.

    """
    frame = get_frame(stack_offset + 1)  # +1 from @contextmanager
    builtin_import = _get_builtin_import(frame.f_builtins)

    import_wrapper = partial(
        _slothy_import_locally,
        _target=frame.f_globals["__name__"],
        _builtin_import=builtin_import,
    )
    import_wrapper.__slothy__ = True  # type: ignore[attr-defined]

    frame.f_builtins["__import__"] = import_wrapper
    try:
        yield
    finally:
        _process_slothy_objects(frame.f_locals, fallback=_fallback)
        frame.f_builtins["__import__"] = builtin_import


def type_importing(
    *,
    default_type: object = Any,
    stack_offset: int = 1,
) -> AbstractContextManager[None]:
    """
    Use this to import symbols recognized by type checkers that do not exist at runtime.

    This function should generally be considered a runtime-friendly alternative to
    using `if typing.TYPE_CHECKING`.

    Parameters
    ----------
    default_type
        The item to import in case of a failure. Defaults to [`typing.Any`][]
    stack_offset
        The stack offset to use.

    Returns
    -------
    AbstractContextManager[None]
        The context manager.

    """
    return slothy_importing(
        prevent_eager=True,
        stack_offset=stack_offset,
        _fallback=default_type,
    )


def slothy_importing_if(
    condition: object,
    *,
    prevent_eager: bool = True,
    stack_offset: int = 1,
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
        A general recommendation is to set this to `True` in applications
        and `False` in libraries.
    stack_offset
        The stack offset to use.

    Returns
    -------
    AbstractContextManager[None]
        The context manager.

    """
    return (
        slothy_importing(prevent_eager=prevent_eager, stack_offset=stack_offset)
        if condition
        else nullcontext()
    )


def _is_slothy_import(obj: object) -> object:
    """Determine if an `__import__` function is slothy-managed."""
    return getattr(obj, "__slothy__", None)


def _process_slothy_objects(
    local_ns: dict[str, object],
    fallback: object = FALLBACK_MISSING,
) -> None:
    """
    Bind slothy objects and their aliases to special keys triggering on lookup.

    This function has a side effect of cleaning up [`sys.modules`][]
    from slothily-imported modules.

    Parameters
    ----------
    local_ns
        The local namespace where the slothy objects are stored.

    fallback
        The fallback object to bind to all objects in case their delayed imports fail.

    """
    for ref, value in local_ns.copy().items():
        if not isinstance(value, SlothyObject):
            continue

        value._SlothyObject__fallback = fallback

        if isinstance(ref, _SlothyKey):
            ref.obj = value
            continue

        local_ns[_SlothyKey(ref, value)] = value
        module_name = value._SlothyObject__args.module_name
        modules.pop(module_name, None)


class _ImportArgs(NamedTuple):
    """Arguments eventually passed to [`builtins.__import__`][]."""

    module_name: str
    global_ns: dict[str, object]
    local_ns: dict[str, object]
    from_list: tuple[str, ...]
    level: int


def _import_item_from_list(
    import_args: _ImportArgs,
    builtin_import: Callable[..., ModuleType],
    module: ModuleType,
    item_from_list: str,
) -> object:
    """Import an item in a `from ... import item` statement."""
    # https://docs.python.org/3/reference/simple_stmts.html#import
    # 1. Check if the imported module has an attribute by that name.
    # 2. If not, attempt to import a submodule with that name
    #    and then check the imported module again for that attribute.
    #    If the attribute is not found, raise ImportError.
    #    Otherwise, store a reference to that value in the local namespace
    #    using the name in the as clause if it is present,
    #    otherwise using the attribute name.
    module_name = getattr(module.__spec__, "name", None) or import_args.module_name
    location = getattr(module, "__file__", None) or "unknown location"
    try:
        obj = getattr(module, item_from_list)
    except AttributeError:
        try:
            builtin_import(
                f"{module_name}.{item_from_list}",
                import_args.global_ns,
                import_args.local_ns,
                import_args.from_list or (),
                import_args.level,
            )
        except ImportError:
            pass
        except Exception as tentative_exc:  # noqa: BLE001
            raise tentative_exc from None
        else:
            try:
                # This should always be a module.
                # https://docs.python.org/3/reference/import.html#submodules
                obj = getattr(module, item_from_list)
            except AttributeError:
                pass
            else:
                return obj
        msg = (
            f"cannot import name {item_from_list!r} from {module_name!r} "
            f"({location})"
        )
        raise ImportError(msg) from None
    return obj


def _get_builtin_import(builtins: dict[str, Any]) -> Callable[..., Any]:
    try:
        builtin_import: Callable[..., Any] = builtins["__import__"]
    except KeyError:  # pragma: no cover
        # No possibility of running into this unless (1) you're manually setting
        # `__builtins__` namespace that lacks the `__import__` function or (2) you
        # removed the `__import__` key from parent or target frame's `f_builtins`.
        # This is so unlikely to happen!
        msg = "__import__ not found"
        raise ImportError(msg) from None
    return builtin_import


class SlothyObject:
    """Slothy object. You should not be using this directly."""

    if TYPE_CHECKING:
        _SlothyObject__args: _ImportArgs
        _SlothyObject__builtins: dict[str, Any]
        _SlothyObject__item_from_list: str
        _SlothyObject__source: str | None
        _SlothyObject__fallback: object
        _SlothyObject__refs: set[str]
        _SlothyObject__import: Callable[[Callable[..., ModuleType] | None], None]

        # Trackers are used for garbage collection testing.
        # Set your tracker here.
        __slothy_tracker__: WeakSet[SlothyObject]

    def __init__(
        self,
        args: _ImportArgs,
        builtins: dict[str, Any],
        item_from_list: str | None = None,
        source: str | None = None,
    ) -> None:
        """
        Create a new slothy object.

        Parameters
        ----------
        args
            The arguments to pass to [`builtins.__import__`][].
        builtins
            The builtins namespace.
        item_from_list
            One item in a `from ... import [item1, item2, ...]` import.
        source
            The source of the import.

        """
        super().__init__()
        self.__args = args
        self.__builtins = builtins
        self.__item_from_list = item_from_list
        self.__source = source
        self.__fallback = FALLBACK_MISSING
        self.__refs: set[str] = set()

        if hasattr(self, "__slothy_tracker__"):
            self.__slothy_tracker__.add(self)

    def __import(self, builtin_import: Callable[..., ModuleType]) -> object:
        """Actually import the object."""
        ctx = copy_context()
        ctx.run(binding.set, True)

        @partial(partial, ctx.run)
        def manage_scope(*, remove: bool) -> None:
            local_ns = self.__args.local_ns
            for ref in self.__refs:
                existing_value = local_ns.get(ref)
                if existing_value is self:
                    del local_ns[ref]
                    if not remove:
                        local_ns[ref] = obj

        try:
            import_args = self.__args
            module = builtin_import(*import_args)
            if self.__item_from_list:
                obj = _import_item_from_list(
                    import_args=import_args,
                    builtin_import=builtin_import,
                    module=module,
                    item_from_list=self.__item_from_list,
                )
            else:
                obj = module
        except BaseException as exc:  # noqa: BLE001
            fallback = self.__fallback
            if fallback is not FALLBACK_MISSING:
                obj = fallback
                manage_scope(remove=False)
                return fallback
            manage_scope(remove=True)
            args = exc.args
            if self.__source:
                args = (
                    (args[0] if args else "")
                    + f" (caused by delayed execution of {self.__source})",
                    *args[1:],
                )
            exc = type(exc)(*args).with_traceback(exc.__traceback__)
            raise exc from None
        else:
            manage_scope(remove=False)
            return obj

    def __set_name__(self, owner: type, name: str) -> None:
        """Set the name of the object."""
        msg = "Class-scoped slothy imports are not supported"
        raise RuntimeError(msg)

    def __repr__(self) -> str:
        """Represent the slothy object using a simulated import statement."""
        source = self.__source or ""
        if source:
            source = " " + source.join("()")

        item = self.__item_from_list
        module_name = self.__args.module_name
        from_list = self.__args.from_list

        if item is not None and item in from_list:
            target = item
            if from_list[0] != item:
                target = f"..., {item}"
            if from_list[-1] != item:
                target += ", ..."
            return f"<from {module_name} import {target}{source}>"

        # If there is an item but it doesn't exist in the `fromlist`, we ignore that.
        # slothy *does not* support manual `SlothyObject` creation,
        # so we assume the states of these objects to be consistent at all times.
        return f"<import {module_name}{source}>"

    def __getattr__(self, item: str) -> object:
        """Allow import chains."""
        if item == "__slothy_tracker__":
            raise AttributeError(item)
        if self.__args.from_list and self.__item_from_list is None:
            return SlothyObject(
                args=self.__args,
                builtins=self.__builtins,
                item_from_list=item,
                source=self.__source,
            )
        *_, last_module = self.__args.module_name.rsplit(".", 1)
        if item != last_module:
            raise AttributeError(item)
        return self


binding: ContextVar[bool] = ContextVar("binding", default=False)


class _SlothyKey(str):
    """Slothy key. Activates on namespace lookup."""

    __slots__: tuple[str, ...] = ("key", "obj", "_hash", "_import", "_should_refresh")

    if __debug__:
        # By default, only allow tracking in testing mode (with assertions enabled).
        __slots__ += ("__weakref__",)

    if TYPE_CHECKING:
        # Trackers are used for garbage collection testing.
        # Set your tracker here.
        __slothy_tracker__: WeakSet[_SlothyKey]

    def __new__(cls, key: str, obj: SlothyObject) -> Self:  # noqa: ARG003
        """Create a new slothy key."""
        return super().__new__(cls, key)

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
        self._should_refresh = True
        if hasattr(self, "__slothy_tracker__"):
            self.__slothy_tracker__.add(self)

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
        # Is that check necessary?
        elif key != self.key:  # pragma: no cover  # noqa: RET505 (elifs instead of ifs)
            return False
        elif binding.get():
            return True
        their_import = self.obj._SlothyObject__builtins.get("__import__")
        if not _is_slothy_import(their_import):
            self._import(their_import)
            return True
        local_ns = self.obj._SlothyObject__args.local_ns
        if self._should_refresh:
            del local_ns[key]
            local_ns[self] = self.obj
            self._should_refresh = False
        return True

    def __hash__(self) -> int:
        """Get the hash of the key."""
        return self._hash


def _format_source(frame: FrameType) -> str:
    """Refer to an import in the `<file name>:<line number>` format."""
    ffn = frame.f_code.co_filename
    # Empty and special names (like "<stdin>"). Same logic is used in `linecache`.
    if not ffn or ffn.startswith("<") and ffn.endswith(">"):  # pragma: no cover
        filename = ffn
    else:
        filename = str(Path(ffn).resolve())
    return f'"{filename}", line {frame.f_lineno}'


def _slothy_import(
    name: str,
    global_ns: dict[str, object],
    local_ns: dict[str, object],
    from_list: tuple[str, ...],
    level: int = 0,
    stack_offset: int = 1,
) -> SlothyObject:
    """
    Slothy import.

    Equivalent to [`builtins.__import__`][]. The difference is that
    the returned object will be a `SlothyObject` instead of the actual object.
    """
    if "*" in from_list:
        msg = "Wildcard slothy imports are not supported"
        raise RuntimeError(msg)
    frame = get_frame(stack_offset)
    args = _ImportArgs(name, global_ns, local_ns, from_list, level)
    source = _format_source(frame)
    return SlothyObject(args=args, builtins=frame.f_builtins, source=source)


def _slothy_import_locally(
    name: str,
    global_ns: dict[str, object] | None = None,
    local_ns: dict[str, object] | None = None,
    from_list: tuple[str, ...] | None = None,
    level: int = 0,
    *,
    _target: str,
    _builtin_import: Callable[..., object],
    _stack_offset: int = 1,
) -> object:
    """Slothily import an object only in slothy importing context manager."""
    if name in modules and (parent := name.split(".", 1)[0]) in modules:
        return modules[parent]
    frame = get_frame(_stack_offset)
    global_ns = frame.f_globals if global_ns is None else global_ns
    local_ns = frame.f_locals if local_ns is None else local_ns
    args = name, global_ns, local_ns, from_list or (), level
    if global_ns["__name__"] == _target:
        return _slothy_import(*args, _stack_offset + 1)
    return _builtin_import(*args)
