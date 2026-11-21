# Requirements traced here: FR-CALC-004, FR-CALC-005
"""The mouse on the Calculator page, from emulator check 6, run 5 (H3)."""

from collections.abc import Callable, Iterator
from typing import cast

import flet as ft
import pytest

from cassim.app.theme import DARK
from cassim.device.editor import Editor
from cassim.devices.nspire.pages.calculator import calculator_on
from cassim.devices.nspire.ui import views as views_module
from cassim.devices.nspire.ui.entry import EntryLine
from cassim.devices.nspire.ui.state import AppState
from cassim.devices.nspire.ui.views import CalculatorView


def walk(control: ft.Control) -> Iterator[ft.Control]:
    yield control
    content = getattr(control, "content", None)
    if isinstance(content, ft.Control):
        yield from walk(content)
    for child in getattr(control, "controls", None) or []:
        yield from walk(child)


def _recorded() -> tuple[CalculatorView, list[tuple[str, str]], AppState]:
    state = AppState()
    actions: list[tuple[str, str]] = []
    view = CalculatorView(state, on_action=lambda action, arg: actions.append((action, arg)))
    return view, actions, state


def test_one_two_and_three_clicks_place_select_a_token_and_select_all() -> None:
    """H3 b: a double-click selects a token, a triple-click the whole line."""
    view, actions, _ = _recorded()
    for _ in range(3):
        view._click([], 2)
    assert actions == [("place", ":2"), ("select_token", ":2"), ("select_all", "")]


def test_clicks_far_apart_in_time_or_place_are_single(monkeypatch: pytest.MonkeyPatch) -> None:
    view, actions, _ = _recorded()
    view._click([], 1)
    view._click([], 2)  # somewhere else
    monkeypatch.setattr(views_module, "MULTI_CLICK", -1.0)
    view._click([], 2)  # too late
    assert [action for action, _ in actions] == ["place", "place", "place"]


def test_a_history_line_click_then_clicks_inside_it_count_on() -> None:
    """The first click picks the line (a cursor in it); the clicks after land in its editor."""
    view, actions, _ = _recorded()
    view._click_line("0:entry")
    view._recall_click([], 1)
    view._recall_click([], 1)
    assert actions == [
        ("recall_at", "0:entry"),
        ("recall_token", ":1"),
        ("select_all", ""),
    ]


def test_shift_click_in_a_history_line_extends() -> None:
    state = AppState()
    actions: list[tuple[str, str]] = []
    view = CalculatorView(
        state, on_action=lambda action, arg: actions.append((action, arg)), shift=lambda: True
    )
    view._recall_click([], 2)
    assert actions == [("recall_extend", ":2")]


def test_a_clicked_history_line_is_drawn_as_an_editor() -> None:
    """H3 a: no highlight over the item; a cursor in it, which clicks can move."""
    state = AppState()
    for char in "2+3":
        state.key_event(char)
    state.key_event("Enter")
    view = CalculatorView(state, on_action=state.run_action)
    view.refresh()
    plain = [c for c in walk(view.history) if isinstance(c, ft.Markdown)]
    state.run_action("recall_at", "0:entry")
    view.refresh()
    calculator = calculator_on(state.document.current)
    assert calculator.recall == (0, "entry")
    editors = [c for c in walk(view.history) if isinstance(c, ft.GestureDetector) and c.on_tap]
    assert len([c for c in walk(view.history) if isinstance(c, ft.Markdown)]) < len(plain)
    assert editors
    highlighted = [
        c for c in walk(view.history) if isinstance(c, ft.Container) and c.bgcolor == DARK.selection
    ]
    assert not highlighted


def test_a_selection_drags_and_places_accept_drops() -> None:
    """H3 k: selected parts are draggable; every place in the line takes a drop."""
    editor = Editor("1234")
    editor.place([], 1)
    editor.place([], 3, extend=True)
    dropped: list[tuple[tuple[tuple[int, int], ...], int]] = []
    line = EntryLine(DARK, 20, lambda path, pos: None)
    line.drop = lambda path, pos: dropped.append((tuple(path), pos))
    built = line.build(editor)
    draggables = [c for c in walk(built) if isinstance(c, ft.Draggable)]
    targets = [c for c in walk(built) if isinstance(c, ft.DragTarget)]
    assert len(draggables) == 2
    assert targets
    for target in targets:
        handler = cast("Callable[[object], object]", target.on_accept)
        handler(None)
    assert ((), 4) in dropped
    plain = EntryLine(DARK, 20, lambda path, pos: None).build(editor)
    assert not [c for c in walk(plain) if isinstance(c, (ft.Draggable, ft.DragTarget))]
