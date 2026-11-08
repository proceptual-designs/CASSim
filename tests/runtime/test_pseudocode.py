# Requirements traced here: FR-RUN-005, FR-PSE-004, FR-PSE-005, FR-PSE-006, FR-TRC-002, FR-SET-006
"""Pseudocode parser, interpreter and trace tables (M7b; FR-PSE-*, FR-TRC-*, FR-SET-*)."""

import random
from fractions import Fraction
from typing import Any

import pytest

from cassim.runtime.pseudocode import PRESETS, RunResult, Settings, parse, run, trace
from cassim.runtime.pseudocode.errors import PseudocodeSyntaxError
from cassim.runtime.pseudocode.interp import Interpreter
from cassim.runtime.pseudocode.lexer import tokenize

BISECTION = """\
define bisection(f(x), x, a, b, t)
  c ← (a+b)/2
  if f(a)×f(b) > 0 then
    print "Require f(a) and f(b) to have different signs"
  else
    while (b-a)/2 > t do
      if f(a)×f(c) < 0 then
        b ← c
      else
        a ← c
      end if
      c ← (a+b)/2
    end while
    print c
  end if
end

bisection(x^4+x-2, x, -2, -1, 0.2)
"""


def out(source: str, **settings: Any) -> list[str]:
    result = run(source, Settings(**settings), [])
    assert result.halt == "finished", result.error
    return result.output


def failure(source: str, **settings: Any) -> RunResult:
    result = run(source, Settings(**settings), [])
    assert result.halt != "finished"
    return result


# ------------------------------------------------------------------------------------- lexing


def test_scientific_notation_uses_capital_e_only() -> None:
    """Dialect section 3: lowercase `e` is never an exponent marker, so 2e3 is 2 × e3."""
    kinds = [(t.kind, t.text) for t in tokenize("1E-3 2e3")][:-2]
    assert kinds == [("NUMBER", "1E-3"), ("NUMBER", "2"), ("NAME", "e3")]


def test_superscripts_and_minus_spellings() -> None:
    assert out("print 2³ + 10⁻¹", number="auto") == ["81/10"]
    assert out("print 5 − 2 – 1") == ["2"]


# ------------------------------------------------------------------------------------ parsing


@pytest.mark.parametrize(
    "source",
    [
        "x ← 5\nprint x",
        "x <- 5\nprint x",
        "x := 5\nprint x",
        "x = 5\nprint x",
        "X ← 5\nPRINT X",
        "x ← 5\nOutput(x)",
    ],
)
def test_assignment_and_print_spellings(source: str) -> None:
    """FR-PSE-003: tolerant input."""
    assert out(source) == ["5"]


def test_equals_assignment_warns() -> None:
    program = parse("x = 5")
    assert [w.message for w in program.warnings] == ["'=' used to assign; treated as '←'"]


def test_print_items_without_commas_warn_once() -> None:
    program = parse('print "a" 1 "b"')
    assert len(program.warnings) == 1  # one note per line, not per juxtaposition
    assert out('x ← 3\nprint "x is" x "and" x+1') == ["x is 3 and 4"]


def test_missing_end_if_is_a_warning_closed_by_dedent() -> None:
    """Dialect section 5.3 (VCAA 2023 sample MCQ 6 has no EndIf)."""
    source = "n ← 1\nIf n > 0 Then\n  print 1\nprint 2\n"
    program = parse(source)
    assert [w.message for w in program.warnings] == ["missing 'end if' for the if on line 2"]
    assert out(source) == ["1", "2"]


def test_flat_indentation_does_not_close_blocks() -> None:
    """Indentation is advisory: end keywords decide when the body is not indented."""
    assert out("for i from 1 to 2\nprint i\nend for\nprint 9") == ["1", "2", "9"]


@pytest.mark.parametrize(
    ("source", "fragment"),
    [
        ("end if", "closes nothing"),
        ("while 1 < 2\nprint 1", "missing 'end while'"),
        ("repeat\nprint 1", "no 'until'"),
        ("print (1", "expected"),
        ('print "abc', "unterminated"),
    ],
)
def test_syntax_errors_name_the_problem(source: str, fragment: str) -> None:
    with pytest.raises(PseudocodeSyntaxError, match=fragment):
        parse(source)


def test_syntax_error_in_run_is_a_result_with_a_line() -> None:
    result = run("x ← 1\nend if")
    assert (result.halt, result.error_line) == ("error", 2)


