"""Built-in functions and commands (M1d slice 1): elementary, algebra, lists, matrices, `when`."""

import pytest

from cassim.core.session import Session, same_value
from cassim.core.settings import Angle, CasMode, Settings

DEGREE = Settings(angle=Angle.DEGREE)
GRADIAN = Settings(angle=Angle.GRADIAN)
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


def same(line, wanted, settings=None):
    """The value of `line` equals the value of `wanted`, which is read in Auto mode."""
    got = run(line, settings=settings).value
    expected = run(wanted).value
    assert got is not None
    assert expected is not None
    assert same_value(got, expected), f"{line} gave {text(line, settings=settings)}"


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("sec(pi/3)", "2"),
        ("csc(pi/6)", "2"),
        ("cot(pi/4)", "1"),
        ("sinh(ln(2))", "3/4"),
        ("cosh(0)", "1"),
        ("tanh(0)", "0"),
        ("arcsin(1/2)", "pi/6"),
        ("arcsin(-1)", "-pi/2"),
        ("arccos(-1/2)", "2*pi/3"),
        ("arctan(1)", "pi/4"),
        ("abs(3+4*@i)", "5"),
        ("abs(-3)", "3"),
        ("conj(3+4*@i)", "3-4*@i"),
        ("real(3+4*@i)", "3"),
        ("imag(3+4*@i)", "4"),
        ("angle(1+@i)", "pi/4"),
        ("sign(-3)", "-1"),
        ("floor(-2.5)", "-3"),
        ("int(-2.5)", "-3"),
        ("ceiling(2.3)", "3"),
        ("iPart(-7/3)", "-2"),
        ("fPart(-7/3)", "-1/3"),
        ("round(3.14159,2)", "3.14"),
        ("round(-2.5)", "-3"),
        ("log(1000)", "3"),
        ("log(8,2)", "3"),
        ("exact(0.75)", "3/4"),
        ("nPr(6,2)", "30"),
        ("nCr(10,3)", "120"),
        ("gcd(12,18)", "6"),
        ("lcm(12,18)", "36"),
        ("mod(17,5)", "2"),
        ("sin({0,pi/2})", "{0,1}"),
        ("abs({-1,2,-3})", "{1,2,3}"),
    ],
)
def test_elementary(line, wanted):
    same(line, wanted)


def test_symbolic_results_print_as_ti_does():
    assert text("abs(x-1)") == "abs(x-1)"
    assert text("arcsin(x)") == "sin⁻¹(x)"
    assert text("log(7)") == "ln(7)/ln(10)"
    assert text("arcsinh(1)") == "sinh⁻¹(1)"
    assert text("arcsinh(0)") == "0"


@pytest.mark.parametrize(
    ("line", "settings", "wanted"),
    [
        ("arcsin(1/2)", DEGREE, "30"),
        ("arccos(0)", DEGREE, "90"),
        ("arcsin(1)", GRADIAN, "100"),
        ("arctan(1)", GRADIAN, "50"),
        ("sin(30)", DEGREE, "1/2"),
        ("sec(60)", DEGREE, "2"),
        ("arcsin(0.5)", DEGREE, "30."),
        ("sinh(0)", DEGREE, "0"),  # hyperbolic functions take no angle
    ],
)
def test_angle_mode(line, settings, wanted):
    same(line, wanted, settings)


def test_argument_counts_are_checked():
    assert error("sin()") == "Too few arguments"
    assert error("sin(1,2)") == "Too many arguments"
    assert error("round(1,2,3)") == "Too many arguments"
    assert error("nPr(5)") == "Too few arguments"
    assert error("expand()") == "Too few arguments"


def test_round_places_must_be_an_integer():
    assert error("round(1.234,x)") == "Domain error"
    assert error("round(x)") == "Data type"


@pytest.mark.parametrize("line", ["expand((x+1)^2)", "exact(0.5)"])
def test_cas_only_functions_are_refused_in_cas_off(line):
    assert "restricted" in error(line, settings=CAS_OFF)


def test_when_chooses_a_branch_and_runs_only_that_one():
    session = Session()
    session.eval("f(x):=when(x<0,-x,x^2)")
    assert session.eval("f(-2)").text == "2"
    assert session.eval("f(3)").text == "9"
    assert text("when(1>2,5)") == "undef"
    assert text("when(1<2,5,1/0)") == "5"  # the other branch is never run
    assert text("when(x<0,-x,x)") == "when(x<0,-x,x)"  # undecided stays as it is
    assert text("when(x<0,1,2,3)") == "3"


