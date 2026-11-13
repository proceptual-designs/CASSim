# Requirements traced here: FR-CALC-007
"""The warning triangle: Real mode keeps a real answer from a non-real step, with a warning
(decision 0026, docs/testing/emulator-domain-results.md)."""

import asyncio

import flet as ft
import pytest

from cassim.app.warning import COLOUR, warning_dialog, warning_mark
from cassim.core.errors import NON_REAL_CALCULATION
from cassim.core.session import Session
from cassim.device.engine import LocalEngine
from cassim.device.keys import Binding
from cassim.devices.nspire.document import Document
from cassim.devices.nspire.pages.calculator import calculator_on
from cassim.devices.nspire.runner import Runner
from cassim.devices.nspire.screen import render
from cassim.devices.nspire.ui.state import AppState
from cassim.devices.nspire.ui.views import CalculatorView
from cassim.doc.document import Document as BaseDocument


@pytest.mark.parametrize(
    "entry", ["√(-1)*√(-1)", "(√(-1))^2", "real(3+4*√(-1))", "imag(3+4*√(-1))"]
)
def test_real_mode_warns_on_a_non_real_step(entry: str) -> None:
    result = Session().eval(entry)
    assert result.error is None
    assert result.warnings == (NON_REAL_CALCULATION,)


@pytest.mark.parametrize("domain", ["rectangular", "polar"])
def test_complex_modes_do_not_warn(domain: str) -> None:
    session = Session()
    session.set(domain=domain)
    assert session.eval("√(-1)*√(-1)").warnings == ()


def test_an_ordinary_entry_and_an_error_do_not_warn() -> None:
    session = Session()
    assert session.eval("2+2").warnings == ()
    failed = session.eval("√(-1)")
    assert failed.error == "Non-real result"
    assert failed.warnings == ()


def type_entry(document: BaseDocument, text: str) -> None:
    calculator = calculator_on(document.current)
    for char in text:
        calculator.perform(Binding("insert", char))
    calculator.perform(Binding("enter"))


def test_the_warning_reaches_the_history_through_the_worker() -> None:
    runner = Runner(LocalEngine())
    document = Document(sessions=runner.new_session)
    type_entry(document, "sqrt(-1)*sqrt(-1)")
    asyncio.run(runner.evaluate(calculator_on(document.current)))
    lines = render(document).lines
    assert [line.warnings for line in lines] == [(NON_REAL_CALCULATION,), ()]  # entry row only


def test_the_history_draws_a_triangle_beside_the_entry() -> None:
    state = AppState()
    type_entry(state.document, "sqrt(-1)*sqrt(-1)")
    type_entry(state.document, "1+1")
    view = CalculatorView(state)
    view.refresh()
    marks = [
        control
        for control in walk(view.history)
        if isinstance(control, ft.Icon) and control.color == COLOUR
    ]
    assert len(marks) == 1
    assert marks[0].tooltip == NON_REAL_CALCULATION


def walk(control: object) -> list[object]:
    found = [control]
    for name in ("controls", "content"):
        child = getattr(control, name, None)
        for item in child if isinstance(child, list) else [child] if child is not None else []:
            found += walk(item)
    return found


def test_the_dialog_is_titled_warning_with_the_message_and_ok() -> None:
    dialog = warning_dialog([NON_REAL_CALCULATION])
    assert isinstance(dialog.title, ft.Text)
    assert dialog.title.value == "Warning"
    assert isinstance(dialog.content, ft.Text)
    assert dialog.content.value == NON_REAL_CALCULATION
    assert [getattr(action, "content", None) for action in dialog.actions or []] == ["OK"]
    assert isinstance(warning_mark([]), ft.Container)
