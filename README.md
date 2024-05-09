# <div align="center">slothy<br>[![skeleton](https://img.shields.io/badge/0.0.2rc–237–g7b0b7e3-skeleton?label=%F0%9F%92%80%20skeleton-ci/skeleton-python&labelColor=black&color=grey&link=https%3A//github.com/skeleton-ci/skeleton-python)](https://github.com/skeleton-ci/skeleton-python/tree/0.0.2rc-237-g7b0b7e3) [![Supported Python versions](https://img.shields.io/pypi/pyversions/slothy.svg?logo=python&label=Python)](https://pypi.org/project/slothy/) [![Package version](https://img.shields.io/pypi/v/slothy?label=PyPI)](https://pypi.org/project/slothy/)</div>

[![Tests](https://github.com/bswck/slothy/actions/workflows/test.yml/badge.svg)](https://github.com/bswck/slothy/actions/workflows/test.yml)
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/bswck/slothy.svg)](https://coverage-badge.samuelcolvin.workers.dev/redirect/bswck/slothy)
[![Documentation Status](https://readthedocs.org/projects/slothy/badge/?version=latest)](https://slothy.readthedocs.io/en/latest/?badge=latest)

Super-easy lazy importing in Python.

> [!Important]
> Only CPython is supported.

Intended to be used as a drop-in replacement for `if typing.TYPE_CHECKING` blocks
as well as a convenient guard against expensive imports.

# Usage

```py
from slothy import SLOTHY

with SLOTHY:
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
must be decorated with `supports_slothy`:

```py
from slothy import SLOTHY, supports_slothy

with SLOTHY:
    from pandas import DataFrame

# pandas.DataFrame not imported

@supports_slothy
def main() -> None:
    # pandas.DataFrame not imported
    print(DataFrame)  # <class 'pandas.core.frame.DataFrame'>
    # pandas.DataFrame imported just before print() called; from now on,
    # available everywhere in the module.


if __name__ == "__main__":
    main()
```

## Deleted References

Importing symbols `with SLOTHY` will make them intentionally unavailable in your
namespace after the `with SLOTHY` block finishes.

Consequently,

```py
from slothy import SLOTHY

with SLOTHY:
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
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
<!--
This section was generated from skeleton-ci/skeleton-python@0.0.2rc-237-g7b0b7e3.
Instead of changing this particular file, you might want to alter the template:
https://github.com/skeleton-ci/skeleton-python/tree/0.0.2rc-237-g7b0b7e3/project/README.md.jinja
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
