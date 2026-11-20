"""Serialize structured maths-entry nodes for Nspire page definitions."""

from typing import Any

from cassim.device.editor import GRIDS, Kind, Node, Row, Template
from cassim.doc.serialize import DocumentFileError


def dump_nodes(nodes: Row | tuple[Node, ...]) -> str | list[Any]:
    """Write plain runs as text and templates as their kind and slots."""
    out: list[Any] = []
    for node in nodes:
        if isinstance(node, str):
            if out and isinstance(out[-1], str):
                out[-1] += node
            else:
                out.append(node)
        else:
            item: dict[str, Any] = {
                "kind": node.kind.value,
                "slots": [dump_nodes(slot) for slot in node.slots],
            }
            if node.cols:
                item["cols"] = node.cols
            out.append(item)
    if not out:
        return ""
    if len(out) == 1 and isinstance(out[0], str):
        return out[0]
    return out


def load_nodes(items: str | list[Any]) -> Row:
    """Read the entry representation, including schema-1 single-character runs."""
    if isinstance(items, str):
        return list(items)
    if not isinstance(items, list):
        raise DocumentFileError("bad editor row")
    row: Row = []
    for item in items:
        if isinstance(item, str):
            row.extend(item)
        elif isinstance(item, dict):
            kind = Kind(item["kind"])
            slots = item["slots"]
            cols = item.get("cols", 0)
            if not isinstance(slots, list) or not isinstance(cols, int) or isinstance(cols, bool):
                raise DocumentFileError("bad editor template")
            if kind in GRIDS:
                fixed = GRIDS[kind]
                valid = cols > 0 and bool(slots) and len(slots) % cols == 0
                valid = valid and (not fixed or cols == fixed)
            else:
                valid = cols == 0 and len(slots) == len(Template.empty(kind).slots)
            if not valid:
                raise DocumentFileError("bad editor template shape")
            row.append(Template(kind, [load_nodes(slot) for slot in slots], cols))
        else:
            msg = f"bad editor node {item!r}"
            raise DocumentFileError(msg)
    return row
