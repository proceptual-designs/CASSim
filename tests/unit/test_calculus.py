# Requirements traced here: FR-CAT-001
"""Calculus (M1d slice 3): derivatives, integrals, limits, series, extrema, tangents, ODEs."""

import pytest

from cassim.core.session import Session, same_value
from cassim.core.settings import Calc, CasMode, Settings

CAS_OFF = Settings(cas_mode=CasMode.OFF)


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


def same(line, wanted, settings=None, tolerance=None):
    got = run(line, settings=settings).value
    expected = run(wanted).value
    assert got is not None
    assert expected is not None
    assert same_value(got, expected, tolerance), f"{line} gave {text(line, settings=settings)}"


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("derivative(x^3,x)", "3*x^2"),
        ("derivative(x^3,x,2)", "6*x"),
        ("derivative(x^2*sin(x),x)", "x^2*cos(x)+2*x*sin(x)"),
        ("derivative(x*exp(x),x)", "(x+1)*ⅇ^x"),
        ("derivative(x/(x^2+1),x)", "-(x^2-1)/(x^2+1)^2"),
        ("derivative(sin(x^2),x)", "2*x*cos(x^2)"),
        ("derivative(a*x^2,x)", "2*a*x"),
        ("derivative(ln(x),x)", "1/x"),
        ("derivative(sin(x),x)|x=pi/2", "0"),
        ("derivative(x^2,x)|x=3", "6"),
    ],
)
def test_derivative(line, wanted):
    same(line, wanted)


def test_a_value_the_variable_already_has_is_put_in_afterwards():
    # a function body is evaluated with its argument bound, as in df(3)
    assert text("f(x):=x^2", "df(x):=derivative(f(x),x)", "df(3)") == "6"
    assert text("f(x):=x^3", "df(x):=derivative(f(x),x)", "df(a+1)") == "3*(a+1)^2"
    assert text("f(x):=x^3", "derivative(f(x),x)|x=2") == "12"
    assert text("x:=4", "derivative(x^2,x)") == "8"


def test_the_variable_is_symbolic_inside_the_expression():
    assert text("f(x):=x^3", "f(x)", "derivative(f(x),x)") == "3*x^2"
    assert text("x:=4", "derivative(a*x^2,x)", "x") == "4"


def test_derivative_errors():
    assert error("derivative(x^2)") == "Too few arguments"
    assert error("derivative(x^2,x,0)") == "Domain error"
    assert error("derivative(x^2,3)") == "Syntax error"


def test_derivative_in_cas_off_only_works_at_a_point():
    assert error("derivative(x^2*sin(x),x)", settings=CAS_OFF) == "Use Derivative at a Point"
    session = Session(CAS_OFF)
    result = session.eval("derivative(x^2*sin(x),x)|x=2")
    same_value_ok = result.value is not None and abs(float(result.text) - 1.9726024) < 1e-7
    assert same_value_ok
    session.eval("f(x):=x^2")
    session.eval("df(x):=derivative(f(x),x)")
    assert session.eval("df(3)").text == "6"


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("integral(x^2,x,0,1)", "1/3"),
        ("integral(sin(x),x)", "-cos(x)"),
        ("integral(x*exp(x),x)", "(x-1)*ⅇ^x"),
        ("integral(x*exp(x),x,0,1)", "1"),
        ("integral(x*sin(x),x)", "sin(x)-x*cos(x)"),
        ("integral(1/(x^2+1),x)", "arctan(x)"),
        ("integral(sqrt(1-x^2),x,-1,1)", "π/2"),
        ("integral(x/sqrt(1-x^2),x)", "-√(1-x^2)"),
        ("integral(pi*x^4,x,0,1)", "π/5"),
        ("integral(sqrt(1+4*x^2),x,0,1)", "ln(√(5)+2)/4+√(5)/2"),
        ("integral(abs(x-1),x,0,3)", "5/2"),
        ("integral(abs(x-x^2),x,0,2)", "1"),
        ("integral(abs(x),x,-1,2)", "5/2"),
        ("integral(1/(x^2-1),x)", "-ln(abs(x+1)/abs(x-1))/2"),
        ("integral(a*x,x,0,2)", "2*a"),
    ],
)
def test_integral(line, wanted):
    same(line, wanted)


def test_an_antiderivative_of_one_over_x_has_an_absolute_value():
    assert text("integral(1/x,x)") == "ln(abs(x))"
    assert text("integral(x/(x^2+1),x)") == "ln(x^2+1)/2"  # the argument is positive
    assert text("integral(1/(x+1),x,0,1)") == "ln(2)"  # a definite integral has no abs


def test_integral_with_a_piecewise_function():
    assert text("f(x):=when(x<1,x,2-x)", "integral(f(x),x,0,2)") == "1"


def test_integral_with_no_closed_form_is_echoed():
    assert text("integral(exp(sin(x)),x,0,1)").startswith("integral(")


def test_integral_argument_counts():
    assert error("integral(x^2,x,1)") == "Too few arguments"
    assert error("integral(x^2)") == "Too few arguments"
    assert error("integral(x^2,x,0,1,2)") == "Too many arguments"


def test_integral_in_cas_off():
    result = Session(CAS_OFF).eval("integral(x*exp(x),x,0,1)")
    assert result.error is None
    assert abs(float(result.text) - 1) < 1e-9
    assert "restricted" in error("integral(x^2,x)", settings=CAS_OFF)


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("limit(sin(x)/x,x,0)", "1"),
        ("limit(sin(3*x)/x,x,0)", "3"),
        ("limit((x^2-1)/(x-1),x,1)", "2"),
        ("limit((1+1/n)^n,n,∞)", "ⅇ"),
        ("limit((1+1/n)^n,n,infinity)", "ⅇ"),
        ("limit(1/x,x,0,1)", "∞"),
        ("limit(1/x,x,0,-1)", "-∞"),
        ("limit(1/x,x,0)", "undef"),
        ("limit(x*ln(x),x,0,1)", "0"),
    ],
)
def test_limit(line, wanted):
    same(line, wanted)


