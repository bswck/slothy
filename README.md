# <div align="center">slothy<br>[![skeleton](https://img.shields.io/badge/0.0.2rc–238–g68b0ab8-skeleton?label=%F0%9F%92%80%20scaffops/python&labelColor=black&color=grey&link=https%3A//github.com/scaffops/python)](https://github.com/scaffops/python/tree/0.0.2rc-238-g68b0ab8) [![Supported Python versions](https://img.shields.io/pypi/pyversions/slothy.svg?logo=python&label=Python)](https://pypi.org/project/slothy/) [![Package version](https://img.shields.io/pypi/v/slothy?label=PyPI)](https://pypi.org/project/slothy/)</div>

[![Tests](https://github.com/bswck/slothy/actions/workflows/test.yml/badge.svg)](https://github.com/bswck/slothy/actions/workflows/test.yml)
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/bswck/slothy.svg)](https://coverage-badge.samuelcolvin.workers.dev/redirect/bswck/slothy)

Super-easy lazy importing in Python.

Intended to be used as a guard for expensive or type-checking imports.

> [!tip]
> In case you're just looking around, feel free to install the latest **beta**
> version of _slothy_ from PyPI and have some fun experimenting.<br>
> Don't forget to share your feedback in [the issue tracker](/issues)!

# Usage

```pycon
>>> from slothy import lazy_importing
>>> 
>>> with lazy_importing():
...     from asyncio import get_event_loop, run, erroneous_import
...     print(get_event_loop)
...     print(run)
...     print(erroneous_import)
... 
<from asyncio import get_event_loop, ... ("<stdin>", line 2)>
<from asyncio import ..., run, ... ("<stdin>", line 2)>
<from asyncio import ..., erroneous_import ("<stdin>", line 2)>
>>> get_event_loop
<built-in function get_event_loop>
>>> globals()["run"]
<function run at 0x7f49978a1160>
>>> erroneous_import
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "./slothy/_importing.py", line 423, in __eq__
    self._import(their_import)
  File "./slothy/_importing.py", line 304, in __import
    raise exc from None
  File "./slothy/_importing.py", line 286, in __import
    obj = _import_item_from_list(
  File "./slothy/_importing.py", line 203, in _import_item_from_list
    raise ImportError(msg) from None
ImportError: cannot import name 'erroneous_import' from 'asyncio' (caused by delayed execution of "<stdin>", line 2)
```

By default, `with lazy_importing()` statements fail immediately on unsupported Python
implementations, i.e. those that don't define [`sys._getframe`](https://docs.python.org/3/library/sys.html#sys._getframe). To disable this behavior,
which might be particularly useful in libraries, use `with lazy_importing(prevent_eager=False)`.

# Credits
Many thanks to Jelle Zijlstra [@JelleZijlstra](https://github.com/JelleZijlstra) who wrote a [basic
dict key lookup-based lazy importing implementation](https://gist.github.com/JelleZijlstra/23c01ceb35d1bc8f335128f59a32db4c)
that is now the core solution of slothy.

Kudos to Carl Meyer [@carljm](https://github.com/carljm) who willingly sacrificed his time
to consult the project with me and share his deep knowledge of the problem at the bigger picture.
His experience with [PEP 690](https://peps.python.org/pep-0690) as a Meta software engineer
significantly helped me.

I'm very grateful to Jim Fulton for [making the library possible in the first place](https://github.com/python/cpython/commit/d47a0a86b4ae4afeb17d8e64e1c447e4d4025f10) almost 30 years ago.

Special thanks to Alex Waygood [@AlexWaygood](https://github.com/AlexWaygood) who made this project possible
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
