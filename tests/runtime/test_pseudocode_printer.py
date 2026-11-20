"""The printer and round trips (FR-SYN-005, FR-SYN-007).

FR-SYN-007: for every built-in preset and for generated valid syntax files, printing a program tree
in that file's style and parsing it again gives the same tree; every golden program survives
restyling under every built-in preset.
"""

from typing import Any

import pseudo_cases
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from cassim.runtime.pseudocode import (
    DEFAULT,
    PRESETS,
    PrintError,
    Syntax,
    SyntaxFileError,
    load_syntax,
    parse,
    print_expr,
    print_program,
    shape,
)
from cassim.runtime.pseudocode.tree import (
    Append,
    Assign,
    Binary,
    Break,
    Call,
    Compare,
    Constant,
    Define,
    Expr,
    ExprStmt,
    For,
    ForEach,
    If,
    Index,
    Input,
    ListLit,
    Name,
    Num,
    Param,
    Paren,
    Print,
    RepeatTimes,
    RepeatUntil,
    Return,
    Stmt,
    Str,
    Unary,
    While,
)

# The tuple case does not parse yet (FR-PSE-008, Could); the printer cannot be tested on it.
CASES = [c for c in pseudo_cases.CASES if c["id"] not in pseudo_cases.NOT_YET]
CASE_IDS = [c["id"] for c in CASES]
PRESET_NAMES = list(PRESETS)


def restyle(source: str, source_syntax: Syntax, target: Syntax) -> tuple[Any, Any]:
    """(shape of the original, shape after printing in `target` and parsing with `target`)."""
    tree = parse(source, source_syntax)
    again = parse(print_program(tree, target), target)
    return shape(tree.body), shape(again.body)


# --------------------------------------------------------------------------- golden programs


@pytest.mark.parametrize("preset", PRESET_NAMES)
@pytest.mark.parametrize("case", CASES, ids=CASE_IDS)
def test_golden_programs_survive_restyling(case: dict[str, Any], preset: str) -> None:
    """FR-SYN-007: every golden program keeps its tree under every built-in preset."""
    source_syntax = PRESETS[case.get("syntax", "default")]
    try:
        before, after = restyle(case["pseudocode"], source_syntax, PRESETS[preset])
    except PrintError as e:
        pytest.skip(f"{preset} cannot write this program: {e}")
    assert after == before


def test_only_strict_gives_up_on_golden_programs() -> None:
    """The tolerant presets write every golden program; only `strict` may refuse some."""
    for name in ("default", "vcaa", "author"):
        for case in CASES:
            tree = parse(case["pseudocode"], PRESETS[case.get("syntax", "default")])
            print_program(tree, PRESETS[name])


def test_printing_is_stable() -> None:
    """Printing, parsing and printing again gives the same text (no drift)."""
    for case in CASES:
        for preset in PRESET_NAMES:
            syn = PRESETS[preset]
            try:
                first = print_program(
                    parse(case["pseudocode"], PRESETS[case.get("syntax", "default")]), syn
                )
            except PrintError:
                continue
            assert print_program(parse(first, syn), syn) == first


# --------------------------------------------------------------------------- the emit section


SAMPLE = """\
x <- 3
for i from 1 to 5
  if i mod 2 = 0 then
    print i
  else if i > 3
    print "big"
  else
    print x * i
  end if
next i
"""


def test_default_style() -> None:
    out = print_program(parse(SAMPLE))
    assert out.splitlines() == [
        "x ← 3",
        "for i from 1 to 5",
        "  if i mod 2 = 0 then",
        "    print i",
        "  else if i > 3 then",
        '    print "big"',
        "  else",
        "    print x × i",
        "  end if",
        "end for",
    ]


def test_vcaa_style_uses_capitalised_keywords_and_run_together_terminators() -> None:
    out = print_program(parse(SAMPLE), PRESETS["vcaa"])
    assert out.splitlines()[1:3] == ["For i From 1 To 5", "  If i Mod 2 = 0 Then"]
    assert "  EndIf" in out.splitlines()
    assert out.splitlines()[-1] == "EndFor"


