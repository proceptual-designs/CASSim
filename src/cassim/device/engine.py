"""The engine split (decisions 0005 and 0016): maths runs apart from the UI, so Cancel can end it.

In the browser the UI and the document model live in Flet's Python worker and `cassim.core` runs in
a second worker that Cancel terminates. Nothing synchronous can cross between them, so:

- `EngineCore` runs where the maths runs: one `Session` per Problem, driven by JSON-ready *ops*
  (`new_problem`, `settings`, `store`, `ans`, `eval`) and answering with the result and the
  variables that changed since its last reply (a *delta*, decision 0031).
- `RemoteSession` stands in for a `Session` on the UI side. It answers `is_function` and
  `variables` from its `VariableStore`, queues settings changes as ops, and keeps a journal of every
  op the engine has accepted. A fresh engine is rebuilt from the journals after a Cancel.
- `Engine` is the async transport. `LocalEngine` (here) calls an `EngineCore` in-process, for tests
  and `CASSIM_ENGINE=remote` on the desktop; the browser's worker engine is in `cassim.app.web`.

Ops and replies are `TypedDict`s, so they cross `postMessage` as JSON; `check_op` checks each op
where it enters the engine (PLAN.md section 12, A1).
"""

from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING, Literal, NotRequired, Protocol, TypedDict, cast

from cassim.core.builtin_names import is_builtin
from cassim.core.results import Result, VariableInfo
from cassim.core.settings import Settings, updated, variable_key

if TYPE_CHECKING:
    from collections.abc import Iterable

    from cassim.core.session import Session
    from cassim.device.sheets import ProblemSheets


# ---- the protocol -------------------------------------------------------------------------------


class NewProblemOp(TypedDict):
    op: Literal["new_problem"]


class SettingsOp(TypedDict):
    op: Literal["settings"]
    values: dict[str, str]


class StoreOp(TypedDict):
    op: Literal["store"]
    numbers: dict[str, float]


class AnsOp(TypedDict):
    op: Literal["ans"]
    line: str | None


class EvalOp(TypedDict):
    op: Literal["eval"]
    line: str
    approximate: bool


type SheetAction = Literal[
    "cell",
    "formula",
    "name",
    "fill",
    "sort",
    "insert",
    "delete",
    "generate",
    "recalculate",
    "view",
    "restore",
    "drop",
    "put",
    "move",
]


class SheetOp(TypedDict):
    """An action on the Lists & Spreadsheet page `page` of the Problem (slice 3a). `args` are
    checked against `SHEET_ARGS` for the action; the engine side is `cassim.device.sheets`."""

    op: Literal["sheet"]
    page: int
    action: SheetAction
    args: dict[str, object]


type Op = NewProblemOp | SettingsOp | StoreOp | AnsOp | EvalOp | SheetOp

# What each sheet action takes. "span" is [left, top, right, bottom] (columns from 0, rows from
# 1); "choose" maps a name to "cell" or "variable" (Conflict Detected).
SHEET_ARGS: dict[str, dict[str, str]] = {
    "cell": {"column": "int", "row": "int", "text": "str", "choose": "choose"},
    "formula": {"column": "int", "text": "str", "choose": "choose"},
    "name": {"column": "int", "text": "str"},
    "fill": {"source": "span", "target": "span"},
    "sort": {"span": "span", "by": "int", "descending": "bool", "confirm": "bool"},
    "insert": {"what": "part", "column": "int", "row": "int"},
    "delete": {"what": "part", "column": "int", "row": "int"},
    "generate": {
        "column": "int",
        "formula": "str",
        "initial": "str",
        "first": "int",
        "last": "int",
        "step": "int",
        "ceiling": "str",
        "confirm": "bool",
    },
    "recalculate": {},
    "view": {"span": "span"},
    "restore": {"cells": "cells", "columns": "columns"},
    "put": {"cells": "cells"},
    "move": {"column": "int", "to": "int"},
    "drop": {},
}
_PARTS = ("cell", "row", "column")


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _arg_ok(kind: str, value: object) -> bool:  # noqa: PLR0911 (one case a kind)
    match kind:
        case "int":
            return _is_int(value)
        case "str":
            return isinstance(value, str)
        case "bool":
            return isinstance(value, bool)
        case "part":
            return value in _PARTS
        case "span":
            return isinstance(value, list) and len(value) == 4 and all(map(_is_int, value))  # noqa: PLR2004
        case "choose":
            return isinstance(value, dict) and all(
                isinstance(k, str) and v in ("cell", "variable") for k, v in value.items()
            )
        case "cells":  # [[column, row, "entry" | "formula", text], ...]; "" text clears
            return isinstance(value, list) and all(
                isinstance(cell, list)
                and len(cell) == 4  # noqa: PLR2004
                and _is_int(cell[0])
                and _is_int(cell[1])
                and cell[2] in ("entry", "formula")
                and isinstance(cell[3], str)
                for cell in value
            )
        case _:  # "columns": [[name, shown name, formula], ...], each text or null
            return isinstance(value, list) and all(
                isinstance(info, list)
                and len(info) == 3  # noqa: PLR2004
                and all(part is None or isinstance(part, str) for part in info)
                for info in value
            )


