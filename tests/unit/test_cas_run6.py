# Requirements traced here: FR-CAT-001
"""CAS behaviour from emulator check 6, run 6 (`docs/testing/emulator-check6-run6-plan.md` 1.1):
arbitrary constants numbered through a Problem, integer families, and derivative forms.
"""

from cassim.core.session import Session
from cassim.core.settings import PRESETS


def texts(*lines: str, course: str = "specialist") -> list[str]:
    session = Session(PRESETS[course])
    shown = []
    for line in lines:
        result = session.eval(line)
        assert result.error is None, result.error
        shown.append(result.text)
    return shown


def text(*lines: str) -> str:
    return texts(*lines)[-1]


SYSTEM = "solve(2x+y+z=1 and x-y=2,x,y,z)"


# R6-B3: the c and n counters


def test_free_parameters_count_up_through_a_problem():
    first, second = texts(SYSTEM, SYSTEM)
    assert first == "x=-(c1-3)/3 and y=-(c1+3)/3 and z=c1"
    assert second == "x=-(c2-3)/3 and y=-(c2+3)/3 and z=c2"


def test_arbitrary_integers_count_up_separately_from_constants():
    shown = texts(
        "domain(tan(x),x)",
        SYSTEM,
        "solve(sin(x)=0,x)",
        "solve(sin(x)=0,x)",
        "fMin(sin(x)+cos(x),x)",
    )
    assert shown == [
        "x≠(2*@n1-1)*π/2",
        "x=-(c1-3)/3 and y=-(c1+3)/3 and z=c1",
        "x=@n2*π",
        "x=@n3*π",
        "x=(4*@n4-3)*π/4 and (-1)^@n4>0",
    ]


def test_a_new_problem_restarts_the_counters():
    session = Session(PRESETS["specialist"])
    session.eval(SYSTEM)
    session.eval("solve(sin(x)=0,x)")
    session.new_problem()
    assert session.eval("solve(sin(x)=0,x)").text == "x=@n1*π"
    assert session.eval(SYSTEM).text == "x=-(c1-3)/3 and y=-(c1+3)/3 and z=c1"


def test_recalling_an_answer_keeps_its_constants_and_uses_no_new_number():
    shown = texts(SYSTEM, "ans", SYSTEM)
    assert shown[1] == shown[0]
    assert "c2" in shown[2]


def test_a_failed_entry_uses_no_number():
    session = Session(PRESETS["specialist"])
    assert session.eval("solve(sin(x)=0,x").error is not None
    assert session.eval("solve(sin(x)=0,x)").text == "x=@n1*π"


def test_a_preview_uses_no_number():
    session = Session(PRESETS["specialist"])
    session.preview("solve(sin(x)=0,x)")
    assert session.eval("solve(sin(x)=0,x)").text == "x=@n1*π"


def test_desolve_constants_share_the_c_counter():
    shown = texts(SYSTEM, "deSolve(y''=-y,x,y)")
    assert shown[1] == "y=c2*cos(x)+c3*sin(x)"


# R6-B2, R6-B3: families


def test_evenly_spaced_families_are_one():
    assert text("solve(sin(x)=0,x)") == "x=@n1*π"
    assert text("solve(sin(x)=1/2,x)") == "x=2*@n1*π+π/6 or x=2*@n1*π+5*π/6"


def test_the_domain_of_tan_is_a_family_of_gaps():
    assert text("domain(tan(x),x)") == "x≠(2*@n1-1)*π/2"


def test_fmin_of_a_periodic_function_is_a_family_when_it_solves_exactly():
    assert text("fMin(sin(x)+cos(x),x)") == "x=(4*@n1-3)*π/4 and (-1)^@n1>0"
    assert text("fMax(sin(x)+cos(x),x)") == "x=(4*@n1-3)*π/4 and (-1)^@n1<0"


def test_fmin_keeps_a_decimal_when_the_critical_points_are_not_one_family():
    assert text("fMin(sin(x/2)+cos(2x),x)") == "x=-1.6557595"


# R6-B4: derivative forms


def test_a_shared_exponential_is_taken_out_of_a_derivative():
    assert text("derivative(x*@e^(-x),x)") == "(1-x)*ⅇ^(-x)"
    assert text("derivative(x^2*@e^(x),x)") == "x*(x+2)*ⅇ^x"


def test_different_exponentials_stay_apart():
    assert text("derivative(@e^(-2*a)-2*@e^(-a)+1,a)") == "2*ⅇ^(-a)-2*ⅇ^(-2*a)"


def test_a_negated_factor_gives_its_sign_to_the_product():
    assert text("(1-x)*y") == "-y*(x-1)"


# R6-B5: exact definite integrals


def test_an_exact_integral_ti_can_write_is_kept_with_its_logarithms_combined():
    shown = text("integral(1/(x^3+x+2),x,0,2)")
    assert "ln(9/2)/8" in shown
    assert "tan⁻¹" in shown


def test_a_long_exact_integral_is_still_a_decimal():
    assert text("f1(x):=3*x/(x^3+x+2)", "integral(pi*(f1(x))^2,x,0,2)") == "2.2880103"


def test_the_logarithm_of_a_fraction_stays_whole():
    assert texts("ln(9/2)", "ln(4)", "ln(1/2)") == ["ln(9/2)", "2*ln(2)", "-ln(2)"]


# R6-B7: tCollect, expand with a variable, and `|` after solve


def test_tcollect_multiplies_out_a_sum_of_squares_when_that_is_shorter():
    vector = "[5cos(t)-4cos(5t/2),5sin(t)-4sin(5t/2)]"
    assert text(f"tCollect(dotP({vector},{vector}))") == "41-40*cos(3*t/2)"
    assert text("tCollect(sin(x)*cos(x))") == "sin(2*x)/2"


def test_expand_with_a_variable_divides_a_quotient_out():
    assert text("expand((x^2+a)/(b*x+c),x)") == "x/b-c/b^2+(a*b^2+c^2)/(b^2*(b*x+c))"
    assert text("expand((x^2+1)/(x+1),x)") == "x-1+2/(x+1)"
    assert text("expand((x^2+a)/(b*x+c))") == "x^2/(b*x+c)+a/(b*x+c)"


def test_a_condition_on_the_solved_variable_is_not_put_into_the_answer():
    assert text("solve(x^2=4,x)|x=2") == "x=-2 or x=2"
    assert text("solve(x^2=a,x)|a=4") == "x=-2 or x=2"
    assert text("solve(x^2=4,x)|x>0") == "x=2"


# R6-B9, R6-D1: statistics and distributions


def test_a_frequency_of_zero_is_a_domain_error():
    session = Session(PRESETS["specialist"])
    result = session.eval("LinRegtTest {1,2,3,4,5},{2.1,3.9,6.2,7.8,10.1},0")
    assert result.error == "Domain error"


def test_matrix_form_gives_the_answer_and_the_value_before_it():
    assert text("invBinom(0.9,10,0.5,1)") == "[6,0.828125;7,0.9453125]"
    assert text("invBinomN(0.9,0.5,5,1)") == "[7,0.9375;8,0.85546875]"
    assert text("invBinom(0.9,10,0.5,0)") == "7"
