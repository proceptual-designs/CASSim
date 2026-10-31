"""Build the command coverage matrix from the TI-Nspire Reference Guide and the golden corpus.

Usage:  uv run python tools/ref_matrix.py            (writes docs/command_matrix.csv and .md)

Needs ``pdftotext`` (poppler) on PATH. The guide in ``references/`` is the non-CAS edition, so
CAS-only commands (solve, cSolve, zeros, limit, ...) cannot come from it; they are reported
separately from the corpus as "not in guide".
"""

from __future__ import annotations

import csv
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "references" / "TI-Nspire_ReferenceGuide_EN_4.5.pdf"
DRAFT = ROOT / "docs" / "reference_index_draft.txt"
CORPUS = ROOT / "corpus" / "seed"
OUT_CSV = ROOT / "docs" / "command_matrix.csv"
OUT_MD = ROOT / "docs" / "command_matrix.md"

# Names that appear in corpus input but are not commands.
NOT_COMMANDS = {"f", "g", "h", "k", "a", "b", "n", "p", "r", "s", "t", "u", "v", "w", "x", "y", "z"}


def norm(name: str) -> str:
    """Normalise a heading for matching: drop spaces, the parentheses suffix and arrows."""
    name = name.split(" (", maxsplit=1)[0] if name.endswith(")") and " (" in name else name
    return re.sub(r"[\s()►▶]", "", name).lower()


# Right-hand access tag on a heading line: "Catalog >" or "<glyph> key(s)" (sin(), ln(), Ans, ...).
TAG = r"(?:Catalog >|\S{1,3} keys?)"
HEADING = re.compile(rf"^\s*(\S.*?)\s{{2,}}{TAG}\s*$")
CALL = re.compile(r"^([►▶]?[A-Za-z][A-Za-z0-9_.⁻¹]*)\s?\(")
BARE = re.compile(r"^\s*([►▶]?[A-Za-z][A-Za-z0-9_.⁻¹]*\s?(?:\(\))?)\s*$")
WORD = re.compile(r"^[►▶]?[A-Za-z][A-Za-z0-9_.]*[A-Za-z0-9_]$|^[A-Za-z]$")


def heading_name(raw: str) -> tuple[str, bool] | None:
    """Return (name, is_call) for a heading line, or None for prose or a wrapped syntax line."""
    raw = raw.strip()
    if m := CALL.match(raw):
        return m.group(1) + "()", True
    if WORD.match(raw):
        return raw, False
    return None


def guide_headings() -> dict[str, tuple[str, int, bool]]:
    """Map normalised heading -> (name, PDF page, is_call) for the first occurrence."""
    text = subprocess.run(
        ["pdftotext", "-enc", "UTF-8", "-layout", str(GUIDE), "-"],
        capture_output=True,
        text=True,
        check=True,
        encoding="utf-8",
    ).stdout
    found: dict[str, tuple[str, int, bool]] = {}
    for number, page in enumerate(text.split(""), start=1):
        lines = page.splitlines()
        for i, line in enumerate(lines):
            m = HEADING.match(line)
            if not m and (bare := BARE.match(line)):
                # Name alone on its line, then a syntax line that starts with the same name.
                base = bare.group(1).removesuffix("()").strip()
                nxt = next((x.strip() for x in lines[i + 1 : i + 4] if x.strip()), "")
                if base and nxt.startswith(base) and nxt[len(base) : len(base) + 1] in "( [":
                    m = bare
            if m and (parsed := heading_name(m.group(1))):
                found.setdefault(norm(parsed[0]), (parsed[0], number, parsed[1]))
    return found


def corpus_usage() -> Counter[str]:
    """Return, per lower-cased name, the number of cases that use it (``name(`` or ``▶name``)."""
    counts: Counter[str] = Counter()
    for path in sorted(CORPUS.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for case in data.get("cases", []):
            text = " ".join(str(s.get("in", "")) for s in case.get("steps", []))
            names = set(re.findall(r"([A-Za-z_][A-Za-z0-9_.]*)\s*\(", text))
            names |= set(re.findall(r"[►▶]\s*([A-Za-z0-9]+)", text))
            for name in names - NOT_COMMANDS:
                counts[name.lower()] += 1
    return counts


def main() -> int:
    if not GUIDE.exists():
        print(f"missing {GUIDE}", file=sys.stderr)
        return 1
    headings = guide_headings()
    counts = corpus_usage()
    draft = {norm(n.strip()) for n in DRAFT.read_text(encoding="utf-8").splitlines() if n.strip()}

    rows = []
    for key, (name, page, is_call) in headings.items():
        in_draft = key in draft
        # A bare word (no parentheses) could be prose; trust it only if the draft agrees.
        status = "todo" if is_call or in_draft else "review"
        rows.append(
            {
                "command": name,
                "guide_pdf_page": page,
                "in_draft_index": "yes" if in_draft else "NO",
                "corpus_cases": counts.get(key, 0),
                "status": status,
            }
        )
    missing = sorted(k for k in counts if k not in headings)
    new_vs_draft = [
        r["command"] for r in rows if r["in_draft_index"] == "NO" and r["status"] == "todo"
    ]
    to_review = [r["command"] for r in rows if r["status"] == "review"]
    draft_only = sorted(draft - set(headings))

    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    used = sum(1 for r in rows if r["corpus_cases"])
    lines = [
        "# Command coverage matrix",
        "",
        "Generated by `tools/ref_matrix.py`; do not edit. Full table: `command_matrix.csv`.",
        "",
        f"- Guide headings found in the PDF: {len(rows)}; used by a corpus case: {used}.",
        f"- Headings missing from `reference_index_draft.txt`: {len(new_vs_draft)}. "
        f"Names in the draft but not matched as headings: {len(draft_only)}.",
        "- **Source gap:** `references/TI-Nspire_ReferenceGuide_EN_4.5.pdf` is the non-CAS guide. "
        "It has no entries for CAS-only commands (solve, cSolve, zeros, limit, taylor, deSolve, "
        "expand, ...), "
        "so this matrix cannot be complete for the CX CAS.",
        "",
        "## Used by the corpus but not in the guide",
        "",
        "CAS-only commands, user-defined functions and Catalog items. Review by hand.",
        "",
        *(f"- `{k}` ({counts[k]} cases)" for k in missing),
        "",
        "## In the guide but missing from the draft index",
        "",
        *(f"- {n}" for n in new_vs_draft),
        "",
        "## Bare words that may be prose (status `review` in the CSV)",
        "",
        *(f"- {n}" for n in to_review),
        "",
        "## In the draft index but not matched as a heading",
        "",
        *(f"- {n}" for n in draft_only),
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"{len(rows)} headings, {len(new_vs_draft)} new vs draft, {len(to_review)} to review, "
        f"{len(draft_only)} draft-only, {used} used by corpus, "
        f"{len(missing)} corpus names not in guide"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
