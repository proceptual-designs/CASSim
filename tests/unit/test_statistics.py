"""OneVar, TwoVar and the regressions (M1d slice 5)."""

import math
from fractions import Fraction

import pytest
from hypothesis import given
from hypothesis import strategies as st

from cassim.core.compat import statistics as stats
from cassim.core.session import Session, same_value
from cassim.core.settings import Angle, Settings

DEGREE = Settings(angle=Angle.DEGREE)


def run(*lines, settings=None):
    session = Session(settings)
    result = None
    for line in lines:
        result = session.eval(line)
    assert result is not None
    return result


def text(*lines, settings=None):
    result = run(*lines, settings=settings)
    assert result.error is None, result.error
    return result.text


def error(*lines, settings=None):
    return run(*lines, settings=settings).error


def number(*lines, settings=None):
    return _float(text(*lines, settings=settings))


def _float(shown):
    """Read a result such as `-3.7052106ᴇ-16`."""
    return float(shown.replace("ᴇ", "e"))


def session_after(*lines, settings=None):
    """A session that has already run `lines`, so that `stat.` variables can be read in turn."""
    session = Session(settings)
    for line in lines:
        assert session.eval(line).error is None, line
    return session


def read(session, line):
    result = session.eval(line)
    assert result.error is None, result.error
    return _float(result.text)


def F(*values):
    return [Fraction(v) for v in values]


# ---- quartiles and descriptive statistics ----------------------------------------------------


def test_quartiles_are_the_median_of_the_halves_not_numpys():
    data = F(1, 4, 9, 16, 25, 36, 49, 64)
    assert stats.quartiles(data) == (Fraction(13, 2), Fraction(41, 2), Fraction(85, 2))
    assert stats.quartiles(F(2, 4, 4, 4, 5, 5, 7, 9)) == (4, Fraction(9, 2), 6)


def test_the_median_is_left_out_of_the_halves_when_n_is_odd():
    assert stats.quartiles(F(1, 2, 3, 4, 5)) == (Fraction(3, 2), 3, Fraction(9, 2))
    assert stats.quartiles(F(1, 2, 3)) == (1, 2, 3)
    assert stats.quartiles(F(7)) == (7, 7, 7)
    assert stats.quartiles(F(7, 9)) == (7, 8, 9)


@given(st.lists(st.fractions(min_value=-1000, max_value=1000), min_size=1, max_size=40))
def test_quartiles_are_ordered_and_inside_the_data(values):
    q1, mid, q3 = stats.quartiles(values)
    assert min(values) <= q1 <= mid <= q3 <= max(values)
    assert sorted(values) == sorted(reversed(values))


@given(
    st.fractions(min_value=-50, max_value=50),
    st.fractions(min_value=-50, max_value=50),
    st.lists(st.integers(-20, 20), min_size=3, max_size=15, unique=True),
)
def test_a_straight_line_is_recovered_exactly(slope, intercept, xs):
    points = [Fraction(x) for x in xs]
    ys = [slope * x + intercept for x in points]
    fit = stats.polynomial_fit(points, ys, 1)
    assert fit == [slope, intercept]


def test_summary_of_a_list():
    summary = stats.summarise(F(2, 4, 4, 4, 5, 5, 7, 9))
    assert (summary.n, summary.total, summary.total_squares) == (8, 40, 232)
    assert summary.sum_squared_deviations == 32
    assert summary.population_deviation == 2.0
    assert summary.sample_deviation == pytest.approx(2.1380899353)
    assert math.isnan(stats.summarise(F(5)).sample_deviation)


def test_frequencies_repeat_values():
    assert stats.expand(F(1, 2, 3), [1, 2, 1]) == F(1, 2, 2, 3)
    assert stats.expand(F(1, 2), None) == F(1, 2)
    with pytest.raises(ValueError, match=r"."):
        stats.expand(F(1, 2), [1])
    with pytest.raises(ValueError, match=r"."):
        stats.expand(F(1, 2), [1, -1])


def test_one_var_matches_the_corpus_values():
    session = session_after("x:={2,4,4,4,5,5,7,9}")
    assert session.eval("OneVar x,1").text == "Done"
    assert read(session, "stat.n") == 8
    assert read(session, "stat.sx") == pytest.approx(2.1380899)
    assert read(session, "stat.σx") == 2
    assert read(session, "stat.v") == 5
    assert read(session, "stat.sumx") == 40
    assert read(session, "stat.sumx2") == 232
    assert [read(session, f"stat.{n}") for n in ("minx", "q1x", "medx")] == [2, 4, 4.5]
    assert [read(session, f"stat.{n}") for n in ("q3x", "maxx", "ssx")] == [6, 9, 32]


