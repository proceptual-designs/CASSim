"""Value -> TI linear text AND a 2D layout tree (fraction, sqrt, power, matrix)."""

import re
from decimal import ROUND_HALF_UP, Decimal

from cassim.core import ast, pretty
from cassim.core.compat import sympy_adapter as cas
from cassim.core.settings import Settings
from cassim.core.values import Bool, Expr, ListValue, Shown, Str, Unevaluated, Value, Void

# Below this, Float mode changes to scientific form. Fix mode keeps fixed form up to this size.
_SMALLEST_FLOAT_EXPONENT = -3
_LARGEST_FIX = Decimal(10) ** 12
_ENGINEERING_STEP = 3

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


def _scaled_text(value: Decimal, places: int, *, engineering: bool) -> str:
    """Scientific form (one digit before the point) or engineering (exponent a multiple of 3)."""
    rounded = _round_significant(value, places)
    exponent = rounded.adjusted()
    if engineering:
        exponent -= exponent % _ENGINEERING_STEP
    return f"{_trimmed(rounded.scaleb(-exponent))}ᴇ{exponent}"


def decimal_text(value: Decimal, digits: str, exp_format: str = "normal") -> str:
    """Show a non-negative decimal under a `floatN` or `fixN` display setting."""
    is_fix = digits.startswith("fix")
    places = int(digits.removeprefix("fix" if is_fix else "float"))
    if value == 0:
        return _with_point(format(Decimal(0).scaleb(-places), "f")) if is_fix else "0."
    if exp_format != "normal" and not is_fix:
        return _scaled_text(value, places, engineering=exp_format == "engineering")
    return _fix_text(value, places) if is_fix else _float_text(value, places)


def _atom_node(value: Str | Bool | Void | Shown) -> ast.Expr:
    if isinstance(value, Shown):
        return ast.Name(value.text)
    if isinstance(value, Str):
        return ast.String(value.value)
    if isinstance(value, Bool):
        return ast.Name("true" if value.value else "false")
    return ast.Name("Done")


def _node(value: Value, settings: Settings) -> ast.Expr:
    if isinstance(value, Expr):
        return cas.to_ast(
            value.raw, lambda d: decimal_text(d, settings.digits, settings.exp_format)
        )
    if isinstance(value, Str | Bool | Void | Shown):
        return _atom_node(value)
    if isinstance(value, Unevaluated):
        return ast.Call(value.name, tuple(_node(arg, settings) for arg in value.args))
    if isinstance(value, ListValue):
        return ast.ListLit(tuple(_node(item, settings) for item in value.items))
    return ast.Matrix(tuple(tuple(_node(cell, settings) for cell in row) for row in value.rows))


def to_text(value: Value, settings: Settings) -> str:
    """Show a value as TI linear text in canonical Unicode."""
    return str(_node(value, settings))


def to_pretty(value: Value, settings: Settings, *, unicode: bool = True) -> str:
    """Show a value in two dimensions, like SymPy's `pprint`; `unicode=False` draws in ASCII."""
    return pretty.draw(_node(value, settings), unicode=unicode)


def _atom_latex(value: Str | Bool | Void | Shown) -> str:
    if isinstance(value, Shown):
        return rf"\text{{{value.text}}}"
    if isinstance(value, Str):
        return rf"\text{{{value.value}}}"
    if isinstance(value, Bool):
        return rf"\text{{{str(value.value).lower()}}}"
    return r"\text{Done}"


def to_latex(value: Value) -> str:
    if isinstance(value, Expr):
        return cas.latex(value.raw)
    if isinstance(value, Str | Bool | Void | Shown):
        return _atom_latex(value)
    if isinstance(value, Unevaluated):
        arguments = ",".join(to_latex(arg) for arg in value.args)
        return rf"\text{{{value.name}}}\left({arguments}\right)"
    if isinstance(value, ListValue):
        return r"\{" + ",".join(to_latex(item) for item in value.items) + r"\}"
    rows = r"\\".join("&".join(to_latex(cell) for cell in row) for row in value.rows)
    return rf"\begin{{bmatrix}}{rows}\end{{bmatrix}}"
