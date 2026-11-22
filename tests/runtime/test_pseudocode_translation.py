"""Python/pseudocode translation tests (FR-XLT-001 to FR-XLT-006)."""

import ast
from io import StringIO

import pytest

from cassim.runtime.pseudocode import (
    TRANSLATION_MARKER,
    TranslationError,
    parse,
    pseudocode_to_python,
    python_to_pseudocode,
    run,
    shape,
)
from cassim.runtime.pseudocode.settings import Settings
from cassim.runtime.pseudocode.to_python import pseudocode_to_python as _to_python
from cassim.runtime.pseudocode.tree import Binary, If, Name, Num, Program


def same_program(before: str, after: str) -> bool:
    return shape(parse(before).body, parens=False) == shape(parse(after).body, parens=False)


def test_round_trip_supported_program() -> None:
    """FR-XLT-004 and FR-XLT-005: a complete program survives both converters."""
    source = """\
items ← [1, 2, 3]
define total(a, n)
  s ← 0
  for i from 1 to n
    s ← s + a[i]
  end for
  return s
end
input value
if value ≥ 0 and value != 2 then
  print total(items, 3), value
else
  print "negative"
end if
"""
    translated = pseudocode_to_python(source)
    assert same_program(source, python_to_pseudocode(translated))
    compile(translated, "<translated>", "exec")


def test_indexes_are_converted_between_one_and_zero_based() -> None:
    source = "x ← values[3]\nvalues[i + 1] ← x\n"
    python = pseudocode_to_python(source)
    tree = ast.parse(python)
    assert ast.unparse(tree.body[-2]) == "x = values[2]"  # constants fold
    assert ast.unparse(tree.body[-1]) == "values[i] = x"

    pseudocode = python_to_pseudocode("x = values[i]\nvalues[j] = x\n")
    assert pseudocode == "x ← values[i + 1]\nvalues[j + 1] ← x\n"


def test_python_while_and_for_function_print_and_input_forms() -> None:
    source = """\
def scale(items, n=2):
    result = []
    for i in range(n):
        result = result + [items[i]]
    return result

value = input()
while value != "done":
    print(value, scale([1, 2], 2))
    break
"""
    expected = """\
define scale(items, n = 2)
  result ← []
  for i from 1 to n
    result ← result + [items[i]]
  end for
  return result
end

input value
while value ≠ "done" do
  print value, scale([1, 2], 2)
  break
end while
"""
    assert python_to_pseudocode(source) == expected


def test_repeat_until_and_python_break_pattern_round_trip() -> None:
    source = "repeat\n  x ← x + 1\nuntil x > 3\n"
    translated = pseudocode_to_python(source)
    assert "while True:" in translated
    assert "if x > 3:\n        break" in translated
    assert same_program(source, python_to_pseudocode(translated))

    python = """\
while True:
    x = x + 1
    if x > 3:
        break
"""
    assert python_to_pseudocode(python) == "repeat\n  x ← x + 1\nuntil x > 3\n"


@pytest.mark.parametrize(
    ("source", "line", "construct"),
    [
        ("x = 1\nclass Thing:\n    pass\n", 2, "class definition"),
        ("value = (x for x in [1, 2])\n", 1, "GeneratorExp"),
        ("x = {'a': 1}\n", 1, "dict"),
        ("while True:\n    x = 1\n    break\n", 3, "while True"),
    ],
)
def test_unsupported_python_is_named_with_its_line(source: str, line: int, construct: str) -> None:
    """FR-XLT-003: unsupported Python is refused, never approximated."""
    with pytest.raises(TranslationError) as error:
        python_to_pseudocode(source)
    assert error.value.line == line
    assert construct in error.value.construct


def test_settings_are_reflected_in_python() -> None:
    translated = pseudocode_to_python(
        "answer ← 1 / 2\ny ← sin(angle)\n",
        Settings(number="exact", angle="degree"),
    )
    assert "from fractions import Fraction" in translated
    assert "Fraction(1) / Fraction(2)" in translated
    assert "sin(radians(angle))" in translated
    assert "from math import radians, sin" in translated


def test_python_names_that_clash_are_renamed_and_restored() -> None:
    source = "sum ← 1\nlambda ← sum + 2\nprint lambda\n"
    translated = pseudocode_to_python(source)
    assert "sum_ = 1" in translated
    assert "lambda_ = sum_ + 2" in translated
    assert "renamed pseudocode identifier 'sum'" in translated
    assert same_program(source, python_to_pseudocode(translated))


