# <div align="center">slothy<br>[![skeleton](https://img.shields.io/badge/0.0.2rc–238–g68b0ab8-skeleton?label=%F0%9F%92%80%20scaffops/python&labelColor=black&color=grey&link=https%3A//github.com/scaffops/python)](https://github.com/scaffops/python/tree/0.0.2rc-238-g68b0ab8) [![Supported Python versions](https://img.shields.io/pypi/pyversions/slothy.svg?logo=python&label=Python)](https://pypi.org/project/slothy/) [![Package version](https://img.shields.io/pypi/v/slothy?label=PyPI)](https://pypi.org/project/slothy/)</div>

[![Tests](https://github.com/bswck/slothy/actions/workflows/test.yml/badge.svg)](https://github.com/bswck/slothy/actions/workflows/test.yml)
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/bswck/slothy.svg)](https://coverage-badge.samuelcolvin.workers.dev/redirect/bswck/slothy)

Super-easy lazy importing in Python.

Intended to be used as a drop-in replacement for `if typing.TYPE_CHECKING` blocks
as well as a convenient guard against expensive imports.

# Usage

```py
>>> from slothy import lazy_importing
>>>
>>> with lazy_importing(prevent_eager=False):
...     from functools import partial, reduce
...     print(partial)  # <from functools import partial, ...>
...     print(reduce)  # <from functools import ..., reduce>
>>>
>>> # First time imported items are referenced, they're imported.
... # If a declared item is never referenced, the module containing it is never
... # imported too, provided it was not imported by some external instruction.
... partial, reduce
(<class 'functools.partial'>, <built-in function reduce>)
```

`lazy_importing()` will default to eager imports on unsupported Python implementations,
i.e. those that don't define `sys._getframe`. While this library is 3.8+
and that eliminates the risk of running slothy in most of these implementations now,
future versions of them can finally support 3.8.

To prevent eager imports in `with lazy_importing()` statements and instead fail immediately
on unsupported Python implementations, use `with lazy_importing(prevent_eager=True)`.
Preventing eager imports might be useful in type-checking sections, where eager imports
could cause cycles resulting in less readable tracebacks.

# Credits
Many thanks to Jelle Zijlstra [@JelleZijlstra](https://github.com/JelleZijlstra) who wrote a [basic
dict key lookup-based lazy importing implementation](https://gist.github.com/JelleZijlstra/23c01ceb35d1bc8f335128f59a32db4c)
that is now the core solution of slothy.

Special thanks to Carl Meyer [@carljm](https://github.com/carljm) who willingly sacrificed his time
to consult the project with me and share his deep knowledge of the problem at the bigger picture.
His experience with [PEP 690](https://peps.python.org/pep-0690) as a Meta software engineer
helped me grasp the topic in the context of real production. I find it delightful!

Kudos to Alex Waygood [@AlexWaygood](https://github.com/AlexWaygood) who made this project possible
by sharing his knowledge of CPython implementation details regarding name lookup behavior.

Shoutout to Will McGugan [@willmcgugan](https://github.com/willmcgugan) who supported the idea of slothy
from the very beginning and [promoted the project on Twitter](https://twitter.com/willmcgugan/status/1781327396773208427).

# Installation
You might simply install it with pip:

```shell
pip install slothy
```

If you use [Poetry](https://python-poetry.org/), then you might want to run:

```shell
poetry add slothy
```

## For Contributors
[![Rye](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/rye/main/artwork/badge.json)](https://rye.astral.sh)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
<!--
This section was generated from scaffops/python@0.0.2rc-238-g68b0ab8.
Instead of changing this particular file, you might want to alter the template:
https://github.com/scaffops/python/tree/0.0.2rc-238-g68b0ab8/project/README.md.jinja
-->
> [!Note]
> If you use Windows, it is highly recommended to complete the installation in the way presented below through [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install).
1.  Fork the [slothy repository](https://github.com/bswck/slothy) on GitHub.

1.  [Install Poetry](https://python-poetry.org/docs/#installation).<br/>
    Poetry is an amazing tool for managing dependencies & virtual environments, building packages and publishing them.
    You might use [pipx](https://github.com/pypa/pipx#readme) to install it globally (recommended):

    ```shell
    pipx install poetry
    ```

    <sub>If you encounter any problems, refer to [the official documentation](https://python-poetry.org/docs/#installation) for the most up-to-date installation instructions.</sub>

    Be sure to have Python 3.8 installed—if you use [pyenv](https://github.com/pyenv/pyenv#readme), simply run:

    ```shell
    pyenv install 3.8
    ```

1.  Clone your fork locally and install dependencies.

    ```shell
    git clone https://github.com/your-username/slothy path/to/slothy
    cd path/to/slothy
    poetry env use $(cat .python-version)
    poetry install
    ```

    Next up, simply activate the virtual environment and install pre-commit hooks:

    ```shell
    poetry shell
    pre-commit install
    ```

For more information on how to contribute, check out [CONTRIBUTING.md](https://github.com/bswck/slothy/blob/HEAD/CONTRIBUTING.md).<br/>
Always happy to accept contributions! ❤️

# Legal Info
© Copyright by Bartosz Sławecki ([@bswck](https://github.com/bswck)).
<br />This software is licensed under the terms of [MIT License](https://github.com/bswck/slothy/blob/HEAD/LICENSE).
