"""Control functions that choose what to evaluate."""

from cassim.core import ast
from cassim.core.catalog.registry import Host, lazy
from cassim.core.compat import sympy_adapter as cas
from cassim.core.valueops import raw_of
from cassim.core.values import Bool, Expr, Value

# `when(condition, then, otherwise, unknown)` has two arguments after `then`.
_WITH_UNKNOWN = 2


@lazy("when", 2, 4)
def when(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    """`when(condition, then[, otherwise[, unknown]])`: only the branch that is chosen is run.

    That is what lets a recursive definition such as `u(n):=when(n=1,2,u(n-1)+3)` end.
    """
    test, then, *rest = args
    condition = host.expr(test)
    truth = condition.value if isinstance(condition, Bool) else cas.truth(raw_of(condition))
    if truth is True:
        return host.expr(then)
    if truth is False:
        return host.expr(rest[0]) if rest else Expr(cas.constant("undef"))
    if len(rest) == _WITH_UNKNOWN:
        return host.expr(rest[1])
    # Undecided because the condition is symbolic: keep the choice for later.
    otherwise = raw_of(host.expr(rest[0])) if rest else None
    return Expr(cas.when(raw_of(condition), raw_of(host.expr(then)), otherwise))
