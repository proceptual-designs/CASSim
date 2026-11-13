# Requirements traced here: NFR-MAINT-002
"""Dependency rules from PLAN.md section 3. Each rule is a package that must not import another."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src" / "cassim"

# (package, forbidden top-level import roots, reason)
RULES = [
    (
        "core",
        {"flet", "cassim.device", "cassim.app", "cassim.profiles", "cassim.devices", "cassim.doc"},
        "core is pure Python",
    ),
    (
        "device",
        {"flet", "cassim.app", "cassim.profiles", "cassim.devices"},
        "FR-DEV-007: device is headless",
    ),
    (
        "runtime",
        {"flet", "cassim.app", "cassim.device", "cassim.devices"},
        "the runtime is UI-free",
    ),
    ("profiles", {"flet", "cassim.app"}, "profiles are data"),
    ("doc", {"flet", "cassim.app", "cassim.profiles", "cassim.devices"}, "decision 0032 item 6"),
    ("devices", {"flet", "cassim.app"}, "a device imports without Flet (decision 0032)"),
]


def imports(path: Path) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module)
    return found


@pytest.mark.parametrize(("package", "forbidden", "why"), RULES)
def test_package_does_not_import_forbidden_modules(
    package: str, forbidden: set[str], why: str
) -> None:
    for path in (SRC / package).rglob("*.py"):
        for name in imports(path):
            hit = any(name == bad or name.startswith(bad + ".") for bad in forbidden)
            assert not hit, f"{path.relative_to(SRC)} imports {name} ({why})"


def test_a_device_never_imports_another_device() -> None:
    """FR-PROF-008: each device is a plug-in that stands alone (decision 0032 item 6)."""
    devices = [p.name for p in (SRC / "devices").iterdir() if (p / "__init__.py").exists()]
    for device in devices:
        others = {f"cassim.devices.{other}" for other in devices if other != device}
        for path in (SRC / "devices" / device).rglob("*.py"):
            for name in imports(path):
                hit = any(name == bad or name.startswith(bad + ".") for bad in others)
                assert not hit, f"{path.relative_to(SRC)} imports {name}"


PLAN = Path(__file__).resolve().parents[1] / "PLAN.md"


def _packages() -> list[Path]:
    return sorted(p for p in SRC.iterdir() if p.is_dir() and (p / "__init__.py").exists())


def _map_line(text: str, name: str) -> str | None:
    for line in text.splitlines():
        parts = line.split()
        if parts and parts[0] in {f"{name}/", f"src/cassim/{name}/"}:
            return line
    return None


@pytest.mark.parametrize("package", [p.name for p in _packages()])
def test_plan_architecture_map_lists_every_package(package: str) -> None:
    """PLAN.md section 3 stays in step with the code (see section 12)."""
    text = PLAN.read_text(encoding="utf-8")
    line = _map_line(text, package)
    assert line is not None, f"PLAN.md section 3 does not list src/cassim/{package}/"
    modules = [m for m in (SRC / package).rglob("*.py") if m.name != "__init__.py"]
    tagged = "[placeholder" in line
    assert tagged == (not modules), (
        f"src/cassim/{package}/ has {'no' if not modules else 'some'} modules but its map entry "
        f"is {'tagged' if tagged else 'not tagged'} [placeholder]"
    )
