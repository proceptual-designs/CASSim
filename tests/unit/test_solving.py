# Requirements traced here: FR-CAT-001
"""solve, cSolve, zeros, cZeros, polyRoots and the `|` domain (M1d slice 2)."""

import pytest

from cassim.core.session import Session, same_value
from cassim.core.settings import Angle, Calc, CasMode, Settings

DEGREE = Settings(angle=Angle.DEGREE)
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
        ("solve(x^2-4=0,x)", "x=-2 or x=2"),
        ("solve(x^3-3*x^2+2*x=0,x)", "x=0 or x=1 or x=2"),
        ("solve(x^4-5*x^2+4=0,x)", "x=-2 or x=-1 or x=1 or x=2"),
        ("solve(abs(x-1)=3,x)", "x=-2 or x=4"),
        ("solve(2^x=8,x)", "x=3"),
        ("solve(ln(x)=2,x)", "x=ⅇ^2"),
        ("solve(exp(x)=5,x)", "x=ln(5)"),
        ("solve(exp(2*x)-5*exp(x)+6=0,x)", "x=ln(2) or x=ln(3)"),
        ("solve(a*x+b=0,x)", "x=-b/a"),
        ("solve(y=3*x-2,x)", "x=(y+2)/3"),
        ("solve(x^2=2,x)", "x=-√(2) or x=√(2)"),
        ("solve(x^2+1=0,x)", "false"),
        ("solve(x=x,x)", "true"),
        ("solve(x=x+1,x)", "false"),
    ],
)
def test_solve_one_equation(line, wanted):
    same(line, wanted)


def test_a_root_that_does_not_satisfy_the_equation_is_dropped():
    # SymPy offers x=-1 here, where both logarithms are of negative numbers
    same("solve(ln(x)+ln(x-1)=ln(2),x)", "x=2")


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("solve(x^2>4,x)", "x<-2 or x>2"),
        ("solve(x^2+2*x-3<=0,x)", "-3≤x≤1"),
        ("solve(x^2+2*x-3<=0,x)", "x≥-3 and x≤1"),
        ("solve(x>2,x)", "x>2"),
    ],
)
def test_solve_inequalities(line, wanted):
    same(line, wanted)


def test_roots_print_in_increasing_order_and_ranges_as_chains():
    assert text("solve(x^3-3*x^2+2*x=0,x)") == "x=0 or x=1 or x=2"
    assert text("solve(x^2>4,x)") == "x<-2 or x>2"
    assert text("solve(x^2+2*x-3<=0,x)") == "-3≤x≤1"


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("solve({x+y=3,x-y=1},{x,y})", "x=2 and y=1"),
        ("solve({y=x^2,y=2*x+3},{x,y})", "x=-1 and y=1 or x=3 and y=9"),
        ("solve({x+y+z=6,x-y+z=2,2*x+y-z=1},{x,y,z})", "x=1 and y=2 and z=3"),
        ("solve({x+y=3,x+y=4},{x,y})", "false"),
        # The same systems typed with `and`, as the handheld's system template writes them
        ("solve(x+y=3 and x-y=1,{x,y})", "x=2 and y=1"),
        ("solve(y=x^2 and y=2*x+3,{x,y})", "x=-1 and y=1 or x=3 and y=9"),
        ("solve(x+y+z=6 and x-y+z=2 and 2*x+y-z=1,{x,y,z})", "x=1 and y=2 and z=3"),
        ("solve(x+y=3 and x+y=4,{x,y})", "false"),
    ],
)
def test_solve_systems(line, wanted):
    same(line, wanted)


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("cSolve(x^2+1=0,x)", "x=ⅈ or x=-ⅈ"),
        ("cSolve(x^2+2*x+5=0,x)", "x=-1+2*ⅈ or x=-1-2*ⅈ"),
        ("cSolve(x^3=1,x)", "x=1 or x=-1/2+√(3)/2*ⅈ or x=-1/2-√(3)/2*ⅈ"),
        ("cSolve(z^4=16,z)", "z=2 or z=-2 or z=2*ⅈ or z=-2*ⅈ"),
    ],
)
def test_csolve(line, wanted):
    same(line, wanted)


