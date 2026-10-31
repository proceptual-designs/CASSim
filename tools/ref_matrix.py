"""Build the command coverage matrix: Reference Guides x golden corpus x VCE resource books.

Usage:  uv run python tools/ref_matrix.py     (writes docs/command_matrix.csv and .md)

Sources, in order of authority:
  1. the TI-Nspire CAS Reference Guide (primary; software 3.2, older than the emulator);
  2. the TI-Nspire Reference Guide 4.5 (non-CAS; fills in newer numeric commands);
  3. the emulator Catalog (not automated yet; the ``emulator_verified`` column is left empty).
Priority hints come from the corpus and from how often the VCE books mention a command.
Needs ``pdftotext`` (poppler) on PATH; extracted text is cached under ``builds/cache/``.
"""

from __future__ import annotations

import csv
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "references"
CAS_GUIDE = REF / "TI-NspireCAS_ReferenceGuide_EN_3.2.pdf"
NUM_GUIDE = REF / "TI-Nspire_ReferenceGuide_EN_4.5.pdf"
BOOKS = {
    "methods": REF / "VCE Mathematical Methods Teacher Resource Book digital 2026.pdf",
    "specialist": REF / "VCE Specialist Mathematics Teacher Resource Book.pdf",
    "general": REF / "VCE General Maths Teacher Resource Book.pdf",
}
CORPUS = ROOT / "corpus" / "seed"
CACHE = ROOT / "builds" / "cache"
OUT_CSV = ROOT / "docs" / "command_matrix.csv"
OUT_MD = ROOT / "docs" / "command_matrix.md"

# Names that appear in corpus input but are not commands.
NOT_COMMANDS = {"f", "g", "h", "k", "a", "b", "n", "p", "r", "s", "t", "u", "v", "w", "x", "y", "z"}
LIKELY_MENTIONS = 5  # book mentions at which a command not in the corpus is still "likely"

# Right-hand access tag on a heading line: "Catalog >" or "<glyph> key(s)" (sin(), ln(), Ans, ...).
TAG = r"(?:Catalog >|\S{1,3} keys?)"
HEADING = re.compile(rf"^\s*(\S.*?)\s{{2,}}{TAG}\s*$")
CALL = re.compile(r"^([►▶]?[A-Za-z][A-Za-z0-9_.⁻¹]*)\s?\(")
BARE = re.compile(r"^\s*([►▶]?[A-Za-z][A-Za-z0-9_.⁻¹]*\s?(?:\(\))?)\s*$")
WORD = re.compile(r"^[►▶]?[A-Za-z][A-Za-z0-9_.]*[A-Za-z0-9_]$|^[A-Za-z]$")


def norm(name: str) -> str:
    """Normalise a heading for matching: drop spaces, the parentheses suffix and arrows."""
    name = name.split(" (", maxsplit=1)[0] if name.endswith(")") and " (" in name else name
    return re.sub(r"[\s()►▶]", "", name).lower()


def heading_name(raw: str) -> tuple[str, bool] | None:
    """Return (name, is_call) for a heading line, or None for prose or a wrapped syntax line."""
    raw = raw.strip()
    if m := CALL.match(raw):
        return m.group(1) + "()", True
    if WORD.match(raw):
        return raw, False
    return None


def pdf_text(path: Path, *, layout: bool) -> str:
    """Return the text of a PDF via pdftotext, cached under builds/cache/."""
    CACHE.mkdir(parents=True, exist_ok=True)
    cached = CACHE / f"{path.stem}{'.layout' if layout else ''}.txt"
    if cached.exists() and cached.stat().st_mtime >= path.stat().st_mtime:
        return cached.read_text(encoding="utf-8")
    cmd = ["pdftotext", "-enc", "UTF-8", *(["-layout"] if layout else []), str(path), "-"]
    out = subprocess.run(cmd, capture_output=True, check=True).stdout
    text = out.decode("utf-8", errors="replace")
    cached.write_text(text, encoding="utf-8")
    return text


@dataclass
class Heading:
    """One guide entry: printed name, PDF page and whether it was written as ``name(``."""

    name: str
    page: int
    is_call: bool


def guide_headings(path: Path) -> dict[str, Heading]:
    """Map normalised name -> first heading found in the guide."""
    found: dict[str, Heading] = {}
    for number, page in enumerate(pdf_text(path, layout=True).split("\f"), start=1):
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
                base = parsed[0].removesuffix("()")
                if len(base) == 1 and base != "d":  # error-code and symbol sections, not commands
                    continue
                found.setdefault(norm(parsed[0]), Heading(parsed[0], number, parsed[1]))
    return found


@dataclass
class CorpusCase:
    """A corpus case reduced to what the matrix needs."""

    id: str
    steps: int
    names: set[str] = field(default_factory=set)


