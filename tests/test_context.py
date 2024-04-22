import runpy


def test_context_in_module_imports() -> None:
    runpy.run_path("tests/context_tests/test_module.py")


def test_context_in_package_imports() -> None:
    runpy.run_path("tests/context_tests/test_package.py")