def test_csolve_answers_are_not_collapsed_to_false():
    # x is a real symbol, and SymPy decides x=1+2i is false unless the equation is kept as typed
    assert text("cSolve(x^2+1=0,x)") == "x=ⅈ or x=-ⅈ"
    assert text("x=ⅈ") == "x=ⅈ"


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("solve(x^2=4,x)|x>0", "x=2"),
        ("solve(x^2=4,x)|x<0", "x=-2"),
        ("solve(x^2=4,x)|x>5", "false"),
        ("solve(x^2-4=0,x)|x>=2", "x=2"),
        ("solve(sin(x)=0.5,x)|0<=x<=2*pi", "x=0.52359878 or x=2.6179939"),
        ("solve(cos(x)=1/2,x)|0<=x<=2*pi", "x=π/3 or x=5*π/3"),
        ("solve(tan(x)=1,x)|0<=x<=2*pi", "x=π/4 or x=5*π/4"),
        ("solve(2*sin(x)^2-sin(x)-1=0,x)|0<=x<=2*pi", "x=π/2 or x=7*π/6 or x=11*π/6"),
        ("solve(x^2>4,x)|x>0", "x>2"),
    ],
)
def test_constraint_restricts_the_domain(line, wanted):
    same(line, wanted, tolerance=1e-7)


def test_constraint_with_a_user_function():
    assert text("f(x):=x^2-4", "solve(f(x)=0,x)|x>0") == "x=2"
    assert text("f(x):=x^3", "7→c", "solve(f(x)=8,x)") == "x=2"


def test_solving_in_degree_mode_reads_trig_in_degrees():
    same("solve(sin(x)=1/2,x)|0<x and x<360", "x=30 or x=150", DEGREE)
    same("solve(sin(x)=1/2,x)|0<x<360", "x=30 or x=150", DEGREE)
    same("solve(cos(x)=0,x)|0<=x<=360", "x=90 or x=270", DEGREE)
    # the bounds are plain numbers; only the argument of the trig function is an angle
    same("solve(x^2=4,x)|x>0", "x=2", DEGREE)


def test_a_periodic_equation_gives_the_family_of_solutions():
    assert text("solve(sin(x)=1/2,x)") == "x=2*@n1*π+π/6 or x=2*@n1*π+5*π/6"
    same("solve(sin(x)=1/2,x)", "x=2*@n1*π+π/6 or x=2*@n1*π+5*π/6")
    same("solve(cos(x)=0,x)", "x=@n1*π+π/2")  # evenly spaced families merge (run 6, R6-B3)


def test_a_family_in_degree_mode_is_in_degrees():
    same("solve(sin(x)=1/2,x)", "x=360*@n1+30 or x=360*@n1+150", DEGREE)


def test_an_answer_with_no_finite_form_stays_as_typed():
    assert text("solve(exp(x)=x,x)") == "solve(ⅇ^x=x,x)"


def test_roots_that_need_a_parameter_to_be_non_negative_say_so():
    same("solve(x^2=a,x)", "x=-√(a) and a≥0 or x=√(a) and a≥0")
    assert text("solve(x^2=a,x)") == "x=-√(a) and a≥0 or x=√(a) and a≥0"
    assert text("solve(a*x+b=0,x)") == "x=-b/a"


def test_the_unknown_is_symbolic_even_if_it_holds_a_value():
    assert text("x:=5", "solve(x^2=9,x)") == "x=-3 or x=3"
    assert text("x:=5", "solve(x^2=9,x)", "x") == "5"


