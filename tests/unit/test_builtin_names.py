"""The UI starts without SymPy (decision 0027): its built-in names are a generated copy of the
catalog's, and nothing it imports at start-up loads the engine."""

import subprocess
import sys

from tools.builtin_names import planned

from cassim.core.builtin_names import NAMES, PLANNED, is_builtin
from cassim.core.catalog import registry


def test_names_match_the_catalog() -> None:
    """Run `python -m tools.builtin_names` when this fails."""
    assert registry.canonical_names() == NAMES


def test_planned_names_match_the_command_matrix() -> None:
    """Run `python -m tools.builtin_names` when this fails."""
    assert sorted(PLANNED) == planned(NAMES)
    assert {"count", "coldim", "arcsech"} <= PLANNED
    assert not PLANNED & NAMES


def test_is_builtin_agrees_with_the_catalog() -> None:
    for name in ["sin", "SIN", "sin⁻¹", "arcsin", "tanh⁻¹", "solve", "nosuch", "f"]:
        assert is_builtin(name) == registry.is_builtin(name), name


def test_the_app_imports_without_sympy() -> None:
    """The browser's UI worker never has SymPy: importing it there took 4 s on every start."""
    code = (
        "import sys, cassim.app.main, cassim.devices.nspire.ui.app\n"
        "import cassim.devices.nspire.ui.views, cassim.devices.nspire.ui.entry\n"
        "heavy = sorted(m for m in sys.modules if m.split('.')[0] in ('sympy', 'mpmath', 'yaml')"
        " or m.startswith(('cassim.core.session', 'cassim.core.catalog')))\n"
        "print(heavy)\n"
    )
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert done.stdout.strip() == "[]"
