"""The numeric tower (integer, rational, real, complex), string operations and display.

Number modes (dialect section 8): Approx makes every `/` a real; Auto keeps integers and fractions
exact while a decimal literal makes a real; Exact also reads decimal literals as fractions.
Irrational results (`sqrt(2)`, `sin(1)`) are reals in every mode.
"""

import math
import operator
from collections.abc import Callable
from fractions import Fraction
from typing import TypeGuard

from cassim.runtime.pseudocode.errors import PseudocodeRuntimeError
from cassim.runtime.pseudocode.settings import Settings

type Real = int | Fraction | float
type Number = Real | complex

MINUS = "−"


def is_number(v: object) -> TypeGuard[Number]:
    return isinstance(v, int | Fraction | float | complex) and not isinstance(v, bool)


def norm(v: Number) -> Number:
    """A fraction with denominator 1 is an integer."""
    if isinstance(v, Fraction) and v.denominator == 1:
        return int(v.numerator)
    return v


def parse_literal(text: str, settings: Settings) -> Number:
    if "." in text or "E" in text or "e" in text:
        if settings.number == "exact":
            return norm(Fraction(text))
        return float(text)
    return int(text)


def type_name(v: object) -> str:
    if isinstance(v, bool):
        return "a true/false value"
    if isinstance(v, str):
        return "text"
    if isinstance(v, list):
        return "a list"
    if is_number(v):
        return "a number"
    return "a function"


def _numbers(op: str, a: object, b: object) -> tuple[Number, Number]:
    if is_number(a) and is_number(b):
        return a, b
    raise PseudocodeRuntimeError(f"cannot apply {op} to {type_name(a)} and {type_name(b)}")


def _reals(op: str, a: object, b: object) -> tuple[Real, Real]:
    x, y = _numbers(op, a, b)
    if isinstance(x, complex) or isinstance(y, complex):
        raise PseudocodeRuntimeError(f"{op} needs real numbers")
    return x, y


def add(a: object, b: object) -> object:
    if isinstance(a, str) and isinstance(b, str):
        return a + b
    if isinstance(a, list) and isinstance(b, list):
        return a + b
    x, y = _numbers("+", a, b)
    return norm(x + y)


def sub(a: object, b: object) -> object:
    x, y = _numbers("-", a, b)
    return norm(x - y)


def mul(a: object, b: object) -> object:
    x, y = _numbers("×", a, b)
    return norm(x * y)


def div(a: object, b: object, settings: Settings) -> object:
    x, y = _numbers("÷", a, b)
    if y == 0:
        raise PseudocodeRuntimeError("division by zero")
    exact = isinstance(x, int | Fraction) and isinstance(y, int | Fraction)
    if exact and settings.number != "approx":
        return norm(Fraction(x) / Fraction(y))
    return x / y


