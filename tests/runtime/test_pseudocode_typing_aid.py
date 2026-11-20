"""Typing aid behaviour (FR-SYN-013)."""

from cassim.runtime.pseudocode.typing_aid import replacement_before_cursor


def test_typing_aid_replaces_unambiguous_operator_suffixes() -> None:
    replacement = replacement_before_cursor("x <-", 4)

    assert replacement is not None
    assert (replacement.start, replacement.end, replacement.replacement) == (2, 4, "←")


def test_typing_aid_requires_a_terminator_for_latex_words() -> None:
    assert replacement_before_cursor(r"\theta", 6) is None

    replacement = replacement_before_cursor(r"\theta ", 7)

    assert replacement is not None
    assert (replacement.start, replacement.end, replacement.replacement) == (0, 7, "θ ")


def test_typing_aid_does_not_rewrite_plain_names() -> None:
    assert replacement_before_cursor("pi ", 3) is None
    assert replacement_before_cursor("sqrt ", 5) is None