def _check_sheet_op(raw: dict[str, object]) -> SheetOp:
    action, page, args = raw.get("action"), raw.get("page"), raw.get("args")
    if not isinstance(action, str) or action not in SHEET_ARGS:
        msg = f"unknown sheet action {action!r}"
        raise EngineError(msg)
    if not isinstance(page, int) or isinstance(page, bool) or not isinstance(args, dict):
        msg = "a sheet op needs a page number and args"
        raise EngineError(msg)
    wanted = SHEET_ARGS[action]
    if set(args) != set(wanted) or not all(_arg_ok(wanted[k], args[k]) for k in wanted):
        msg = f"bad args for sheet {action}: {args!r}"
        raise EngineError(msg)
    return {
        "op": "sheet",
        "page": page,
        "action": cast("SheetAction", action),
        "args": {str(k): v for k, v in args.items()},
    }


class ResultPayload(TypedDict):
    text: str
    latex: str
    error: str | None
    full: str
    warnings: list[str]


class Row(TypedDict):
    """One variable-list row (`VariableInfo` as JSON)."""

    name: str
    text: str
    latex: str
    is_function: bool


class NoticePayload(TypedDict):
    title: str
    message: str


class SheetErrorPayload(TypedDict):
    """A sheet action refused: the dialog to show. `names` lists the Cell-or-Variable choices
    for Conflict Detected; "Data Loss" asks OK before the action is sent again confirmed."""

    title: str
    message: str
    names: list[str]


type ColumnPayload = tuple[str | None, str | None, str | None]


class SheetReply(TypedDict):
    page: int
    revision: int  # raised whenever anything drawn on the sheet changes
    notices: list[NoticePayload]  # dialogs for changes that were kept
    error: SheetErrorPayload | None
    cells: list[tuple[int, int, str, bool, str]]  # a view: column, row, shown, right, entry text
    span: list[int]  # the view's [left, top, right, bottom]; [] when none was asked for
    # The page's definitions as they changed since its last reply, for the UI's copy (it saves
    # the document): cells as (column, row, kind, text) with kind "" for a cleared cell, and every
    # column's (name, shown name, formula) when any of them changed.
    edits: list[tuple[int, int, str, str]]
    columns: list[ColumnPayload]


class Reply(TypedDict):
    result: ResultPayload | None  # the last `eval`'s result
    full: bool  # `changed` is every variable: replace, do not merge
    changed: list[Row]  # rows stored since the last reply
    deleted: list[str]  # names deleted since the last reply
    sheets: NotRequired[list[SheetReply]]  # the sheets that changed or were asked about


class EngineError(RuntimeError):
    """The engine could not run an op (a crashed worker, or an op it does not know); not a TI
    error, which is in the result."""


def _text(value: object, what: str) -> str:
    if not isinstance(value, str):
        msg = f"{what} must be text"
        raise EngineError(msg)
    return value


