import importlib

import pytest

PACKAGES = [
    "cassim",
    "cassim.core",
    "cassim.core.compat.sympy_adapter",
    "cassim.core.session",
    "cassim.cli",
]


@pytest.mark.parametrize("name", PACKAGES)
def test_imports(name: str) -> None:
    importlib.import_module(name)
