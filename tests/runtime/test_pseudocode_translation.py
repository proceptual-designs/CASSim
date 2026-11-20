"""Python/pseudocode translation tests (FR-XLT-001 to FR-XLT-006)."""

import ast
from io import StringIO

import pytest

from cassim.runtime.pseudocode import (
    TranslationError,
    parse,
    pseudocode_to_python,
    python_to_pseudocode,
    shape,
)
from cassim.runtime.pseudocode.settings import Settings


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
    assert ast.unparse(tree.body[-2]) == "x = values[3 - 1]"
    assert ast.unparse(tree.body[-1]) == "values[i + 1 - 1] = x"

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
  for i from 0 to n - 1
    result ← result + [items[i + 1]]
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