def test_one_var_results_matrix_has_the_ti_labels():
    session = Session()
    session.eval("OneVar {2,4,4,4,5,5,7,9}")
    shown = session.eval("stat.results").text
    for label in ("One-Variable Statistics", "x̄", "sx := sn-1x", "Q₁X", "Q₃X", "SSX"):
        assert label in shown


def test_quartiles_of_a_list_with_the_school_convention():
    session = session_after("OneVar {1,4,9,16,25,36,49,64}")
    assert read(session, "stat.q1x") == 6.5
    assert read(session, "stat.q3x") == 42.5


def test_one_var_with_frequencies_and_a_count_of_lists():
    assert number("OneVar {1,2,3},{1,2,1}", "stat.n") == 4
    assert number("OneVar {1,2,3},{1,2,1}", "stat.v") == 2
    assert number("OneVar {1,2,3},2", "stat.n") == 6
    assert number("OneVar 1,{1,2,3},{1,2,1}", "stat.n") == 4


def test_one_var_with_a_single_value_has_no_sample_deviation():
    assert text("OneVar {5}", "stat.sx") == "undef"


def test_two_var_matches_the_corpus_values():
    session = session_after("x:={1,2,3,4,5}", "y:={2,4,5,4,5}")
    assert session.eval("TwoVar x,y,1").text == "Done"
    assert read(session, "stat.r") == pytest.approx(0.77459667)
    assert read(session, "stat.sumxy") == 66
    assert read(session, "stat.w") == 4
    assert read(session, "stat.ssy") == 6
    assert read(session, "stat.sy") == pytest.approx(1.2247449)
    assert session.eval("stat.values").text.startswith('["Two-Variable Statistics",3.,15.,55.')


def test_statistics_errors():
    assert error("OneVar") == "Too few arguments"
    assert error("OneVar 5") == "Too few arguments"
    assert error("OneVar x") == "Data type"
    assert error("OneVar {}") == "Invalid list or matrix"
    assert error("OneVar {1,x}") == "Data type"
    assert error("OneVar {1,2},{1}") == "Dimension mismatch"
    assert error("OneVar {1,2},{1,-1}") == "Domain error"
    assert error("OneVar {1,2},{0.5,1}") == "Domain error"
    assert error("TwoVar {1,2,3}") == "Too few arguments"
    assert error("TwoVar {1,2,3},{1,2}") == "Dimension mismatch"


# ---- regressions -----------------------------------------------------------------------------


def _same(line, wanted, tolerance=1e-7):
    got = run(line).value
    expected = run(wanted).value
    assert got is not None
    assert expected is not None
    assert same_value(got, expected, tolerance), f"{line} gave {text(line)}"


def test_linear_regression_matches_the_corpus():
    run("x:={1,2,3,4}", "y:={3,4,6,9}")
    results = '[["Title","Linear Regression (a+bx)"],["RegEqn","a+b*x"],["a",0.5],["b",2.],'
    results += '["r²",0.95238095],["r",0.97590007],["Resid","{...}"]]'
    _same("x:={1,2,3,4}:y:={3,4,6,9}:LinRegBx x,y,1:stat.results", results)
    _same(
        "x:={1,2,3,4,5}:y:={2,4,5,4,5}:LinRegMx x,y,1:stat.results",
        '[["Title","Linear Regression (mx+b)"],["RegEqn","m*x+b"],["m",0.6],["b",2.2],'
        '["r²",0.6],["r",0.77459667],["Resid","{...}"]]',
    )


def test_linear_regression_stat_variables():
    session = session_after("x:={1,2,3,4,5}", "y:={2,4,5,4,5}")
    assert session.eval("LinRegMx x,y").text == "Done"
    assert read(session, "stat.m") == pytest.approx(0.6)
    assert read(session, "stat.b") == pytest.approx(2.2)
    assert read(session, "stat.r²") == pytest.approx(0.6)
    assert session.eval("stat.regeqn").text == '"m*x+b"'
    assert session.eval("stat.resid").text.startswith("{")


def test_a_negative_slope_gives_a_negative_r():
    assert number("LinRegBx {1,2,3},{3,2,1}", "stat.r") == pytest.approx(-1)


