"""Conversions (`x▶Base16`, `x▶Polar`, ...), `string`, `expr`, `list▶mat` and `mat▶list`."""

import re

from cassim.core import angles, ast, errors
from cassim.core.catalog.registry import Host, conversion, eager
from cassim.core.compat import sympy_adapter as cas
from cassim.core.errors import TIError
from cassim.core.format import to_text
from cassim.core.parser import parse
from cassim.core.settings import Angle, Settings
from cassim.core.valueops import (
    list_of,
    map_value,
    matrix_of,
    raw_list,
    raw_of,
    raw_rows,
    vector_parts,
)
from cassim.core.values import Expr, MatrixValue, Raw, Shown, Str, Value

_WORD_BITS = 64
_ATOM = re.compile(r"-?[\w.ⅇⅈπ∞]+")
_SEXAGESIMAL = 60
_SECONDS_PRECISION = 6
_SPACE_VECTOR_PARTS = 3


def _show(raw: Raw, settings: Settings) -> str:
    return to_text(Expr(cas.finish(raw, settings)), settings)


def _with_unit(text: str, unit: str) -> str:
    """`30°` for a plain number, `(18000/π)ᵍ` for anything that needs brackets."""
    return text + unit if _ATOM.fullmatch(text) else f"({text}){unit}"


# ---- number bases ----------------------------------------------------------------------------


def _integer(value: Value) -> int:
    number = cas.integer_value(raw_of(value))
    if number is None:
        raise TIError(errors.DOMAIN)
    return number


def _based(value: Value, prefix: str, base: str) -> Value:
    number = _integer(value)
    # A negative number is shown as its 64-bit two's complement.
    unsigned = number + (1 << _WORD_BITS) if number < 0 else number
    return Shown(Expr(cas.integer(number)), prefix + format(unsigned, base).upper())


@conversion("Base16")
def to_hexadecimal(host: Host, value: Value, args: list[Value]) -> Value:
    return _based(value, "0h", "x")


@conversion("Base2")
def to_binary(host: Host, value: Value, args: list[Value]) -> Value:
    return _based(value, "0b", "b")


@conversion("Base10")
def to_decimal_base(host: Host, value: Value, args: list[Value]) -> Value:
    return Expr(cas.integer(_integer(value)))


# ---- decimals and fractions ------------------------------------------------------------------


@conversion("Decimal")
def to_decimal(host: Host, value: Value, args: list[Value]) -> Value:
    return map_value(lambda v: Expr(cas.approximate(raw_of(v))), value)


@conversion("approxFraction")
def approx_fraction(host: Host, value: Value, args: list[Value]) -> Value:
    tolerance = cas.real_float(raw_of(args[0])) if args else cas.APPROX_FRACTION_TOLERANCE
    if tolerance is None or tolerance <= 0:
        raise TIError(errors.DOMAIN)
    return map_value(lambda v: Expr(cas.nearby_fraction(raw_of(v), tolerance)), value)


# ---- angles ----------------------------------------------------------------------------------


def _angle(host: Host, value: Value, target: Angle, unit_text: str) -> Value:
    settings = host.settings

    def convert(item: Value) -> Value:
        raw = angles.convert(raw_of(item), settings.angle, target)
        return Shown(Expr(raw), _with_unit(_show(raw, settings), unit_text))

    return map_value(convert, value)


@conversion("DD")
def to_degrees(host: Host, value: Value, args: list[Value]) -> Value:
    return _angle(host, value, Angle.DEGREE, "°")


@conversion("Rad")
def to_radians(host: Host, value: Value, args: list[Value]) -> Value:
    return _angle(host, value, Angle.RADIAN, "ʳ")


@conversion("Grad")
def to_gradians(host: Host, value: Value, args: list[Value]) -> Value:
    return _angle(host, value, Angle.GRADIAN, "ᵍ")


def _sexagesimal(degrees: float) -> str:
    sign = "-" if degrees < 0 else ""
    total = round(abs(degrees) * 3600, _SECONDS_PRECISION)
    whole, rest = divmod(total, 3600)
    minutes, seconds = divmod(rest, _SEXAGESIMAL)
    shown_seconds = f"{seconds:g}" if seconds else ""
    tail = f'{shown_seconds}"' if shown_seconds else ""
    return f"{sign}{int(whole)}°{int(minutes)}'{tail}"


@conversion("DMS")
def to_degrees_minutes_seconds(host: Host, value: Value, args: list[Value]) -> Value:
    settings = host.settings

    def convert(item: Value) -> Value:
        degrees = angles.convert(raw_of(item), settings.angle, Angle.DEGREE)
        number = cas.real_float(cas.approximate(degrees))
        if number is None:
            raise TIError(errors.DATA_TYPE)
        return Shown(Expr(degrees), _sexagesimal(number))

    return map_value(convert, value)


