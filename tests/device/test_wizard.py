# Requirements traced here: FR-DEV-009
"""Dialogs that build commands (FR-CALC-005) and pasting linear text into the 2D editor."""

import pytest

from cassim.device.editor import Editor, Kind, Template
from cassim.device.wizard import CURSOR, Field, Wizard
from cassim.devices.nspire.menus import WIZARDS, polynomial
from cassim.devices.nspire.pages.calculator import Calculator, calculator_of
from cassim.devices.nspire.ui.state import AppState


def _calculator(state: AppState) -> Calculator:
    calculator = calculator_of(state.document.current)
    assert calculator is not None
    return calculator


def _finish(name: str, **values: str) -> AppState:
    state = AppState()
    wizard = WIZARDS[name]
    assert state.finish_wizard(wizard, {**wizard.defaults(), **values}) == []
    return state


def test_normal_cdf_pastes_and_runs() -> None:
    state = _finish("normCdf", lower="-1", upper="1")
    entry = _calculator(state).history[-1]
    assert entry.text == "normCdf(-1,1,0,1)"
    assert entry.result.text == "0.68268949"


def test_normal_cdf_starts_from_minus_infinity() -> None:
    """The device's Lower Bound default is the symbol −∞; Upper Bound starts blank."""
    state = _finish("normCdf", upper="1.96")
    entry = _calculator(state).history[-1]
    assert entry.text == "normCdf(-∞,1.96,0,1)"
    assert entry.result.text == "0.9750021"


def test_empty_trailing_arguments_are_dropped() -> None:
    state = _finish("binomPdf", n="3", p="0.5")
    assert _calculator(state).history[-1].text == "binomPdf(3,0.5)"


def test_derivative_at_a_point_leaves_the_cursor_in_the_expression() -> None:
    state = _finish("derivative_at", value="2", order="2")
    calculator = _calculator(state)
    assert calculator.editor.linear() == "derivative(,x,2)|x=2"
    calculator.editor.insert_text("x")
    calculator.editor.insert_linear("^3")
    state.run_action("enter")
    assert calculator.history[-1].result.text == "12"


def test_create_matrix_is_a_template_and_checks_its_size() -> None:
    state = AppState()
    wizard = WIZARDS["matrix"]
    assert state.finish_wizard(wizard, {"rows": "0", "cols": "2"})
    assert state.finish_wizard(wizard, {"rows": "3", "cols": "1"}) == []
    node = _calculator(state).editor.root[0]
    assert isinstance(node, Template)
    assert (node.kind, len(node.slots), node.cols) == (Kind.MATRIX, 3, 1)


def test_solve_system_has_a_slot_per_equation() -> None:
    state = _finish("solve_system", count="3", vars="x,y,z")
    calculator = _calculator(state)
    assert calculator.editor.linear() == "solve({,,},{x,y,z})"
    template = calculator.editor.root[len("solve(")]
    assert isinstance(template, Template)
    assert (template.kind, len(template.slots)) == (Kind.SYSTEM, 3)
    assert calculator.editor.path == [(len("solve("), 0)]  # the cursor in the first equation


def test_find_roots_of_polynomial_pastes_without_running() -> None:
    """As on the device: the command is pasted, the cursor at its end; Enter runs it."""
    state = _finish("poly_roots", coeffs="1,-3,2")
    calculator = _calculator(state)
    assert calculator.history == []
    state.run_action("enter")
    assert calculator.history[-1].result.text == "{1,2}"


@pytest.mark.parametrize(
    ("coeffs", "text"),
    [
        ("1,-3,2", "x^2-3*x+2"),
        ("2,0,0", "2*x^2"),
        ("-1,1", "-x+1"),
        ("a+1,0", "(a+1)*x"),
        ("0", "0"),
    ],
)
def test_polynomial_from_coefficients(coeffs: str, text: str) -> None:
    assert polynomial(coeffs, "x") == text


_LOAN = {"n": "10", "i": "5", "pv": "-100", "pmt": "0", "fv": "", "ppy": "1", "cpy": "1"}


def test_finance_solver_works_out_the_box_it_is_asked_for() -> None:
    """Live, as on the handheld: Enter in a box calculates that box from the others."""
    wizard = WIZARDS["finance"]
    assert wizard.calculate is not None
    values = wizard.calculate({**wizard.defaults(), **_LOAN}, "fv")
    assert values["fv"] == "162.889463"
    assert wizard.calculate({**values, "n": ""}, "n")["n"] == "10"
    rate = wizard.calculate({**values, "i": "99"}, "i")["i"]  # the box's own value is ignored
    assert float(rate) == pytest.approx(5, abs=1e-6)  # FV was rounded to 9 digits
    payment = wizard.calculate({**values, "pmtat": "1"}, "pmt")["pmt"]
    assert float(payment) == pytest.approx(0, abs=1e-6)


def test_finance_solver_reports_what_is_missing() -> None:
    wizard = WIZARDS["finance"]
    assert wizard.calculate is not None
    with pytest.raises(ValueError, match="PV: enter a number"):
        wizard.calculate({**_LOAN, "pv": "lots"}, "fv")
    with pytest.raises(ValueError, match="Choose"):
        wizard.calculate(_LOAN, "ppy")
    assert wizard.calculate({**_LOAN, "pv": "-1/2", "i": "5ᴇ0"}, "fv")["fv"] == "0.814447313"