@pytest.mark.parametrize(
    ("command", "wanted"),
    [
        ("QuadReg x,z,1", {"a": 1, "b": 0, "c": 0, "r²": 1}),
        ("ExpReg x,y,1", {"a": 1, "b": 2, "r²": 1, "r": 1}),
        ("PowerReg x,w,1", {"a": 2, "b": 2, "r²": 1}),
        ("LnReg x,l,1", {"a": 2, "b": 3, "r²": 1}),
    ],
)
def test_exact_data_gives_exact_parameters(command, wanted):
    session = Session()
    session.eval("x:={1,2,3,4,5}")
    session.eval("z:=x^2")
    session.eval("y:={2,4,8,16,32}")
    session.eval("w:={2,8,18,32,50}")
    session.eval("l:=approx(2+3*ln(x))")
    assert session.eval(command).text == "Done"
    for name, value in wanted.items():
        assert read(session, f"stat.{name}") == pytest.approx(value, abs=1e-9), name


def test_polynomial_regressions_of_higher_degree():
    session = Session()
    session.eval("cx:={1,2,3,4,5,6}")
    session.eval("cw:={3,10,29,66,127,218}")
    session.eval("cq:=cx^4-2*cx^2+1")
    session.eval("CubicReg cx,cw")
    got = [read(session, f"stat.{n}") for n in "abcd"]
    assert got == pytest.approx([1, 0, 0, 2], abs=1e-9)
    session.eval("QuartReg cx,cq")
    got = [read(session, f"stat.{n}") for n in "abcde"]
    assert got == pytest.approx([1, 0, -2, 0, 1], abs=1e-9)
    assert read(session, "stat.R²") == pytest.approx(1)


def test_median_median_line():
    session = session_after("cx:={1,2,3,4,5,6}", "cm:={1,3,2,5,4,7}")
    assert session.eval("MedMed cx,cm").text == "Done"
    assert read(session, "stat.m") == pytest.approx(0.875)
    assert read(session, "stat.b") == pytest.approx(0.60416667)
    # 7 points split 2,3,2 and 8 points split 3,2,3
    assert stats.median_median_line(F(*range(1, 8)), F(*range(1, 8))) == (1, 0)
    assert stats.median_median_line(F(*range(1, 9)), F(*range(1, 9))) == (1, 0)


def test_logistic_regressions_recover_exact_parameters():
    session = Session()
    session.eval("cu:=seq(k,k,1,12)")
    session.eval("cg:=approx(10/(1+4*exp(-0.5*cu)))")
    assert session.eval("Logistic cu,cg").text == "Done"
    got = [read(session, f"stat.{n}") for n in "abc"]
    assert got == pytest.approx([4, 0.5, 10], abs=1e-6)
    session.eval("cd:=cg+2")
    session.eval("LogisticD cu,cd")
    got = [read(session, f"stat.{n}") for n in "abcd"]
    assert got == pytest.approx([4, 0.5, 10, 2], abs=1e-6)


def test_sinusoidal_regression_in_degree_mode_reports_radians():
    session = Session(DEGREE)
    session.eval("cu:=seq(k,k,1,12)")
    session.eval("cv:=approx(3*sin(30*cu)+1)")
    assert session.eval("SinReg cu,cv").text == "Done"
    got = [read(session, f"stat.{n}") for n in "abcd"]
    assert got == pytest.approx([3, math.pi / 6, 0, 1], abs=1e-6)


def test_regression_with_frequencies():
    # a frequency of 2 on every point changes nothing
    lines = ("x:={1,2,3,4}", "y:={3,4,6,9}", "LinRegBx x,y,{2,2,2,2}", "stat.b")
    assert number(*lines) == pytest.approx(2)


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("LinRegMx {1,1,1},{2,4,5}", "Domain error"),  # x does not vary
        ("ExpReg {1,2,3},{1,-2,3}", "Domain error"),  # needs positive y
        ("PowerReg {0,1,2},{1,2,3}", "Domain error"),  # needs positive x
        ("LnReg {-1,1,2},{1,2,3}", "Domain error"),
        ("QuadReg {1,2},{1,4}", "Domain error"),  # too few points
        ("MedMed {1,2},{1,2}", "Domain error"),
        ("LinRegBx {1,2,3},{2,4}", "Dimension mismatch"),
        ("LinRegBx {1,2,3}", "Too few arguments"),
        ("LinRegBx x,y", "Data type"),
    ],
)
def test_regression_errors(line, message):
    assert error(line) == message


def test_results_matrix_cannot_be_used_as_numbers():
    assert error("LinRegBx {1,2,3},{2,4,7}", "stat.results+1") == "Data type"
    assert error("LinRegBx {1,2,3},{2,4,7}", "det(stat.results)") == "Data type"
