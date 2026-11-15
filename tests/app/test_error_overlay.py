"""Calculator error display (FR-EVAL-005): straight quotes and click-to-dismiss."""

from collections.abc import Callable, Iterator

import flet as ft

from cassim.app.theme import DARK
from cassim.device.keys import Action, Binding
from cassim.devices.nspire.ui.state import AppState
from cassim.devices.nspire.ui.views import CalculatorView


def walk(control: ft.Control) -> Iterator[ft.Control]:
    yield control
    content = getattr(control, "content", None)
    if isinstance(content, ft.Control):
        yield from walk(content)
    for child in getattr(control, "controls", None) or []:
        yield from walk(child)


def test_error_history_uses_ascii_quotes() -> None:
    state = AppState()
    state.run(Binding("insert", "solve("))
    state.run(Binding("enter"))
    view = CalculatorView(state)
    view.refresh()

    expected = f'"{state.screen().error}"'
    error_text = [
        control
        for control in walk(view.history)
        if isinstance(control, ft.Text) and control.value == expected
    ]
    assert error_text
    assert error_text[0].font_family == "serif"


def test_clicking_the_red_error_message_dismisses_it() -> None:
    state = AppState()
    state.run(Binding("insert", "solve("))
    state.run(Binding("enter"))
    view: CalculatorView

    def act(action: Action, arg: str) -> None:
        state.run_action(action, arg)
        view.refresh()

    view = CalculatorView(state, DARK, on_action=act)
    view.refresh()
    assert state.screen().error is not None
    error_card = next(
        control
        for control in walk(view.error)
        if isinstance(control, ft.Container) and control.bgcolor == DARK.error
    )
    assert error_card.on_click is not None
    card_text = [
        control.value or "" for control in walk(error_card) if isinstance(control, ft.Text)
    ]
    assert any("click" in text for text in card_text)

    handler: Callable[[object], object] = error_card.on_click  # ty: ignore[invalid-assignment]
    handler(None)

    assert state.screen().error is None
    assert not view.error.visible