def test_unknowns_need_no_list():
    """`solve(eqs, x, y)` is `solve(eqs, {x,y})`, as on the handheld."""
    system = "solve(x^2+y^2=1 and x+y=1,x,y)"
    assert text(system) == text("solve(x^2+y^2=1 and x+y=1,{x,y})")
    assert text("solve(x+y=3 and x-y=1,x,y)") == "x=2 and y=1"


def test_arguments_are_checked():
    assert error("solve(x^2=1)") == "Too few arguments"
    assert error("solve(x^2=1,x,x)") == "Too many arguments"
    assert error("solve(x^2=1,5)") == "Syntax error"
    assert error("solve(x^2=1,{})") == "Syntax error"
    assert error("zeros(x^2-1,{x,y})") == "Syntax error"


@pytest.mark.parametrize("command", ["solve", "cSolve"])
def test_solving_requires_an_equation_or_inequality(command):
    assert error(f"{command}(x^2-2,x)") == "Syntax error"


@pytest.mark.parametrize("command", ["zeros", "zeroes", "cZeros"])
@pytest.mark.parametrize("input_text", ["x^2-2=0", "x^2>2"])
def test_zeros_requires_an_expression(command, input_text):
    assert error(f"{command}({input_text},x)") == "Syntax error"


def test_solve_and_zeros_keep_accepting_their_respective_argument_kinds():
    assert text("solve(x^2-2=0,x)") == "x=-√(2) or x=√(2)"
    assert text("solve(x^2>2,x)") == "x<-√(2) or x>√(2)"
    assert text("zeros(x^2-2,x)") == "{-√(2),√(2)}"


@pytest.mark.parametrize(
    "line",
    ["solve(x^2-4=0,x)", "solve({x+y=3,x-y=1},{x,y})", "cSolve(x^2+1=0,x)", "zeros(x^2-1,x)"],
)
def test_solving_is_refused_in_cas_off(line):
    assert "restricted" in error(line, settings=CAS_OFF)


def test_solve_in_approximate_mode_gives_decimals():
    session = Session(Settings(angle=Angle.DEGREE, calc=Calc.APPROXIMATE))
    assert session.eval("solve(x^2-5*x+6=0,x)").text == "x=2. or x=3."


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("zeros(x^3-x,x)", "{-1,0,1}"),
        ("zeros(x^2+1,x)", "{}"),
        ("cZeros(x^3-1,x)", "{-1/2+√(3)/2*ⅈ,-1/2-√(3)/2*ⅈ,1}"),
        ("cZeros(x^2+1,x)", "{ⅈ,-ⅈ}"),
        ("polyRoots(x^3-6*x^2+11*x-6,x)", "{1,2,3}"),
        ("polyRoots((x-1)^2*(x+2),x)", "{-2,1,1}"),
        ("polyEval({1,-2,3},2)", "3"),
        ("polyEval({2,0,-1},3)", "17"),
    ],
)
def test_zeros_and_polynomials(line, wanted):
    same(line, wanted)


def test_zeros_are_listed_by_real_part_then_imaginary_part_descending():
    assert text("cZeros(x^3-1,x)").startswith("{-1/2+")


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("0<=2<=3", "true"),
        ("0<=2<=1", "false"),
        ("1<2<3<4", "true"),
        ("x<=3 and x>=1", "x≤3 and x≥1"),
    ],
)
def test_chained_relations(line, wanted):
    same(line, wanted)


def test_a_chained_relation_with_a_symbol_is_a_conjunction():
    assert text("1<x<3") == "1<x<3"


def test_relations_with_a_symbol_are_not_decided_for_it():
    assert text("x=x") == "true"
    assert text("x=1") == "x=1"
    assert text("x≠x") == "false"


def test_trig_equal_to_a_parameter_gives_the_general_solution():
    session = Session()
    assert session.eval("solve(sin(x)=y,x)").text == "x=2*@n1*π+sin⁻¹(y) or x=2*@n1*π-sin⁻¹(y)+π"
    assert session.eval("solve(cos(x)=a,x)").error is None
