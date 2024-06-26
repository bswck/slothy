# Guidelines

_slothy_ offers advanced use cases for highly aware Python developers.

!!! tip
    Pick your weapons carefully. If lazy importing with _slothy_ doesn't make
    your codebase significantly easier to maintain, then maybe it's a bad idea to use it.

This document aims to present general DOs and DON'Ts to follow if using _slothy_.
They gather **opinions** from the author(s) of _slothy_.

!!! warning
    The rest of this document can be very technical sometimes.
    Check out the [tutorial](tutorial.md) for a more beginner-friendly description
    of the intended uses of _slothy_.

## 1. Don't use _slothy_ without a reason

Here are some obviously unnecessary uses of _slothy_:

=== "Importing lazily to eagerly import right after"

    Instead of

    ```py
    with lazy_importing():
        import pandas as pd

    # In the line below, right under the lazy import, you import pandas eagerly.
    df = pd.DataFrame()
    ```

    You can just do

    ```py
    import pandas as pd
    df = pd.DataFrame()
    ```

    and that will be faster.

    This could make sense if you make a module that creates `df` lazily, e.g. when
    a function is called:

    ```py
    with lazy_importing():
        import pandas as pd

    def make_df() -> pd.DataFrame:
        return pd.DataFrame()

    # make_df() not called at the module level at all!
    # Someone else could import us and THEN call make_df(), perhaps
    # due to the instruction stack initiated in their
    # `if __name__ == "__main__"` section.
    ```

=== "Mixing lazy and eager imports unconditionally"

    ```py
    import pandas as pd

    with lazy_importing():
        from pandas import DataFrame
    ```

    You don't need _slothy_ in this case.
    `pandas.DataFrame` was already imported by the first line.

    Just use

    ```py
    import pandas as pd
    from pandas import DataFrame
    ```

    instead.

    Similarly, in

    ```py
    with lazy_importing():
        # Declares a lazy import.
        import pandas as pd  

    # Immediately destroys the entire point of declaring a lazy import.
    import pandas as pd
    ```

    you can just

    ```py
    import pandas as pd
    ```
    instead.

    Mixing eager and lazy imports might make sense if there's a logical branch
    of your code where the lazy import is not eventually performed.

## 2. Don't rely on delayed imports programmatically

While _slothy_ changes the underlying import system behavior to delay imports,
you should never rely on the side effects it brings.

For example, if from `spam.py` you import a module `eggs.py` that is located in the same directory:

```py
# ./spam.py

with lazy_importing():
    from .eggs import Ham
```

you should never rely on `from .eggs import Ham` _not_ executing some code it otherwise would
if it wasn't lazy. For example, don't base off on the fact that `Ham` is not present in `Ham.__base__.__subclasses__()`
after that lazy import.

In other words, stick to [decoupling](https://en.wikipedia.org/wiki/Coupling_(computer_programming))
and give your separate modules autonomy. Never make decisions based on side effect mutations to the global state of your program.

## 3. Don't prevent eager imports in libraries
!!! note
    You can ignore this rule if you need [`type_importing()`][slothy._importing.type_importing] in your library.

**As a general recommendation**:

- Use `with lazy_importing()` in **apps**.
- Use `with lazy_importing(prevent_eager=False)` in **libraries**.

Try to make libraries as much compatible with non-CPython implementations
as possible. _slothy_, tailored for applications, raises a [`RuntimeError`][]
if it can't ensure imports aren't lazy inside a `with lazy_importing()` block.

## 4. Use [`type_importing()`][slothy._importing.type_importing] for type-checking imports that may eventually be needed at runtime

If you need _slothy_ for delaying imports of typing-only items that might eventually
be requested at runtime (for example [by Pydantic](https://docs.pydantic.dev/2.7/concepts/postponed_annotations/)),
use a dedicated context manager [`type_importing()`][slothy._importing.type_importing].
That manager falls back to [`typing.Any`][] (or other configured runtime-available type)
when it cannot import the actual type-checking item.

For instance:
```pycon
>>> with type_importing():
...     from _typeshed import StrPath
...
>>> print(StrPath)
typing.Any
```

!!! warning
    If your type-checking imports aren't used at runtime, simply drop using [`type_importing()`][slothy._importing.type_importing]
    (or even entire _slothy_) at all. However, if you need to pick up type-checking items at runtime,
    use [`type_importing()`][slothy._importing.type_importing] consistently in the entire codebase
    to minimize the "I'm confused" factor (amongst [other factors](https://en.wikipedia.org/wiki/Bus_factor)).

## 5. Don't lazy-import in class scopes

This won't work:
```py
class Foo:
    with lazy_importing():
        from whatever import maybe_descriptor
```

The reason for this is that `Foo.maybe_descriptor` might potentially be a [descriptor](https://docs.python.org/3/howto/descriptor.html),
which implies _slothy_ would need to broker between its `__get__`, `__set__`, `__delete__` and even `__set_name__` which is already
a reason to import it eagerly.

You can imagine that `maybe_descriptor` can be

```py
# whatever.py

@property
def maybe_descriptor(self) -> None:
    print("I'm here against all the linting rules!")
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

or, even better than that, don't do such a thing at all.

!!! note
    **Opinion:** Property getters should ideally not have any side effects.
    A kind reminder: [`inspect.getmembers_static`][] was only added in 3.11!