def test_ascii_symbols_and_emit_choices() -> None:
    syn = load_syntax(
        {"emit": {"symbols": "ascii", "indent": 4, "keyword_case": "UPPER", "if_then": "never"}}
    )
    out = print_program(parse("x ← 1 ≤ 2 ∧ 3 ≠ 4\nif x\n print x × 2\nend if"), syn)
    assert out.splitlines() == [
        "x <- 1 <= 2 AND 3 != 4",
        "IF x",
        "    PRINT x * 2",
        "END IF",
    ]


def test_superscripts_follow_the_syntax() -> None:
    tree = parse("y ← x² + a^-1")
    assert print_program(tree) == "y ← x² + a⁻¹\n"
    assert print_program(tree, load_syntax({"emit": {"symbols": "ascii"}})) == "y <- x^2 + a^-1\n"
    assert print_program(tree, PRESETS["strict"]) == "y ← x^2 + a^-1\n"


def test_explicit_constants_print_in_the_selected_symbol_style() -> None:
    tree = parse("print @e + @pi")
    assert print_program(tree) == "print ⅇ + π\n"
    assert print_program(tree, load_syntax({"emit": {"symbols": "ascii"}})) == "print @e + @pi\n"
    assert shape(parse(print_program(tree)).body) == shape(tree.body)
    assert shape(parse(print_program(tree, load_syntax({"emit": {"symbols": "ascii"}}))).body) == (
        shape(tree.body)
    )


def test_printer_never_writes_a_spelling_the_syntax_refuses() -> None:
    """Strict refuses `*`, `/`, `<-`, `=`, `endif`, `do` and `then`-less ifs; the output obeys."""
    src = "x <- 6 / 3 * 2\nwhile x > 0 do\n x <- x - 1\nwend\nif x = 0\n print x\nendif"
    out = print_program(parse(src), PRESETS["strict"])
    assert out.splitlines() == [
        "x ← 6 ÷ 3 × 2",
        "while x > 0",
        "  x ← x - 1",
        "end while",
        "if x = 0 then",
        "  print x",
        "end if",
    ]
    assert parse(out, PRESETS["strict"]).warnings == []


def test_terminator_choices_and_next_variable() -> None:
    syn = load_syntax({"emit": {"terminators": {"for": "next"}}})
    assert print_program(parse("for i from 1 to 2\nprint i\nnext"), syn).endswith("next\n")
    syn = load_syntax(
        {
            "constructs": {
                "for": {"terminators": {"end for": "no", "endfor": "no", "next": "no", "end": "no"}}
            },
            "emit": {"terminators": {"for": "end for"}},
        }
    )
    out = print_program(parse("for i from 1 to 2\nprint i\nend for"), DEFAULT)
    assert print_program(parse(out, DEFAULT), syn).splitlines()[-1] == "next i"


def test_define_ended_by_dedent_when_no_end_is_accepted() -> None:
    syn = load_syntax(
        {
            "constructs": {
                "define": {
                    "terminators": {
                        "end": "no", "end define": "no", "end function": "no", "dedent": "ok",
                    }
                }
            }
        }
    )  # fmt: skip
    tree = parse("define f(x)\n return x\nprint f(1)")
    out = print_program(tree, syn)
    assert out.splitlines() == ["define f(x)", "  return x", "print f(1)"]
    assert shape(parse(out, syn).body) == shape(tree.body)


def test_unwritable_things_are_refused_by_name() -> None:
    tree = parse("P(x) ← x + 1", PRESETS["default"])
    with pytest.raises(PrintError, match="by assignment"):
        print_program(tree, PRESETS["strict"])
    with pytest.raises(PrintError, match="quote"):
        print_program([ExprStmt(Str('a"”b'), 1)], DEFAULT)


@pytest.mark.parametrize(
    "bad",
    [
        {"emit": {"if_then": "sometimes"}},
        {"emit": {"times": "x"}},
        {"emit": {"print_parentheses": True}},
        {"emit": {"terminators": {"if": ""}}},
    ],
)
def test_emit_entries_are_validated(bad: dict[str, Any]) -> None:
    with pytest.raises(SyntaxFileError) as err:
        load_syntax(bad)
    assert err.value.problems[0].startswith("emit.")


# --------------------------------------------------------------------------- generated trees