def test_recursive_definition_ends_through_when():
    session = Session()
    session.eval("u(n):=when(n=1,2,u(n-1)+3)")
    assert session.eval("u(5)").text == "14"
    assert session.eval("u(1)").text == "2"


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("seq(n^2,n,1,5)", "{1,4,9,16,25}"),
        ("seq(2^k,k,0,4)", "{1,2,4,8,16}"),
        ("seq(n,n,5,1,-2)", "{5,3,1}"),
        ("seq(n,n,1,10,4)", "{1,5,9}"),
        ("seq(n,n,1,0)", "{}"),
        ("seq(3+4*(n-1),n,1,5)", "{3,7,11,15,19}"),
        ("sum({1,2,3})", "6"),
        ("sum({1,2,3,4},2,3)", "5"),
        ("sum(seq(n,n,1,100))", "5050"),
        ("sum(seq(2*k-1,k,1,10))", "100"),
        ("sum(seq(1/(k*(k+1)),k,1,10))", "10/11"),
        ("product({1,2,3,4})", "24"),
        ("max({1,5,3})", "5"),
        ("min({4,2,8})", "2"),
        ("max(3,7)", "7"),
        ("mean({1,2,3,4})", "5/2"),
        ("median({1,2,3,4,10})", "3"),
        ("median({1,2,3,4})", "5/2"),
        ("stDevSamp({2,4,4,4,5,5,7,9})", "4*sqrt(14)/7"),
        ("stDevPop({2,4,4,4,5,5,7,9})", "2"),
        ("varSamp({2,4,4,4,5,5,7,9})", "32/7"),
        ("varPop({2,4,4,4,5,5,7,9})", "4"),
        ("cumulativeSum({1,2,3})", "{1,3,6}"),
        ("dim({1,2,3})", "3"),
        ("dim([1,2,3;4,5,6])", "{2,3}"),
        ("mean({0.5,1.5})", "1."),
    ],
)
def test_lists(line, wanted):
    same(line, wanted)


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("seq(x,3,1,5)", "Syntax error"),
        ("seq(n,n,1,10,0)", "Domain error"),
        ("seq(n,n,1,x)", "Data type"),
        ("seq(n,n,1,1ᴇ9)", "Memory"),
        ("sum({1,2,3},4)", "Domain error"),
        ("sum(5)", "Data type"),
        ("mean({})", "Domain error"),
        ("stDevSamp({1})", "Domain error"),
        ("dim(5)", "Data type"),
    ],
)
def test_list_errors(line, message):
    assert error(line) == message


def test_seq_index_does_not_leak_and_sees_variables():
    assert text("a:=2", "seq(a*n,n,1,3)") == "{2,4,6}"
    assert text("seq(n,n,1,3)", "n") == "n"
    assert text("n:=7", "seq(n,n,1,3)", "n") == "7"


def test_seq_inside_a_function_body():
    assert text("f(m):=seq(k^2,k,1,m)", "f(3)") == "{1,4,9}"


def test_sorting_a_stored_list():
    assert text("l:={3,1,2}", "SortA l", "l") == "{1,2,3}"
    assert text("l:={3,1,2}", "SortD l", "l") == "{3,2,1}"
    assert text("l:={3,1,2}", "SortA l") == "Done"


def test_sorting_reorders_the_other_lists_to_match():
    assert text("a:={3,1,2}", "b:={10,20,30}", "SortA a,b", "b") == "{20,30,10}"
    assert text("a:={3,1,2}", "b:={10,20,30}", "SortD a,b", "b") == "{10,30,20}"
    assert error("a:={3,1,2}", "b:={1,2}", "SortA a,b") == "Dimension mismatch"


