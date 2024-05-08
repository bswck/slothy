"""All auditing events raised by lazy importing."""

from __future__ import annotations

from functools import partial
from sys import audit
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from importlib.machinery import ModuleSpec
    from types import ModuleType
    from typing import Any

    from typing_extensions import ParamSpec, TypeAlias

    from slothy.api import (
        SlothyContext,
        SlothyImporter,
        SlothyLoader,
    )
    from slothy.object import SlothyObject

    ExpectedArgs = ParamSpec("ExpectedArgs")
    Audit: TypeAlias = Callable[ExpectedArgs, None]


__all__ = (
    "AFTER_AUTOBIND",
    "AFTER_DISABLE",
    "AFTER_ENABLE",
    "AFTER_FIND_SPEC",
    "AFTER_INJECT_LOADER",
    "ALL_AUDITING_EVENTS",
    "BEFORE_AUTOBIND",
    "BEFORE_DISABLE",
    "BEFORE_ENABLE",
    "BEFORE_FIND_SPEC",
    "BEFORE_INJECT_LOADER",
    "CREATE_MODULE",
    "EXEC_MODULE",
    "LAZY_OBJECT_DELATTR",
    "LAZY_OBJECT_SETATTR",
)


ALL_AUDITING_EVENTS: set[str] = set()


def _event(name: str) -> str:
    ALL_AUDITING_EVENTS.add(name)
    return name


AuditFunc = partial(partial, audit)


BEFORE_ENABLE: str = _event("slothy.before_enable")
"""
Auditing event raised before enabling lazy importing.
Takes 1 argument: relevant [importer][slothy.api.SlothyImporter] object.
"""

before_enable: Audit[[SlothyImporter]] = AuditFunc(BEFORE_ENABLE)


AFTER_ENABLE: str = _event("slothy.after_enable")
"""
Auditing event raised after enabling lazy importing.
Takes 1 argument: relevant [importer][slothy.api.SlothyImporter] object.
"""

after_enable: Audit[[SlothyImporter]] = AuditFunc(AFTER_ENABLE)

BEFORE_DISABLE: str = _event("slothy.before_disable")
"""
Auditing event raised before disabling lazy importing.
Takes 1 argument: relevant [importer][slothy.api.SlothyImporter] object.
"""

before_disable: Audit[[SlothyImporter]] = AuditFunc(BEFORE_DISABLE)

AFTER_DISABLE: str = _event("slothy.after_disable")
"""
Auditing event raised after disabling lazy importing.
Takes 1 argument: relevant [importer][slothy.api.SlothyImporter] object.
"""

after_disable: Audit[[SlothyImporter]] = AuditFunc(AFTER_DISABLE)

BEFORE_FIND_SPEC: str = _event("slothy.before_find_spec")
"""
Auditing event raised before creating a temporary spec for a lazily imported module.
Takes 4 arguments:

- relevant [importer][slothy.api.SlothyImporter] object,
- module full name ([str][]),
- module path ([Sequence][collections.abc.Sequence][[str][]] or [None][]),
- module target ([types.ModuleType][] or [None][]).
"""

before_find_spec: Audit[
    [SlothyImporter, str, Sequence[str] | None, ModuleType | None]
] = AuditFunc(
    BEFORE_FIND_SPEC,
)

AFTER_FIND_SPEC: str = _event("slothy.after_find_spec")
"""
Auditing event raised after creating a temporary spec for a lazily imported module.
Takes 2 arguments:

- relevant [importer][slothy.api.SlothyImporter] object,
- newly created [module spec][importlib.machinery.ModuleSpec] object.
"""

after_find_spec: Audit[[SlothyImporter, ModuleSpec]] = AuditFunc(AFTER_FIND_SPEC)

CREATE_MODULE: str = _event("slothy.on_create_module")
"""
Auditing event raised after creating lazy object as a module
upon import system request.

Takes 3 arguments:

- relevant [importer][slothy.api.SlothyImporter] object,
- relevant [module spec][importlib.machinery.ModuleSpec] object.
- newly created [lazy object][slothy.object.SlothyObject].
"""

on_create_module: Audit[[SlothyImporter, ModuleSpec, SlothyObject]] = AuditFunc(
    CREATE_MODULE,
)

EXEC_MODULE: str = _event("slothy.on_exec_module")
"""
Auditing event raised when module execution is requested.
Takes 2 arguments:

- relevant [importer][slothy.api.SlothyImporter] object,
- relevant [lazy object][slothy.object.SlothyObject].
"""

on_exec_module: Audit[[SlothyImporter, SlothyObject]] = AuditFunc(EXEC_MODULE)

BEFORE_AUTOBIND: str = _event("slothy.before_autobind")
"""
Auditing event raised before automatically binding a lazy object in the targeted
namespace.
Takes 4 arguments:

- relevant [lazy object][slothy.object.SlothyObject],
- finally loaded object to replace the lazy object,
- targeted namespace,
- identifier of the object (collected upon
    [context manager][slothy.api.SlothyContext] exit).
"""

before_autobind: Audit[[SlothyObject, Any, dict[str, Any], str]] = AuditFunc(
    BEFORE_AUTOBIND,
)

AFTER_AUTOBIND: str = _event("slothy.after_autobind")
"""
Auditing event raised after automatically binding a lazy object in the targeted
namespace.
Takes 4 arguments:

- relevant [lazy object][slothy.object.SlothyObject],
- finally loaded object to replace the lazy object,
- targeted namespace,
- identifier of the object (collected upon
    [context manager][slothy.api.SlothyContext] exit).
"""

after_autobind: Audit[[SlothyObject, Any, dict[str, Any], str]] = AuditFunc(
    AFTER_AUTOBIND,
)

BEFORE_INJECT_LOADER: str = _event("slothy.before_inject_loader")
"""
Auditing event raised before injecting a
[lazy object loader][slothy.api.SlothyLoader] in the targeted namespace.
Takes 2 arguments:

- relevant [context manager][slothy.api.SlothyContext],
- the loader.
"""

before_inject_loader: Audit[[SlothyContext, SlothyLoader]] = AuditFunc(
    BEFORE_INJECT_LOADER,
)

AFTER_INJECT_LOADER: str = _event("slothy.after_inject_loader")
"""
Auditing event raised after injecting a
[lazy object loader][slothy.api.SlothyLoader] in the targeted namespace.
Takes 2 arguments:

- relevant [context manager][slothy.api.SlothyContext],
- the loader.
"""

after_inject_loader: Audit[[SlothyContext, SlothyLoader]] = AuditFunc(
    AFTER_INJECT_LOADER,
)

LAZY_OBJECT_SETATTR: str = _event("slothy.SlothyPlaceholder.__setattr__")
"""
Auditing event raised before setting an attribute on a lazy object.
Takes 3 arguments:

- relevant [lazy object][slothy.object.SlothyObject],
- attribute name,
- value.
"""

on_slothy_setattr: Audit[[SlothyObject, str, Any]] = AuditFunc(
    LAZY_OBJECT_SETATTR,
)

LAZY_OBJECT_DELATTR: str = _event("slothy.SlothyPlaceholder.__delattr__")
"""
Auditing event raised before deleting an attribute from a lazy object.
Takes 2 arguments:

- relevant [lazy object][slothy.object.SlothyObject],
- attribute name.
"""

on_slothy_delattr: Audit[[SlothyObject, str]] = AuditFunc(LAZY_OBJECT_DELATTR)
