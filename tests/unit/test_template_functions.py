"""Functions behind the 2D templates: `root(` (nth root) and `piecewise(` (FR-CALC-005)."""

import pytest

from cassim.core.session import Session


def text(line: str, session: Session | None = None) -> str:
    return (session or Session()).eval(line).text


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("root(8,3)", "2"),
        ("root(-8,3)", "-2"),  # an odd root of a negative number is real, as on TI
        ("root(16,4)", "2"),
        ("root(x,3)", "x^(1/3)"),
        ("log(8,2)", "3"),  # the log-with-base template
    ],
)
def test_root_and_log_templates(line: str, wanted: str) -> None:
    assert text(line) == wanted


def test_piecewise_picks_the_first_true_piece() -> None:
    session = Session()
    text("Define f(x)=piecewise(x^2,x<0,x,x>=0)", session)
    assert [text(f"f({x})", session) for x in (-3, 0, 3)] == ["9", "0", "3"]


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("piecewise(1,2>3,5)", "5"),  # a last value with no condition is the otherwise
        ("piecewise(1,2>3)", "undef"),  # no piece true
        ("piecewise(1,2<3,1/0,1>0)", "1"),  # only the chosen piece is evaluated
    ],
)
def test_piecewise_choices(line: str, wanted: str) -> None:
    assert text(line) == wanted


def test_piecewise_stays_symbolic_while_undecided() -> None:
    result = Session().eval("piecewise(x^2,x<0,x,x>=0)")
    assert "cases" in result.latex


def test_undef_is_drawn_as_undef_not_nan() -> None:
    assert Session().eval("1/0").latex == r"\text{undef}"
