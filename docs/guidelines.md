# (Informal yet Informative) Guidelines

_slothy_ offers advanced use cases for highly aware Python developers.

!!! tip
    Pick your weapons carefully. If lazy importing with _slothy_ doesn't make
    your codebase significantly easier to maintain, then maybe it's a bad idea to use it.

This document aims to present general _do_s and _don't_s to follow if using _slothy_.

!!! warning
    The rest of this document is very technical, but at least in some places maybe even funny.
    The author is not responsible for segmentation faults between synapses as a result of reading the whole thing.

## 1. Don't rely on delayed imports programmatically

While _slothy_ changes the underlying import system behavior to delay imports,
you should never rely on the side effects it brings.

For example, if from `spam.py` you import a module `eggs.py` that is located in the same directory:

```py
# ./spam.py

with lazy_importing():
    from .eggs import ham
```

you should never rely on `from .eggs import ham` _not_ executing some code as a side effect it otherwise would execute
if it wasn't lazy.

In other words, stick to [decoupling](https://en.wikipedia.org/wiki/Coupling_(computer_programming))
and give your separate modules autonomy; do not rely on mutations to the global state of your program.

## 2. Don't prevent eager imports in libraries
!!! note
    You can ignore this rule if you need [`type_importing()`][slothy._importing.type_importing] in your library.

**As a general recommendation**:

- in apps, use `with lazy_importing()` (or less intuitive, but equivalent `with slothy_importing()`).
- in libraries, use `with lazy_importing(prevent_eager=False)`.

Try to make libraries as much compatible with non-CPython or non-PyPy implementations
as possible. _slothy_, tailored for applications, raises a [`RuntimeError`][]
if it can't ensure imports aren't lazy inside a `with slothy_importing()` block.

## 3. Use [`type_importing()`][slothy._importing.type_importing] for type-checking imports that may eventually be needed at runtime

If you need _slothy_ for delaying imports of typing-only items that might eventually
be requested at runtime (for example [by Pydantic](https://docs.pydantic.dev/2.7/concepts/postponed_annotations/)),
use a dedicated context manager [`type_importing()`][slothy._importing.type_importing].
That manager falls back to [`typing.Any`][] (or other configured runtime-available type)
when it cannot import the actual type-checking item.

For instance:
```pycon
>>> with type_importing():
>>>     from _typeshed import StrPath
...
>>> print(StrPath)
typing.Any
```

!!! warning
    If your type-checking imports aren't used at runtime, simply drop using [`type_importing()`][slothy._importing.type_importing]
    (or even entire _slothy_) at all. However, if you need to pick up type-checking items at runtime,
    use [`type_importing()`][slothy._importing.type_importing] consistently in the entire codebase
    to minimize the "I'm confused" factor (amongst [other factors](https://en.wikipedia.org/wiki/Bus_factor)).

## 4. Don't lazy-import in class scopes

This won't work:
```py
class Foo:
    with lazy_importing():
        from whatever import maybe_descriptor
```

The reason for this is that `Foo.maybe_descriptor` might potentially be a [descriptor](https://docs.python.org/3/howto/descriptor.html),
which implies _slothy_ would need to broke between its `__get__`, `__set__`, `__delete__` and even `__set_name__` which is already
a reason to import it eagerly.

You can imagine that `maybe_descriptor` can be

```py
# whatever.py

@property
def maybe_descriptor(self) -> None:
    print("I'm here against all lint rules!")
    return None

@maybe_descriptor.setter
def maybe_descriptor(self, _value: object) -> None:
    print("What's up?")
```

Even though this _is_ legal in Python, _slothy_, similarly to [mypy](https://mypy.readthedocs.io/en/stable/),
doesn't support descriptors bound via imports.

If you need to lazy-import inside classes, use a class-local property (or a custom descriptor):

```py
with lazy_importing():
    from whatever import anything


class BetterFoo:
    @property
    def descriptor(self) -> Anything:
        return anything  # this binds the item in globals() forever
```

or, even better:


```py
class EvenBetterFoo:
    @property
    def descriptor(self) -> ???:
        from whatever import anything
        return anything
```

or, yet better, don't do such a thing at all.

!!! note
    The following is an opinion.

Property getters should ideally not have any side effects.
A kind reminder: [`inspect.getmembers_static`][] was only added in 3.11!
