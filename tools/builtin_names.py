"""Regenerate `src/cassim/core/builtin_names.py` from the catalog.

    python -m tools.builtin_names

The UI asks whether a name is a built-in function (to set it upright) and how the Catalog spells
it (to correct its case on Return), but must not import the catalog, which loads SymPy (decision
0027). `tests/unit/test_builtin_names.py` fails when the file and the catalog disagree.
"""

from __future__ import annotations

from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "src" / "cassim" / "core" / "builtin_names.py"
MARK = "SPELLINGS: dict[str, str] = {\n"


def render() -> str:
    from cassim.core.catalog import registry

    head = TARGET.read_text(encoding="utf-8").split(MARK)[0]
    rows = "".join(
        f'    "{key}": "{name}",\n' for key, name in sorted(registry.spellings().items())
    )
    return f"{head}{MARK}{rows}}}\nNAMES = frozenset(SPELLINGS)\n"


def main() -> None:
    TARGET.write_text(render(), encoding="utf-8", newline="\n")
    print(f"wrote {TARGET}")


if __name__ == "__main__":
    main()
