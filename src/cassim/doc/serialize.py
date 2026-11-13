"""Documents as plain, versioned JSON (FR-DOC-003, FR-DOC-004).

Each page type writes and reads its own part of the file (`PageType.dump` and `load`). A page
saves what was typed, not results: loading replays it, so every result and variable is recomputed
by the engine and a file can never hold a stale answer. Random results therefore differ after a
load. The file names its device (FR-PROF-009); one with no name is an Nspire document.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Generator
from dataclasses import asdict
from typing import TYPE_CHECKING, Any

from cassim.core.settings import Settings
from cassim.device.engine import RemoteSession, local_session
from cassim.doc.document import Document, Page, PageTypes

if TYPE_CHECKING:
    from cassim.core.session import Session

SCHEMA = 1
FORMAT = "cassim-document"
FIRST_DEVICE = "nspire"  # files written before files named their device
SUFFIX = ".cassim.json"
"""Open and Save read and write only this native format (FR-DOC-006). Foreign formats such as
`.tns`, if ever supported, belong under File > Import and Export, never Open or Save."""
OPEN_EXTENSIONS = ("json",)
"""What the Open dialog offers. Browsers filter on the last extension only, so `.cassim.json`
files are offered as `json`; anything that is not a CASSim document fails in `parse`."""


def file_name(document: Document) -> str:
    """The name Save gives the document's file."""
    return f"{document.name}{SUFFIX}"


class DocumentFileError(ValueError):
    """The text is not a CASSim document this version can open."""


# ---- documents ------------------------------------------------------------------------------


def to_dict(document: Document) -> dict[str, Any]:
    """The document as JSON-ready data."""
    problems = []
    for problem in document.problems:
        pages = []
        for page in problem.pages:
            item: dict[str, Any] = {"kind": str(page.kind)}
            if page.model is not None:
                item.update(page.type.dump(page.model))
            pages.append(item)
        problems.append({"pages": pages})
    return {
        "format": FORMAT,
        "schema": SCHEMA,
        "device": document.types.device,
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
    data: dict[str, Any],
    types: PageTypes,
    sessions: Callable[[Settings], Session | RemoteSession] = local_session,
) -> Document:
    """Rebuild a document, replaying every entry through the engine (all in this process)."""
    steps = replay_steps(data, types, sessions)
    while True:
        try:
            next(steps)  # a deferred session would yield here; `Session` never does
        except StopIteration as done:
            return done.value


def replay_steps(
    data: dict[str, Any],
    types: PageTypes,
    sessions: Callable[[Settings], Session | RemoteSession],
) -> Generator[Any, None, Document]:
    """Replay a document's entries: the public interface for loading, shared by `from_dict` (all in
    this process) and `Runner.load` (through a worker).

    A generator: each time an entry waits for a remote engine it yields the page model that is
    waiting, the driver evaluates it (`Runner.evaluate`) and resumes; the finished Document is the
    return value (`StopIteration.value`). Sessions that never yield run straight through."""
    data = migrate(data)
    device = data.get("device", FIRST_DEVICE)
    if device != types.device:
        msg = f"the document is for the {device} device, which this build does not hold"
        raise DocumentFileError(msg)
    try:
        settings = Settings(**data.get("settings", {}))
        document = Document(types, str(data.get("name", "Untitled")), settings, sessions)
        document.problems.clear()
        for saved in data["problems"]:
            document.problem = len(document.problems) - 1
            document.add_problem()  # a fresh Problem (and Session) at the end, with one page
            problem = document.problems[document.problem]
            problem.pages.clear()
            for page_data in saved["pages"]:
                page_type = types[page_data["kind"]]
                model = yield from page_type.load(page_type, problem, page_data)
                problem.pages.append(Page(page_type, model))
            for page in problem.pages:
                page.type.after(page.model)
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


def loads(text: str, types: PageTypes) -> Document:
    return from_dict(parse(text), types)
