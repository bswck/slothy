
<!--
This file was generated from skeleton-ci/skeleton-python@0.0.2rc-234-gca605f0.
Instead of changing this particular file, you might want to alter the template:
https://github.com/skeleton-ci/skeleton-python/tree/0.0.2rc-234-gca605f0/project/%23%25%20if%20docs%20%25%23docs%23%25%20endif%20%25%23/contributing.md.jinja
-->
# Contributing to [lazy-importing](https://github.com/bswck/lazy-importing) 🎉
Contributions are very welcome. 🚀

There are many ways to contribute, ranging from **writing tutorials and improving the documentation**, to **submitting bug reports and feature requests** or **writing code** which can be incorporated into lazy-importing.

## Report bugs and request features 🐛
Report these in the [issue tracker](https://github.com/bswck/lazy-importing/issues).
Relevant forms provide guidance on how to write a good bug report or feature request.

## Implement new features ⭐
[Look here](https://github.com/bswck/lazy-importing/issues?q=is%3Aopen+label%3Aenhancement+sort%3Aupdated-desc).
Anything tagged with "enhancement" is open to whoever wants to implement it.

## Write documentation 📖
The project could always use more documentation, whether as part of the official project
docs. If you're interested in helping out, check the [docs/](https://github.com/bswck/lazy-importing/tree/HEAD/docs)
folder in the repository.

## Share your feedback 🌍
The best way to send feedback is to file an issue in the [issue tracker](https://github.com/bswck/lazy-importing).

If you are proposing a feature:

-   Explain in detail how it would work.
-   Keep the scope as narrow as possible, to make it easier to implement.
-   Remember that this is a volunteer-driven project, and that contributions are
    welcome! ✨

## Pull Request guidelines 📝
1. Initially mark the PR as a draft, so that the maintainers know that you are making final touches.

1. Ensure that the [test coverage](https://coverage-badge.samuelcolvin.workers.dev/redirect/bswck/lazy-importing) is not decreased. If you add a new feature, please add tests for it. [Read more about coverage](https://coverage.readthedocs.io/en/latest/index.html).

1. Ensure that all GitHub checks pass. If they are disabled in your PR, ping the maintainers to request enabling them.

1. Don't forget to link the relevant issue(s) in the PR description and describe the changes you made.

# Get started! 🕹️

Ready to contribute? Here's a quick guide on how to set up lazy-importing and make a change.


<!--
This section was generated from skeleton-ci/skeleton-python@0.0.2rc-234-gca605f0.
Instead of changing this particular file, you might want to alter the template:
https://github.com/skeleton-ci/skeleton-python/tree/0.0.2rc-234-gca605f0/project/%23%25%20if%20docs%20%25%23docs%23%25%20endif%20%25%23/contributing.md.jinja
-->
!!! Note
    If you use Windows, it is highly recommended to complete the installation in the way presented below through [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install).
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

1.  Create a branch for local development:

    ```shell
    git checkout -b name-of-your-bugfix-or-feature
    ```

    Now you can make your changes locally.

1.  When you're done making changes, check that your changes pass all tests:

    ```shell
    poe check
    ```

1.  Commit your changes and push your branch to GitHub:

    ```shell
    git add -A
    git commit -m "Short description of changes (50 chars max)" -m "Optional extended description"
    git push origin name-of-your-bugfix-or-feature
    ```

1.  Submit a pull request through the GitHub website.

