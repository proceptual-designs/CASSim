"""The engine split (decisions 0005 and 0016): maths runs apart from the UI, so Cancel can end it.

In the browser the UI and the document model live in Flet's Python worker and `cassim.core` runs in
a second worker that Cancel terminates. Nothing synchronous can cross between them, so:

- `EngineCore` runs where the maths runs: one `Session` per Problem, driven by JSON-ready *ops*
  (`new_problem`, `settings`, `eval`) and answering with the result and a *snapshot* (the variable
  list, which the UI cannot ask for synchronously).
- `RemoteSession` stands in for a `Session` on the UI side. It answers `is_function` and
  `variables` from the last snapshot, queues settings changes as ops, and keeps a journal of every
  op the engine has accepted. A fresh engine is rebuilt from the journals after a Cancel.
- `Engine` is the async transport. `LocalEngine` (here) calls an `EngineCore` in-process, for tests
  and `CASSIM_ENGINE=remote` on the desktop; the browser's worker engine is in `cassim.app.web`.

Ops and replies are plain dicts so they cross `postMessage` as JSON.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Protocol

from cassim.core.builtin_names import is_builtin
from cassim.core.results import Result, VariableInfo
from cassim.core.settings import Settings, updated, variable_key

if TYPE_CHECKING:
    from collections.abc import Iterable

    from cassim.core.session import Session

type Op = dict[str, Any]
type Reply = dict[str, Any]


def settings_op(settings: Settings) -> Op:
    return {"op": "settings", "values": {k: str(v) for k, v in asdict(settings).items()}}


def eval_op(line: str, *, approximate: bool) -> Op:
    return {"op": "eval", "line": line, "approximate": approximate}


def store_op(numbers: dict[str, float]) -> Op:
    return {"op": "store", "numbers": numbers}


def local_session(settings: Settings | None = None) -> Session:
    """A `Session` that does its maths in this process.

    The import waits until one is wanted: it loads SymPy, which takes seconds in the browser, and
    the UI's worker there only ever makes `RemoteSession`s (decision 0027).
    """
    from cassim.core.session import Session  # noqa: PLC0415

    return Session(settings)


class EngineError(RuntimeError):
    """The engine could not run an op (a crashed worker); not a TI error, which is in the result."""


class EngineCore:
    """One Session per Problem id, driven by ops. Pure Python, no UI and no transport."""

    def __init__(self) -> None:
        self.sessions: dict[int, Session] = {}

    def apply(self, problem: int, ops: Iterable[Op]) -> Reply:
        """Apply `ops` in order; the reply holds the last `eval`'s result and the snapshot."""
        session = self.sessions.get(problem)
        if session is None:
            session = self.sessions[problem] = local_session()
        result: dict[str, Any] | None = None
        for op in ops:
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
                    done = session.eval(op["line"], approximate=bool(op["approximate"]))
                    result = {
                        "text": done.text,
                        "latex": done.latex,
                        "error": done.error,
                        "full": done.full,
                    }
                case other:
                    msg = f"unknown engine op {other!r}"
                    raise ValueError(msg)
        rows = session.variables()
        return {
            "result": result,
            "variables": [asdict(row) for row in rows],
            "functions": sorted(row.name for row in rows if row.is_function),
        }

    def reset(self, journals: dict[int, list[Op]]) -> None:
        """Forget everything and rebuild each Problem by replaying its journal."""
        self.sessions.clear()
        for problem, ops in journals.items():
            self.apply(problem, ops)


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
        self._rows: list[VariableInfo] = []
        self._functions: set[str] = set()
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

    def is_function(self, name: str) -> bool:
        return is_builtin(name.casefold()) or (
            variable_key(self._settings, name) in self._functions
        )

    def is_defined(self, name: str) -> bool:
        key = variable_key(self._settings, name)
        return any(variable_key(self._settings, row.name) == key for row in self._rows)

    def variables(self) -> list[VariableInfo]:
        return list(self._rows)

    # ---- the Runner's side ------------------------------------------------------------------

    def take(self) -> list[Op]:
        """The queued ops, for sending. They stay queued until `accept`."""
        return list(self.outbox)

    def accept(self, sent: list[Op], reply: Reply) -> None:
        """The engine applied `sent`: move them to the journal and keep its snapshot."""
        del self.outbox[: len(sent)]
        self.journal.extend(sent)
        self._rows = [VariableInfo(**row) for row in reply["variables"]]
        self._functions = set(reply["functions"])