NAMES = st.sampled_from(["x", "y", "n", "total", "a1", "pi"])
NUMS = st.sampled_from(["0", "1", "2", "10", "3.5", ".5", "2E3"])
CONSTANTS = st.sampled_from(["ⅇ", "π"])


def leaf() -> st.SearchStrategy[Expr]:
    return st.one_of(
        NUMS.map(Num),
        NAMES.map(Name),
        CONSTANTS.map(Constant),
        st.sampled_from(["", "hi", "a b"]).map(Str),
    )


def tame(e: Expr) -> bool:
    """Whether `e` can sit on either side of an implicit product."""
    return isinstance(e, Name | Paren | Call | Num) and not isinstance(e, Str)


@st.composite
def implicit_product(draw: st.DrawFn, sub: st.SearchStrategy[Expr]) -> Expr:
    left = draw(sub.filter(lambda e: isinstance(e, Num | Name | Paren)))
    right = draw(sub.filter(lambda e: isinstance(e, Name | Call | Paren | Num)))
    if (isinstance(left, Num) and isinstance(right, Num)) or (
        isinstance(left, Name) and isinstance(right, Paren)
    ):
        right = Name("k")
    return Binary("*", left, right, implicit=True)


def expressions() -> st.SearchStrategy[Expr]:
    def extend(sub: st.SearchStrategy[Expr]) -> st.SearchStrategy[Expr]:
        arith = st.sampled_from(["+", "-", "*", "/", "÷", "mod", "div", "^", "and", "or"])
        return st.one_of(
            st.builds(Binary, arith, sub, sub),
            implicit_product(sub),
            st.builds(Unary, st.sampled_from(["-", "not", "abs", "sqrt"]), sub),
            st.builds(
                Compare,
                sub,
                st.lists(
                    st.sampled_from(["=", "≠", "<", ">", "≤", "≥"]), min_size=1, max_size=2
                ).map(tuple),
                st.lists(sub, min_size=2, max_size=2).map(tuple),
            ).map(lambda c: Compare(c.first, c.ops, c.rest[: len(c.ops)])),
            st.builds(
                Call,
                st.sampled_from(["f", "g", "sqrt", "abs"]),
                st.lists(sub, max_size=2).map(tuple),
            ),
            st.builds(Index, NAMES.map(Name), sub),
            st.lists(sub, max_size=3).map(tuple).map(ListLit),
        )

    return st.recursive(leaf(), extend, max_leaves=6)


def run_expr_round_trip(e: Expr, syn: Syntax) -> None:
    try:
        text = print_expr(e, syn)
        stmt = parse(f"print {text}\n", syn).body[0]
    except PrintError:
        return
    assert isinstance(stmt, Print), text
    # A bare `print (a)` is read as print(a); only the item matters here.
    (item,) = stmt.items
    assert shape(item, parens=False) == shape(e, parens=False), text


@pytest.mark.parametrize("preset", PRESET_NAMES)
@settings(max_examples=150, suppress_health_check=[HealthCheck.too_slow], deadline=None)
@given(e=expressions())
def test_generated_expressions_round_trip(preset: str, e: Expr) -> None:
    syn = PRESETS[preset]
    # Pure-bar nesting and a leading abs inside a product are read differently; skip those shapes.
    run_expr_round_trip(e, syn)


# --------------------------------------------------------------------------- generated statements


def statements() -> st.SearchStrategy[Stmt]:
    expr = expressions()
    names = NAMES.map(Name)

    def block(sub: st.SearchStrategy[Stmt]) -> st.SearchStrategy[list[Stmt]]:
        return st.lists(sub, min_size=1, max_size=3)

    simple: st.SearchStrategy[Stmt] = st.one_of(
        st.builds(Assign, names, expr, st.just(1)),
        st.builds(Input, names, st.just(1)),
        st.builds(Print, st.lists(expr, min_size=1, max_size=3), st.just(1)),
        st.builds(Append, expr, names, st.just(1)),
        st.builds(Return, st.one_of(st.none(), expr), st.just(1)),
        st.just(Break(1)),
    )

    def extend(sub: st.SearchStrategy[Stmt]) -> st.SearchStrategy[Stmt]:
        branch = st.tuples(expr, block(sub), st.just(1))
        return st.one_of(
            st.builds(
                If,
                st.lists(branch, min_size=1, max_size=3),
                st.one_of(st.none(), block(sub)),
                st.just(1),
            ),
            st.builds(While, expr, block(sub), st.just(1)),
            st.builds(For, NAMES, expr, expr, st.one_of(st.none(), expr), block(sub), st.just(1)),
            st.builds(ForEach, NAMES, expr, block(sub), st.just(1)),
            st.builds(RepeatTimes, expr, block(sub), st.just(1)),
            st.builds(RepeatUntil, block(sub), expr, st.just(1)),
            st.builds(
                Define,
                st.sampled_from(["f", "g"]),
                st.lists(NAMES.map(Param), max_size=2).map(tuple),
                block(sub),
                st.just(1),
            ),
        )

    return st.recursive(simple, extend, max_leaves=5)


