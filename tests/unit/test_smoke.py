import importlib

import pytest

PACKAGES = [
    "emcas",
    "emcas.core",
    "emcas.core.compat.sympy_adapter",
    "emcas.cli",
    "emcas_app",
]


@pytest.mark.parametrize("name", PACKAGES)
def test_imports(name: str) -> None:
    importlib.import_module(name)
