"""The accent key: it turns the letter before the cursor into its next accented form.

The forms of a letter are the precomposed Unicode letters whose canonical decomposition (NFD)
starts with it: `e` has `è é ê ë ē ĕ ė ę ě ...`. One accent comes before two (`ệ` is `e` with a
dot below and a circumflex), and within each group the order is the code point's. After the last
form the key goes back to the plain letter. The lists come from Python's own Unicode database, so
there is no table to keep. Other languages' letters and keyboards are a later piece of work.
"""

from __future__ import annotations

import sys
import unicodedata
from functools import cache

_LATIN_END = 0x2000  # precomposed Latin letters all sit below the General Punctuation block


@cache
def _forms() -> dict[str, tuple[str, ...]]:
    """Every base letter with at least one accented form, mapped to the cycle starting with it."""
    found: dict[str, list[str]] = {}
    for code in range(0xC0, min(_LATIN_END, sys.maxunicode)):
        char = chr(code)
        if not char.isalpha():
            continue
        parts = unicodedata.normalize("NFD", char)
        base, marks = parts[0], parts[1:]
        if base == char or not base.isascii() or not base.isalpha():
            continue
        if not marks or not all(unicodedata.combining(mark) for mark in marks):
            continue
        found.setdefault(base, []).append(char)
    return {
        base: (base, *sorted(chars, key=lambda c: (len(unicodedata.normalize("NFD", c)), c)))
        for base, chars in found.items()
    }


def accent_forms(letter: str) -> tuple[str, ...]:
    """The cycle the accent key steps through for `letter` (or any of its forms); empty if
    the character has no accented forms."""
    if len(letter) != 1:
        return ()
    return _forms().get(unicodedata.normalize("NFD", letter)[0], ())


def next_accent(letter: str) -> str | None:
    """The form after `letter` in its cycle, or None when it has no accented forms."""
    forms = accent_forms(letter)
    if not forms:
        return None
    return forms[(forms.index(letter) + 1) % len(forms)] if letter in forms else forms[0]
