# Requirements traced here: FR-SCOPE-001, FR-CAT-006
"""Variables, user functions, DelVar/ClearAZ and the `|` constraint (M1c)."""

import pytest

from cassim.core.format import to_latex
from cassim.core.session import Session, same_value
from cassim.core.settings import Angle, Settings
from cassim.core.values import Void


def run(*lines, settings=None):
    """Enter each line in one Session and return the text of the last result."""
    session = Session(settings)
    result = None
    for line in lines:
        result = session.eval(line)
        assert result.error is None, f"{line}: {result.error}"
    assert result is not None
    return result.text


def fails(*lines, settings=None):
    session = Session(settings)
    for line in lines[:-1]:
        assert session.eval(line).error is None
    return session.eval(lines[-1]).error


@pytest.mark.parametrize(
    ("lines", "text"),
    [
        (("k:=7",), "7"),
        (("k:=7", "k*2"), "14"),
        (("5→a", "a+1"), "6"),
        (("a:=1/3", "a"), "1/3"),
        (("x:={1,2,3}", "x"), "{1,2,3}"),
        (("m:=[1,2;3,4]", "m"), "[1,2;3,4]"),
        (("A:=2", "a"), "2"),  # names are case-insensitive
        (("a:=2:a^2",), "4"),  # the last statement of the line is the result
        (("a:=2", "a:=a+1", "a"), "3"),
        (("a:=x+1", "a"), "x+1"),  # a symbolic value is stored as it is
        (("a:=5", "b:=a^2", "a:=1", "b"), "25"),  # values are fixed when stored
        (("a:=3", "5+a→b", "b"), "8"),
    ],
)
def test_variables(lines, text):
    assert run(*lines) == text


def test_stored_value_is_finished_like_a_result():
    assert run("a:=0.1+0.2") == "0.3"
    assert run("a:=sqrt(8)", "a") == "2*√(2)"


def test_an_undefined_name_still_echoes():
    assert run("a:=2", "b") == "b"


@pytest.mark.parametrize(
    "line",
    ["pi:=3", "ⅇ:=1", "true:=1", "ans:=2", "5→pi", "Define sin(x)=x", "count(x):=x"],
)
def test_reserved_names_cannot_be_stored(line):
    assert "reserved" in fails(line)


@pytest.mark.parametrize(
    "line", ["count:={5,3,1,1}", "sin:=1", "MEAN:=2", "5→seqGen", "colDim:=1", "sech⁻¹:=1"]
)
def test_a_function_name_reads_as_a_call(line):
    """The handheld refuses `count:={5,3,1,1}` with "Missing (" (check 6, part J),
    for the Reference Guide's functions that CASSim has not built yet as well."""
    assert fails(line) == "Missing ("


def test_names_near_a_function_name_are_free():
    assert run("counts:={1,2}", "counts") == "{1,2}"
    assert run("d:=4", "d") == "4"


def test_ans_ignores_statements_that_print_done():
    assert run("2+3", "f(x):=x^2", "ans*2") == "10"
    assert run("2+3", "a:=7", "ans*2") == "14"
    assert run("2+3", "delVar a", "ans*2") == "10"


@pytest.mark.parametrize(
    ("lines", "text"),
    [
        (("f(x):=x^2",), "Done"),
        (("Define f(x)=x^2",), "Done"),
        (("Define a=5",), "Done"),
        (("f(x):=x^2", "f(3)"), "9"),
        (("Define f(x)=x^2", "f(3)"), "9"),
        (("f(x):=x^2", "F(3)"), "9"),
        (("f(x):=x^2", "f(x)"), "x^2"),
        (("g(x,y):=x*y+1", "g(2,3)"), "7"),
        (("g(x,y):=x-y", "g(y,x)"), "-x+y"),  # parameters do not capture the caller's names
        (("f(x):=x^2", "f({1,2,3})"), "{1,4,9}"),
        (("f(x):=x^2", "f(x):=x^3", "f(3)"), "27"),  # redefining replaces
        (("a:=2", "f(x):=a*x", "f(5)"), "10"),  # globals are read at the call
        (("a:=2", "f(x):=a*x", "a:=3", "f(5)"), "15"),
        (("f(x):=x^2", "g(x):=f(x)+1", "g(3)"), "10"),
        (("f(x):=x^2", "f(f(3))"), "81"),
        (("f(x):=y", "y:=4", "f(1)"), "4"),
        (("f(x):=x", "x:=9", "f(2)"), "2"),  # a parameter hides a variable of the same name
        (("f(x):=x^2", "x:=3", "f(2)"), "4"),
        (("f(x):=0.1+0.2", "f(1)"), "0.3"),
    ],
)
def test_functions(lines, text):
    assert run(*lines) == text