def test_limit_errors():
    assert error("limit(x,x)") == "Too few arguments"
    assert error("limit(1/x,x,0,2)") == "Domain error"
    assert "restricted" in error("limit(sin(x)/x,x,0)", settings=CAS_OFF)


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("taylor(exp(x),x,3,0)", "1+x+x^2/2+x^3/6"),
        ("taylor(exp(x),x,3)", "1+x+x^2/2+x^3/6"),
        ("taylor(sin(x),x,5)", "x-x^3/6+x^5/120"),
        ("taylor(1/(1-x),x,3)", "1+x+x^2+x^3"),
    ],
)
def test_taylor(line, wanted):
    same(line, wanted)


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("fMax(-x^2+4*x,x)", "x=2"),
        ("fMin(x^2-4*x,x)", "x=2"),
        ("fMax(x^3-3*x,x)|x<=0", "x=-1"),
        ("fMin(x^3-3*x,x)|x>=0", "x=1"),
        ("fMax(sin(x),x)|0<=x<=pi", "x=π/2"),
        ("fMin(x^2,x)|1<=x<=3", "x=1"),
        ("fMax(x^2,x)|1<=x<=3", "x=3"),
    ],
)
def test_extrema(line, wanted):
    same(line, wanted)


def test_an_extremum_that_is_not_reached_is_echoed():
    assert text("fMin(x^3,x)") == "fMin(x^3,x)"
    assert text("fMax(-x^2,x)|x>1") == "fMax(-x^2,x)"
    assert text("fMin(exp(-x),x)") == "fMin(ⅇ^-x,x)"


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("tangentLine(x^3-3*x,x,2)", "9*x-16"),
        ("normalLine(x^2,x,1)", "3/2-x/2"),
        ("impDif(x^2+y^2=25,x,y)", "-x/y"),
        ("impDif(x*y=1,x,y)", "-y/x"),
    ],
)
def test_lines_and_implicit_differentiation(line, wanted):
    same(line, wanted)


def test_tangent_line_of_a_user_function():
    assert text("Define h(x)=x^3-3*x", "tangentLine(h(x),x,2)") == "9*x-16"


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("nInt(exp(-x^2),x,-1,1)", "1.4936483"),
        ("nInt(x^2,x,0,3)", "9."),
        ("nDerivative(x^2,x=3)", "6."),
        ("nDerivative(sin(x),x=0)", "1."),
        ("nSolve(x^3+x=1,x)", "0.6823278"),
        ("nSolve(cos(x)=x,x=0.5)", "0.73908513"),
        ("nSolve(x^2=2,x)", "1.4142136"),
    ],
)
def test_numerical_functions(line, wanted):
    same(line, wanted, tolerance=1e-7)


def test_nsolve_without_a_root():
    assert error("nSolve(x^2=-1,x)") == "No solution found"
    assert error("nDerivative(x^2,x)") == "Syntax error"


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("deSolve(y'=y,x,y)", "y=c1*ⅇ^x"),
        ("deSolve(y'=2*y,x,y)", "y=c1*ⅇ^(2*x)"),
        ("deSolve(y'=y and y(0)=2,x,y)", "y=2*ⅇ^x"),
        ("deSolve(y'=x*y and y(0)=1,x,y)", "y=ⅇ^(x^2/2)"),
        ("deSolve(y''=-y,x,y)", "y=c1*cos(x)+c2*sin(x)"),
        ("deSolve(y'=y+1,x,y)", "y=c1*ⅇ^x-1"),
    ],
)
def test_desolve(line, wanted):
    same(line, wanted)


def test_prime_only_means_something_inside_desolve():
    assert "Not implemented yet" in error("y'")
    assert text("deSolve(y'=y,x,y)") == "y=c1*ⅇ^x"
    assert "Not implemented yet" in error("y'")  # and does not leak out afterwards


def test_calculus_in_approximate_mode_gives_decimals():
    session = Session(Settings(calc=Calc.APPROXIMATE))
    assert session.eval("derivative(x^3,x)").text == "3.*x^2"
    assert session.eval("integral(x^2,x,0,1)").text == "0.33333333"


def test_tangent_fmax_and_limit_are_refused_in_cas_off():
    for line in ("tangentLine(x^2,x,1)", "fMax(-x^2,x)", "taylor(exp(x),x,2)", "impDif(x=y,x,y)"):
        assert "restricted" in error(line, settings=CAS_OFF)


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("sumSeq(2*k-1,k,1,10)", "100"),
        ("Σ(n,n,1,10)", "55"),
        ("sumSeq(1/2^n,n,0,∞)", "2"),
        ("Σ(1/n^2,n,1,∞)", "π^2/6"),
        ("prodSeq(n,n,1,5)", "120"),
        ("Π(k,k,1,4)", "24"),
        ("∫(x^2,x,0,2)", "8/3"),
        ("∫(x^2,x)", "x^3/3"),
    ],
)
def test_series_and_template_spellings(line, wanted):
    """The templates `Σ(`, `Π(` and `∫(` are `sumSeq`, `prodSeq` and `integral`."""
    assert text(line) == wanted


def test_symbolic_upper_limit_of_a_sum():
    same("sumSeq(k,k,1,n)", "n*(n+1)/2")