def check_op(raw: object) -> Op:
    """`raw` as an op, checked field by field: what arrives from another worker is only JSON."""
    if not isinstance(raw, dict) or not isinstance(raw.get("op"), str):
        msg = f"not an engine op: {raw!r}"
        raise EngineError(msg)
    name = raw["op"]
    if name == "new_problem":
        return {"op": "new_problem"}
    if name == "settings":
        values = raw.get("values")
        if not isinstance(values, dict):
            msg = "settings values must be a mapping"
            raise EngineError(msg)
        return {
            "op": "settings",
            "values": {_text(k, "a setting"): _text(v, k) for k, v in values.items()},
        }
    if name == "store":
        numbers = raw.get("numbers")
        if not isinstance(numbers, dict) or not all(
            isinstance(v, int | float) and not isinstance(v, bool) for v in numbers.values()
        ):
            msg = "store numbers must be a mapping of names to numbers"
            raise EngineError(msg)
        return {
            "op": "store",
            "numbers": {_text(k, "a name"): float(v) for k, v in numbers.items()},
        }
    if name == "ans":
        line = raw.get("line")
        return {"op": "ans", "line": None if line is None else _text(line, "the Ans line")}
    if name == "eval":
        approximate = raw.get("approximate")
        if not isinstance(approximate, bool):
            msg = "eval needs approximate: true or false"
            raise EngineError(msg)
        return {
            "op": "eval",
            "line": _text(raw.get("line"), "the entry"),
            "approximate": approximate,
        }
    if name == "sheet":
        return _check_sheet_op(raw)
    msg = f"unknown engine op {name!r}"
    raise EngineError(msg)


def check_reply(raw: object) -> Reply:
    """`raw` as a reply, checked where it comes back from the engine's worker."""
    if not (
        isinstance(raw, dict)
        and "result" in raw
        and isinstance(raw.get("full"), bool)
        and isinstance(raw.get("changed"), list)
        and isinstance(raw.get("deleted"), list)
        and (raw.get("result") is None or isinstance(raw.get("result"), dict))
    ):
        msg = f"not an engine reply: {str(raw)[:80]}"
        raise EngineError(msg)
    for row in raw["changed"]:
        if not (isinstance(row, dict) and set(row) == {"name", "text", "latex", "is_function"}):
            msg = f"not a variable row: {row!r}"
            raise EngineError(msg)
    result = raw["result"]
    if result is not None and set(result) != {"text", "latex", "error", "full", "warnings"}:
        msg = f"not a result: {result!r}"
        raise EngineError(msg)
    checked: Reply = {
        "result": result,
        "full": raw["full"],
        "changed": raw["changed"],
        "deleted": [_text(name, "a deleted name") for name in raw["deleted"]],
    }
    if "sheets" in raw:
        sheets = raw["sheets"]
        keys = {"page", "revision", "notices", "error", "cells", "span", "edits", "columns"}
        if not isinstance(sheets, list) or not all(
            isinstance(sheet, dict) and set(sheet) == keys for sheet in sheets
        ):
            msg = f"not sheet replies: {str(sheets)[:80]}"
            raise EngineError(msg)
        checked["sheets"] = sheets
    return checked


def settings_op(settings: Settings) -> SettingsOp:
    return {"op": "settings", "values": {k: str(v) for k, v in asdict(settings).items()}}


def eval_op(line: str, *, approximate: bool) -> EvalOp:
    return {"op": "eval", "line": line, "approximate": approximate}


def store_op(numbers: dict[str, float]) -> StoreOp:
    return {"op": "store", "numbers": numbers}


def local_session(settings: Settings | None = None) -> Session:
    """A `Session` that does its maths in this process.

    The import waits until one is wanted: it loads SymPy, which takes seconds in the browser, and
    the UI's worker there only ever makes `RemoteSession`s (decision 0027).
    """
    from cassim.core.session import Session  # noqa: PLC0415

    return Session(settings)


# ---- the engine side ----------------------------------------------------------------------------


