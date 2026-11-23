# Requirements traced here: FR-CALC-004
"""Results are drawn from their text through the editor tree (decision 0035, stage 3)."""

import pytest

from cassim.core.results import Result
from cassim.core.session import Session
from cassim.device.editor import Editor, Kind, Template
from cassim.device.editor_ast import result_latex, row_from_text
from cassim.device.keys import Binding
from cassim.devices.nspire.document import Document
from cassim.devices.nspire.pages.calculator import Calculator, calculator_on
from cassim.devices.nspire.screen import render


@pytest.mark.parametrize(
    ("text", "latex"),
    [
        # products keep their dot, as the device shows them (TESTING.md: 2·√2, (a-2)·(a+1))
        ("2*√(2)", r"2\cdot \sqrt{2}"),
        ("(x-2)*(x+1)", r"(x-2)\cdot (x+1)"),
        # word operators and values are upright regular (emulator calc2 results)
        ("x=-2 or x=2", r"x=-2\ \mathrm{o}\mathrm{r}\ x=2"),
        ("true", r"\mathrm{t}\mathrm{r}\mathrm{u}\mathrm{e}"),
        ("undef", r"\mathrm{u}\mathrm{n}\mathrm{d}\mathrm{e}\mathrm{f}"),
        # a negative fraction has its minus in front: −½, not (−1)/2
        (
            "[-2,1;3/2,-1/2]",
            r"\left[\begin{matrix}-2 & 1 \\ \frac{3}{2} & -\frac{1}{2}\end{matrix}\right]",
        ),
        # brackets round something tall grow with it
        ("cos(π/9)", r"\mathrm{c}\mathrm{o}\mathrm{s}\left(\frac{\pi }{9}\right)"),
        ("(x-1)^2", r"(x-1){}^{2}"),
        # a string keeps its quotes, straight as on the device, and its letters are upright text
        ('"hi"', r'\mathtt{"}\mathrm{h}\mathrm{i}\mathtt{"}'),
        # solve's arbitrary integers are bold italic, without the @ (emulator calc4 results)
        ("x=2*π*@n1", r"x=2\cdot \pi \cdot \boldsymbol{n}\boldsymbol{1}"),
    ],
)
def test_results_drawn_from_the_tree(text: str, latex: str) -> None:
    assert result_latex(text) == latex


@pytest.mark.parametrize("text", ["Done", "when(x<0,1,2)", "2+", "piecewise(1,x<0)"])
def test_sympy_draws_what_the_tree_should_not(text: str) -> None:
    assert result_latex(text) is None


def test_a_selection_edge_inside_brackets_keeps_them_plain() -> None:
    """The highlight box cannot hold one half of a \\left \\right pair."""
    editor = Editor()
    editor.root = row_from_text("cos(π/9)")
    editor.pos = 5  # just after the fraction, inside the brackets
    editor.select_left()
    assert r"\left(" not in editor.latex()
    editor.select_all()
    assert r"\left(" in editor.latex()


def test_a_picked_result_looks_the_same_before_and_after_the_cursor_moves() -> None:
    """Up then Left used to change a result from SymPy's drawing to the tree's."""
    document = Document()
    calc = calculator_on(document.current)
    calc.perform(Binding("insert_linear", "solve(x^2=3,x)"))
    calc.perform(Binding("enter"))
    calc.perform(Binding("up"))
    before = render(document).lines[1].latex
    calc.perform(Binding("end"))  # moves inside the picked row, cursor still at its end
    after = render(document).lines[1].latex
    assert calc.recall_touched
    assert after.replace(_cursor(), "") == before


def test_an_error_result_is_not_drawn_from_the_tree() -> None:
    """An error is kept as its quoted message, drawn as text as before."""
    calc = Calculator(Session())
    calc.finish(Result('"x"', r"\text{x}", None, "Syntax error"), "2+", approximate=False)
    document = Document()
    document.current.model = calc
    assert render(document).lines[1].latex == r'\text{"Syntax error"}'


def test_a_constant_typed_as_at_e_is_still_upright_bold() -> None:
    row = row_from_text("@e^(2)")
    assert row[0] == "ⅇ"  # the parser reads @e as the constant
    assert isinstance(row[1], Template)
    assert row[1].kind is Kind.POWER
    assert result_latex("@e^(2)") == r"\mathbf{e}{}^{2}"


def _cursor() -> str:
    editor = Editor()
    return editor.latex()  # an empty line is only the cursor