def test_translated_program_runs_with_pseudocode_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = "for i from 1 to 3\n  print i\nend for\ninput x\nprint x\n"
    translated = pseudocode_to_python(source)
    output = StringIO()
    monkeypatch.setattr("builtins.input", lambda: "4")
    monkeypatch.setattr("sys.stdout", output)
    exec(translated, {})
    assert output.getvalue() == "1\n2\n3\n4.0\n"


def test_python_translation_covers_expression_and_statement_forms() -> None:
    source = """\
def helper(x, step=1):
    if x > 0 and x != 2:
        return x
    elif not x:
        return -step
    else:
        return +step

values = [True, False, 2.5]
values.append(values[1])
helper(values[0])
for _ in range(2):
    print("repeat")
for i in range(3):
    print(i)
for i in range(1, 8, 2):
    print(i)
for i in range(8, 0, -2):
    print(i)
"""

    pseudocode = python_to_pseudocode(source)
    translated = pseudocode_to_python(pseudocode)

    assert "define helper(x, step = 1)" in pseudocode
    assert "append values[2] to values" in pseudocode
    assert "for i from 1 to 7 step 2" in pseudocode  # range(1, 8, 2): the end folded
    assert "for i from 8 to 1 step -2" in pseudocode  # range(8, 0, -2)
    compile(translated, "<translated>", "exec")


def test_pseudocode_translation_covers_control_flow_forms() -> None:
    source = """\
define choose(x)
  if x > 0 then
    return x
  else
    return
  end if
end
P(x) ← x^2
items ← [1, 2, 3]
append 4 to items
choose(1)
for each item in items
  print item
end for
repeat 2 times
  print "again"
end repeat
repeat
  print "once"
until true
while false
  break
end while
"""

    translated = pseudocode_to_python(source)

    assert "def P(" in translated
    assert "items.append(4)" in translated
    assert "for item in items:" in translated
    assert "for _ in range(2):" in translated
    assert "while True:" in translated
    compile(translated, "<translated>", "exec")


@pytest.mark.parametrize(
    "source",
    [
        "x = y = 1",
        "x: int = 1",
        "x += 1",
        "x.a = 1",
        "x[1:2] = 3",
        "1 + 2",
        "print(1, end='')",
        "f(x=1)",
        "obj.method()",
        "x = (1, 2)",
        "x = {1, 2}",
        "x = ~1",
        "while True:\n    print(1)\n",
        "while True:\n    print(1)\nelse:\n    pass",
        "for x in [1, 2]:\n    pass",
        "for x, y in range(2):\n    pass",
        "for x in range():\n    pass",
        "for x in range(4, 1, 0):\n    pass",
        "for x in range(1, n, step):\n    pass",
        "@decorator\ndef f():\n    return",
        "def f() -> int:\n    return 1",
        "def f(*args):\n    return 1",
        "def f(x: int):\n    return x",
        "try:\n    x = 1\nexcept Exception:\n    pass",
    ],
)
def test_python_translation_rejects_unsupported_forms(source: str) -> None:
    with pytest.raises(TranslationError):
        python_to_pseudocode(source)


def test_python_translation_handles_generated_helpers_and_angle_wrappers() -> None:
    source = """\
for x from 0.5 to 2.5 step 0.5
  y ← degrees(asin(x/3))
  z ← radians(y)
end for
"""
    translated = pseudocode_to_python(
        source,
        Settings(number="auto", angle="degree"),
    )

    assert "def _inclusive_range" in translated
    assert "from math import" in translated
    assert "degrees(asin" in translated
    compile(translated, "<translated>", "exec")


def test_pseudocode_translation_rejects_empty_if_and_unknown_nodes() -> None:
    with pytest.raises(TranslationError, match="has no branch"):
        _to_python(Program([If([], None, 1)], []))
    with pytest.raises(TranslationError, match="operator"):
        _to_python(
            Program(
                [If([(Binary("unknown", Name("x"), Num("1")), [], 1)], None, 1)],
                [],
            )
        )


@pytest.mark.parametrize(
    ("loop", "python"),
    [
        ("for i from 1 to 8", "for i in range(1, 9):"),
        ("for i from 1 to len(xs)-1", "for i in range(1, len(xs)):"),
        ("for i from 1 to len(xs)", "for i in range(1, len(xs) + 1):"),
        ("for i from n to 1 step -1", "for i in range(n, 0, -1):"),
    ],
)
def test_whole_number_loops_translate_to_a_plain_range(loop: str, python: str) -> None:
    """FR-PY-*: no `_inclusive_range` helper when the bounds are whole numbers (`len` is)."""
    translated = pseudocode_to_python(f"xs ← [1, 2]\nn ← 2\n{loop}\n  print i\nend for")
    assert python in translated
    assert "_inclusive_range" not in translated
    compile(translated, "<translated>", "exec")


