"""Elementary functions: roots, exponentials, logarithms, trigonometry, rounding and counting."""

from collections.abc import Callable

from cassim.core import angles, errors
from cassim.core.catalog.registry import Host, eager
from cassim.core.compat import sympy_adapter as cas
from cassim.core.errors import TIError
from cassim.core.format import to_text
from cassim.core.settings import Angle
from cassim.core.valueops import as_expr, map_value, raw_of
from cassim.core.values import Bool, Expr, Raw, Shown, Value

_FORWARD_TRIG = frozenset({"sin", "cos", "tan", "sec", "csc", "cot"})
_INVERSE_TRIG = frozenset({"arcsin", "arccos", "arctan", "arcsec", "arccsc", "arccot"})
_HYPERBOLIC = frozenset({"sinh", "cosh", "tanh", "sech", "csch", "coth"})
_INVERSE_HYPERBOLIC = frozenset({"arcsinh", "arccosh", "arctanh"})


def _compute(name: str, raw: Raw, angle: Angle) -> Raw:
    function = cas.FUNCTIONS[name]
    if name in _FORWARD_TRIG:
        # A symbolic argument stays as typed, so sin(x) in Degree mode prints as sin(x).
        is_number = cas.number_value(raw) is not None
        return function(angles.to_radians(raw, angle) if is_number else raw)
    if name in _INVERSE_TRIG:
        result = function(raw)
        return result if cas.is_symbolic(result) else angles.from_radians(result, angle)
    if name in _HYPERBOLIC:
        return cas.hyperbolic(name, raw)
    if name in _INVERSE_HYPERBOLIC:
        return cas.inverse_hyperbolic(name, raw)
    return function(raw)


def _kept_as_typed(name: str, raw: Raw, result: Raw, angle: Angle) -> bool:
    """Is this a trig function of a plain number that stays unevaluated, such as `sin(1)` in
    Degree mode (where SymPy holds `sin(π/180)`)? TI shows it as it was typed."""
    return (
        name in _FORWARD_TRIG
        and angle is not Angle.RADIAN
        and cas.number_value(raw) is not None
        and result.is_Function
    )


def _note_non_real(host: Host, raw: Raw, result: Raw) -> None:
    """In Real mode a real number that gives a complex result (√-1, ln(-1), sin⁻¹(2)) is an error
    unless the final value is real, as in √(-1)·√(-1) (device: -1 with a warning triangle)."""
    if host.settings.domain == "real" and raw.is_real is True and cas.is_non_real_number(result):
        host.note_non_real()


def _unary(name: str) -> Callable[[Host, list[Value]], Value]:
    def run(host: Host, args: list[Value]) -> Value:
        settings = host.settings

        def one(value: Value) -> Value:
            raw = raw_of(value)
            result = _compute(name, raw, settings.angle)
            _note_non_real(host, raw, result)
            if _kept_as_typed(name, raw, result, settings.angle):
                return Shown(Expr(result), f"{name}({to_text(Expr(raw), settings)})")
            return Expr(result)

        return map_value(one, args[0])

    return run


for _name in cas.FUNCTIONS:
    eager(_name, 1)(_unary(_name))


@eager("approx", 1)
def approx(host: Host, args: list[Value]) -> Value:
    return map_value(lambda value: Expr(cas.approximate(raw_of(value))), args[0])


@eager("exact", 1, cas=True)
def exact(host: Host, args: list[Value]) -> Value:
    return map_value(lambda value: Expr(cas.exact(raw_of(value))), args[0])


@eager("isPrime", 1)
def is_prime(host: Host, args: list[Value]) -> Value:
    """true or false for a whole number; a Domain error for anything else."""
    answer = cas.is_prime(raw_of(args[0]))
    if answer is None:
        raise TIError(errors.DOMAIN)
    return Bool(answer)


@eager("log", 1, 2)
def log(host: Host, args: list[Value]) -> Value:
    base = raw_of(args[1]) if len(args) > 1 else None

    def one(value: Value) -> Value:
        raw = raw_of(value)
        result = cas.log(raw, base)
        _note_non_real(host, raw, result)
        return Expr(result)

    return map_value(one, args[0])


@eager("iPart", 1)
def integer_part(host: Host, args: list[Value]) -> Value:
    return map_value(lambda value: Expr(cas.integer_part(raw_of(value))), args[0])


@eager("fPart", 1)
def fractional_part(host: Host, args: list[Value]) -> Value:
    return map_value(lambda value: Expr(cas.fractional_part(raw_of(value))), args[0])


@eager("round", 1, 2)
def round_value(host: Host, args: list[Value]) -> Value:
    # With no digits, round to 12 places: `round(2.5)` is 2.5 on the handheld (check 6, D4).
    places = 12
    if len(args) > 1:
        wanted = cas.integer_value(raw_of(args[1]))
        if wanted is None:
            raise TIError(errors.DOMAIN)
        places = wanted

    def one(value: Value) -> Value:
        raw = raw_of(value)
        if cas.number_value(raw) is None:
            raise TIError(errors.DATA_TYPE)
        return Expr(cas.round_to(raw, places))

    return map_value(one, args[0])


def _pair(function: Callable[[Raw, Raw], Raw]) -> Callable[[Host, list[Value]], Value]:
    def run(host: Host, args: list[Value]) -> Value:
        left, right = as_expr(args[0]), as_expr(args[1])
        return Expr(function(left.raw, right.raw))

    return run


eager("remain", 2)(_pair(cas.remainder))


@eager("root", 2)
def root(host: Host, args: list[Value]) -> Value:
    """The nth-root template, `root(radicand, index)`. In Real mode an even root of a negative
    number is an error, as on the device (²√-4 gives "Non-real result")."""
    radicand = as_expr(args[0]).raw
    result = cas.nth_root(radicand, as_expr(args[1]).raw)
    _note_non_real(host, radicand, result)
    return Expr(result)


eager("nPr", 2)(_pair(cas.permutations))
eager("nCr", 2)(_pair(cas.combinations))
eager("gcd", 2)(_pair(cas.gcd))
eager("lcm", 2)(_pair(cas.lcm))
eager("mod", 2)(_pair(cas.modulo))
