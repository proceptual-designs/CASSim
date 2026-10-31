import pytest

from emcas.core.ast import (
    Assign,
    Binary,
    Call,
    Command,
    Compare,
    Convert,
    Define,
    Dms,
    Index,
    Line,
    ListLit,
    Matrix,
    Name,
    Number,
    Postfix,
    Store,
    String,
    Unary,
)
from emcas.core.errors import (
    MISSING_CLOSE_BRACE,
    MISSING_CLOSE_BRACKET,
    MISSING_CLOSE_PAREN,
    MISSING_OPEN_PAREN,
    SYNTAX,
    TISyntaxError,
)
from emcas.core.parser import parse, parse_expression

x, y, a, b = Name("x"), Name("y"), Name("a"), Name("b")
n1, n2, n3 = Number("1"), Number("2"), Number("3")


@pytest.mark.parametrize(
    ("text", "grouped"),
    [
        # Examples from the guide's EOS section
        ("4^3!", "4^(3!)"),
        ("2^3^2", "2^(3^2)"),
        ("-9^2", "-(9^2)"),
        ("-x^2", "-(x^2)"),
        ("4(1+2)", "4*(1+2)"),
        # Level order
        ("a+b*x", "a+(b*x)"),
        ("a&b*x", "(a&b)*x"),
        ("-a&b", "(-a)&b"),
        ("-a*b", "(-a)*b"),
        ("a+b=x", "(a+b)=x"),
        ("a=b and x=y", "(a=b) and (x=y)"),
        ("not a=b", "not (a=b)"),
        ("not a and b", "(not a) and b"),
        ("a and b or x", "(a and b) or x"),
        ("a or b xor x", "(a or b) xor x"),
        ("a xor b⇒x", "(a xor b)⇒x"),
        ("a⇒b⇔x", "(a⇒b)⇔x"),
        ("a⇔b|x", "(a⇔b)|x"),
        ("a+b|x=1", "(a+b)|(x=1)"),
        ("x^y!", "x^(y!)"),
        # Associativity and signs
        ("a-b-x", "(a-b)-x"),
        ("a/b/x", "(a/b)/x"),
        ("a.^b.^x", "a.^(b.^x)"),
        ("2^-1", "2^(-1)"),
        ("2^-3^2", "2^(-(3^2))"),
        ("2^-1*3", "(2^(-1))*3"),
        ("a*-b", "a*(-b)"),
        ("a--b", "a-(-b)"),
        # Implied multiplication has the strength of *
        ("2x", "2*x"),
        ("2x^2", "2*(x^2)"),
        ("1/2x", "(1/2)*x"),
        ("2^3x", "(2^3)*x"),
        ("-2x", "(-2)*x"),
        ("2π", "2*π"),
        ("2√(3)", "2*√(3)"),
        ("(x+1)(x-1)", "(x+1)*(x-1)"),
        ("2(x+1)", "2*(x+1)"),
        ("(x+1)2", "(x+1)*2"),
        ("2sin(x)", "2*sin(x)"),
        ("x y", "x*y"),
        ("sin(x)cos(x)", "sin(x)*cos(x)"),
        ("2[1,2]", "2*[1,2]"),
        ("{1,2}x", "{1,2}*x"),
        # Conversions apply to the whole entry
        ("5*exp(1)▶Rect", "(5*exp(1))▶Rect"),
        ("a+b@>Polar", "(a+b)▶Polar"),
        ("a@>Rad@>DD", "(a▶Rad)▶DD"),
        # Polar form
        ("2∠π/4+1", "2∠((π/4)+1)"),
        ("2@<π", "2∠π"),
    ],
)
def test_grouping(text, grouped):
    assert parse_expression(text) == parse_expression(grouped)


def test_name_then_parens_is_a_call():
    assert parse_expression("a(b+x)") == Call("a", (Binary("+", b, x),))
    assert parse_expression("2x(x-1)") == Binary("*", n2, Call("x", (Binary("-", x, n1),)))
    assert parse_expression("sin (x)") == Call("sin", (x,))


def test_call_forms():
    assert parse_expression("rand()") == Call("rand", ())
    assert parse_expression("lib\\fn(1,2)") == Call("lib\\fn", (n1, n2))
    assert parse_expression("√(2)") == Call("√", (n2,))
    assert parse_expression("list@>mat({1})") == Call("list▶mat", (ListLit((n1,)),))


