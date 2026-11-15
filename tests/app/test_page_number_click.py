# Requirements traced here: FR-DOC-001
"""The problem.page number opens the page sorter."""

from collections.abc import Callable

import flet as ft
import pytest
from tests.app.test_status_click import walk

from cassim.device.keys import Action
from cassim.devices.nspire.ui.state import AppState, Mode
from cassim.devices.nspire.ui.views import CalculatorView


@pytest.mark.parametrize("mode", [Mode.COMPUTER, Mode.HANDHELD])
@pytest.mark.parametrize("kind", ["calculator", "spreadsheet", "graphs"])
def test_page_number_opens_and_closes_sorter(mode: Mode, kind: str) -> None:
    state = AppState(mode=mode)
    state.run_action("add_problem", kind)

    def act(action: Action, arg: str) -> None:
        state.run_action(action, arg)
        view.refresh()

    view = CalculatorView(state, on_action=act)
    view.refresh()
    assert view.title.value == "2.1"
    buttons = [
        control
        for control in walk(view.control)
        if isinstance(control, ft.Container) and control.content is view.title
    ]
    assert len(buttons) == 1
    handler: Callable[[object], object] | None = buttons[0].on_click  # ty: ignore[invalid-assignment]
    assert handler is not None
    handler(None)
    assert state.sorting
    assert state.screen().sorter is not None
    assert (state.document.problem, state.document.page) == (1, 0)
    handler(None)
    assert not state.sorting
    assert (state.document.problem, state.document.page) == (1, 0)
