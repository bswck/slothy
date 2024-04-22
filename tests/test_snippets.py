import runpy


def test_context_in_module_imports() -> None:
    runpy.run_path("tests/snippets/test_module.py")


def test_context_in_package_imports() -> None:
    runpy.run_path("tests/snippets/test_package.py")
