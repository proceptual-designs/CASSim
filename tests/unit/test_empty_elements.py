# Requirements traced here: FR-EVAL-001
"""Empty (void) elements, `_`: the Reference Guide's examples (Empty (Void) Elements), needed by
spreadsheet cells and linked columns with gaps (slice 3a)."""

import pytest

from cassim.core.format import to_latex
from cassim.core.session import Session
from cassim.core.values import Empty


def run(*lines):
    session = Session()
    result = None
    for line in lines:
        result = session.eval(line)
        assert result.error is None, f"{line}: {result.error}"
    assert result is not None
    return result.text


@pytest.mark.parametrize(
    ("lines", "text"),
    [
        (("_",), "_"),
        (("void",), "_"),
        (("3+_",), "_"),
        (("-_",), "_"),
        (("gcd(100,_)",), "_"),
        (("{5,_,10}-{3,6,9}",), "{2,_,1}"),
        (("{1,_}*2",), "{2,_}"),
        (("sin({0,_})",), "{0,_}"),
        (("approx({1/2,_})",), "{0.5,_}"),
        (("[1,_;3,4]",), "[1,_;3,4]"),
        (("x:={1,_,3}", "x"), "{1,_,3}"),
        (("dim({1,_})",), "2"),
        # the list statistics skip empty elements
        (("sum({2,_,3,5,6.6})",), "16.6"),
        (("median({1,2,_,_,3})",), "2"),
        (("mean({1,_,3})",), "2"),
        (("max({1,_,3})",), "3"),
        (("cumulativeSum({1,2,_,4,5})",), "{1,3,_,7,12}"),
        (("isVoid(_)",), "true"),
        (("isVoid({1,_})",), "{false,true}"),
        (("delVoid({1,_,2})",), "{1,2}"),
    ],
)
def test_empty_elements(lines, text):
    assert run(*lines) == text


def test_sorta_puts_empty_elements_last_and_carries_the_other_lists():
    lines = ("l1:={5,4,3,_,1}", "l2:={5,4,3,2,1}", "SortA l1,l2")
    assert run(*lines, "l1") == "{1,3,4,5,_}"
    assert run(*lines, "l2") == "{1,3,4,5,2}"


def test_sortd_puts_empty_elements_last():
    assert run("l1:={1,2,3,_,5}", "l2:={1,2,3,4,5}", "SortD l1,l2", "l1") == "{5,3,2,1,_}"
    assert run("l1:={1,2,3,_,5}", "l2:={1,2,3,4,5}", "SortD l1,l2", "l2") == "{5,3,2,1,4}"


def test_onevar_leaves_out_empty_elements():
    assert run("OneVar {1,_,3}", "stat.n") == "2."


def test_twovar_leaves_out_a_row_with_an_empty_element_in_either_list():
    assert run("TwoVar {1,2,3,4},{2,_,6,8}", "stat.n") == "3."


@pytest.mark.parametrize("line", ["_:=1", "void:=1"])
def test_empty_names_cannot_be_stored_to(line):
    assert Session().eval(line).error is not None


def test_empty_prints_as_an_underscore_in_latex():
    assert to_latex(Empty()) == r"\_"
