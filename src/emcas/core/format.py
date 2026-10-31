"""Value -> TI linear text AND a 2D layout tree (fraction, sqrt, power, matrix)."""

import re

# Canonical text is Unicode, which the GUI shows directly. This is the plain-keyboard spelling of
# each symbol that has one, for the REPL. ∠, ∞ and ° have none and stay as they are.
_ASCII = str.maketrans(
    {
        "ⅇ": "@e",
        "ⅈ": "@i",
        "ᴇ": "@E",
        "π": "pi",
        "√": "sqrt",
        "≤": "<=",
        "≥": ">=",
        "≠": "/=",
        "→": "->",
        "▶": "@>",
        "⇒": "=>",
        "⇔": "<=>",
        "ᵀ": "@t",
        "ʳ": "@r",
        "ᴳ": "@g",
    }
)
# String contents must not change, and the `"` of 45" does not open a string.
_LITERAL_RE = re.compile(r"""([0-9.]+°[0-9.]+'(?:[0-9.]+")?|"[^"]*")""")


def to_ascii(text: str) -> str:
    """Respell canonical text so that it can be typed on a plain keyboard.

    The result reads back as the same entry, because the lexer accepts every spelling used here.
    """
    parts = _LITERAL_RE.split(text)
    # re.split with one group alternates between plain text and literals.
    return "".join(p if i % 2 else p.translate(_ASCII) for i, p in enumerate(parts))