def comparable(body: list[Stmt]) -> Any:
    return shape(body, parens=False)


@pytest.mark.parametrize("preset", PRESET_NAMES)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow], deadline=None)
@given(body=st.lists(statements(), min_size=1, max_size=3))
def test_generated_programs_round_trip(preset: str, body: list[Stmt]) -> None:
    syn = PRESETS[preset]
    try:
        text = print_program(body, syn)
        again = parse(text, syn)
    except PrintError:
        return
    assert comparable(again.body) == comparable(body), text


# --------------------------------------------------------------------------- generated syntax files


EMIT = st.fixed_dictionaries(
    {
        "keyword_case": st.sampled_from(["lower", "UPPER", "Capitalised"]),
        "indent": st.integers(1, 8),
        "assign": st.sampled_from(["←", "<-", ":=", "="]),
        "times": st.sampled_from(["×", "*", "·"]),
        "divide": st.sampled_from(["÷", "/"]),
        "if_then": st.sampled_from(["always", "never"]),
        "while_do": st.sampled_from(["always", "never"]),
        "for_do": st.sampled_from(["always", "never"]),
        "print_parentheses": st.sampled_from(["always", "never"]),
        "symbols": st.sampled_from(["unicode", "ascii", "keep"]),
        "terminators": st.fixed_dictionaries(
            {
                "if": st.sampled_from(["end if", "endif", "EndIf"]),
                "while": st.sampled_from(["end while", "endwhile", "wend", "EndWhile"]),
                "for": st.sampled_from(["end for", "endfor", "next", "next <variable>"]),
                "repeat": st.sampled_from(["end repeat", "endrepeat"]),
                "define": st.sampled_from(["end", "end define", "end function"]),
            }
        ),
    }
)
POLICY = st.sampled_from(["required", "optional", "forbidden"])
MODE = st.sampled_from(["ok", "warn"])


@st.composite
def syntax_files(draw: st.DrawFn) -> Syntax:
    """A valid, generated syntax file: random emit section, random accepted-token policies."""
    data: dict[str, Any] = {
        "emit": draw(EMIT),
        "lexical": {"keywords_case_insensitive": draw(st.booleans())},
        "constructs": {
            "if": {"then": draw(POLICY)},
            "while": {"do": draw(POLICY)},
            "for": {"do": draw(POLICY)},
            "print": {"parentheses": draw(POLICY)},
            "define": {"colon_after_header": draw(POLICY)},
        },
    }
    if draw(st.booleans()):
        data["based_on"] = draw(st.sampled_from(PRESET_NAMES))
    return load_syntax(data)


@settings(max_examples=60, suppress_health_check=[HealthCheck.too_slow], deadline=None)
@given(syn=syntax_files(), body=st.lists(statements(), min_size=1, max_size=3))
def test_generated_syntax_files_round_trip(syn: Syntax, body: list[Stmt]) -> None:
    try:
        text = print_program(body, syn)
        again = parse(text, syn)
    except PrintError:
        return
    assert comparable(again.body) == comparable(body), text


def test_superscript_after_scientific_notation_is_a_power() -> None:
    """Found by the round-trip property: `2E3²` is 2E3 squared, not an exponent 3²."""
    tree = parse("y ← 2E3²")
    assert shape(tree.body) == shape(parse("y ← 2E3^2").body)
    assert print_program(tree) == "y ← 2E3²\n"
