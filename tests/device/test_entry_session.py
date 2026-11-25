"""FR-CALC-004: the shared entry-line session (editing, undo groups, clipboard, page rules)."""

from cassim.device.clipboard import Clipboard
from cassim.device.editor import Editor, Kind, Template
from cassim.device.entry_session import EntryRules, EntrySession
from cassim.device.keys import Action, Binding


def run[Extra](session: EntrySession[Extra], *keys: tuple[Action, str]) -> None:
    for action, arg in keys:
        assert session.perform(Binding(action, arg)), action


def test_an_operator_first_gets_ans_only_with_the_rule() -> None:
    plain, calculator = EntrySession(), EntrySession(rules=EntryRules(ans_prefix=True))
    for session in (plain, calculator):
        run(session, ("insert", "-"), ("insert", "x"))
    assert plain.editor.linear() == "-x"
    assert calculator.editor.linear() == "Ans-x"


def test_an_editor_put_in_takes_the_session_rule() -> None:
    session = EntrySession(rules=EntryRules(ans_prefix=True))
    session.editor = Editor()
    run(session, ("insert", "*2"))
    assert session.editor.linear() == "Ans*2"


def test_undo_takes_a_run_of_operands_back_in_one_step() -> None:
    session = EntrySession()
    run(session, ("insert", "1"), ("insert", "2"), ("insert", "+"), ("insert", "x"))
    assert session.editor.linear() == "12+x"
    run(session, ("undo", ""))
    assert session.editor.linear() == "12+"
    run(session, ("undo", ""))
    assert session.editor.linear() == "12"
    run(session, ("undo", ""))
    assert session.editor.linear() == ""
    assert not session.can_undo
    run(session, ("redo", ""), ("redo", ""))
    assert session.editor.linear() == "12+"


def test_templates_power_and_paste_share_the_clipboard() -> None:
    clipboard = Clipboard()
    first, second = EntrySession(clipboard), EntrySession(clipboard)
    run(first, ("template", "fraction"), ("insert", "1"), ("select_all", ""), ("copy", ""))
    run(second, ("paste", ""))
    assert isinstance(second.editor.root[0], Template)
    assert second.editor.root[0].kind is Kind.FRACTION
    run(second, ("template", "matrix:2,3"))
    assert second.editor.path == [(1, 0)]
    run(second, ("end", ""), ("insert", "x"), ("power", "2"))
    assert second.editor.linear().endswith("x^(2)")


def test_the_owner_keeps_its_own_state_in_each_undo_step() -> None:
    history: list[str] = []
    touched: list[bool] = []
    session: EntrySession[tuple[str, ...]] = EntrySession(
        keep=lambda: tuple(history),
        restore=lambda saved: history.__setitem__(slice(None), saved),
        on_key=lambda: touched.append(True),
    )
    session.remember()
    history.append("1+1")
    run(session, ("insert", "2"))
    assert touched
    run(session, ("undo", ""), ("undo", ""))
    assert history == []
    run(session, ("redo", ""))
    assert history == ["1+1"]


def test_the_sheet_paste_rule_and_no_undo() -> None:
    clipboard = Clipboard()
    clipboard.copy_cells(object(), "1\t2")
    cell = EntrySession(clipboard, EntryRules(cells_paste=True, undo=False))
    entry = EntrySession(clipboard)
    run(cell, ("paste", ""))
    run(entry, ("paste", ""))
    assert cell.editor.linear() == "1\t2"
    assert entry.editor.linear() == ""
    assert not cell.can_undo


def test_an_unknown_action_is_not_taken() -> None:
    session = EntrySession()
    assert not session.perform(Binding("enter"))
    assert not session.handles("enter")
    assert session.handles("drop")
