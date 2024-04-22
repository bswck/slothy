# <div align="center">lazy-importing<br>[![skeleton](https://img.shields.io/badge/0.0.2rc–226–g9c7f11f-skeleton?label=%F0%9F%92%80%20skeleton-ci/skeleton-python&labelColor=black&color=grey&link=https%3A//github.com/skeleton-ci/skeleton-python)](https://github.com/skeleton-ci/skeleton-python/tree/0.0.2rc-226-g9c7f11f) [![Supported Python versions](https://img.shields.io/pypi/pyversions/lazy-importing.svg?logo=python&label=Python)](https://pypi.org/project/lazy-importing/) [![Package version](https://img.shields.io/pypi/v/lazy-importing?label=PyPI)](https://pypi.org/project/lazy-importing/)</div>

[![Tests](https://github.com/bswck/lazy-importing/actions/workflows/test.yml/badge.svg)](https://github.com/bswck/lazy-importing/actions/workflows/test.yml)
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/bswck/lazy-importing.svg)](https://coverage-badge.samuelcolvin.workers.dev/redirect/bswck/lazy-importing)
[![Documentation Status](https://readthedocs.org/projects/lazy-importing/badge/?version=latest)](https://lazy-importing.readthedocs.io/en/latest/?badge=latest)

Super-easy lazy importing in Python.

> [!Note]
> The first release of `lazy-importing` is scheduled for **Apr 26, 2024.**
> It's not available on PyPI yet.

> [!Important]
> Only CPython is supported.

Intended to be used as a drop-in replacement for `if typing.TYPE_CHECKING` blocks
as well as a convenient guard against expensive imports.

# Usage

```py
from lazy_importing import LAZY_IMPORTING

with LAZY_IMPORTING:
    from pandas import DataFrame

# pandas.DataFrame not imported

def main() -> None:
    # pandas.DataFrame not imported
    print(DataFrame)  # <class 'pandas.core.frame.DataFrame'>
    # pandas.DataFrame imported just before print() called; from now on,
    # available everywhere in the module.


if __name__ == "__main__":
    main()
```

# Caveats

## Python <3.10 Boilerplate
On Python 3.8-3.9, every function accessing a lazily-imported object
must be decorated with `supports_lazy_access`:

```py
from lazy_importing import LAZY_IMPORTING, supports_lazy_access

with LAZY_IMPORTING:
    from pandas import DataFrame

# pandas.DataFrame not imported

@supports_lazy_access
def main() -> None:
    # pandas.DataFrame not imported
    print(DataFrame)  # <class 'pandas.core.frame.DataFrame'>
    # pandas.DataFrame imported just before print() called; from now on,
    # available everywhere in the module.


if __name__ == "__main__":
    main()
```

## Deleted References

Importing symbols `with LAZY_IMPORTING` will make them intentionally unavailable in your
namespace after the `with LAZY_IMPORTING` block finishes.

Consequently,

```py
from lazy_importing import LAZY_IMPORTING

with LAZY_IMPORTING:
    from pandas import DataFrame

try:
    DataFrame
except NameError:
    print("DataFrame undefined")
```

outputs `DataFrame undefined`.
This is caused by the fact that there must be at least 1 frame between "declared import"
and usage. More in-depth technical explanation will be provided soon.

# Credits
Kudos to [@AlexWaygood](https://github.com/AlexWaygood) who made this project possible
by sharing his knowledge of CPython implementation details regarding name lookup behavior.

# Installation
You might simply install it with pip:

```shell
pip install lazy-importing
```

If you use [Poetry](https://python-poetry.org/), then you might want to run:

```shell
poetry add lazy-importing
```

## For Contributors
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
<!--
This section was generated from skeleton-ci/skeleton-python@0.0.2rc-226-g9c7f11f.
Instead of changing this particular file, you might want to alter the template:
https://github.com/skeleton-ci/skeleton-python/tree/0.0.2rc-226-g9c7f11f/project/README.md.jinja
-->
> [!Note]
> If you use Windows, it is highly recommended to complete the installation in the way presented below through [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install).
1.  Fork the [lazy-importing repository](https://github.com/bswck/lazy-importing) on GitHub.

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
    git clone https://github.com/your-username/lazy-importing path/to/lazy-importing
    cd path/to/lazy-importing
    poetry env use $(cat .python-version)
    poetry install
    ```

    Next up, simply activate the virtual environment and install pre-commit hooks:

    ```shell
    poetry shell
    pre-commit install
    ```

For more information on how to contribute, check out [CONTRIBUTING.md](https://github.com/bswck/lazy-importing/blob/HEAD/CONTRIBUTING.md).<br/>
Always happy to accept contributions! ❤️

# Legal Info
© Copyright by Bartosz Sławecki ([@bswck](https://github.com/bswck)).
<br />This software is licensed under the terms of [MIT License](https://github.com/bswck/lazy-importing/blob/HEAD/LICENSE).
