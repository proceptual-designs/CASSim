"""Regenerate `src/cassim/core/builtin_names.py` from the catalog.

    python -m tools.builtin_names

The UI asks whether a name is a built-in function (to set it upright and bold) but must not import
the catalog, which loads SymPy (decision 0027). `tests/unit/test_builtin_names.py` fails when the
file and the catalog disagree.
"""

from __future__ import annotations

from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "src" / "cassim" / "core" / "builtin_names.py"
MARK = "NAMES = frozenset(\n"


def render() -> str:
    from cassim.core.catalog import registry

    head = TARGET.read_text(encoding="utf-8").split(MARK)[0]
    rows = "".join(f'        "{name}",\n' for name in sorted(registry.canonical_names()))
    return f"{head}{MARK}    {{\n{rows}    }}\n)\n"


def main() -> None:
    TARGET.write_text(render(), encoding="utf-8", newline="\n")
    print(f"wrote {TARGET}")


if __name__ == "__main__":
    main()