class EngineCore:
    """One Session per Problem id, driven by ops. Pure Python, no UI and no transport."""

    def __init__(self) -> None:
        self.sessions: dict[int, Session] = {}
        self.sheets: dict[int, ProblemSheets] = {}  # the Problems that have a sheet
        # Per Problem: the scope revision and settings of the last reply. A Problem with no entry
        # (new, or after `reset`) gets every variable; a settings change does too, since the
        # display text of every value may change with it.
        self._sent: dict[int, tuple[int, Settings]] = {}

    def apply(self, problem: int, ops: Iterable[object]) -> Reply:
        """Apply `ops` in order; the reply holds the last `eval`'s result and the variables that
        changed since the previous reply for this Problem."""
        checked = [check_op(op) for op in ops]  # all of them before any runs
        session = self.sessions.get(problem)
        if session is None:
            session = self.sessions[problem] = local_session()
        result: ResultPayload | None = None
        sheet_replies: dict[int, SheetReply] = {}
        for op in checked:
            settings = session.settings
            match op["op"]:
                case "new_problem":
                    session.new_problem()
                case "settings":
                    session.settings = updated(session.settings, op["values"])
                case "store":
                    session.store_numbers(op["numbers"])
                case "ans":
                    session.set_ans(op["line"])
                case "eval":
                    done = session.eval(op["line"], approximate=op["approximate"])
                    result = {
                        "text": done.text,
                        "latex": done.latex,
                        "error": done.error,
                        "full": done.full,
                        "warnings": list(done.warnings),
                    }
                case "sheet":
                    self._sheets_of(problem, session).run(op, sheet_replies)
            if problem in self.sheets:
                changed = session.settings != settings
                self.sheets[problem].settle(sheet_replies, recalculate=changed)
        scope = session.scope
        sent = self._sent.get(problem)
        full = sent is None or sent[1] != session.settings
        names = scope.names() if full else scope.changed_since(sent[0])
        self._sent[problem] = (scope.revision, session.settings)
        rows = session.rows(names)
        present = {row.name for row in rows}
        reply: Reply = {
            "result": result,
            "full": full,
            "changed": [
                {"name": r.name, "text": r.text, "latex": r.latex, "is_function": r.is_function}
                for r in rows
            ],
            "deleted": [] if full else sorted(names - present),
        }
        if sheet_replies:
            reply["sheets"] = [sheet_replies[page] for page in sorted(sheet_replies)]
        return reply

    def _sheets_of(self, problem: int, session: Session) -> ProblemSheets:
        if problem not in self.sheets:
            from cassim.device.sheets import ProblemSheets  # noqa: PLC0415 (loads SymPy)

            self.sheets[problem] = ProblemSheets(session)
        return self.sheets[problem]

    def reset(self, journals: dict[int, list[Op]]) -> None:
        """Forget everything and rebuild each Problem by replaying its journal. The next reply for
        each Problem is a full one, since the UI did not see the replay's replies. A sheet's
        random numbers are drawn again, as Ctrl+R draws them (decision 0031)."""
        self.sessions.clear()
        self.sheets.clear()
        for problem, ops in journals.items():
            self.apply(problem, ops)
        self._sent.clear()


class Engine(Protocol):
    """The async side the UI talks to."""

    async def run(self, problem: int, ops: list[Op]) -> Reply: ...

    async def reset(self, journals: dict[int, list[Op]]) -> None:
        """Replace the engine's state with a replay of `journals` (after a Cancel)."""

    def cancel(self) -> bool:
        """Stop the run in progress. False when this engine cannot be interrupted."""
        ...


class LocalEngine:
    """An `EngineCore` called in-process: nothing can interrupt it, so Cancel is refused."""

    def __init__(self) -> None:
        self.core = EngineCore()

    async def run(self, problem: int, ops: list[Op]) -> Reply:
        return self.core.apply(problem, ops)

    async def reset(self, journals: dict[int, list[Op]]) -> None:
        self.core.reset(journals)

    def cancel(self) -> bool:
        return False


# ---- the UI side --------------------------------------------------------------------------------


class VariableStore:
    """The UI's copy of one Problem's variable list, kept up to date from the engine's replies.

    Each name has a revision of the store's own, raised when its row changes, so a page can record
    what it drew and redraw only when a revision it used is newer (FR-DOC-008). The store's
    revisions are its own, so they keep rising when a Cancel replaces the engine.
    """

    def __init__(self) -> None:
        self._rows: dict[str, VariableInfo] = {}
        self._revisions: dict[str, int] = {}
        self.revision = 0

    def _set(self, name: str, row: VariableInfo | None) -> None:
        if self._rows.get(name) == row:
            return
        if row is None:
            del self._rows[name]
        else:
            self._rows[name] = row
        self.revision += 1
        self._revisions[name] = self.revision

    def apply(self, reply: Reply) -> None:
        rows = {row["name"]: VariableInfo(**row) for row in reply["changed"]}
        gone = set(reply["deleted"])
        if reply["full"]:
            gone |= set(self._rows) - set(rows)
        for name in sorted(gone & set(self._rows)):
            self._set(name, None)
        for name, row in rows.items():
            self._set(name, row)

    def variables(self) -> list[VariableInfo]:
        return [self._rows[name] for name in sorted(self._rows)]

    def revision_of(self, name: str) -> int:
        return self._revisions.get(name, 0)

    def get(self, name: str) -> VariableInfo | None:
        return self._rows.get(name)


