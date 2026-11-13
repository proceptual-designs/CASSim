"""Fail when a package's coverage falls below its floor in `pyproject.toml` (NFR-MAINT-004).

    uv run pytest -m "not e2e" --cov=cassim --cov-branch --cov-report=json
    python -m tools.coverage_check [coverage.json]

coverage.py has only one global `fail_under`, so the per-package floors in `[tool.cassim.coverage]`
are checked here. The figure is lines and branches combined, as coverage.py reports them.
"""

from __future__ import annotations

import json
import sys
import tomllib
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def by_package(report: dict[str, object]) -> dict[str, float]:
    """Percent covered per top-level package under `src/cassim/`. A device's Flet views
    (`devices/<id>/ui/`) are counted as `ui`, which has no floor: like `app`, they are covered
    by Playwright."""
    totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    files = report["files"]
    assert isinstance(files, dict)
    for name, data in files.items():
        parts = name.replace("\\", "/").split("src/cassim/")[-1].split("/")
        if len(parts) < 2:
            continue
        summary = data["summary"]
        package = "ui" if parts[0] == "devices" and "ui" in parts[1:-1] else parts[0]
        totals[package][0] += summary["covered_lines"] + summary.get("covered_branches", 0)
        totals[package][1] += summary["num_statements"] + summary.get("num_branches", 0)
    return {k: 100 * c / n if n else 100.0 for k, (c, n) in totals.items()}


def floors() -> dict[str, float]:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return {k: float(v) for k, v in data["tool"]["cassim"]["coverage"].items()}


def check(report: dict[str, object]) -> list[str]:
    found = by_package(report)
    problems = []
    for package, floor in floors().items():
        if package not in found:
            problems.append(f"{package}: not in the coverage report")
        elif found[package] < floor:
            problems.append(f"{package}: {found[package]:.1f}% is below the floor of {floor:g}%")
    return problems


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "coverage.json")
    report = json.loads(path.read_text(encoding="utf-8"))
    found = by_package(report)
    for package, floor in floors().items():
        print(f"{package:10} {found.get(package, 0):5.1f}%  (floor {floor:g}%)")
    problems = check(report)
    for problem in problems:
        print(problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
