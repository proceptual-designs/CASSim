# Requirements traced here: FR-CAT-005
"""Heading detection and name normalisation in tools/ref_matrix.py."""

import pytest
from tools import ref_matrix


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("approx()", ("approx()", True)),
        ("colAugment(Matrix1, Matrix2) ⇒ matrix", ("colAugment()", True)),
        ("►approxFraction()", ("►approxFraction()", True)),
        ("cosh⁻¹()", ("cosh⁻¹()", True)),
        ("CopyVar", ("CopyVar", False)),
        ("occurs.", None),
        ("appended to Matrix1. The matrices must", None),
    ],
)
def test_heading_name(raw: str, expected: tuple[str, bool] | None) -> None:
    assert ref_matrix.heading_name(raw) == expected


def test_norm_ignores_parens_spaces_arrows_and_case() -> None:
    assert ref_matrix.norm("►approxFraction()") == ref_matrix.norm("approxFraction ()")
    assert ref_matrix.norm("d() (derivative)") == "d"


def test_guide_headings_detects_empty_parentheses_with_spacing(monkeypatch, tmp_path) -> None:
    page = """
completeSquare( )

completeSquare(ExprOrEqn, Var) => expression or equation
"""
    monkeypatch.setattr(ref_matrix, "pdf_text", lambda path, *, layout: page)
    heading = ref_matrix.guide_headings(tmp_path / "guide.pdf")["completesquare"]
    assert (heading.name, heading.page, heading.is_call) == ("completeSquare()", 1, True)


def test_priority_prefers_corpus_then_book_mentions() -> None:
    assert ref_matrix.priority(1, 0) == "core"
    assert ref_matrix.priority(0, ref_matrix.LIKELY_MENTIONS) == "likely"
    assert ref_matrix.priority(0, ref_matrix.LIKELY_MENTIONS - 1) == "later"


def test_mentions_counts_calls_and_skips_ambiguous_words() -> None:
    call = ref_matrix.Heading("solve()", 1, is_call=True)
    assert ref_matrix.mentions("solve(x=1,x) and Solve(", call) == 1  # case-sensitive
    assert ref_matrix.mentions("this and that", ref_matrix.Heading("and", 1, is_call=False)) == -1
    word = ref_matrix.Heading("Disp", 1, is_call=False)
    assert ref_matrix.mentions("Disp x; Display", word) == 1  # whole word only
