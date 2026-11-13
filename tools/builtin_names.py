"""Regenerate `src/cassim/core/builtin_names.py` from the catalog and the command matrix.

    python -m tools.builtin_names

The UI asks whether a name is a built-in function (to set it upright) and how the Catalog spells
it (to correct its case on Return), but must not import the catalog, which loads SymPy (decision
0027). `tests/unit/test_builtin_names.py` fails when the file and the catalog disagree.

`PLANNED` holds the Reference Guide's functions that the catalog does not have yet, read from
`docs/command_matrix.csv`. Their names are taken already: the handheld refuses `count:={5,3,1,1}`
with "Missing (" (emulator check 6, part J), so CASSim must not let a student store to one.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "src" / "cassim" / "core" / "builtin_names.py"
MATRIX = ROOT / "docs" / "command_matrix.csv"
MARK = "SPELLINGS: dict[str, str] = {\n"
# A matrix row for a function is its name and `()`: `count()`, `colDim()`, `sech⁻¹()`.
_FUNCTION_ROW = re.compile(r"([A-Za-z][A-Za-z0-9_]*(?:⁻¹)?)\(\)")
# Rows whose name pdftotext garbled (`χ²` read as `c2`, `▶` as `4`), and `d()`, the derivative,
# which is written `d(`: plain `d` stays a variable name.
_NOT_NAMES = frozenset(
    {"c2cdf", "c2pdf", "invc2", "x2", "exp4list", "list4mat", "mat4list"}
    | {"p4rx", "p4ry", "r4pq", "r4pr", "gint", "dimension", "d"}
)


def planned(known: frozenset[str]) -> list[str]:
    """The matrix's function names that the catalog does not know, by their canonical key."""
    from cassim.core.builtin_names import canonical

    with MATRIX.open(encoding="utf-8", newline="") as handle:
        commands = [row["command"] for row in csv.DictReader(handle)]
    keys = {canonical(m[1]) for c in commands if (m := _FUNCTION_ROW.fullmatch(c))}
    return sorted(keys - known - _NOT_NAMES)


def render() -> str:
    from cassim.core.catalog import registry

    head = TARGET.read_text(encoding="utf-8").split(MARK)[0]
    spellings = registry.spellings()
    rows = "".join(f'    "{key}": "{name}",\n' for key, name in sorted(spellings.items()))
    later = "".join(f'        "{key}",\n' for key in planned(frozenset(spellings)))
    return (
        f"{head}{MARK}{rows}}}\nNAMES = frozenset(SPELLINGS)\n"
        f"PLANNED = frozenset(\n    {{\n{later}    }}\n)\n"
    )


def main() -> None:
    TARGET.write_text(render(), encoding="utf-8", newline="\n")
    print(f"wrote {TARGET}")


if __name__ == "__main__":
    main()