def test_sorting_needs_a_variable_holding_a_list():
    assert error("SortA {3,1,2}") == "Argument must be a variable name"
    assert error("SortA nothing") == "Data type"
    assert error("a:=5", "SortA a") == "Data type"
    assert error("SortA") == "Too few arguments"


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("det([1,2;3,4])", "-2"),
        ("det([2,1;1,3])", "5"),
        ("det([[1,2,3],[4,5,6],[7,8,10]])", "-3"),
        ("identity(2)", "[1,0;0,1]"),
        ("[1,2;3,4]^-1", "[-2,1;3/2,-1/2]"),
        ("[[1,2,3],[4,5,6],[7,8,10]]^(-1)", "[[-2/3,-4/3,1],[-2/3,11/3,-2],[1,-2,1]]"),
        ("[1,2;3,4]^2", "[7,10;15,22]"),
        ("[1,2;3,4]^0", "[1,0;0,1]"),
        ("rref([1,2,3;4,5,6])", "[1,0,-1;0,1,2]"),
        ("rref([[1,2,3,4],[2,5,7,9],[1,0,1,2]])", "[[1,0,1,2],[0,1,1,1],[0,0,0,0]]"),
        ("simult([1,2;3,4],[5;6])", "[-4;9/2]"),
        ("augment([1,2;3,4],[5;6])", "[1,2,5;3,4,6]"),
        ("dotP([1,2,3],[4,5,6])", "32"),
        ("dotP({1,2,3},{4,5,6})", "32"),
        ("crossP([1,0,0],[0,1,0])", "[0,0,1]"),
        ("crossP([1,2,3],[4,5,6])", "[-3,6,-3]"),
        ("crossP({1,0,0},{0,1,0})", "{0,0,1}"),
        ("crossP([1,0],[0,1])", "[0,0,1]"),
        ("norm([3,4])", "5"),
        ("norm([1,2;3,4])", "sqrt(30)"),
        ("unitV([3,4])", "[3/5,4/5]"),
        ("[1,2;3,4]*[0,1;1,0]", "[2,1;4,3]"),
    ],
)
def test_matrices_and_vectors(line, wanted):
    same(line, wanted)


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("[1,2;2,4]^-1", "Singular matrix"),
        ("[1,2,3]^2", "Dimension mismatch"),
        ("[1,2;3,4]^(1/2)", "Domain error"),
        ("det([1,2,3;4,5,6])", "Dimension mismatch"),
        ("dotP([1,2],[1,2,3])", "Dimension mismatch"),
        ("crossP([1,2,3,4],[1,2,3,4])", "Dimension mismatch"),
        ("simult([1,2;2,4],[1;2])", "Singular matrix"),
        ("simult([1,2;3,4],[1;2;3])", "Dimension mismatch"),
        ("augment([1,2;3,4],[1,2,3])", "Dimension mismatch"),
        ("identity(0)", "Domain error"),
        ("unitV([0,0])", "Domain error"),
        ("det(5)", "Data type"),
    ],
)
def test_matrix_errors(line, message):
    assert error(line) == message


def test_a_name_that_is_not_a_function_echoes_even_with_a_list_argument():
    assert text("transpose([1,2;3,4])") == "transpose([1,2;3,4])"
    assert text("stdDev({2,4,4,4,5,5,7,9})") == "stddev({2,4,4,4,5,5,7,9})"
    assert text("sort({3,1,2})") == "sort({3,1,2})"


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("expand((x+1)^3)", "x^3+3*x^2+3*x+1"),
        ("expand((x-2)*(x-3))", "x^2-5*x+6"),
        ("factor(x^4-1)", "(x-1)*(x+1)*(x^2+1)"),
        ("factor(x^4-1,x)", "(x-1)*(x+1)*(x^2+1)"),
        ("factor(x^3-8)", "(x-2)*(x^2+2*x+4)"),
        ("propFrac((x^2+1)/(x-1))", "2/(x-1)+x+1"),
        ("comDenom(1/x+1/(x+1))", "(2*x+1)/(x^2+x)"),
    ],
)
def test_algebra(line, wanted):
    same(line, wanted)


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("remain(-7,3)", "-1"),
        ("remain(7,-3)", "1"),
        ("remain(7.5,2)", "1.5"),
        ("left({1,2,3,4},2)", "{1,2}"),
        ("right({1,2,3,4},3)", "{2,3,4}"),
        ("left({1,2},5)", "{1,2}"),
        ("subMat([1,2,3;4,5,6;7,8,9],2,2)", "[5,6;8,9]"),
        ("subMat([1,2,3;4,5,6;7,8,9],2,1,3,2)", "[4,5;7,8]"),
        ("subMat([1,2;3,4])", "[1,2;3,4]"),
        ("avgRC(x^2,x=1,0.5)", "5/2"),
        ("avgRC(x^2,x=1)", "2001/1000"),
    ],
)
def test_small_commands(line, wanted):
    same(line, wanted)


def test_strings_and_primes_and_small_command_errors():
    assert text('left("hello",2)') == '"he"'
    assert text('right("hello",3)') == '"llo"'
    assert text('right("hello")') == '"hello"'
    assert text("isPrime(97)") == "true"
    assert text("isPrime(91)") == "false"
    assert error("isPrime(2.5)") == "Domain error"
    assert error("left({1,2},-1)") == "Domain error"
    assert error("subMat([1,2;3,4],3)") == "Domain error"
    assert error("subMat([1,2;3,4],1,1,3,3)") == "Domain error"
    assert error("subMat([1,2;3,4],x)") == "Domain error"


def test_avg_rc_takes_the_value_the_variable_already_has():
    assert text("x:=3", "avgRC(x^2,x,1)") == "7"
