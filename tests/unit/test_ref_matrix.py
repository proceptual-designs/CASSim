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
