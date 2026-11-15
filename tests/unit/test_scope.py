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
    assert fails(line) == "Invalid variable or function name"


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
    assert fails("f(n):=f(n+1)", "f(0)") == "Recursion too deep"
    assert fails("f(n):=g(n)", "g(n):=f(n)", "f(0)") == "Recursion too deep"
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


@pytest.mark.parametrize("line", ["Define LibPub f(x)=x", "{1,2}[1]:=5"])
def test_unsupported_forms_say_so(line):
    assert "Not implemented yet" in fails(line)


# Indexed store, emulator check 6 G7 (slice 3a: a sheet column linked to `xs` takes these).
@pytest.mark.parametrize(
    ("lines", "text"),
    [
        (("xs:={1,2,3}", "xs[2]:=20"), "20"),
        (("xs:={1,2,3}", "xs[2]:=20", "xs"), "{1,20,3}"),
        (("xs:={1,2,3}", "7→xs[1]", "xs"), "{7,2,3}"),
        (("xs:={1,2,3}", "xs[4]:=9", "xs"), "{1,2,3,9}"),  # one past the end appends
        (("xs:={1,2,3}", "xs[1+1]:=x^2", "xs"), "{1,x^2,3}"),
        (("XS:={1,2}", "xs[1]:=5", "Xs"), "{5,2}"),
        (("new[1]:=4", "new"), "{4}"),
    ],
)
def test_indexed_store(lines, text):
    assert run(*lines) == text


@pytest.mark.parametrize(
    ("lines", "message"),
    [
        (("xs:={1,2,3}", "xs[5]:=5"), "Dimension error"),
        (("xs:={1,2,3}", "xs[0]:=5"), "Dimension error"),
        (("xs:={1,2,3}", "xs[1.5]:=5"), "Domain error"),
        # Emulator check 6, S13: a list into an element, and an element of a number.
        (("xs:={1,2,3}", "xs[1]:={4,5}"), "Domain error"),
        (("k:=5", "k[1]:=2"), "Dimension error"),
        (("sin[1]:=2",), "Missing ("),
    ],
)
def test_indexed_store_errors(lines, message):
    assert message in fails(*lines)


def test_a_failed_indexed_store_leaves_the_list():
    session = Session()
    session.eval("xs:={1,2,3}")
    session.eval("xs[5]:=5")
    assert session.eval("xs").text == "{1,2,3}"


def test_indexed_store_raises_the_revision():
    session = Session()
    session.eval("xs:={1,2,3}")
    before = session.revision_of("xs")
    session.eval("xs[1]:=9")
    assert session.revision_of("xs") > before


def test_calling_a_variable_that_is_not_a_function():
    """Emulator check 6, C5: `a:=5` then `a(2)` is an error, not 10."""
    assert fails("a:=5", "a(2)") == "Name is not a function"
    assert run("b(2)") == "b(2)"


@pytest.mark.parametrize(
    ("line", "shown"),
    [
        # Emulator check 6, part B.
        ("mean({})", "undef"),
        ("round(2.5)", "2.5"),
        ("2 xor 3", "1"),
        ("true xor false", "true"),
        ("a!", "a!"),
        ("a!=b", "a!=b"),
        ("2+3▶Rad", "5ʳ"),
    ],
)
def test_check6_part_b_results(line, shown):
    assert run(line) == shown


def test_a_conversion_ends_the_entry():
    assert fails("2+3▶Rad+4") == "Syntax error"


def test_check6_run4_results():
    """Emulator check 6 run 4: category rows (S9), empty loan arguments and decimal zeros
    (D19), and `ⅇ` in the logistic RegEqn (D26)."""
    data = 'OneVar {2,4,4,4,5,5,7,9},1,{"a","b","a","c","b","a","c","a"},{"a"}'
    assert run(data, "stat.n") == "4."
    assert run(data, "stat.SSX") == "26."
    table = run("amortTbl(3,12,5,5000,,0,12,12,0,4)")
    assert table.startswith("[0,0.,0.,5000.;1,-20.8333,-407.2041,4592.7959;")
    assert fails("f(1,)") == "Syntax error"
    data = "{1,2,3,4,5,6,7,8},{2.1,3.9,6.2,7.8,10.1,12.2,13.8,16.1}"
    assert "ⅇ" in run(f"Logistic {data}", "stat.RegEqn(x)")  # a function (run 4, S3)