def test_closers_for_all_loop_spellings() -> None:
    source = (
        "for i from 1 to 2 do\nprint i\nnext i\nwhile false\nendwhile\nrepeat 2 times\nendrepeat"
    )
    assert out(source) == ["1", "2"]


def test_only_parens_group_and_brackets_make_lists() -> None:
    assert out("print (1+2)*3") == ["9"]
    assert out("a ← [1, 2, 3]\nprint a") == ["[1, 2, 3]"]
    assert out("a ← [7]\nprint a, len(a)") == ["[7] 1"]
    assert out("a ← []\nprint len(a)") == ["0"]
    assert failure("print [1+2]*3").halt == "error"  # a list, not a grouping


def test_one_line_if() -> None:
    assert out("x ← 2\nif x > 1 then print 7\nprint 8") == ["7", "8"]


# ------------------------------------------------------------------------- numbers and settings


def test_integer_division_by_mode() -> None:
    """Dialect section 8: Approx gives reals, Auto and Exact keep rationals."""
    assert out("print 1/3", number="approx", display=6) == ["0.333333"]
    assert out("print 1/3", number="auto") == ["1/3"]
    assert out("print 4/2", number="auto") == ["2"]
    assert out("print 0.5 × 3/4", number="auto") == ["0.375"]
    assert out("print 0.5 × 3/4", number="exact") == ["3/8"]


def test_whole_reals_keep_a_point() -> None:
    assert out("print 5.0\nprint 5", display=6) == ["5.", "5"]
    assert out("print 4/2", number="approx") == ["2."]


def test_display_precision() -> None:
    assert out("print 22000/7", display=6) == ["3142.86"]
    assert out("print 0.1+0.2", display=6) == ["0.3"]
    assert out("print 0.1+0.2", display="full") == ["0.30000000000000004"]


def test_sqrt_of_a_perfect_square_is_exact() -> None:
    assert out("print sqrt(4)\nprint sqrt(1/4)", number="auto") == ["2", "1/2"]


def test_power_rules() -> None:
    assert out("print 2^10") == ["1024"]
    assert out("print 2^-1", number="approx") == ["0.5"]
    assert out("print 2^-1", number="auto") == ["1/2"]
    assert "not a real number" in (failure("print (-8)^(1/3)", number="auto").error or "")


def test_real_domain_rejects_roots_of_negatives() -> None:
    assert "negative" in (failure("print sqrt(-4)").error or "")
    assert out("print sqrt(-4)", complex_domain=True) == ["0.+2.ⅈ"]


def test_angle_mode() -> None:
    assert out("print sin(30)", angle="degree", display=6) == ["0.5"]
    assert out("print asin(0.5)", angle="degree", display=6) == ["30."]


def test_mod_div_floor_semantics() -> None:
    assert out("print -7 div 2\nprint -7 mod 3\nprint 7 % 3") == ["-4", "2", "1"]


def test_round_is_half_up() -> None:
    assert out("print round(2.5)\nprint round(-2.5)\nprint round(1.25, 1)") == ["3", "-3", "1.3"]


def test_chained_comparison_and_logic() -> None:
    assert out("x ← 0.5\nprint -1 < x < 1\nprint 1 < x < 2\nprint not (x > 1) and true") == [
        "TRUE",
        "FALSE",
        "TRUE",
    ]


def test_strings() -> None:
    assert out('s ← "ab" + "cd"\nprint s, len(s)\nprint s = "abcd"') == ["abcd 4", "TRUE"]


def test_implicit_multiplication_and_split_names() -> None:
    source = "a ← 2\nb ← 3\nprint 2a + 3b\nprint ab\nprint a(b+1)\nprint ab²"
    for preset in ("vcaa", "author"):
        result = run(source, Settings(), [], syntax=PRESETS[preset])
        assert result.output == ["13", "6", "8", "18"]
    # The default and strict presets do not split a name: `ab` must be written a*b.
    result = run(source, Settings(), [], syntax=PRESETS["default"])
    assert result.output == ["13"]
    assert "did you mean a*b?" in (result.error or "")
    strict = run("a ← 2\nb ← 3\nprint ab", Settings(), [], syntax=PRESETS["strict"])
    assert "did you mean a*b?" in (strict.error or "")