def test_a_symbolic_argument_is_substituted_into_the_body():
    session = Session()
    session.eval("g(x):=x^2-3*x")
    got = session.eval("g(a+1)").value
    wanted = Session().eval("(a-2)*(a+1)").value
    assert got is not None
    assert wanted is not None
    assert same_value(got, wanted)


def test_define_is_done_and_not_a_number():
    session = Session()
    result = session.eval("Define f(x)=x")
    assert result.value == Void()
    assert result.text == "Done"
    assert to_latex(Void()) == r"\text{Done}"


def test_function_argument_counts():
    assert fails("f(x):=x", "f(1,2)") == "Too many arguments"
    assert fails("f(x,y):=x", "f(1)") == "Too few arguments"


@pytest.mark.parametrize("line", ["f(x,x):=x", "f(2):=x", "f(x+1):=x"])
def test_bad_parameter_lists_are_syntax_errors(line):
    assert fails(line) == "Syntax error"


def test_runaway_recursion_is_an_error_not_a_crash():
    assert fails("f(n):=f(n+1)", "f(0)") == "Recursion is too deep"
    assert fails("f(n):=g(n)", "g(n):=f(n)", "f(0)") == "Recursion is too deep"
    # and the Session still works afterwards
    session = Session()
    session.eval("f(n):=f(n)")
    assert session.eval("f(1)").error is not None
    assert session.eval("2+2").text == "4"


def test_a_call_that_fails_leaves_no_binding_behind():
    session = Session()
    session.eval("f(x):=x^2")
    assert session.eval("f(1,2)").error is not None
    assert session.eval("x").text == "x"


def test_del_var_removes_variables_and_functions():
    assert run("a:=5", "a^2+1", "delVar a", "a^2") == "a^2"
    assert run("f(x):=x^2", "delVar f", "f(3)") == "f(3)"
    assert run("a:=1", "b:=2", "DelVar a,b", "a+b") == "a+b"
    assert run("a:=1", "delVar a") == "Done"
    assert run("delVar nothing") == "Done"


def test_del_var_needs_names():
    assert fails("delVar 5") == "Syntax error"


def test_clear_az_removes_single_letters_only():
    assert run("a:=1", "z:=2", "ab:=3", "f(x):=x", "ClearAZ", "a+z") == "a+z"
    assert run("a:=1", "ab:=3", "ClearAZ", "ab") == "3"
    assert run("f(x):=x", "ClearAZ", "f(3)") == "f(3)"


def test_new_problem_clears_variables_and_functions():
    session = Session()
    session.eval("a:=5")
    session.eval("f(x):=x^2")
    session.new_problem()
    assert session.eval("a").text == "a"
    assert session.eval("f(3)").text == "f(3)"


def test_variables_follow_the_mode_of_the_line_that_reads_them():
    degree = Settings(angle=Angle.DEGREE)
    assert run("x:=30", "sin(x)", settings=degree) == "1/2"
    assert run("sin(x)", settings=degree) == "sin(x)"


@pytest.mark.parametrize(
    ("lines", "text"),
    [
        (("x^2+1|x=3",), "10"),
        (("x^2|x=3",), "9"),
        (("x^2+y|x=2 and y=1",), "5"),
        (("x:=5", "x^2|x=3"), "9"),  # the constraint wins over the stored value
        (("x:=5", "x^2|x=3", "x"), "5"),  # and does not outlast the entry
        (("f(x):=x^2+1", "f(x)|x=2"), "5"),
        (("x*y|x=2",), "2*y"),
        (("x^2|X=3",), "9"),
        (("x+1|x=y+1",), "y+2"),
    ],
)
def test_equality_constraint(lines, text):
    assert run(*lines) == text


def test_constraint_applies_in_degree_mode():
    assert run("sin(x)|x=30", settings=Settings(angle=Angle.DEGREE)) == "1/2"


@pytest.mark.parametrize("line", ["x^2|x>0", "x^2|0<x<2", "x^2|x=1 or x=2", "x^2|x>0 and x<3"])
def test_a_condition_nothing_uses_leaves_the_result_alone(line):
    assert run(line) == "x^2"


@pytest.mark.parametrize("line", ["Define LibPub f(x)=x", "l[1]:=5"])
def test_unsupported_forms_say_so(line):
    assert "Not implemented yet" in fails(line)
