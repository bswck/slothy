# Usage

_slothy_ offers advanced use cases for highly aware Python developers.

!!! tip
    Pick your weapons carefully. If lazy importing with _slothy_ doesn't make
    your codebase signicantly easier to maintain, then it's a bad idea.

This document aims to present general recommendations when using _slothy_.

## 1. Don't rely on delayed imports programmatically

While _slothy_ changes the underlying import system behavior to delay imports,
you should never rely on side effects it brings.

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

## 2. Use [`type_importing()`][slothy._importing.type_importing] for type-checking imports that may eventually be needed at runtime

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

## 3. Don't use [`type_importing()`][slothy._importing.type_importing] if you can use [`TYPE_CHECKING`][typing.TYPE_CHECKING], but use only one for the entire project
If your type-checking imports aren't used at runtime, simply drop using [`type_importing()`][slothy._importing.type_importing]
(or even entire _slothy_) at all. However, if you need to pick up type-checking items at runtime,
use [`type_importing()`][slothy._importing.type_importing] consistently in the entire codebase
to minimize the "I'm confused" factor (amongst [other factors](https://en.wikipedia.org/wiki/Bus_factor)).

