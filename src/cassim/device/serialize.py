"""Documents as plain, versioned JSON (FR-DOC-003, FR-DOC-004).

A saved Calculator page holds the entries as typed (the editor's nodes, so templates survive), not
their results: loading replays them in order, so every result and variable is recomputed by the
engine and a file can never hold a stale answer. Random results therefore differ after a load.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Generator
from dataclasses import asdict
from typing import TYPE_CHECKING, Any

from cassim.core.settings import Settings
from cassim.device.calculator import Calculator
from cassim.device.document import Document, Page, PageKind
from cassim.device.editor import Kind, Node, Row, Template
from cassim.device.engine import RemoteSession, local_session
from cassim.device.keys import Binding

if TYPE_CHECKING:
    from cassim.core.session import Session

SCHEMA = 1
FORMAT = "cassim-document"


class DocumentFileError(ValueError):
    """The text is not a CASSim document this version can open."""


# ---- nodes ----------------------------------------------------------------------------------


def _dump_nodes(nodes: Row | tuple[Node, ...]) -> list[Any]:
    out: list[Any] = []
    for node in nodes:
        if isinstance(node, str):
            out.append(node)
        else:
            item: dict[str, Any] = {
                "kind": node.kind.value,
                "slots": [_dump_nodes(slot) for slot in node.slots],
            }
            if node.cols:
                item["cols"] = node.cols
            out.append(item)
    return out


def _load_nodes(items: list[Any]) -> Row:
    row: Row = []
    for item in items:
        if isinstance(item, str):
            row.append(item)
        elif isinstance(item, dict):
            row.append(
                Template(
                    Kind(item["kind"]),
                    [_load_nodes(slot) for slot in item["slots"]],
                    int(item.get("cols", 0)),
                )
            )
        else:
            msg = f"bad editor node {item!r}"
            raise DocumentFileError(msg)
    return row


# ---- documents ------------------------------------------------------------------------------


def to_dict(document: Document) -> dict[str, Any]:
    """The document as JSON-ready data."""
    problems = []
    for problem in document.problems:
        pages = []
        for page in problem.pages:
            item: dict[str, Any] = {"kind": page.kind.value}
            if page.calculator is not None:
                calculator = page.calculator
                item["entries"] = [
                    {
                        "nodes": _dump_nodes(entry.source or entry.nodes),
                        "approximate": entry.approximate,
                    }
                    for entry in calculator.history
                ]
                item["entry"] = _dump_nodes(calculator.editor.root)
            pages.append(item)
        problems.append({"pages": pages})
    return {
        "format": FORMAT,
        "schema": SCHEMA,
        "name": document.name,
        "settings": {key: str(value) for key, value in asdict(document.settings).items()},
        "problem": document.problem,
        "page": document.page,
        "problems": problems,
    }


def dumps(document: Document) -> str:
    return json.dumps(to_dict(document), ensure_ascii=False, indent=1)


def migrate(data: dict[str, Any]) -> dict[str, Any]:
    """Bring older files up to `SCHEMA`. There is only one schema so far; each later one adds a
    step here (FR-DOC-004)."""
    if data.get("format") != FORMAT:
        msg = "this is not a CASSim document"
        raise DocumentFileError(msg)
    version = data.get("schema")
    if not isinstance(version, int) or version < 1:
        msg = "the document has no valid schema version"
        raise DocumentFileError(msg)
    if version > SCHEMA:
        msg = f"the document was saved by a newer CASSim (schema {version}, this reads {SCHEMA})"
        raise DocumentFileError(msg)
    return data


def from_dict(
    data: dict[str, Any], sessions: Callable[[Settings], Session | RemoteSession] = local_session
) -> Document:
    """Rebuild a document, replaying every entry through the engine (all in this process)."""
    steps = replay_steps(data, sessions)
    while True:
        try:
            next(steps)  # a deferred session would yield here; `Session` never does
        except StopIteration as done:
            return done.value


def replay_steps(
    data: dict[str, Any], sessions: Callable[[Settings], Session | RemoteSession]
) -> Generator[Calculator, None, Document]:
    """Replay a document's entries: the public interface for loading, shared by `from_dict` (all in
    this process) and `Runner.load` (through a worker).

    A generator: each time an entry waits for a remote engine it yields its Calculator, the driver
    evaluates it (`Runner.evaluate`) and resumes; the finished Document is the return value
    (`StopIteration.value`). Sessions that never yield run straight through."""
    data = migrate(data)
    try:
        settings = Settings(**data.get("settings", {}))
        document = Document(str(data.get("name", "Untitled")), settings, sessions)
        document.problems.clear()
        for saved in data["problems"]:
            document.problem = len(document.problems) - 1
            document.add_problem()  # a fresh Problem (and Session) at the end, with one page
            problem = document.problems[document.problem]
            problem.pages.clear()
            for page_data in saved["pages"]:
                problem.pages.append((yield from _load_page(document, page_data)))
        document.go(
            min(int(data.get("problem", 0)), len(document.problems) - 1),
            0,
        )
        document.page = max(
            0, min(int(data.get("page", 0)), len(document.problems[document.problem].pages) - 1)
        )
    except (KeyError, TypeError, ValueError) as error:
        msg = f"the document is damaged: {error}"
        raise DocumentFileError(msg) from error
    document.forget_history()
    return document


def _load_page(document: Document, data: dict[str, Any]) -> Generator[Calculator, None, Page]:
    problem = document.problems[document.problem]
    page = problem.new_page(PageKind(data["kind"]))
    calculator = page.calculator
    if calculator is None:
        return page
    for entry in data.get("entries", []):
        calculator.editor.clear()
        calculator.editor.root = _load_nodes(entry["nodes"])
        calculator.editor.pos = len(calculator.editor.root)
        calculator.perform(Binding("approximate" if entry.get("approximate") else "enter"))
        if calculator.pending is not None:
            yield calculator
        calculator.error = None  # an entry that fails now was kept as typed; drop its dialog
    calculator.editor.clear()
    calculator.editor.root = _load_nodes(data.get("entry", []))
    calculator.editor.pos = len(calculator.editor.root)
    calculator.forget_undo()  # loading is not something to undo
    return page


def parse(text: str) -> dict[str, Any]:
    """The JSON of a document file, checked to be an object."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        msg = f"the file is not valid JSON: {error}"
        raise DocumentFileError(msg) from error
    if not isinstance(data, dict):
        msg = "this is not a CASSim document"
        raise DocumentFileError(msg)
    return data


def loads(text: str) -> Document:
    return from_dict(parse(text))