# ---- complex numbers and vectors -------------------------------------------------------------


def _exponential_form(modulus: Raw, argument: Raw, settings: Settings) -> str:
    """`ⅇ^(ⅈ*θ)*r` as the device writes it: the modulus last, and left out when it is 1."""
    angle = to_text(Expr(argument), settings)
    if argument.is_Add:
        angle = f"({angle})"
    sign, angle = ("-", angle[1:]) if angle.startswith("-") else ("", angle)
    text = f"ⅇ^({sign}ⅈ*{angle})"
    if modulus == 1:
        return text
    size = to_text(Expr(modulus), settings)
    return f"{text}*({size})" if modulus.is_Add else f"{text}*{size}"


def polar_form(value: Expr, settings: Settings) -> Value:
    """A complex number written as `r*ⅇ^(ⅈ*θ)`, or `(r∠θ)` when the angle is not in radians."""
    number = cas.number_value(value.raw)
    if number is None or number.imag == 0:
        return value
    modulus, argument = cas.polar_parts(value.raw)
    if settings.angle is Angle.RADIAN:
        # Finish the two parts, but not their product, which would turn back into a+bⅈ.
        text = _exponential_form(
            cas.finish(modulus, settings), cas.finish(argument, settings), settings
        )
    else:
        turned = angles.from_radians(argument, settings.angle)
        text = f"({_show(modulus, settings)}∠{_show(turned, settings)})"
    return Shown(value, text)


@conversion("Polar")
def to_polar(host: Host, value: Value, args: list[Value]) -> Value:
    settings = host.settings
    return map_value(lambda v: polar_form(Expr(raw_of(v)), settings), value)


@conversion("Rect")
def to_rectangular(host: Host, value: Value, args: list[Value]) -> Value:
    return map_value(lambda v: Expr(cas.rectangular(raw_of(v))), value)


def _vector_row(texts: list[str]) -> str:
    return "[" + " ".join(texts) + "]"


def _three_parts(value: Value) -> list[Raw]:
    parts = vector_parts(value)
    if len(parts) != _SPACE_VECTOR_PARTS:
        raise TIError(errors.DIMENSION_MISMATCH)
    return parts


@conversion("Cylind")
def to_cylindrical(host: Host, value: Value, args: list[Value]) -> Value:
    x, y, z = _three_parts(value)
    radius, azimuth = cas.cylindrical(x, y)
    settings = host.settings
    turned = angles.from_radians(azimuth, settings.angle)
    shown = [_show(radius, settings), "∠" + _show(turned, settings), _show(z, settings)]
    return Shown(value, _vector_row(shown))


@conversion("Sphere")
def to_spherical(host: Host, value: Value, args: list[Value]) -> Value:
    x, y, z = _three_parts(value)
    radius, azimuth, polar = cas.spherical(x, y, z)
    settings = host.settings
    shown = [
        _show(radius, settings),
        "∠" + _show(angles.from_radians(azimuth, settings.angle), settings),
        "∠" + _show(angles.from_radians(polar, settings.angle), settings),
    ]
    return Shown(value, _vector_row(shown))


# ---- strings, lists and matrices -------------------------------------------------------------


@eager("string", 1)
def string(host: Host, args: list[Value]) -> Value:
    return Str(to_text(args[0], host.settings))


@eager("expr", 1)
def expression(host: Host, args: list[Value]) -> Value:
    """Read a string as an entry and evaluate it."""
    text = args[0]
    if not isinstance(text, Str):
        raise TIError(errors.DATA_TYPE)
    statements = parse(text.value).statements
    if len(statements) != 1:
        raise TIError(errors.SYNTAX)
    (statement,) = statements
    if isinstance(statement, ast.Assign | ast.Store | ast.Define | ast.Command):
        raise TIError(errors.SYNTAX)
    return host.expr(statement)


@eager("list▶mat", 1, 2)
def list_to_matrix(host: Host, args: list[Value]) -> Value:
    """A list becomes a one-row matrix, or a matrix with the given number of columns."""
    items = raw_list(args[0])
    if len(args) == 1:
        return matrix_of([items])
    columns = cas.integer_value(raw_of(args[1]))
    if columns is None or columns < 1 or len(items) % columns:
        raise TIError(errors.DIMENSION_MISMATCH)
    return matrix_of([items[i : i + columns] for i in range(0, len(items), columns)])


@eager("mat▶list", 1)
def matrix_to_list(host: Host, args: list[Value]) -> Value:
    if not isinstance(args[0], MatrixValue):
        raise TIError(errors.DATA_TYPE)
    return list_of([cell for row in raw_rows(args[0]) for cell in row])