def test_euler_toggle() -> None:
    """FR-SET-008: `e` is Euler's number by default; the toggle can turn it off."""
    assert out("print 2e^0") == ["2."]
    assert out("e ← 5\nprint e") == ["5"]
    assert "e is not defined" in (failure("print 2e^1", euler_e=False).error or "")


# ------------------------------------------------------------------------------- functions


def test_expression_form_and_function_form_agree() -> None:
    """FR-PSE-002: both ways of passing a function."""
    expression = "define twice(f(x), x, v)\n  return f(f(v))\nend\nprint twice(x^2, x, 3)"
    first_class = (
        "define g(x)\n  return x^2\nend\n"
        "define twice(f, v)\n  return f(f(v))\nend\nprint twice(g, 3)"
    )
    assert out(expression) == out(first_class) == ["81"]


def test_variable_mismatch_names_both() -> None:
    result = failure("define h(f(x), x)\n  return f(1)\nend\nprint h(t^2, x)")
    assert result.error == "the expression for f uses t but its variable is x"
    assert result.error_line == 4


def test_assignment_inside_function_is_local_and_globals_are_readable() -> None:
    source = "x ← 10\ndefine f()\n  y ← x + 1\n  x ← 99\n  return y\nend\nprint f(), x"
    assert out(source) == ["11 10"]


def test_default_parameters_and_recursion() -> None:
    source = (
        "define fact(n, k = 1)\n  if n <= 1 then\n    return k\n  end if\n"
        "  return fact(n-1, k*n)\nend\nprint fact(5)"
    )
    assert out(source) == ["120"]


def test_function_by_assignment() -> None:
    assert out("P(x) ← x² + 1\nprint P(3)") == ["10"]


def test_function_without_return_has_no_value() -> None:
    result = failure("define f()\n  x ← 1\nend\ny ← f()")
    assert "no value" in (result.error or "")


def test_undefined_variable_suggests_a_close_name() -> None:
    result = failure("R ← 3\nprint r + right")
    assert result.error == "r is not defined, did you mean R?"
    assert result.error_line == 2


def test_division_by_zero_keeps_the_trace() -> None:
    result = failure("x ← 1\ny ← 5/(x-1)\nprint y")
    assert (result.error, result.error_line) == ("division by zero", 2)
    assert [s.kind for s in result.steps] == ["assign", "halt"]


# ------------------------------------------------------------------------------ run limits


def test_loop_limit_stops_with_a_steppable_trace() -> None:
    """FR-SET-009, FR-TRC-005."""
    result = failure("x ← 0\nwhile true\n  x ← x + 1\nend while", max_iterations=50)
    assert result.halt == "step_limit"
    assert "50 loop passes" in (result.error or "")
    assert result.steps[-1].kind == "halt"
    assert result.variables["x"] == 50


def test_default_run_limits() -> None:
    """FR-SET-009: 1,000 passes per loop, 20,000 recorded steps, recursion depth 100."""
    s = Settings()
    assert (s.max_iterations, s.max_events, s.max_depth) == (1_000, 20_000, 100)
    assert failure("x ← 0\nwhile true\n  x ← x + 1\nend while").variables["x"] == 1_000


def test_loop_limit_is_per_loop_not_across_loops() -> None:
    two = "for i from 1 to 600\n  x ← i\nend for\nfor j from 1 to 600\n  y ← j\nend for\nprint x, y"
    assert out(two, max_events=100_000) == ["600 600"]


def test_recursion_limit() -> None:
    result = failure("define f(n)\n  return f(n+1)\nend\nprint f(0)", max_depth=20)
    assert result.halt == "step_limit"
    assert "20 deep" in (result.error or "")


def test_event_cap_is_reported_not_silent() -> None:
    result = failure("for i from 1 to 100\n  x ← i\nend for", max_events=10)
    assert result.halt == "event_cap"


# ---------------------------------------------------------------------- lists, random, input


def test_lists_are_one_based_by_default() -> None:
    source = "a ← [10, 20, 30]\nappend 40 to a\na[1] ← 11\nprint a[1], a[4], len(a), sum(a)"
    assert out(source) == ["11 40 4 101"]
    assert out("a ← [10, 20]\nprint a[0]", index_base=0) == ["10"]
    assert "outside the list" in (failure("a ← [1, 2]\nprint a[3]").error or "")


def test_for_each() -> None:
    assert out("t ← 0\nfor each v in [1, 2, 3]\n  t ← t + v\nend for\nprint t") == ["6"]


