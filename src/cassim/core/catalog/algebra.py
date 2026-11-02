"""Algebra: expand, factor, partial fractions and common denominators."""

from collections.abc import Callable

from cassim.core.catalog.registry import Host, eager
from cassim.core.compat import sympy_adapter as cas
from cassim.core.format import to_text
from cassim.core.valueops import map_value, raw_of
from cassim.core.values import Expr, Raw, Shown, Value


def _rewrite(function: Callable[[Raw], Raw]) -> Callable[[Host, list[Value]], Value]:
    """An optional second argument names the variable; the rewrites here do not need it."""

    def run(host: Host, args: list[Value]) -> Value:
        return map_value(lambda value: Expr(function(raw_of(value))), args[0])

    return run


eager("expand", 1, 2, cas=True)(_rewrite(cas.expand))
eager("factor", 1, 2)(_rewrite(cas.factor))
eager("comDenom", 1, 2)(_rewrite(cas.common_denominator))
eager("cFactor", 1, 2, cas=True)(_rewrite(cas.factor_over_gaussian_integers))
eager("tExpand", 1, cas=True)(_rewrite(cas.expand_trig))
eager("tCollect", 1, cas=True)(_rewrite(cas.collect_trig))


def _proper_fraction(host: Host, value: Value) -> Value:
    raw = raw_of(value)
    if not raw.is_Rational or raw.is_Integer:
        return Expr(cas.partial_fractions(raw))
    # A rational number is shown as a whole part and a proper fraction: 7/3 is 2+1/3.
    whole, rest = cas.proper_fraction_text(raw)
    settings = host.settings
    fraction = to_text(Expr(abs(rest)), settings)
    sign = "-" if raw < 0 else "+"
    if whole == 0:
        return Expr(raw)
    return Shown(Expr(raw), f"{to_text(Expr(whole), settings)}{sign}{fraction}")


@eager("propFrac", 1, 2)
def prop_frac(host: Host, args: list[Value]) -> Value:
    return map_value(lambda value: _proper_fraction(host, value), args[0])
