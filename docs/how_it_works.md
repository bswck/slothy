# How It Works

_slothy_ can feel like it's magic, but **the trick is super simple.**

## It all started with a dictionary

Python [scopes](https://docs.python.org/3/reference/executionmodel.html#resolution-of-names) are essentially dictionaries.<br>
Most of the times they can be accessed via [`locals()`][locals] and [`globals()`][globals].

=== "Define a variable `foo`"

    ```pycon hl_lines="1"
    {!> ./snippets/print_locals_1.pycon!}
    ```

=== "See `foo` in `locals()`"

    ```pycon hl_lines="2 10"
    {!> ./snippets/print_locals_2.pycon!}
    ```

    !!! note
        This includes a bunch of things Python automatically assigns to the module-level
        variables to work correctly. Unsurprisingly, they are
        [dunders](https://peps.python.org/pep-0008/#module-level-dunder-names)
        and we typically don't need to know they are there.


=== "See `foo` in `globals()`"

    ```pycon hl_lines="11 21-23"
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

    and... [>>>](#__tabbed_2_3)

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

What is interesting, those built-ins are typically mounted through the `__builtins__`
variable that you could have noticed before:

```pycon hl_lines="4"
{!> ./snippets/print_locals_2.pycon!}
```

In CPython, changing the value of `__builtins__` can change the actual built-in scope
entirely for child frames, i.e. any function call stack starting from that place further on.

This is what _slothy_ initially relied on: it captured undefined names (since built-ins is the last scope checked) from a program and then looked it up in "lazy import declarations" to import them on demand.

However, that didn't work outside CPython, because it's not in the standard.

So, what _slothy_ does instead is...

## Intercepting dictionary access

From [the documentation on mappings](https://docs.python.org/3/library/stdtypes.html#mapping-types-dict):

> A mapping object maps hashable values to arbitrary objects. Mappings are mutable objects. There is currently only one standard mapping type, the dictionary. (...)
> A dictionary’s keys are almost arbitrary values. Values that are not hashable (...) may not be used as keys. Values that compare equal (such as `1`, `1.0`, and `True`) can be used interchangeably to index the same dictionary entry.

From [the documentation on hashable objects](https://docs.python.org/3/glossary.html#term-hashable):

> An object is hashable if it has a hash value which never changes during its lifetime (it needs a `__hash__()` method), and can be compared to other objects (it needs an `__eq__()` method). Hashable objects which compare equal must have the same hash value.

Which makes sense with regard to the previous quote:

```pycon
>>> hash(1)
1
>>> 1 == 1.0
True
>>> hash(1.0)
1
>>> 1 == True
True
>>> hash(True)
1
```

> Hashability makes an object usable as a dictionary key and a set member, because these data structures use the hash value internally.

Knowing that, let's see what happens if we try to insert a custom key to a dictionary.<br>The new, "special" key will:

- log every `__hash__` and `__eq__` call
- be equal to every string of value `"special"`.

```pycon
>>> class SpecialKey:
...     def __eq__(self, other):
...         print("__eq__ called")
...         return "special" == other
...     def __hash__(self):
...         print("__hash__ called")
...         return hash("special")
``` 

And we are good to go!

=== "Create a dictionary"

    Let's create the dictionary we will experiment on.

    ```pycon hl_lines="1-2"
    {!> ./snippets/dict_intercept_1.pycon!}
    ```

=== "Insert the special key"

    Let's insert the key.

    ```pycon hl_lines="4-6"
    {!> ./snippets/dict_intercept_2.pycon!}
    ```

    Notice that `__hash__` was called.

=== "Check against invalid key"

    Just to make sure, we will try to get a key that can't exist in that dictionary.

    ```pycon hl_lines="8-12"
    {!> ./snippets/dict_intercept_3.pycon!}
    ```

    The reason for the dictionary to know this is an invalid key is that
    there is no value under a key with the same hash.

    Hash-based lookup is what makes dictionaries (and [hash tables](https://en.wikipedia.org/wiki/Hash_table) in general) fast.


=== "Check against `"special"`"

    We intended the special key to be interoperable with a string `"special"`.
    Let's try to get it.

    ```pycon hl_lines="14-16"
    {!> ./snippets/dict_intercept_4.pycon!}
    ```

    Now that works! Notice that `__eq__` was called.

    You might ask: **why**? If _hashable objects which compare equal must have
    the same hash value_, why would we have to additionally check their equality?
    [>>>](#__tabbed_3_5)

=== "Check against a colliding key"

    Well, imagine an object that very randomly has the same hash as the string
    `"special"`.

    ```pycon hl_lines="18-39"
    {!> ./snippets/dict_intercept_5.pycon!}
    ```

    What `__eq__` ultimately gives us is the possibility of maintaining distinct keys
    with colliding hashes in the same dictionary.

----

In conclusion, Python dictionaries let us map objects with possibly colliding hashes to values and
retrieve them quickly, making sure we get (and set) what we intend.

Since arbitrary objects participate in the process of dictionary key resolution,
_slothy_ does its magic by modifying the first step to operate on a slightly different dictionary:

=== "Our experiment"

    ```pycon hl_lines="1-2"
    {!> ./snippets/dict_intercept_1.pycon!}
    ```


=== "_slothy_"

    ```pycon hl_lines="1-2"
    {!> ./snippets/dict_intercept_1_slothy.pycon!}
    ```

    You get the point?

    _slothy_ essentially uses the "special key" idea and implements behavior that
    dynamically imports items on their first actual lookup inside your `locals()`.

    These keys are created on every import inside _slothy_ context managers that
    temporarily patch [`__import__`][] in your built-in scope: the function without
    which the `import` statement wouldn't work.

    This was _How It Works_. Congrats for making it this far! 🎉

