import runpy


def test_side_effects_in_module_imports() -> None:
    runpy.run_path("tests/side_effects_tests/test_module.py")


def test_side_effects_in_package_imports() -> None:
    runpy.run_path("tests/side_effects_tests/test_package.py")
