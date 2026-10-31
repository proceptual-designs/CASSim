"""Value -> TI linear text AND a 2D layout tree (fraction, sqrt, power, matrix)."""

import re

# Canonical text is Unicode, which the GUI shows directly. These are TI's own keyboard spellings
# (CAS guide 3.2, pp. 164-165), for the REPL.
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
        "°": "@d",
        "∠": "@<",
        "∞": "infinity",
    }
)
# String contents must not change, and the `"` of 45" does not open a string.
_LITERAL_RE = re.compile(r"""([0-9.]+°[0-9.]+'(?:[0-9.]+")?|"[^"]*")""")


_INVERSE_RE = re.compile(r"([a-z]+)⁻¹")


def to_ascii(text: str) -> str:
    """Respell canonical text so that it can be typed on a plain keyboard.

    The result reads back as the same entry, because the lexer accepts every spelling used here.
    """
    parts = _LITERAL_RE.split(text)
    return "".join(p if p.startswith('"') else _spell(p) for p in parts)


def _spell(text: str) -> str:
    return _INVERSE_RE.sub(r"arc\1", text).translate(_ASCII)
