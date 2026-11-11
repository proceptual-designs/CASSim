# Requirements traced here: FR-CALC-003
"""LaTeX output for the GUI (decision 0014): TI's conventions and Flet's Markdown transport."""

import pytest

from cassim.core.results import latex_for_markdown
from cassim.core.session import Session
from cassim.core.settings import Logic, Settings


def latex(line: str) -> str:
    result = Session().eval(line)
    assert result.error is None, result.error
    return result.latex


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("ⅇ^(ⅈ*x)", r"\mathbf{e}^{\boldsymbol{i} x}"),
        ("ⅇ^2+√(2)/2", r"\frac{\sqrt{2}}{2} + \mathbf{e}^{2}"),
        ("ln(x)", r"\ln{\left(x \right)}"),
        ("sin⁻¹(x)", r"\sin^{-1}{\left(x \right)}"),
    ],
)
def test_ti_conventions(line, wanted):
    """ⅇ and ⅈ are upright; `ln` and `sin⁻¹` are written as TI does."""
    assert latex(line) == wanted


def test_conditions_are_joined_with_words_or_symbols():
    """TI writes `and` and `or`; the symbols are an option (setting `logic`)."""
    line = "solve(x^2+y^2=1 and x+y=1,x,y)"
    words = latex(line)
    assert r"\mathbf{and}" in words
    assert r"\wedge" not in words
    shown = Session(Settings(logic=Logic.SYMBOLS)).eval(line).latex
    assert r"\wedge" in shown
    assert "mathbf{and}" not in shown


def test_matrix_rows_survive_markdown():
    """A fraction at the start of a row must not lose its backslash in Flet's Markdown control."""
    tex = latex("[[1,2],[3/2,4]]")
    assert latex_for_markdown(tex) == r"\begin{bmatrix}1&2\cr \frac{3}{2}&4\end{bmatrix}"


def test_a_result_too_large_to_print_is_a_memory_error_not_a_crash():
    """A result of thousands of terms must come back as a TI error, never raise (decision 0016)."""
    session = Session()
    result = session.eval("expand((x+y+z)^60)")
    assert result.error == "Memory"
    assert session.eval("1+1").text == "2"