class RemoteSession:
    """The UI's view of one Problem's session while the maths runs elsewhere.

    It looks like a `Session` to the device model, but `eval` is not available: the Calculator
    notices `deferred` and hands the entry to the app's `Runner` instead.
    """

    deferred = True

    def __init__(self, problem_id: int, settings: Settings | None = None) -> None:
        self.id = problem_id
        self._settings = settings if settings is not None else Settings()
        self.journal: list[Op] = []  # ops the engine has accepted: the state, as a replay
        self.outbox: list[Op] = []  # ops it has not seen yet
        self.store = VariableStore()
        # Sheet replies by page id, until the page takes them (`cassim.device.sheet_link`)
        self.sheet_inbox: dict[int, list[SheetReply]] = {}
        if self._settings != Settings():
            self.outbox.append(settings_op(self._settings))

    @property
    def settings(self) -> Settings:
        return self._settings

    @settings.setter
    def settings(self, settings: Settings) -> None:
        if settings != self._settings:
            self._settings = settings
            self.outbox.append(settings_op(settings))

    def set(self, **changes: str) -> None:
        self.settings = updated(self._settings, changes)

    def new_problem(self) -> None:
        self.outbox.append({"op": "new_problem"})

    def store_numbers(self, numbers: dict[str, float]) -> None:
        self.outbox.append(store_op(numbers))

    def set_ans(self, line: str | None) -> None:
        self.outbox.append({"op": "ans", "line": line})

    def eval(self, line: str, *, approximate: bool = False) -> Result:
        msg = "a RemoteSession evaluates through the app's Runner, not synchronously"
        raise NotImplementedError(msg)

    def _row(self, name: str) -> VariableInfo | None:
        return self.store.get(variable_key(self._settings, name))

    def is_function(self, name: str) -> bool:
        row = self._row(name)
        return is_builtin(name.casefold()) or (row is not None and row.is_function)

    def is_defined(self, name: str) -> bool:
        return self._row(name) is not None

    def variables(self) -> list[VariableInfo]:
        return self.store.variables()

    def revision_of(self, name: str) -> int:
        """When the variable `name` last changed, by the store's count (FR-DOC-008)."""
        return self.store.revision_of(variable_key(self._settings, name))

    # ---- the Runner's side ------------------------------------------------------------------

    def take(self) -> list[Op]:
        """The queued ops, for sending. They stay queued until `accept`."""
        return list(self.outbox)

    def accept(self, sent: list[Op], reply: Reply) -> None:
        """The engine applied `sent`: move them to the journal and take its changes."""
        del self.outbox[: len(sent)]
        self.journal.extend(op for op in sent if not _is_view(op))  # a view changes nothing
        self.store.apply(reply)
        for sheet in reply.get("sheets", []):
            self.sheet_inbox.setdefault(sheet["page"], []).append(sheet)

    def compact(self, page: int, restore: SheetOp) -> None:
        """Keep one op for a sheet in the journal: `restore` with its contents now, where its
        last op was. A rebuild then replays the sheet as it is, not every edit (decision 0031).
        An entry made between two of its edits replays against the sheet's later state."""
        last = max(
            (n for n, op in enumerate(self.journal) if op["op"] == "sheet" and op["page"] == page),
            default=None,
        )
        if last is None:
            return
        self.journal[last] = restore
        self.journal[:last] = [
            op for op in self.journal[:last] if not (op["op"] == "sheet" and op["page"] == page)
        ]


def _is_view(op: Op) -> bool:
    return op["op"] == "sheet" and op["action"] == "view"
