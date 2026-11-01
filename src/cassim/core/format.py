"""Value -> TI linear text AND a 2D layout tree (fraction, sqrt, power, matrix)."""

import re
from decimal import ROUND_HALF_UP, Decimal

from cassim.core import ast
from cassim.core.compat import sympy_adapter as cas
from cassim.core.settings import Settings
from cassim.core.values import Bool, Expr, ListValue, Str, Value

# Below this, Float mode changes to scientific form. Fix mode keeps fixed form up to this size.
_SMALLEST_FLOAT_EXPONENT = -3
_LARGEST_FIX = Decimal(10) ** 12

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
        "ᵍ": "@g",
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


def _round_significant(value: Decimal, places: int) -> Decimal:
    step = Decimal(1).scaleb(value.adjusted() - places + 1)
    return value.quantize(step, ROUND_HALF_UP)


def _with_point(text: str) -> str:
    """TI shows a decimal point on every approximate number, as in `2.`."""
    return text if "." in text else f"{text}."


def _trimmed(value: Decimal) -> str:
    text = format(value, "f")
    return _with_point(text.rstrip("0") if "." in text else text)


def _float_text(value: Decimal, places: int) -> str:
    rounded = _round_significant(value, places)
    exponent = rounded.adjusted()
    if _SMALLEST_FLOAT_EXPONENT <= exponent < places:
        return _trimmed(rounded)
    return f"{_trimmed(rounded.scaleb(-exponent))}ᴇ{exponent}"


def _fix_text(value: Decimal, places: int) -> str:
    step = Decimal(1).scaleb(-places)
    if step <= value < _LARGEST_FIX:
        return _with_point(format(value.quantize(step, ROUND_HALF_UP), "f"))
    rounded = _round_significant(value, places + 1)
    exponent = rounded.adjusted()
    mantissa = format(rounded.scaleb(-exponent).quantize(step), "f")
    return f"{_with_point(mantissa)}ᴇ{exponent}"


def decimal_text(value: Decimal, digits: str) -> str:
    """Show a non-negative decimal under a `floatN` or `fixN` display setting."""
    is_fix = digits.startswith("fix")
    places = int(digits.removeprefix("fix" if is_fix else "float"))
    if value == 0:
        return _with_point(format(Decimal(0).scaleb(-places), "f")) if is_fix else "0."
    return _fix_text(value, places) if is_fix else _float_text(value, places)


def _node(value: Value, settings: Settings) -> ast.Expr:
    if isinstance(value, Expr):
        return cas.to_ast(value.raw, lambda d: decimal_text(d, settings.digits))
    if isinstance(value, Str):
        return ast.String(value.value)
    if isinstance(value, Bool):
        return ast.Name("true" if value.value else "false")
    if isinstance(value, ListValue):
        return ast.ListLit(tuple(_node(item, settings) for item in value.items))
    return ast.Matrix(tuple(tuple(_node(cell, settings) for cell in row) for row in value.rows))


def to_text(value: Value, settings: Settings) -> str:
    """Show a value as TI linear text in canonical Unicode."""
    return str(_node(value, settings))


def to_latex(value: Value) -> str:
    if isinstance(value, Expr):
        return cas.latex(value.raw)
    if isinstance(value, Str):
        return rf"\text{{{value.value}}}"
    if isinstance(value, Bool):
        return rf"\text{{{str(value.value).lower()}}}"
    if isinstance(value, ListValue):
        return r"\{" + ",".join(to_latex(item) for item in value.items) + r"\}"
    rows = r"\\".join("&".join(to_latex(cell) for cell in row) for row in value.rows)
    return rf"\begin{{bmatrix}}{rows}\end{{bmatrix}}"
