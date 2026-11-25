"""Exact and decimal values for CASSim Scientific (SDD-14 section 6.2).

A natural-display scientific calculator gives exact answers in a few fixed shapes: fractions,
surds such as `3√2/4` or `1 + √3`, and rational multiples of π. A value here is either `Exact`, a
sum of at most two such terms, or a `float` once the result leaves those shapes (sin 1, e², ...).
Arithmetic keeps exactness while it can and drops to a float otherwise, so the S⇔D key can only
ever show a form that is really equal to the answer.

Pure Python: no Flet, no SymPy.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction

MAX_MAGNITUDE = 1e100  # |x| at or above this is a Math ERROR, as on the device
TINY = 1e-99  # smaller magnitudes underflow to zero
MAX_DIGITS = 60  # an exact coefficient longer than this is carried as a float instead
MAX_TERMS = 2
MAX_FACTOR = 10**12  # the largest radicand split into a square part exactly
MAX_EXACT_POWER = 1000


class CalcError(Exception):
    """A calculation the device refuses. `kind` is the word before ERROR on the screen."""

    def __init__(self, kind: str = "Math") -> None:
        super().__init__(f"{kind} ERROR")
        self.kind = kind

    @property
    def message(self) -> str:
        return f"{self.kind} ERROR"


def math_error() -> CalcError:
    return CalcError("Math")


def syntax_error() -> CalcError:
    return CalcError("Syntax")


@dataclass(frozen=True)
class Exact:
    """A sum of `coeff * √radicand * π**pi_power` terms: radicand is square-free and at least 1,
    pi_power is 0 or 1, and no coefficient is zero. No terms at all is zero."""

    terms: tuple[tuple[int, int, Fraction], ...] = ()

    def __float__(self) -> float:
        return math.fsum(
            float(coeff) * math.sqrt(radicand) * math.pi**power
            for radicand, power, coeff in self.terms
        )

    @property
    def rational(self) -> Fraction | None:
        """The value as a fraction, or None when it has a surd or π."""
        if not self.terms:
            return Fraction(0)
        if len(self.terms) == 1 and self.terms[0][:2] == (1, 0):
            return self.terms[0][2]
        return None


type Number = Exact | float

ZERO = Exact()
PI = Exact(((1, 1, Fraction(1)),))


def rational(value: Fraction | int) -> Exact:
    q = Fraction(value)
    return Exact(((1, 0, q),)) if q else ZERO


def as_float(value: Number) -> float:
    return float(value)


def as_rational(value: Number) -> Fraction | None:
    return value.rational if isinstance(value, Exact) else None


def as_integer(value: Number) -> int | None:
    """The value as an int when it is a whole number (a float within 1e-9 counts)."""
    q = as_rational(value)
    if q is not None:
        return q.numerator if q.denominator == 1 else None
    x = float(value)
    if math.isfinite(x) and abs(x) < MAX_MAGNITUDE and abs(x - round(x)) < 1e-9:  # noqa: PLR2004
        return round(x)
    return None


def check(value: Number) -> Number:
    """Raise Math ERROR for a value the device cannot hold; flush tiny floats to zero."""
    x = float(value)
    if not math.isfinite(x) or abs(x) >= MAX_MAGNITUDE:
        raise math_error()
    if isinstance(value, float) and abs(value) < TINY:
        return 0.0
    return value


def _digits(n: int) -> int:
    return len(str(abs(n)))


def _make(terms: dict[tuple[int, int], Fraction]) -> Number:
    kept = {key: coeff for key, coeff in terms.items() if coeff}
    if not kept:
        return ZERO
    powers = {power for _, power in kept}
    too_long = any(
        _digits(c.numerator) > MAX_DIGITS or _digits(c.denominator) > MAX_DIGITS
        for c in kept.values()
    )
    shapes_ok = (powers == {0} and len(kept) <= MAX_TERMS) or (powers == {1} and len(kept) == 1)
    exact = Exact(tuple(sorted((r, p, c) for (r, p), c in kept.items())))
    if too_long or not shapes_ok:
        return check(float(exact))
    return check(exact)


def square_part(n: int) -> tuple[int, int]:
    """(a, b) with n == a*a*b and b square-free. Only for 0 < n <= MAX_FACTOR."""
    outside, inside = 1, n
    factor = 2
    while factor * factor <= inside:
        square = factor * factor
        while inside % square == 0:
            inside //= square
            outside *= factor
        factor += 1 if factor == 2 else 2  # noqa: PLR2004
    return outside, inside


def _integer_root(n: int, k: int) -> int | None:
    """The exact k-th root of n >= 0, or None."""
    if n < 0:
        return None
    root = round(n ** (1 / k))
    for guess in (root - 1, root, root + 1):
        if guess >= 0 and guess**k == n:
            return guess
    return None


# ---- arithmetic ---------------------------------------------------------------------------------


def add(a: Number, b: Number) -> Number:
    if isinstance(a, Exact) and isinstance(b, Exact):
        terms: dict[tuple[int, int], Fraction] = {}
        for radicand, power, coeff in (*a.terms, *b.terms):
            terms[radicand, power] = terms.get((radicand, power), Fraction(0)) + coeff
        return _make(terms)
    return check(float(a) + float(b))


def neg(a: Number) -> Number:
    if isinstance(a, Exact):
        return Exact(tuple((r, p, -c) for r, p, c in a.terms))
    return -a


def sub(a: Number, b: Number) -> Number:
    return add(a, neg(b))


def mul(a: Number, b: Number) -> Number:
    if isinstance(a, Exact) and isinstance(b, Exact):
        terms: dict[tuple[int, int], Fraction] = {}
        for r1, p1, c1 in a.terms:
            for r2, p2, c2 in b.terms:
                common = math.gcd(r1, r2)
                radicand = (r1 // common) * (r2 // common)
                key = (radicand, p1 + p2)
                terms[key] = terms.get(key, Fraction(0)) + c1 * c2 * common
        if any(power > 1 for _, power in terms):
            return check(float(a) * float(b))
        return _make(terms)
    return check(float(a) * float(b))


def inverse(a: Number) -> Number:
    if isinstance(a, Exact):
        if not a.terms:
            raise math_error()
        if len(a.terms) == 1:
            radicand, power, coeff = a.terms[0]
            if power == 0:
                return _make({(radicand, 0): 1 / (coeff * radicand)})
        elif all(power == 0 for _, power, _ in a.terms):
            (r1, _, c1), (r2, _, c2) = a.terms
            denominator = c1 * c1 * r1 - c2 * c2 * r2
            if denominator:
                return _make({(r1, 0): c1 / denominator, (r2, 0): -c2 / denominator})
    x = float(a)
    if x == 0:
        raise math_error()
    return check(1 / x)


def div(a: Number, b: Number) -> Number:
    if float(b) == 0:
        raise math_error()
    return mul(a, inverse(b))


def sqrt(a: Number) -> Number:
    x = float(a)
    if x < 0:
        raise math_error()
    q = as_rational(a)
    if q is not None and q.numerator * q.denominator <= MAX_FACTOR:
        outside, inside = square_part(q.numerator * q.denominator)
        return _make({(inside, 0): Fraction(outside, q.denominator)})
    return check(math.sqrt(x))


def root(k: int, a: Number) -> Number:
    """The real k-th root (k >= 1); an odd root of a negative number is negative."""
    if k == 2:  # noqa: PLR2004
        return sqrt(a)
    x = float(a)
    if x < 0 and k % 2 == 0:
        raise math_error()
    q = as_rational(a)
    if q is not None:
        sign = -1 if q < 0 else 1
        top = _integer_root(abs(q.numerator), k)
        bottom = _integer_root(q.denominator, k)
        if top is not None and bottom is not None:
            return rational(Fraction(sign * top, bottom))
    return check(math.copysign(abs(x) ** (1 / k), x))


def power(a: Number, b: Number) -> Number:
    exponent = as_rational(b)
    base = float(a)
    if base == 0:
        if float(b) <= 0:
            raise math_error()
        return ZERO if isinstance(a, Exact) else 0.0
    if exponent is not None and isinstance(a, Exact):
        if exponent.denominator == 1 and abs(exponent.numerator) <= MAX_EXACT_POWER:
            if abs(exponent.numerator) * math.log10(max(abs(base), 1 / abs(base))) > 100:  # noqa: PLR2004
                raise math_error()
            result: Number = rational(1)
            for _ in range(abs(exponent.numerator)):
                result = mul(result, a)
            return inverse(result) if exponent < 0 else result
        if exponent.denominator <= MAX_EXACT_POWER and abs(exponent.numerator) <= MAX_EXACT_POWER:
            return power(root(exponent.denominator, a), rational(exponent.numerator))
    if exponent is not None and exponent.denominator % 2 == 1 and base < 0:
        magnitude = abs(base) ** float(exponent)
        return check(-magnitude if exponent.numerator % 2 else magnitude)
    if base < 0 and as_integer(b) is None:
        raise math_error()
    try:
        return check(base ** float(b))
    except OverflowError:
        raise math_error() from None


def recognise_fraction(x: float) -> Fraction | None:
    """A fraction of at most ten digits in all that equals x to twelve places, or None. This is
    what S⇔D offers for a decimal answer: 0.75 is 3/4, but π stays a decimal."""
    if not math.isfinite(x):
        return None
    candidate = Fraction(x).limit_denominator(10**6)
    if abs(float(candidate) - x) > 1e-12 * max(1.0, abs(x)):
        return None
    if _digits(candidate.numerator) + _digits(candidate.denominator) > 10:  # noqa: PLR2004
        return None
    return candidate


# ---- exact values of the trigonometric functions at multiples of 30° and 45° -------------------

_HALF = Fraction(1, 2)
_SQRT2_2 = Exact(((2, 0, _HALF),))
_SQRT3_2 = Exact(((3, 0, _HALF),))
_SQRT3 = Exact(((3, 0, Fraction(1)),))
_SQRT3_3 = Exact(((3, 0, Fraction(1, 3)),))
_SIN_TABLE: dict[int, Exact] = {
    0: ZERO,
    30: rational(_HALF),
    45: _SQRT2_2,
    60: _SQRT3_2,
    90: rational(1),
}


def _sin_degrees(angle: Fraction) -> Exact | None:
    """sin of a whole number of degrees that is a multiple of 30 or 45, or None."""
    if angle.denominator != 1:
        return None
    degrees = angle.numerator % 360
    sign = 1
    if degrees >= 180:  # noqa: PLR2004
        degrees -= 180
        sign = -1
    if degrees > 90:  # noqa: PLR2004
        degrees = 180 - degrees
    found = _SIN_TABLE.get(degrees)
    if found is None:
        return None
    return found if sign == 1 else Exact(tuple((r, p, -c) for r, p, c in found.terms))


def exact_trig(name: str, degrees: Fraction) -> Number | None:
    """sin, cos or tan of an angle given in degrees, exactly, or None if it has no exact form."""
    if name == "sin":
        return _sin_degrees(degrees)
    if name == "cos":
        return _sin_degrees(degrees + 90)
    sine, cosine = _sin_degrees(degrees), _sin_degrees(degrees + 90)
    if sine is None or cosine is None:
        return None
    if not cosine.terms:
        raise math_error()
    return div(sine, cosine)


def _key(value: Number) -> tuple[tuple[int, int, Fraction], ...] | None:
    return value.terms if isinstance(value, Exact) else None


_ASIN: dict[tuple[tuple[int, int, Fraction], ...], int] = {}
_ATAN: dict[tuple[tuple[int, int, Fraction], ...], int] = {}
for _deg in (0, 30, 45, 60, 90):
    for _sign in (1, -1):
        _value = _SIN_TABLE[_deg]
        _signed = _value if _sign == 1 else Exact(tuple((r, p, -c) for r, p, c in _value.terms))
        _ASIN[_signed.terms] = _sign * _deg
for _deg, _value in ((0, ZERO), (30, _SQRT3_3), (45, rational(1)), (60, _SQRT3)):
    for _sign in (1, -1):
        _signed = _value if _sign == 1 else Exact(tuple((r, p, -c) for r, p, c in _value.terms))
        _ATAN[_signed.terms] = _sign * _deg


def exact_inverse_trig(name: str, value: Number) -> int | None:
    """The angle in degrees for sin⁻¹, cos⁻¹ or tan⁻¹ of a value in the exact table, or None."""
    key = _key(value)
    if key is None:
        return None
    if name == "asin":
        return _ASIN.get(key)
    if name == "acos":
        found = _ASIN.get(key)
        return None if found is None else 90 - found
    return _ATAN.get(key)
