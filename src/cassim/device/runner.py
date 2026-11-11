"""Runs entries on the engine and owns Cancel (decisions 0005 and 0016).

The device model is synchronous, so a Calculator on a `RemoteSession` only queues an entry
(`Calculator.pending`). The app calls `Runner.evaluate` to send it to the `Engine` and finish it,
and `Runner.cancel` to stop a run: the engine is replaced and rebuilt from the journals of every
`RemoteSession` the runner has made, so Problems, variables and functions survive.
"""

from __future__ import annotations

import asyncio
from enum import StrEnum
from typing import TYPE_CHECKING

from cassim.core.session import Result
from cassim.core.settings import Settings
from cassim.device.engine import Engine, EngineError, RemoteSession, Reply, eval_op
from cassim.device.serialize import parse, replay_steps

if TYPE_CHECKING:
    from cassim.device.calculator import Calculator
    from cassim.device.document import Document


class Status(StrEnum):
    IDLE = "idle"
    BUSY = "busy"
    RESTARTING = "restarting"  # a Cancel is rebuilding the engine


class Runner:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.status = Status.IDLE
        self.sessions: list[RemoteSession] = []  # every one made, so a rebuild keeps them all
        self._task: asyncio.Future[Reply] | None = None

    def new_session(self, settings: Settings) -> RemoteSession:
        """The `Document` session factory."""
        session = RemoteSession(len(self.sessions), settings)
        self.sessions.append(session)
        return session

    def retain(self, document: Document) -> None:
        """Forget the sessions of Problems that were closed, so a rebuild replays only live ones."""
        live = {id(p.session) for p in document.problems}
        self.sessions = [s for s in self.sessions if id(s) in live]

    @property
    def idle(self) -> bool:
        return self.status is Status.IDLE

    # ---- running ----------------------------------------------------------------------------

    async def evaluate(self, calculator: Calculator) -> bool:
        """Send the Calculator's pending entry to the engine and finish it. False if cancelled."""
        pending = calculator.pending
        session = calculator.session
        if pending is None or not isinstance(session, RemoteSession):
            return True
        sent = [*session.take(), eval_op(pending.text, approximate=pending.approximate)]
        self.status = Status.BUSY
        self._task = asyncio.ensure_future(self.engine.run(session.id, sent))
        try:
            reply = await self._task
        except asyncio.CancelledError:
            calculator.pending = None  # the entry stays in the editor, as typed
            return False
        except EngineError as error:
            calculator.finish(Result(str(error), "", None, str(error)), pending.text, False)
            return True
        finally:
            self._task = None
            if self.status is Status.BUSY:
                self.status = Status.IDLE
        session.accept(sent, reply)
        found = reply["result"]
        calculator.finish(
            Result(found["text"], found["latex"], None, found["error"], found.get("full", "")),
            pending.text,
            pending.approximate,
        )
        return True

    def dirty(self, document: Document) -> bool:
        """Whether a settings change has not reached the engine yet."""
        return any(
            isinstance(p.session, RemoteSession) and p.session.outbox for p in document.problems
        )

    async def sync(self, document: Document) -> None:
        """Send queued settings changes, so the variable list is redrawn in the new format."""
        for problem in document.problems:
            session = problem.session
            if isinstance(session, RemoteSession) and session.outbox:
                sent = session.take()
                session.accept(sent, await self.engine.run(session.id, sent))

    # ---- cancel -----------------------------------------------------------------------------

    async def cancel(self) -> bool:
        """Stop the run in progress. False when there is none or the engine cannot be stopped."""
        if self.status is not Status.BUSY or not self.engine.cancel():
            return False
        self.status = Status.RESTARTING
        if self._task is not None:
            self._task.cancel()
        try:
            await self.engine.reset({s.id: list(s.journal) for s in self.sessions})
        finally:
            self.status = Status.IDLE
        return True

    # ---- loading ----------------------------------------------------------------------------

    async def load(self, text: str) -> Document:
        """`loads` for a remote engine: replay the document's entries through it."""
        steps = replay_steps(parse(text), self.new_session)
        while True:
            try:
                calculator = next(steps)
            except StopIteration as done:
                return done.value
            if not await self.evaluate(calculator):
                msg = "loading was cancelled"
                raise asyncio.CancelledError(msg)
