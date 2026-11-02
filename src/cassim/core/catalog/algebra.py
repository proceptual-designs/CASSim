"""Algebra: expand, factor, partial fractions and common denominators."""

from collections.abc import Callable

from cassim.core.catalog.registry import Host, eager
from cassim.core.compat import sympy_adapter as cas
from cassim.core.valueops import map_value, raw_of
from cassim.core.values import Expr, Raw, Value


def _rewrite(function: Callable[[Raw], Raw]) -> Callable[[Host, list[Value]], Value]:
    """An optional second argument names the variable; the rewrites here do not need it."""

    def run(host: Host, args: list[Value]) -> Value:
        return map_value(lambda value: Expr(function(raw_of(value))), args[0])

    return run


eager("expand", 1, 2, cas=True)(_rewrite(cas.expand))
eager("factor", 1, 2)(_rewrite(cas.factor))
eager("propFrac", 1, 2)(_rewrite(cas.partial_fractions))
eager("comDenom", 1, 2)(_rewrite(cas.common_denominator))
