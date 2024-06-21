# How Does _slothy_ Work?!

_slothy_ can feel like it's magic, but **the trick is awfully simple.**

## It all starts with a dictionary

Python [scopes](https://docs.python.org/3/reference/executionmodel.html#resolution-of-names) are essentially dictionaries.<br>
Most of the times they can be accessed via [`locals()`][locals] and [`globals()`][globals].

=== "Define a variable `foo`"

    ```pycon hl_lines="1"
    {!> ./snippets/print_locals_1.pycon!}
    ```

=== "See `foo` in `locals()`"

    This includes a bunch of things Python automatically assigns to the module-level
    variables to work correctly. Unsurprisingly, they are
    [dunders](https://peps.python.org/pep-0008/#module-level-dunder-names)
    and we typically don't need to know they are there.

    ```pycon hl_lines="10"
    {!> ./snippets/print_locals_2.pycon!}
    ```

=== "See `foo` in `globals()`"

    ```pycon hl_lines="21"
    {!> ./snippets/print_locals_3.pycon!}
    ```

----

At the module level (outside any functions/classes), `locals()` and `globals()` are
the same dictionary.

We can reference a global variable from inside a module-level function,
and that will first look up the `locals()` dictionary from there and then `globals()`
without us having to do it manually:

<!--
For the best editing experience open the snippet files
on the other side in split view
-->

=== "Call a function"

    Given the code below, we call our `func` first.

    ```py hl_lines="6"
    {!> ./snippets/func_scoped.py!}
    ```

=== "Look up `x`"

    Once `func` is called, `x` is requested:

    ```py hl_lines="4"
    {!> ./snippets/func_scoped.py!}
    ```

    Python looks here (`locals()`):

    ```py hl_lines="3 4"
    {!> ./snippets/func_scoped.py!}
    ```

    Then here (`globals()`):

    ```py hl_lines="1 2 5"
    {!> ./snippets/func_scoped.py!}
    ```

    and...

=== "Resolve `x`"

    ...finally sees it here, in `globals()`:

    ```py hl_lines="1"
    {!> ./snippets/func_scoped.py!}
    ```

=== "Return `x`"

    Now `x` can be returned.

    ```py hl_lines="4"
    {!> ./snippets/func_scoped_return.py!}
    ```

----

But `globals()` isn't where the lookup ends: as you might have already noticed,
we often use names that aren't inside `globals()` nor any subsequent `locals()`.
That is, why does [`print`][] work in the first place?!

```pycon
>>> print
<built-in function print>
>>> "print" in globals()
False
>>> # How on earth is that possible?
```

Well, there's another scope that they probably don't want you to know about.<br>
It's called the **built-in scope** and it correlates with the [`builtins`][] module.

What is interesting, those builtins are typically mounted through the `__builtins__`
variable that you could have noticed before:

```pycon hl_lines="4"
{!> ./snippets/print_locals_2.pycon!}
```

In CPython, changing the value of `__builtins__` can change the actual built-in scope
entirely for child frames, i.e. any function call chains made from that place further on.

This is what _slothy_ initially relied on: it captured undefined names (since built-ins is the last scope checked) from a program and then looked it up in "lazy import declarations" to import them on demand.

However, that didn't work outside CPython, because it's not in the standard.

So, what _slothy_ does instead is...

## Intercepting dictionary access

!!! warn
    Work in progress.