def test_closing_the_finance_solver_pastes_nothing() -> None:
    """As on the device; its boxes start at 0, PpY and CpY at 1."""
    wizard = WIZARDS["finance"]
    assert wizard.calculate is not None
    assert wizard.defaults() == {
        "n": "0",
        "i": "0",
        "pv": "0",
        "pmt": "0",
        "fv": "0",
        "ppy": "1",
        "cpy": "1",
        "pmtat": "0",
    }
    state = AppState()
    solved = wizard.calculate({**wizard.defaults(), **_LOAN}, "fv")
    assert state.finish_wizard(wizard, solved) == []
    assert _calculator(state).history == []
    assert _calculator(state).editor.linear() == ""


def test_stat_dialogs_show_the_results() -> None:
    state = _finish("one_var", x="{1,2,3,4}")
    assert "One-Variable Statistics" in _calculator(state).history[-1].result.text
    state = _finish("linregmx", x="{1,2,3}", y="{2,4,6}")
    assert "Linear Regression" in _calculator(state).history[-1].result.text


def test_every_dialog_builds_with_its_defaults_filled() -> None:
    for name, wizard in WIZARDS.items():
        values = {field.name: field.default or "1" for field in wizard.fields}
        assert wizard.problems(values) == [], name
        if wizard.calculate is not None:
            assert wizard.calculate(values, "fv")["fv"], name  # live: nothing to paste
        else:
            assert wizard.bindings(values), name


def test_field_checks() -> None:
    choice = Field("c", "Pick", "a", choices=(("a", "A"), ("b", "B")))
    whole = Field("n", "Rows", whole=(1, 99))
    assert choice.problem("a") is None
    assert choice.problem("z")
    assert whole.problem("5") is None
    assert whole.problem("100")
    assert whole.problem("x")
    wizard = Wizard("t", (whole,), "f({n}" + CURSOR + ")")
    assert [b.action for b in wizard.bindings({"n": "2"})] == ["insert_linear"]


def test_a_dialog_opens_through_the_gui_hook() -> None:
    state = AppState()
    shown: list[Wizard] = []
    state.show_wizard = shown.append
    for key in ("F2", "5", "5", "2"):  # Probability > Distributions > Normal Cdf
        state.key_event(key)
    assert shown == [WIZARDS["normCdf"]]


# ---- insert_linear ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    ["x^2+1", "x^(n+1)-2", "2^-3*a", "√(x+1)+2", "ⅇ^(2*x)", "(x+1)^2/3", "a^b^c"],
)
def test_linear_paste_round_trips(text: str) -> None:
    editor = Editor()
    editor.insert_linear(text)
    assert editor.linear().replace("(", "").replace(")", "") == text.replace("(", "").replace(
        ")", ""
    )
    assert editor.path == []


def test_linear_paste_exponent_takes_only_its_operand() -> None:
    editor = Editor()
    editor.insert_linear("x^2+1")
    assert editor.root[0] == "x"
    power = editor.root[1]
    assert isinstance(power, Template)
    assert power.slots == [["2"]]
    assert editor.root[2:] == ["+", "1"]


def test_linear_paste_leaves_the_cursor_at_the_mark() -> None:
    editor = Editor()
    editor.insert_linear("f(" + CURSOR + ",x)", CURSOR)
    editor.insert_text("y")
    assert editor.linear() == "f(y,x)"


def test_paste_from_outside_keeps_exponents_in_place() -> None:
    state = AppState()
    state.paste_text("x^2+1")
    calculator = _calculator(state)
    state.run_action("enter")
    assert calculator.history[-1].result.text == "x^2+1"  # not x^(2+1)


def test_solve_system_of_linear_equations_pastes_lin_solve() -> None:
    state = _finish("solve_linear_system")
    calculator = _calculator(state)
    assert calculator.editor.linear() == "linSolve({,},{x,y})"
    calculator.editor.insert_text("x+y=3")
    calculator.editor.tab()
    calculator.editor.insert_text("x-y=1")
    state.run_action("enter")
    assert calculator.history[-1].result.text == "{2,1}"


def test_differential_equation_solver_joins_the_conditions() -> None:
    state = _finish("desolve", c1="y(0)=1")
    entry = _calculator(state).history[-1]
    assert entry.text == "deSolve(y'=2*y and y(0)=1,x,y)"
    assert entry.result.text == "y=ⅇ^(2*x)"


def test_inverse_binomial_n_dialog() -> None:
    wizard = WIZARDS["invBinomN"]
    assert wizard.title == "Num Trials"
    state = _finish("invBinomN", c="0.5", p="0.5", x="5")
    assert _calculator(state).history[-1].result.text == "12"


def test_finance_solver_ppy_sets_cpy() -> None:
    assert WIZARDS["finance"].copies == (("ppy", "cpy"),)


def test_finance_solver_stores_the_tvm_variables() -> None:
    """The device leaves `tvm.n`, `tvm.i`, ... behind after a calculation (E6)."""
    state = AppState()
    wizard = WIZARDS["finance"]
    known = {"n": "12", "i": "6", "pv": "10000", "fv": "0", "ppy": "12", "cpy": "12"}
    values = {**wizard.defaults(), **known}
    assert wizard.calculate is not None
    found = wizard.calculate(values, "pmt")
    state.store_wizard(wizard, found)
    session = _calculator(state).session
    assert session.eval("tvm.n").text == "12"
    assert session.eval("tvm.pmtat").text == "0"
    assert session.eval("tvm.pv").text == "10000"
    assert abs(float(session.eval("tvm.pmt").text) + 860.664297) < 1e-5