def test_seeded_random_matches_cpython() -> None:
    """FR-PSE-007: the runtime reproduces CPython's seeded sequence."""
    rng = random.Random(42)
    want = [str(rng.randint(1, 6)) for _ in range(5)]
    source = "for i from 1 to 5\n  print randint(1, 6)\nend for"
    assert out(source, seed=42) == want
    assert out(source, seed=42) == out(source, seed=42)


def test_input_infers_numbers_and_text() -> None:
    result = run(
        "input a\ninput b\ninput c\nprint a + 1, b, c", Settings(number="auto"), ["2", "3/4", "hi"]
    )
    assert result.output == ["3 3/4 hi"]
    assert result.variables["b"] == Fraction(3, 4)
    assert run("input a", inputs=[]).error == "the program asked for input but none was given"


# ---------------------------------------------------------------------------------- the trace


def test_trace_step_back_is_a_cursor_not_a_rerun() -> None:
    """FR-TRC-001: the table at any cursor is a prefix of the full table."""
    settings = Settings(number="auto")
    result = Interpreter(parse(BISECTION), settings).run()
    full = trace.vertical(result, settings, max_depth=1)
    for cursor in (1, 4, 9):
        part = trace.vertical(result, settings, cursor=cursor, max_depth=1)
        assert part.rows == full.rows[:cursor]


def test_vertical_table_matches_the_authors_bisection_example() -> None:
    """trace-tables.md section 2: line order and the values that change."""
    settings = Settings(number="auto")
    result = Interpreter(parse(BISECTION), settings).run()
    table = trace.vertical(result, settings, max_depth=1)
    assert [row.line for row in table.rows] == [18, 2, 3, 6, 7, 10, 12, 6, 7, 8, 12, 6, 14]
    changes = [(row.line, row.cells) for row in table.rows if row.cells]
    assert changes == [
        (18, {"a": "−2", "b": "−1", "t": "0.2"}),
        (2, {"c": "−3/2"}),
        (10, {"a": "−3/2"}),
        (12, {"c": "−5/4"}),
        (8, {"b": "−5/4"}),
        (12, {"c": "−11/8"}),
    ]
    assert table.rows[3].calc == "(−1 − −2)/2 > 0.2 is true"
    assert table.rows[-1].calc == "-11/8"


def test_horizontal_table_matches_the_authors_desk_check() -> None:
    """trace-tables.md section 3: Init plus one column per pass, ticks, crosses and (skip)."""
    settings = Settings(number="auto")
    program = parse(BISECTION)
    result = Interpreter(program, settings).run()
    table = trace.horizontal(result, program, settings)
    assert table is not None
    assert table.columns == ["Init", "Loop 1", "Loop 2", "Loop 3"]
    by_code = {row.code: row.cells for row in table.rows}
    assert by_code["if f(a)×f(b) > 0 then"][0] == "12×−2 > 0 ❌"
    assert by_code["while (b-a)/2 > t do"][1:] == [
        "(−1 − −2)/2 > 0.2 ✔",
        "(−1 − −3/2)/2 > 0.2 ✔",
        "(−5/4 − −3/2)/2 > 0.2 ❌",
    ]
    assert by_code["b ← c"] == ["", "(skip)", "b ← −5/4", "(skip)"]
    assert by_code["a ← c"] == ["", "a ← −3/2", "(skip)", "(skip)"]
    assert by_code["print c"][3] == "-11/8"


def test_horizontal_layout_needs_exactly_one_unnested_loop() -> None:
    nested = "for i from 1 to 2\n  for j from 1 to 2\n    print i\n  end for\nend for"
    program = parse(nested)
    result = Interpreter(program, Settings()).run()
    assert not result.horizontal_eligible
    assert trace.horizontal(result, program, Settings()) is None


def test_trace_off_records_nothing_but_runs() -> None:
    result = run(BISECTION, Settings(number="auto"), trace=False)
    assert result.output == ["-11/8"]
    assert [s.kind for s in result.steps] == ["halt"]


def test_trace_cells_follow_the_settings() -> None:
    """FR-TRC-008: the same run shows fractions or decimals according to the number mode."""
    approx = Settings(number="approx", display=6)
    result = Interpreter(parse(BISECTION), approx).run()
    cells = [row.cells for row in trace.vertical(result, approx, max_depth=1).rows if row.cells]
    assert cells[1] == {"c": "−1.5"}