def test_atoms():
    assert parse_expression('"hi"') == String("hi")
    assert parse_expression("30°30'") == Dms("30°30'")
    assert parse_expression("1.") == Number("1.")
    assert parse_expression("@n1") == Name("@n1")
    assert parse_expression("∞") == Name("∞")
    assert parse_expression("_m") == Name("_m")


def test_postfix_operators():
    assert parse_expression("5!") == Postfix("!", Number("5"))
    assert parse_expression("5!!") == Postfix("!", Postfix("!", Number("5")))
    assert parse_expression("30°") == Postfix("°", Number("30"))
    assert parse_expression("y''") == Postfix("'", Postfix("'", y))
    m = Matrix(((n1, n2),))
    assert parse_expression("[1,2]@t") == Postfix("ᵀ", m)


def test_relation_chain_stays_flat():
    assert parse_expression("0≤x<=2*π") == Compare(
        Number("0"), (("≤", x), ("≤", Binary("*", n2, Name("π"))))
    )


def test_parenthesised_relation_is_not_chained():
    assert parse_expression("(a=b)=x") == Compare(Compare(a, (("=", b),)), (("=", x),))


def test_lists_and_matrices():
    assert parse_expression("{}") == ListLit(())
    assert parse_expression("{1,{2}}") == ListLit((n1, ListLit((n2,))))
    assert parse_expression("[1,2;3,x]") == Matrix(((n1, n2), (n3, x)))
    assert parse_expression("[1;2]") == Matrix(((n1,), (n2,)))


def test_nested_matrix_spelling_flattens():
    assert parse_expression("[[1,2],[3,x]]") == Matrix(((n1, n2), (n3, x)))


def test_space_separated_row_from_display():
    assert parse_expression("[1 2 3]") == Matrix(((n1, n2, n3),))
    assert parse_expression("[1 2;3 x]") == Matrix(((n1, n2), (n3, x)))
    assert parse_expression("[√(2) ∠π/4 1]") == Matrix(
        (
            (
                Call("√", (n2,)),
                Unary("∠", Binary("/", Name("π"), Number("4"))),
                n1,
            ),
        )
    )


def test_spaces_mean_multiplication_again_inside_parentheses():
    assert parse_expression("[(a b)]") == Matrix(((Binary("*", a, b),),))
    assert parse_expression("[f(a b)]") == Matrix(((Call("f", (Binary("*", a, b),)),),))


def test_minus_in_a_row_stays_binary():
    assert parse_expression("[1 -2]") == Matrix(((Binary("-", n1, n2),),))


def test_subscripts():
    assert parse_expression("l[1]") == Index(Name("l"), (n1,))
    assert parse_expression("m[1,2]") == Index(Name("m"), (n1, n2))
    assert parse_expression("l[1][2]") == Index(Index(Name("l"), (n1,)), (n2,))


def test_convert_targets():
    assert parse_expression("x@>Base16") == Convert(x, Name("Base16"))
    assert parse_expression("x@>approxFraction(1)") == Convert(x, Call("approxFraction", (n1,)))


def test_indirection_binds_before_post_operators():
    assert parse_expression('#"x"!') == Postfix("!", Unary("#", String("x")))
    assert parse_expression("#(a&b)") == Unary("#", Binary("&", a, b))


def test_constraint_inside_arguments():
    assert parse_expression("f(x|x>0,1)") == Call(
        "f", (Binary("|", x, Compare(x, ((">", Number("0")),))), n1)
    )


def test_assignment():
    assert parse("x:=1") == Line((Assign(x, n1),))
    assert parse("f(x):=x^2") == Line((Assign(Call("f", (x,)), Binary("^", x, n2)),))
    assert parse("l[1]:=2") == Line((Assign(Index(Name("l"), (n1,)), n2),))


def test_store():
    assert parse("5→a") == Line((Store(Number("5"), a),))
    assert parse("a+1->f(x)") == Line((Store(Binary("+", a, n1), Call("f", (x,))),))


