"""Validate corpus YAML files against corpus/schema.json and check basic invariants.

Usage:  uv run python corpus/validate.py [paths...]     (default: corpus/**/*.yaml)
Exit code 1 on any problem. No engine required.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).parent
SCHEMA = json.loads((ROOT / "schema.json").read_text(encoding="utf-8"))


def validate_file(path: Path, seen_ids: set[str]) -> list[str]:
    problems: list[str] = []
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(SCHEMA)
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        loc = "/".join(str(p) for p in err.path)
        problems.append(f"{path.name}: {loc}: {err.message[:160]}")
    for case in (data or {}).get("cases", []):
        cid = case.get("id", "<no id>")
        if cid in seen_ids:
            problems.append(f"{path.name}: duplicate id {cid}")
        seen_ids.add(cid)
        prov = case.get("provenance", {})
        if prov.get("source") == "emulator" and not prov.get("evidence"):
            problems.append(
                f"{path.name}: {cid}: emulator source needs provenance.evidence screenshot"
            )
        if case.get("status") == "xfail" and not case.get("xfail_reason"):
            problems.append(f"{path.name}: {cid}: xfail needs xfail_reason")
    return problems


def main(argv: list[str]) -> int:
    paths = [Path(a) for a in argv] or sorted(ROOT.rglob("*.yaml"))
    seen: set[str] = set()
    problems: list[str] = []
    for p in paths:
        problems += validate_file(p, seen)
    for line in problems:
        print(line)
    print(f"{len(seen)} cases in {len(paths)} file(s); {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
