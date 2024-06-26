
<!--
This file was generated from scaffops/python@0.0.2rc-238-g68b0ab8.
Instead of changing this particular file, you might want to alter the template:
https://github.com/scaffops/python/tree/0.0.2rc-238-g68b0ab8/project/%23%25%20if%20docs%20%25%23docs%23%25%20endif%20%25%23/contributing.md.jinja
-->
# Contributing to [slothy](https://github.com/bswck/slothy) 🎉
Contributions are very welcome. 🚀

There are many ways to contribute, ranging from **writing tutorials and improving the documentation**, to **submitting bug reports and feature requests** or **writing code** which can be incorporated into slothy.

## Report bugs and request features 🐛
Report these in the [issue tracker](https://github.com/bswck/slothy/issues).
Relevant forms provide guidance on how to write a good bug report or feature request.

## Implement new features ⭐
[Look here](https://github.com/bswck/slothy/issues?q=is%3Aopen+label%3Aenhancement+sort%3Aupdated-desc).
Anything tagged with "enhancement" is open to whoever wants to implement it.

## Write documentation 📖
The project could always use more documentation, whether as part of the official project
docs,. If you're interested in helping out, check the [docs/](https://github.com/bswck/slothy/tree/HEAD/docs)
folder in the repository.

## Share your feedback 🌍
The best way to send feedback is to file an issue in the [issue tracker](https://github.com/bswck/slothy).

If you are proposing a feature:

-   Explain in detail how it would work.
-   Keep the scope as narrow as possible, to make it easier to implement.
-   Remember that this is a volunteer-driven project, and that contributions are
    welcome! ✨

# Get started! 🕹️

Ready to contribute? Here's a quick guide on how to set up slothy and make a change.


<!--
This section was generated from scaffops/python@0.0.2rc-238-g68b0ab8.
Instead of changing this particular file, you might want to alter the template:
https://github.com/scaffops/python/tree/0.0.2rc-238-g68b0ab8/project/%23%25%20if%20docs%20%25%23docs%23%25%20endif%20%25%23/contributing.md.jinja
-->
!!! Note
    If you use Windows, it is highly recommended to complete the installation in the way presented below through [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install).
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