def test_define():
    assert parse("Define f(x)=x=1") == Line((Define(Call("f", (x,)), Compare(x, (("=", n1),))),))
    assert parse("define LibPub f(x)=x") == Line((Define(Call("f", (x,)), x, "LibPub"),))
    assert parse("Define LibPriv g(x)=x") == Line((Define(Call("g", (x,)), x, "LibPriv"),))


def test_commands():
    assert parse("SortA l") == Line((Command("SortA", (Name("l"),)),))
    assert parse("LinRegMx x,y,1") == Line((Command("LinRegMx", (x, y, n1)),))
    assert parse("ClearAZ") == Line((Command("ClearAZ", ()),))
    assert parse("onevar x") == Line((Command("OneVar", (x,)),))


def test_statements_split_on_colon():
    assert parse("OneVar x,1:stat.results") == Line(
        (Command("OneVar", (x, n1)), Name("stat.results"))
    )
    assert parse("1→a:2→b") == Line((Store(n1, a), Store(n2, b)))


def test_empty_statements_are_skipped():
    assert parse("") == Line(())
    assert parse(":a::") == Line((a,))


@pytest.mark.parametrize(
    ("text", "code"),
    [
        ("(1+2", MISSING_CLOSE_PAREN),
        ("f(1", MISSING_CLOSE_PAREN),
        ("1+2)", MISSING_OPEN_PAREN),
        ("{1,2", MISSING_CLOSE_BRACE),
        ("[1,2", MISSING_CLOSE_BRACKET),
        ("l[1", MISSING_CLOSE_BRACKET),
        ("√2", MISSING_OPEN_PAREN),
        ("", SYNTAX),
        ("1+", SYNTAX),
        ("*2", SYNTAX),
        ("()", SYNTAX),
        ("2 3", SYNTAX),
        ("1.2.3", SYNTAX),
        ("[]", SYNTAX),
        ("[1,]", SYNTAX),
        ("{1,}", SYNTAX),
        ("f(1,)", SYNTAX),
        ("l[]", SYNTAX),
        ("x@>", SYNTAX),
        ("x@>1", SYNTAX),
    ],
)
def test_expression_errors(text, code):
    with pytest.raises(TISyntaxError) as info:
        parse_expression(text)
    assert info.value.code == code


@pytest.mark.parametrize(
    "text",
    [
        "1:=2",
        "x+1:=2",
        "5→1",
        "5→a+b",
        "1→a→b",
        "Define x",
        "Define 1=2",
        "1+Disp",
        "(Define)",
        "a b:=1",
    ],
)
def test_statement_errors(text):
    with pytest.raises(TISyntaxError) as info:
        parse(text)
    assert info.value.code == SYNTAX


def test_error_position_points_at_the_problem():
    with pytest.raises(TISyntaxError) as info:
        parse("1+*2")
    assert info.value.pos == 2


@pytest.mark.parametrize(
    "text",
    [
        "(" * 60 + "1" + ")" * 60,
        "f(" * 60 + "1" + ")" * 60,
        "{" * 60 + "1" + "}" * 60,
        "[" * 60 + "1" + "]" * 60,
        "a[" * 60 + "1" + "]" * 60,
        "2^" * 60 + "2",
        "#" * 60 + "x",
        "-" * 60 + "1",
        "+".join("x" * 200),
        "*".join("x" * 200),
    ],
)
def test_deep_but_reasonable_entries_round_trip(text):
    tree = parse(text)
    assert parse(str(tree)) == tree


@pytest.mark.parametrize(
    "text",
    [
        "(" * 5000 + "1" + ")" * 5000,
        "f(" * 5000 + "1" + ")" * 5000,
        "{" * 5000 + "1" + "}" * 5000,
        "[" * 5000 + "1" + "]" * 5000,
        "2^" * 5000 + "2",
        "#" * 5000 + "x",
        "-" * 5000 + "1",
        "not " * 5000 + "x",
        "+".join("x" * 5000),
        "x" + "!" * 5000,
        "x" + "[1]" * 5000,
    ],
)
def test_excessive_depth_is_a_syntax_error_not_a_crash(text):
    with pytest.raises(TISyntaxError) as info:
        parse(text)
    assert info.value.code == SYNTAX


def test_long_data_list_is_not_limited():
    text = "{" + ",".join(["1.5"] * 5000) + "}"
    tree = parse(text)
    assert parse(str(tree)) == tree