def floordiv(a: object, b: object) -> object:
    x, y = _reals("div", a, b)
    if y == 0:
        raise PseudocodeRuntimeError("division by zero")
    return norm(x // y)


def mod(a: object, b: object) -> object:
    x, y = _reals("mod", a, b)
    if y == 0:
        raise PseudocodeRuntimeError("division by zero")
    return norm(x % y)


def neg(a: object) -> object:
    if not is_number(a):
        raise PseudocodeRuntimeError(f"cannot negate {type_name(a)}")
    return norm(-a)


def power(a: object, b: object, settings: Settings) -> object:
    x, y = _numbers("^", a, b)
    try:
        return _power(x, y, settings)
    except ZeroDivisionError:
        raise PseudocodeRuntimeError("division by zero") from None
    except OverflowError:
        raise PseudocodeRuntimeError("the result of ^ is too large") from None


def _power(a: Number, b: Number, settings: Settings) -> Number:
    if isinstance(a, int | Fraction) and isinstance(b, int):
        if b >= 0 and isinstance(a, int):
            return a**b
        if settings.number == "approx":
            return float(a) ** b
        return norm(Fraction(a) ** b)
    if isinstance(b, Fraction):
        if b.denominator == 1:
            return _power(a, int(b.numerator), settings)
        b = float(b)
    result = a**b
    real_inputs = not (isinstance(a, complex) or isinstance(b, complex))
    if isinstance(result, complex) and real_inputs and not settings.complex_domain:
        raise PseudocodeRuntimeError("the result is not a real number (Real domain)")
    return norm(result)


_ORDER: dict[str, Callable[[Real, Real], bool]] = {
    "<": operator.lt,
    ">": operator.gt,
    "≤": operator.le,
    "≥": operator.ge,
}


def compare(op: str, a: object, b: object) -> bool:
    if op == "=":
        return _equal(a, b)
    if op == "≠":
        return not _equal(a, b)
    if isinstance(a, str) and isinstance(b, str):
        return {"<": a < b, ">": a > b, "≤": a <= b, "≥": a >= b}[op]
    if not (is_number(a) and is_number(b)):
        raise PseudocodeRuntimeError(f"cannot compare {type_name(a)} with {type_name(b)}")
    x, y = _reals("comparison", a, b)
    return _ORDER[op](x, y)


def _equal(a: object, b: object) -> bool:
    if is_number(a) and is_number(b):
        return a == b
    if isinstance(a, bool) and isinstance(b, bool):
        return a == b
    if isinstance(a, str) and isinstance(b, str):
        return a == b
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_equal(x, y) for x, y in zip(a, b, strict=True))
    return False


def truthy(v: object) -> bool:
    if isinstance(v, bool):
        return v
    raise PseudocodeRuntimeError(f"a condition must be true or false, not {type_name(v)}")


def real_value(name: str, v: object) -> Real:
    """`v` as a real number, or an error saying what `name` needed."""
    if is_number(v) and not isinstance(v, complex):
        return v
    raise PseudocodeRuntimeError(f"{name} needs a real number")


def round_half_up(x: Real, digits: int = 0) -> Number:
    """School rounding: halves go away from zero (Python's round() is banker's rounding)."""
    scale = Fraction(10) ** digits
    exact = Fraction(x) * scale
    r = math.floor(abs(exact) + Fraction(1, 2))
    value = Fraction(r if exact >= 0 else -r) / scale
    return norm(value) if digits <= 0 else float(value)


# ---------------------------------------------------------------------------------------- display


def format_float(x: float, display: int | str) -> str:
    if math.isnan(x):
        return "undef"
    if math.isinf(x):
        return "∞" if x > 0 else "-∞"
    s = repr(x) if display == "full" else f"{x:.{display}g}"
    if "e" in s:
        mantissa, exponent = s.split("e")
        if "." in mantissa:
            mantissa = mantissa.rstrip("0")
        else:
            mantissa += "."
        return f"{mantissa}ᴇ{int(exponent)}"
    if "." in s:
        return s.rstrip("0")
    return s + "."  # a whole real keeps its point, so 5. differs from the integer 5


def format_value(v: object, settings: Settings, *, minus: str = "-") -> str:
    """`v` as text. `minus` is the sign written on numbers (text is never altered)."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return "[" + ", ".join(format_value(x, settings, minus=minus) for x in v) + "]"
    if isinstance(v, int):
        text = str(v)
    elif isinstance(v, Fraction):
        text = f"{v.numerator}/{v.denominator}"
    elif isinstance(v, float):
        text = format_float(v, settings.display)
    elif isinstance(v, complex):
        re_part = format_float(v.real, settings.display)
        im_part = format_float(abs(v.imag), settings.display)
        sign = "-" if math.copysign(1, v.imag) < 0 else "+"
        text = f"{re_part}{sign}{im_part}ⅈ"
    else:
        return str(getattr(v, "describe", lambda: "function")())
    return text if minus == "-" else text.replace("-", minus)
