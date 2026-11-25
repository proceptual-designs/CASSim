"""Editor trees as JSON, and a stand-in for `cassim.device.editor.Template` in the browser.

A row is a list; a character is a one-character str; a template is `{"k": kind, "c": cols,
"s": [rows]}`. Paths are written `"i.s/i.s"` (empty for the root row).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class T:
    """Duck-types `Template`: `kind` compares equal to the `Kind` value string."""

    kind: str
    slots: list[list[Any]] = field(default_factory=list)
    cols: int = 0


def dump_row(row: list[Any]) -> list[Any]:
    return [
        n if isinstance(n, str) else {"k": str(n.kind), "c": n.cols, "s": [dump_row(s) for s in n.slots]}
        for n in row
    ]


def load_row(data: list[Any]) -> list[Any]:
    return [n if isinstance(n, str) else T(n["k"], [load_row(s) for s in n["s"]], n["c"]) for n in data]


def path_key(path: list[tuple[int, int]] | tuple[tuple[int, int], ...]) -> str:
    return "/".join(f"{i}.{s}" for i, s in path)


def styles_for(row: list[Any]) -> dict[str, dict[str, list[str]]]:
    """Host only: the name styles of every row, from the real editor code."""
    from cassim.device.editor import at_constants, constant_style, name_styles  # noqa: PLC0415

    out: dict[str, dict[str, list[str]]] = {}

    def walk(r: list[Any], path: list[tuple[int, int]]) -> None:
        marks: dict[str, list[str]] = {}
        for i, style in name_styles(r, lambda _: False).items():
            marks[str(i)] = [str(style), str(r[i])]
        for i, shown in at_constants(r).items():
            marks[str(i)] = [str(constant_style(shown)) if shown else "hidden", shown]
        if marks:
            out[path_key(path)] = marks
        for i, n in enumerate(r):
            if not isinstance(n, str):
                for s, slot in enumerate(n.slots):
                    walk(slot, [*path, (i, s)])

    walk(row, [])
    return out
