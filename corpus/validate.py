"""Validate corpus YAML files against corpus/schema.json and check basic invariants.

Usage:  uv run python corpus/validate.py [paths...]     (default: corpus/**/*.yaml)
Exit code 1 on any problem. No engine required. Add --check-evidence to check that each
evidence screenshot exists in the evidence repository (decision 0039), when that is present.
"""

from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).parent
SCHEMA = json.loads((ROOT / "schema.json").read_text(encoding="utf-8"))
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg")


def validate_file(path: Path, seen_ids: set[str]) -> list[str]:
    problems: list[str] = []
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(SCHEMA)
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        loc = "/".join(str(p) for p in err.path)
        problems.append(f"{path.name}: {loc}: {err.message[:160]}")
    for case in (data or {}).get("cases", []) + (data or {}).get("app_cases", []):
        cid = case.get("id", "<no id>")
        if cid in seen_ids:
            problems.append(f"{path.name}: duplicate id {cid}")
        seen_ids.add(cid)
        prov = case.get("provenance", {})
        if prov.get("source") == "simulator" and not prov.get("evidence"):
            problems.append(
                f"{path.name}: {cid}: simulator source needs provenance.evidence screenshot"
            )
        if case.get("status") == "xfail" and not case.get("xfail_reason"):
            problems.append(f"{path.name}: {cid}: xfail needs xfail_reason")
    return problems


def missing_evidence(path: Path, evidence_corpus: Path) -> list[str]:
    """Evidence screenshots a file names that are not in the evidence repository's corpus/."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    problems: list[str] = []
    for case in data.get("cases", []) + data.get("app_cases", []):
        named = case.get("provenance", {}).get("evidence") or []
        text = named if isinstance(named, str) else ", ".join(named)
        # The field is free text: paths separated by commas or semicolons, sometimes with notes.
        for part in text.replace(";", ",").split(","):
            shot = part.strip()
            if not shot.lower().endswith(IMAGE_SUFFIXES):
                continue
            # A `*` stands for a numbered set of screenshots.
            if not glob.glob(str(evidence_corpus / shot)):
                problems.append(
                    f"{path.name}: {case.get('id', '<no id>')}: no evidence file {shot}"
                )
    return problems


def evidence_corpus_dir() -> Path | None:
    """corpus/ in the evidence repository (CASSIM_EVIDENCE, or CASSim-evidence beside this one)."""
    named = os.environ.get("CASSIM_EVIDENCE")
    root = Path(named) if named else ROOT.parent.parent / "CASSim-evidence"
    return root / "corpus" if (root / "corpus").is_dir() else None


def main(argv: list[str]) -> int:
    check_evidence = "--check-evidence" in argv
    argv = [a for a in argv if a != "--check-evidence"]
    paths = [Path(a) for a in argv] or sorted(ROOT.rglob("*.yaml"))
    seen: set[str] = set()
    problems: list[str] = []
    for p in paths:
        problems += validate_file(p, seen)
    if check_evidence:
        evidence_corpus = evidence_corpus_dir()
        if evidence_corpus is None:
            print("evidence repository not found; evidence files not checked")
        else:
            for p in paths:
                problems += missing_evidence(p, evidence_corpus)
    for line in problems:
        print(line)
    print(f"{len(seen)} cases in {len(paths)} file(s); {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
