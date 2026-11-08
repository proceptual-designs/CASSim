# Requirements traced here: FR-EVAL-006, NFR-REL-002
"""The engine split: a RemoteSession, the Runner and Cancel (decisions 0005, 0016)."""

import asyncio
from typing import Any

import pytest

from cassim.core.settings import Settings
from cassim.device.document import Document
from cassim.device.engine import EngineCore, LocalEngine, Op, RemoteSession
from cassim.device.keys import Binding
from cassim.device.runner import Runner, Status
from cassim.device.serialize import dumps, loads, to_dict


def make() -> tuple[Runner, Document]:
    runner = Runner(LocalEngine())
    return runner, Document(sessions=runner.new_session)


async def enter(runner: Runner, document: Document, text: str) -> None:
    calculator = document.current.calculator
    assert calculator is not None
    for char in text:
        calculator.perform(Binding("insert", char))
    calculator.perform(Binding("enter"))
    assert calculator.pending is not None  # queued, not evaluated
    await runner.evaluate(calculator)


def last(document: Document) -> str:
    calculator = document.current.calculator
    assert calculator is not None
    return calculator.history[-1].result.text


def test_enter_is_deferred_until_the_runner_evaluates() -> None:
    runner, document = make()

    async def go() -> None:
        await enter(runner, document, "2+3")

    asyncio.run(go())
    assert last(document) == "5"
    calculator = document.current.calculator
    assert calculator is not None
    assert calculator.pending is None
    assert calculator.editor.linear() == ""


def test_keys_are_ignored_while_an_entry_is_pending() -> None:
    _, document = make()
    calculator = document.current.calculator
    assert calculator is not None
    for char in "1+1":
        calculator.perform(Binding("insert", char))
    calculator.perform(Binding("enter"))
    calculator.perform(Binding("insert", "9"))
    assert calculator.editor.linear() == "1+1"


def test_variables_and_functions_come_from_the_snapshot() -> None:
    runner, document = make()

    async def go() -> None:
        await enter(runner, document, "a:=5")
        await enter(runner, document, "f(x):=x*x+a")
        await enter(runner, document, "f(3)")

    asyncio.run(go())
    assert last(document) == "14"
    session = document.problems[0].session
    assert isinstance(session, RemoteSession)
    assert session.is_function("f")
    assert session.is_function("F")  # case insensitive by default
    assert session.is_function("solve")  # built in
    assert not session.is_function("a")
    assert [(v.name, v.is_function) for v in session.variables()] == [("a", False), ("f", True)]


def test_an_error_becomes_a_dialog_and_changes_nothing() -> None:
    runner, document = make()

    async def go() -> None:
        await enter(runner, document, "solve(")

    asyncio.run(go())
    calculator = document.current.calculator
    assert calculator is not None
    assert calculator.error is not None
    assert not calculator.history


def test_settings_changes_reach_the_engine_on_sync() -> None:
    runner, document = make()

    async def go() -> None:
        await enter(runner, document, "x:=1/3")
        document.set(digits="float3")
        assert runner.dirty(document)
        await runner.sync(document)
        assert not runner.dirty(document)
        await enter(runner, document, "1/3.")

    asyncio.run(go())
    session = document.problems[0].session
    assert [v.text for v in session.variables()] == ["1/3"]
    assert last(document) == "0.333"


def test_each_problem_has_its_own_variables() -> None:
    runner, document = make()

    async def go() -> None:
        await enter(runner, document, "a:=1")
        document.add_problem()
        await enter(runner, document, "a")

    asyncio.run(go())
    assert last(document) == "a"  # undefined variables echo unchanged


class StuckEngine:
    """An engine whose `run` never finishes until cancelled, wrapping a real core."""

    def __init__(self) -> None:
        self.core = EngineCore()
        self.stuck = False
        self.resets: list[dict[int, list[Op]]] = []

    async def run(self, problem: int, ops: list[Op]) -> dict[str, Any]:
        if self.stuck:
            await asyncio.Event().wait()
        return self.core.apply(problem, ops)

    async def reset(self, journals: dict[int, list[Op]]) -> None:
        self.resets.append(journals)
        self.core.reset(journals)

    def cancel(self) -> bool:
        return True


def test_cancel_stops_the_run_and_keeps_every_problem() -> None:
    engine = StuckEngine()
    runner = Runner(engine)
    document = Document(sessions=runner.new_session)

    async def go() -> None:
        await enter(runner, document, "a:=5")
        await enter(runner, document, "f(x):=x*x+a")
        document.add_problem()
        await enter(runner, document, "b:=7")
        engine.stuck = True
        calculator = document.current.calculator
        assert calculator is not None
        for char in "expand(x*y+1)":
            calculator.perform(Binding("insert", char))
        calculator.perform(Binding("enter"))
        run = asyncio.ensure_future(runner.evaluate(calculator))
        await asyncio.sleep(0)
        assert runner.status is Status.BUSY
        assert await runner.cancel()
        assert await run is False
        assert runner.status is Status.IDLE
        assert calculator.pending is None
        assert calculator.editor.linear() == "expand(x*y+1)"  # still there to edit
        assert not calculator.error
        calculator.editor.clear()
        engine.stuck = False
        # Both Problems were rebuilt from their journals.
        document.go(0, 0)
        await enter(runner, document, "f(3)")
        assert last(document) == "14"
        document.go(1, 0)
        await enter(runner, document, "b+1")
        assert last(document) == "8"

    asyncio.run(go())
    assert len(engine.resets) == 1


def test_cancel_with_nothing_running_does_nothing() -> None:
    runner, _ = make()
    assert not asyncio.run(runner.cancel())


def test_local_engine_cannot_be_cancelled() -> None:
    assert LocalEngine().cancel() is False


def test_load_replays_through_the_engine_like_the_synchronous_loader() -> None:
    runner, document = make()

    async def go() -> str:
        await enter(runner, document, "a:=5")
        document.add_page()
        await enter(runner, document, "a+1")
        document.add_problem()
        await enter(runner, document, "2*512")
        return dumps(document)

    text = asyncio.run(go())
    fresh = Runner(LocalEngine())
    loaded = asyncio.run(fresh.load(text))
    assert to_dict(loaded) == to_dict(loads(text))
    results = [
        [e.result.text for e in calculator.history]
        for problem in loaded.problems
        for page in problem.pages
        if (calculator := page.calculator) is not None
    ]
    assert results == [["5"], ["6"], ["1024"]]


def test_remote_session_refuses_synchronous_eval() -> None:
    with pytest.raises(NotImplementedError):
        RemoteSession(0, Settings()).eval("1")