def test_a_loop_bound_that_may_be_a_decimal_keeps_the_safe_helper() -> None:
    translated = pseudocode_to_python("x ← 5\nfor i from 1 to x/2\n  print i\nend for")
    assert "_inclusive_range(1, x / 2)" in translated


def test_for_in_without_each_is_a_loop_over_a_list() -> None:
    """`for c in list` (Python's spelling) is accepted as `for each c in list`."""
    assert run("for c in [1, 2, 3]\n  print c\nend for", Settings()).output == ["1", "2", "3"]
    assert "for c in [1, 2, 3]:" in pseudocode_to_python("for c in [1, 2, 3]\n  print c\nend for")


NEWTON = """\
define derivative(coeffs)
  dcoeffs ← []
  n ← len(coeffs) - 1
  for i from 1 to len(coeffs)-1
    append (n - i + 1)*coeffs[i] to dcoeffs
  end for
  return dcoeffs
end
print derivative([1, 0, -2, -5])
"""


def test_a_loop_that_indexes_lists_translates_zero_based() -> None:
    """FR-XLT-004 (Simon, 2026-11-22): `L[i]` stays `L[i]` in Python; the loop runs 0-based
    and the other uses of `i` are folded (`n - i + 1` with i one less is `n - i`)."""
    python = pseudocode_to_python(NEWTON)
    assert "for i in range(len(coeffs) - 1):" in python
    assert "dcoeffs.append((n - i) * coeffs[i])" in python
    assert same_program(NEWTON, python_to_pseudocode(python))  # and back again


def test_a_shifted_loop_computes_what_the_pseudocode_does() -> None:
    source = "xs ← [5, 7, 9]\ntotal ← 0\nfor i from 1 to 3\n  total ← total + i*xs[i]\nend for\n"
    python = pseudocode_to_python(source + "print total\n")
    assert "for i in range(3):" in python
    printed = StringIO()
    exec(compile(python, "<translated>", "exec"), {"print": lambda *a: print(*a, file=printed)})
    assert printed.getvalue().strip() == run(source + "print total", Settings()).output[0] == "46"


def test_a_loop_variable_used_after_the_loop_is_not_shifted() -> None:
    """After a 0-based loop Python's `i` is one less, so a later use keeps the 1-based form."""
    python = pseudocode_to_python(
        "xs ← [1, 2]\nfor i from 1 to 2\n  print xs[i]\nend for\nprint i\n"
    )
    assert "for i in range(1, 3):" in python
    assert "print(xs[i - 1])" in python


def test_python_for_over_a_list_becomes_for_each() -> None:
    """FR-XLT-005: `for coeff in coeffs:` (not just `range`) translates, so Python traces."""
    pseudocode = python_to_pseudocode(
        "total = 0\nfor coeff in [1, 2]:\n    total = total + coeff\n"
    )
    assert "for each coeff in [1, 2]" in pseudocode
    assert run(pseudocode + "print total\n", Settings()).output == ["3"]


def test_comments_survive_translation_both_ways() -> None:
    """Simon, 2026-11-22: full-line comments keep their place (block and indentation) when
    the program is switched to Python and back."""
    source = """\
# sums of squares
define total(n)
  # start from nothing
  s ← 0
  for k from 1 to n
    s ← s + k*k
  end for
  return s
end
// the answer
print total(3)
# done
"""
    python = pseudocode_to_python(source)
    body = python.split(TRANSLATION_MARKER, 1)[1]
    assert "# sums of squares\ndef total(n):\n    # start from nothing\n    s = 0" in body
    assert "# the answer\nprint(total(3))\n# done" in body
    back = python_to_pseudocode(python)
    assert back.startswith("# sums of squares\ndefine total(n)\n  # start from nothing\n")
    assert "# the answer\nprint total(3)\n# done" in back
    assert same_program(source, back)
    assert "CASSim" not in back  # the translator's own notes are not kept as comments


def test_blank_lines_are_kept_both_ways() -> None:
    """Blank lines stay where they were in both directions; a run of them is written as one,
    and blank lines at the end are dropped."""
    pseudocode = """\
a ← 1

b ← 2
for k from 1 to 2
  a ← a + k

  b ← b × k
end for


print a, b

"""
    python = pseudocode_to_python(pseudocode)
    body = python.split("# CASSim pseudocode translation\n")[-1]
    assert (
        body
        == """\
a = 1

b = 2
for k in range(1, 3):
    a = a + k

    b = b * k

print(a, b)
"""
    )
    assert (
        python_to_pseudocode(body)
        == """\
a ← 1

b ← 2
for k from 1 to 2
  a ← a + k

  b ← b × k
end for

print a, b
"""
    )
