"""LaTeX output for the GUI (decision 0014): TI's conventions and Flet's Markdown transport."""

import pytest

from cassim.core.format import latex_for_markdown
from cassim.core.session import Session


def latex(line: str) -> str:
    result = Session().eval(line)
    assert result.error is None, result.error
    return result.latex


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("ⅇ^(ⅈ*x)", r"\mathrm{e}^{\mathrm{i} x}"),
        ("ⅇ^2+√(2)/2", r"\frac{\sqrt{2}}{2} + \mathrm{e}^{2}"),
        ("ln(x)", r"\ln{\left(x \right)}"),
        ("sin⁻¹(x)", r"\sin^{-1}{\left(x \right)}"),
    ],
)
def test_ti_conventions(line, wanted):
    """ⅇ and ⅈ are upright; `ln` and `sin⁻¹` are written as TI does."""
    assert latex(line) == wanted


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
