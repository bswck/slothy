
# lazy-imports [![skeleton](https://img.shields.io/badge/0.0.2rc-62-g52ffbf3-skeleton?label=%F0%9F%92%80%20bswck/skeleton&labelColor=black&color=grey&link=https%3A//github.com/bswck/skeleton)](https://github.com/bswck/skeleton/tree/0.0.2rc-62-g52ffbf3) [![Supported Python versions](https://img.shields.io/pypi/pyversions/lazy-imports.svg?logo=python&label=Python)](https://pypi.org/project/lazy-imports/) [![Package version](https://img.shields.io/pypi/v/lazy-imports?label=PyPI)](https://pypi.org/project/lazy-imports/)

[![Tests](https://github.com/bswck/lazy-imports/actions/workflows/test.yml/badge.svg)](https://github.com/bswck/lazy-imports/actions/workflows/test.yml)
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/bswck/lazy-imports.svg)](https://coverage-badge.samuelcolvin.workers.dev/redirect/bswck/lazy-imports)
[![Documentation Status](https://readthedocs.org/projects/lazy-imports/badge/?version=latest)](https://lazy-imports.readthedocs.io/en/latest/?badge=latest)

Convenient lazy imports for Python.

# Installation
You might simply install it with pip:

```shell
pip install lazy-imports
```

If you use [Poetry](https://python-poetry.org/), then you might want to run:

```shell
poetry add lazy-imports
```

## For contributors
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
<!--
This section was generated from bswck/skeleton@0.0.2rc-62-g52ffbf3.
Instead of changing this particular file, you might want to alter the template:
https://github.com/bswck/skeleton/tree/0.0.2rc-62-g52ffbf3/fragments/readme.md
-->
!!! Note
    If you use Windows, it is highly recommended to complete the installation in the way presented below through [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install).
1.  Fork the [lazy-imports repository](https://github.com/bswck/lazy-imports) on GitHub.

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
    git clone https://github.com/your-username/lazy-imports path/to/lazy-imports
    cd path/to/lazy-imports
    poetry env use $(cat .python-version)
    poetry install
    ```

    Next up, simply activate the virtual environment and install pre-commit hooks:

    ```shell
    poetry shell
    pre-commit install
    ```

For more information on how to contribute, check out [CONTRIBUTING.md](https://github.com/bswck/lazy-imports/blob/HEAD/CONTRIBUTING.md).<br/>
Always happy to accept contributions! ❤️

# Legal info
© Copyright by Bartosz Sławecki ([@bswck](https://github.com/bswck)).
<br />This software is licensed under the terms of [MIT License](https://github.com/bswck/lazy-imports/blob/HEAD/LICENSE).
