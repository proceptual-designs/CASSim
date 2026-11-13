# Requirements traced here: FR-DOC-008
"""Typed engine ops, variable revisions and delta replies (decision 0031, PLAN.md 12 A1)."""

import asyncio

import pytest

from cassim.core.session import Session
from cassim.core.settings import Settings
from cassim.device.engine import (
    EngineCore,
    EngineError,
    LocalEngine,
    Op,
    RemoteSession,
    Row,
    VariableStore,
    check_op,
    check_reply,
    eval_op,
    settings_op,
)
from cassim.devices.nspire.runner import Runner


def names(reply) -> list[str]:
    return [row["name"] for row in reply["changed"]]


def test_a_reply_holds_only_what_changed() -> None:
    core = EngineCore()
    first = core.apply(0, [eval_op("a:=1", approximate=False)])
    assert first["full"]
    assert names(first) == ["a"]
    second = core.apply(0, [eval_op("b:=2", approximate=False)])
    assert not second["full"]
    assert names(second) == ["b"]  # `a` is not formatted again
    third = core.apply(0, [eval_op("1+1", approximate=False)])
    assert names(third) == []
    assert third["result"] is not None
    assert third["result"]["text"] == "2"


def test_a_delete_is_reported() -> None:
    core = EngineCore()
    core.apply(0, [eval_op("a:=1", approximate=False), eval_op("b:=2", approximate=False)])
    reply = core.apply(0, [eval_op("DelVar a", approximate=False)])
    assert reply["deleted"] == ["a"]
    assert names(reply) == []


def test_a_settings_change_sends_every_variable_again() -> None:
    """The display text of every value may change with the settings (Float 3)."""
    core = EngineCore()
    core.apply(0, [eval_op("a:=1/3.", approximate=False), eval_op("b:=1", approximate=False)])
    reply = core.apply(0, [settings_op(Settings(digits="float3"))])
    assert reply["full"]
    assert names(reply) == ["a", "b"]
    assert reply["changed"][0]["text"] == "0.333"


def test_after_a_reset_the_next_reply_is_full() -> None:
    core = EngineCore()
    ops = [eval_op("a:=1", approximate=False)]
    core.apply(0, ops)
    core.reset({0: list(ops)})
    reply = core.apply(0, [eval_op("2", approximate=False)])
    assert reply["full"]
    assert names(reply) == ["a"]


def test_ops_are_checked_where_they_enter_the_engine() -> None:
    assert check_op({"op": "eval", "line": "1", "approximate": False})["op"] == "eval"
    for bad in (
        "eval",
        {"op": "fly"},
        {"op": "eval", "line": 1, "approximate": False},
        {"op": "eval", "line": "1"},
        {"op": "store", "numbers": {"n": "12"}},
        {"op": "store", "numbers": {"n": True}},
        {"op": "settings", "values": [1]},
        {"op": "ans", "line": 3},
    ):
        with pytest.raises(EngineError):
            check_op(bad)
    assert check_op({"op": "store", "numbers": {"n": 12}}) == {
        "op": "store",
        "numbers": {"n": 12.0},
    }
    assert check_op({"op": "ans", "line": None}) == {"op": "ans", "line": None}
    assert check_op({"op": "new_problem"}) == {"op": "new_problem"}


def test_a_bad_op_runs_nothing() -> None:
    core = EngineCore()
    with pytest.raises(EngineError):
        core.apply(0, [eval_op("a:=1", approximate=False), {"op": "fly"}])
    assert names(core.apply(0, [])) == []


def test_scope_revisions_rise_on_every_store_and_delete() -> None:
    session = Session()
    session.eval("a:=1")
    first = session.revision_of("a")
    session.eval("b:=1")
    assert session.revision_of("a") == first
    session.eval("a:=2")
    assert session.revision_of("a") > first
    assert session.revision_of("A") == session.revision_of("a")  # case insensitive
    assert session.revision_of("z") == 0
    session.eval("DelVar b")
    assert session.scope.changed_since(first) == {"a", "b"}
    before = session.scope.revision
    session.eval("ClearAZ")
    assert session.scope.changed_since(before) == {"a"}
    session.eval("q:=1")
    session.new_problem()
    assert "q" in session.scope.changed_since(before)


def test_the_store_keeps_its_own_revisions_and_skips_unchanged_rows() -> None:
    store = VariableStore()
    row: Row = {"name": "a", "text": "1", "latex": "1", "is_function": False}
    store.apply({"result": None, "full": True, "changed": [row], "deleted": []})
    first = store.revision_of("a")
    store.apply({"result": None, "full": True, "changed": [row], "deleted": []})
    assert store.revision_of("a") == first  # the same row: nothing to redraw
    store.apply({"result": None, "full": True, "changed": [], "deleted": []})
    assert store.get("a") is None
    assert store.revision_of("a") > first


def test_a_remote_session_answers_from_its_store_after_a_cancel() -> None:
    """After Cancel the engine is rebuilt; the store's revisions keep rising, never fall back."""
    runner = Runner(LocalEngine())
    session = runner.new_session(Settings())
    assert isinstance(session, RemoteSession)

    async def go() -> None:
        sent: list[Op] = [eval_op("a:=1", approximate=False)]
        session.accept(sent, await runner.engine.run(session.id, sent))

    asyncio.run(go())
    seen = session.revision_of("a")
    assert seen > 0
    asyncio.run(runner.engine.reset({session.id: list(session.journal)}))

    async def again() -> None:
        sent: list[Op] = [eval_op("a:=2", approximate=False)]
        session.accept(sent, await runner.engine.run(session.id, sent))

    asyncio.run(again())
    assert session.revision_of("a") > seen
    assert [row.text for row in session.variables()] == ["2"]


def test_a_reply_from_the_worker_is_checked() -> None:
    """What comes back over `postMessage` is only JSON (PLAN.md 12 A1)."""
    good = EngineCore().apply(0, [eval_op("a:=1", approximate=False)])
    assert check_reply(dict(good)) == good
    for bad in (
        None,
        {"full": True, "changed": [], "deleted": []},
        {"result": None, "full": "yes", "changed": [], "deleted": []},
        {"result": None, "full": True, "changed": [{"name": "a"}], "deleted": []},
        {"result": {"text": "1"}, "full": True, "changed": [], "deleted": []},
        {"result": None, "full": True, "changed": [], "deleted": [3]},
    ):
        with pytest.raises(EngineError):
            check_reply(bad)