def corpus_cases() -> list[CorpusCase]:
    """Return each corpus case with the lower-cased command names its inputs use."""
    cases = []
    for path in sorted(CORPUS.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for case in data.get("cases", []):
            steps = case.get("steps", [])
            text = " ".join(str(s.get("in", "")) for s in steps)
            names = set(re.findall(r"([A-Za-z_][A-Za-z0-9_.]*)\s*\(", text))
            names |= set(re.findall(r"[►▶]\s*([A-Za-z0-9]+)", text))
            cases.append(
                CorpusCase(case["id"], len(steps), {n.lower() for n in names - NOT_COMMANDS})
            )
    return cases


def mentions(text: str, heading: Heading) -> int:
    """Count case-sensitive uses of a command in running text; -1 if too ambiguous to count."""
    base = heading.name.removesuffix("()").lstrip("►▶")
    if heading.is_call:
        return len(re.findall(rf"(?<![A-Za-z]){re.escape(base)}\s?\(", text))
    if base == base.lower():  # "and", "or", "nand": indistinguishable from prose
        return -1
    return len(re.findall(rf"(?<![A-Za-z0-9]){re.escape(base)}(?![A-Za-z0-9])", text))


def priority(corpus: int, books: int) -> str:
    """Return core (in the corpus), likely (often in the books) or later."""
    if corpus:
        return "core"
    return "likely" if books >= LIKELY_MENTIONS else "later"


def main() -> int:
    for path in (CAS_GUIDE, NUM_GUIDE, *BOOKS.values()):
        if not path.exists():
            print(f"missing {path}", file=sys.stderr)
            return 1
    cas, num = guide_headings(CAS_GUIDE), guide_headings(NUM_GUIDE)
    book_text = {k: pdf_text(p, layout=False) for k, p in BOOKS.items()}
    cases = corpus_cases()
    per_cmd = Counter(n for c in cases for n in c.names)

    rows = []
    for key in {**num, **cas}:  # numeric-only additions first, then CAS entries
        h = cas.get(key) or num[key]
        bk = {k: mentions(t, h) for k, t in book_text.items()}
        total = sum(v for v in bk.values() if v > 0)
        rows.append(
            {
                "command": h.name,
                "cas_guide_page": cas[key].page if key in cas else "",
                "numeric_guide_page": num[key].page if key in num else "",
                "corpus_cases": per_cmd.get(key, 0),
                **{f"book_{k}": v for k, v in bk.items()},
                "priority": priority(per_cmd.get(key, 0), total),
                "emulator_verified": "",
                "status": "todo",
            }
        )
    known = set(cas) | set(num)
    unknown = sorted(k for k in per_cmd if k not in known)

    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    by_prio = Counter(r["priority"] for r in rows)

    def table(rank: str) -> list[str]:
        out = [
            "| Command | Corpus cases | Methods | Specialist | General |",
            "|---|---|---|---|---|",
        ]
        picked = sorted(
            (r for r in rows if r["priority"] == rank), key=lambda r: -r["corpus_cases"]
        )
        out += [
            f"| `{r['command']}` | {r['corpus_cases']} | {r['book_methods']} | "
            f"{r['book_specialist']} | {r['book_general']} |"
            for r in picked
        ]
        return out

    multi = sorted((c for c in cases if c.steps > 1), key=lambda c: -c.steps)
    lines = [
        "# Command coverage matrix",
        "",
        "Generated by `tools/ref_matrix.py`; do not edit. Full table: `command_matrix.csv`.",
        "",
        f"- {len(rows)} commands: {len(cas)} from the CAS guide (primary, software 3.2), "
        f"{len(set(num) - set(cas))} more from the numeric guide 4.5.",
        f"- Priority hint: **core** {by_prio['core']} (used by a corpus case), "
        f"**likely** {by_prio['likely']} (not in the corpus, {LIKELY_MENTIONS}+ mentions in the "
        f"VCE books), **later** {by_prio['later']}.",
        "- Book columns count `name(` in running text (-1: bare lower-case word, not countable). "
        "Screenshots in the books are not searchable, so these are lower bounds.",
        "- `emulator_verified` is empty: the guide (3.2, 2012) predates the emulator, so every "
        "entry still needs a Catalog check.",
        "",
        "## Core",
        "",
        *table("core"),
        "",
        "## Likely",
        "",
        *table("likely"),
        "",
        "## Used by the corpus but in neither guide",
        "",
        "Newer commands, user functions, or ASCII stand-ins for templates",
        "(`derivative`, `integral`). Check each against the emulator Catalog.",
        "",
        *(f"- `{k}` ({per_cmd[k]} cases)" for k in unknown),
        "",
        "## Multi-step corpus cases",
        "",
        "| Case | Steps | Commands |",
        "|---|---|---|",
        *(f"| `{c.id}` | {c.steps} | {', '.join(sorted(c.names))} |" for c in multi),
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"{len(rows)} commands (cas {len(cas)}, numeric-only {len(set(num) - set(cas))}); "
        f"core {by_prio['core']}, likely {by_prio['likely']}, later {by_prio['later']}; "
        f"{len(unknown)} corpus names in neither guide; {len(multi)} multi-step cases"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
