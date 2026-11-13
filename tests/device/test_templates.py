"""The 2D templates added for the templates key (FR-CALC-005, decision 0023): slots in the
device's Tab order, the text the engine reads, grid movement, and keeping them in a file."""

import pytest

from cassim.app.state import AppState, Mode
from cassim.device.calculator import Calculator, calculator_of
from cassim.device.editor import Editor, Kind, Template
from cassim.devices.nspire.document import loads
from cassim.doc.serialize import dumps


def _calculator(state: AppState) -> Calculator:
    calculator = calculator_of(state.document.current)
    assert calculator is not None
    return calculator


def _fill(kind: Kind, *slots: str, shape: tuple[int, int] = (2, 2)) -> Editor:
    """A template filled slot by slot with Tab, as a student types it."""
    editor = Editor()
    editor.insert_template(kind, shape)
    for number, text in enumerate(slots):
        if number:
            editor.tab()
        editor.insert_linear(text)
    return editor


@pytest.mark.parametrize(
    ("kind", "slots", "linear", "result"),
    [
        (Kind.NTH_ROOT, ("3", "-8"), "root(-8,3)", "-2"),
        (Kind.LOG, ("2", "8"), "log(8,2)", "3"),
        (Kind.ABS, ("-5",), "abs(-5)", "5"),
        (Kind.DERIVATIVE, ("x", "x^3"), "derivative(x^(3),x)", "3*x^2"),
        (Kind.DERIVATIVE2, ("x", "x^3"), "derivative(x^(3),x,2)", "6*x"),
        (Kind.INTEGRAL, ("0", "1", "x^2", "x"), "∫(x^(2),x,0,1)", "1/3"),
        (Kind.ANTIDERIVATIVE, ("x^2", "x"), "∫(x^(2),x)", "x^3/3"),
        (Kind.SUM, ("k", "1", "10", "k^2"), "Σ(k^(2),k,1,10)", "385"),
        (Kind.PRODUCT, ("k", "1", "5", "k"), "Π(k,k,1,5)", "120"),
        (Kind.LIMIT, ("x", "0", "", "sin(x)/x"), "limit(sin(x)/x,x,0)", "1"),
        (Kind.LIMIT, ("x", "0", "+", "abs(x)/x"), "limit(abs(x)/x,x,0,1)", "1"),  # direction
        (Kind.LIMIT, ("x", "0", "-", "abs(x)/x"), "limit(abs(x)/x,x,0,-1)", "-1"),
        (Kind.DERIVATIVE_N, ("3", "x", "x^5"), "derivative(x^(5),x,3)", "60*x^2"),
        (Kind.DMS, ("30", "15", "0"), "(30°15'0\")", "121*π/720"),  # Radian mode, as on the device
    ],
)
def test_each_template_reads_and_evaluates(
    kind: Kind, slots: tuple[str, ...], linear: str, result: str
) -> None:
    """Slots are filled in Tab order (the device's: shortcuts results S2 for d/dx and ∫)."""
    editor = _fill(kind, *slots)
    assert editor.linear() == linear
    state = AppState()
    calculator = _calculator(state)
    calculator.editor = editor
    state.run_action("enter")
    assert calculator.history[-1].result.text == result


def test_piecewise_and_system_are_grids() -> None:
    piecewise = _fill(Kind.PIECEWISE, "x^2", "x<0", "x", "x>=0", shape=(2, 2))
    assert piecewise.linear() == "piecewise(x^(2),x<0,x,x>=0)"
    system = _fill(Kind.SYSTEM, "x+y=3", "x-y=1", shape=(2, 1))
    assert system.linear() == "{x+y=3,x-y=1}"
    state = AppState()
    calculator = _calculator(state)
    calculator.editor.insert_text("solve(")
    calculator.editor.paste(system.root)
    calculator.editor.insert_text(",{x,y})")
    state.run_action("enter")
    assert calculator.history[-1].result.text == "x=2 and y=1"


def test_up_and_down_move_between_the_rows_of_a_grid() -> None:
    editor = Editor()
    editor.insert_template(Kind.PIECEWISE, (3, 2))
    assert editor.path == [(0, 0)]
    editor.down()
    assert editor.path == [(0, 2)]  # the value of the second piece
    editor.tab()
    editor.up()
    assert editor.path == [(0, 1)]  # the first piece's condition
    editor.down()
    editor.down()
    editor.down()  # no row below the last: stays
    assert editor.path == [(0, 5)]


def test_backspace_in_a_grid_steps_back_a_cell() -> None:
    editor = _fill(Kind.SYSTEM, "a", "", shape=(2, 1))
    editor.backspace()  # at the start of the empty second equation
    assert editor.path == [(0, 0)]
    assert editor.pos == 1


def test_a_function_template_after_a_term_gets_a_times() -> None:
    """`x` then |□| would read as `xabs(` without the `*`."""
    editor = Editor()
    editor.insert_text("2x")
    editor.insert_template(Kind.ABS)
    editor.insert_text("y")
    assert editor.linear() == "2x*abs(y)"


def test_templates_survive_a_saved_file() -> None:
    state = AppState()
    calculator = _calculator(state)
    calculator.editor = _fill(Kind.PIECEWISE, "1", "x<0", "2", "x>=0", shape=(2, 2))
    state.run_action("enter")
    loaded = loads(dumps(state.document))
    page = calculator_of(loaded.current)
    assert page is not None
    node = page.history[-1].nodes[0]
    assert isinstance(node, Template)
    assert (node.kind, node.cols, len(node.slots)) == (Kind.PIECEWISE, 2, 4)


@pytest.mark.parametrize(
    ("keys", "kind"),
    [
        (("ctrl", "pow"), Kind.NTH_ROOT),
        (("ctrl", "10x"), Kind.LOG),
        (("shift", "minus"), Kind.DERIVATIVE),
        (("shift", "plus"), Kind.INTEGRAL),
    ],
)
def test_keypad_layers_give_the_templates(keys: tuple[str, ...], kind: Kind) -> None:
    state = AppState(mode=Mode.HANDHELD)
    for name in keys:
        state.press_keypad(name)
    node = _calculator(state).editor.root[0]
    assert isinstance(node, Template)
    assert node.kind is kind


def test_template_specs_with_one_number() -> None:
    state = AppState()
    state.run_action("template", "system:3")
    node = _calculator(state).editor.root[0]
    assert isinstance(node, Template)
    assert (node.kind, node.cols, len(node.slots)) == (Kind.SYSTEM, 1, 3)
