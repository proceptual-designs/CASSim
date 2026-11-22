"""Calculus: derivatives, integrals, limits, series, extrema, tangents and ODEs."""

from cassim.core import ast, errors
from cassim.core.catalog.registry import Host, lazy
from cassim.core.compat import sympy_adapter as cas
from cassim.core.errors import TIError
from cassim.core.settings import CasMode, variable_key
from cassim.core.valueops import raw_of
from cassim.core.values import Expr, Raw, Value

# The order of the highest derivative that deSolve reads (`y''''`).
_MAX_ODE_ORDER = 4
# Argument counts at which an optional argument is present.
_WITH_ORDER = 3  # derivative(expr, x, n)
_INTEGRAL_UNBOUNDED_ARGS = 2
_INTEGRAL_BOUNDED_ARGS = 4
_WITH_DIRECTION = 4  # limit(expr, x, point, direction)
_WITH_POINT = 4  # taylor(expr, x, order, point)
_AVG_RC_WITH_STEP = 3  # avgRC(expr, x, step)


def _name_of(host: Host, node: ast.Expr) -> str:
    if not isinstance(node, ast.Name):
        raise TIError(errors.SYNTAX)
    return variable_key(host.settings, node.text)


def _expression(host: Host, node: ast.Expr, names: list[str]) -> Raw:
    """Evaluate `node` with the variables of the calculation left symbolic."""
    symbols: dict[str, Value] = {name: Expr(cas.symbol(name)) for name in names}
    with host.bound(symbols):
        return raw_of(host.expr(node))


def _count(host: Host, node: ast.Expr) -> int:
    value = cas.integer_value(raw_of(host.expr(node)))
    if value is None or value < 1:
        raise TIError(errors.DOMAIN)
    return value


def _at_current(raw: Raw, name: str, current: Value | None) -> Raw:
    """If the variable already had a value, such as a function's argument, put it in."""
    if isinstance(current, Expr):
        return cas.substitute(raw, cas.symbol(name), current.raw)
    return raw


def _result(raw: Raw | None, call: str, expression: Raw, name: str) -> Value:
    """A finished value, or the call as it was understood if SymPy had no closed form."""
    if raw is None:
        return Expr(cas.undefined_function(call, (expression, cas.symbol(name))))
    return Expr(raw)


@lazy("derivative", 2, 3)
def derivative(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    """`derivative(expr, x[, n])`. A value the variable already has is put in afterwards, so that
    `df(x):=derivative(f(x),x)` gives `df(3)=6`, as TI does."""
    name = _name_of(host, args[1])
    order = _count(host, args[2]) if len(args) == _WITH_ORDER else 1
    current = host.lookup(name)
    expression = _expression(host, args[0], [name])
    result = _at_current(cas.differentiate(expression, cas.symbol(name), order), name, current)
    if host.settings.cas_mode != CasMode.ON and cas.is_symbolic(result):
        raise TIError(errors.USE_DERIVATIVE_AT_POINT)
    return Expr(result)


@lazy("integral", 2, 4)
@lazy("∫", 2, 4)
def integral(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    """`integral(expr, x)` or `integral(expr, x, lower, upper)`."""
    if len(args) not in (_INTEGRAL_UNBOUNDED_ARGS, _INTEGRAL_BOUNDED_ARGS):
        raise TIError(errors.TOO_FEW_ARGUMENTS)
    name = _name_of(host, args[1])
    expression = _expression(host, args[0], [name])
    bounds = [raw_of(host.expr(arg)) for arg in args[2:]]
    lower, upper = bounds if bounds else (None, None)
    result = cas.integrate(expression, cas.symbol(name), lower, upper)
    if result is None and bounds:
        # Echoed with its bounds: `∫` without them would be a different calculation.
        call = (expression, cas.symbol(name), *bounds)
        return Expr(cas.undefined_function("integral", call))
    return _result(result, "integral", expression, name)


def _series(host: Host, args: tuple[ast.Expr, ...], call: str, *, product: bool) -> Value:
    name = _name_of(host, args[1])
    expression = _expression(host, args[0], [name])
    lower, upper = (raw_of(host.expr(arg)) for arg in args[2:])
    result = cas.series_total(expression, cas.symbol(name), lower, upper, product=product)
    return _result(result, call, expression, name)


@lazy("sumSeq", 4)
@lazy("Σ", 4)
@lazy("∑", 4)
def sum_seq(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    """`sumSeq(expr, k, low, high)`: the template `Σ(expr, k, low, high)`; `high` may be `∞`."""
    return _series(host, args, "sumSeq", product=False)


@lazy("prodSeq", 4)
@lazy("Π", 4)
@lazy("∏", 4)
def prod_seq(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    """`prodSeq(expr, k, low, high)`: the template `Π(expr, k, low, high)`."""
    return _series(host, args, "prodSeq", product=True)


@lazy("limit", 3, 4, cas=True)
@lazy("lim", 3, 4, cas=True)
def limit(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    """`limit(expr, x, point[, direction])`: direction 1 is from the right, -1 from the left."""
    name = _name_of(host, args[1])
    expression = _expression(host, args[0], [name])
    point = raw_of(host.expr(args[2]))
    direction = None
    if len(args) == _WITH_DIRECTION:
        direction = cas.integer_value(raw_of(host.expr(args[3])))
        if direction not in (-1, 0, 1):
            raise TIError(errors.DOMAIN)
        direction = direction or None
    result = cas.limit(expression, cas.symbol(name), point, direction)
    return _result(result, "limit", expression, name)


@lazy("taylor", 3, 4, cas=True)
def taylor(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    """`taylor(expr, x, order[, point])`."""
    name = _name_of(host, args[1])
    expression = _expression(host, args[0], [name])
    order = cas.integer_value(raw_of(host.expr(args[2])))
    if order is None or order < 0:
        raise TIError(errors.DOMAIN)
    point = raw_of(host.expr(args[3])) if len(args) == _WITH_POINT else cas.integer(0)
    return Expr(cas.taylor(expression, cas.symbol(name), order, point))


def _extremum(host: Host, args: tuple[ast.Expr, ...], *, maximum: bool) -> Value:
    name = _name_of(host, args[1])
    expression = _expression(host, args[0], [name])
    found = cas.extremum(expression, cas.symbol(name), host.constraints, maximum=maximum)
    return _result(found, "fMax" if maximum else "fMin", expression, name)


@lazy("fMax", 2, cas=True)
def f_max(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    return _extremum(host, args, maximum=True)


@lazy("fMin", 2, cas=True)
def f_min(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    return _extremum(host, args, maximum=False)


def _line(host: Host, args: tuple[ast.Expr, ...], *, tangent: bool) -> Value:
    name = _name_of(host, args[1])
    expression = _expression(host, args[0], [name])
    point = raw_of(host.expr(args[2]))
    build = cas.tangent_line if tangent else cas.normal_line
    return Expr(build(expression, cas.symbol(name), point))


@lazy("tangentLine", 3, cas=True)
def tangent_line(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    return _line(host, args, tangent=True)


@lazy("normalLine", 3, cas=True)
def normal_line(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    return _line(host, args, tangent=False)


@lazy("impDif", 3, cas=True)
def implicit_derivative(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    """`impDif(equation, x, y)`: dy/dx."""
    x, y = _name_of(host, args[1]), _name_of(host, args[2])
    equation = _expression(host, args[0], [x, y])
    return Expr(cas.implicit_derivative(equation, cas.symbol(x), cas.symbol(y)))


def _point(host: Host, node: ast.Expr) -> tuple[str, Raw | None]:
    """A variable with an optional value after it, as in `x=3`."""
    if isinstance(node, ast.Compare) and len(node.rest) == 1 and node.rest[0][0] == "=":
        return _name_of(host, node.first), raw_of(host.expr(node.rest[0][1]))
    return _name_of(host, node), None


@lazy("nDerivative", 2, 3)
def n_derivative(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    """`nDerivative(expr, x=value[, order])`, as a decimal."""
    name, point = _point(host, args[1])
    if point is None:
        raise TIError(errors.SYNTAX)
    order = _count(host, args[2]) if len(args) == _WITH_ORDER else 1
    expression = _expression(host, args[0], [name])
    symbol = cas.symbol(name)
    slope = cas.substitute(cas.differentiate(expression, symbol, order), symbol, point)
    return Expr(cas.approximate(slope))


# The step avgRC uses when none is given.
_DEFAULT_STEP = 0.001


@lazy("avgRC", 2, 3)
def avg_rc(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    """`avgRC(expr, x[=value][, step])`: the average rate of change from x to x+step."""
    name, point = _point(host, args[1])
    if point is None:
        point = raw_of(host.lookup(name) or Expr(cas.symbol(name)))
    step = (
        raw_of(host.expr(args[2]))
        if len(args) == _AVG_RC_WITH_STEP
        else cas.decimal("0.001", exact=True)
    )
    expression = _expression(host, args[0], [name])
    symbol = cas.symbol(name)
    here = cas.substitute(expression, symbol, point)
    there = cas.substitute(expression, symbol, point + step)
    return Expr((there - here) / step)


@lazy("nInt", 4)
def n_int(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    """`nInt(expr, x, lower, upper)`, as a decimal."""
    name = _name_of(host, args[1])
    expression = _expression(host, args[0], [name])
    lower, upper = (raw_of(host.expr(arg)) for arg in args[2:])
    return Expr(cas.numerical_integral(expression, cas.symbol(name), lower, upper))


@lazy("nSolve", 2, 3)
def n_solve(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    """`nSolve(equation, x[=guess])`: one real root near the guess, as a decimal."""
    name, guess = _point(host, args[1])
    equation = _expression(host, args[0], [name])
    root = cas.numerical_root(equation, cas.symbol(name), guess)
    if root is None:
        raise TIError(errors.NO_SOLUTION)
    return Expr(root)


@lazy("deSolve", 3, cas=True)
def de_solve(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    """`deSolve(ode, x, y)`, with `y'=...` and optionally `and y(a)=b`."""
    x, y = _name_of(host, args[1]), _name_of(host, args[2])
    symbol = cas.symbol(x)
    bindings: dict[str, Value] = {x: Expr(symbol), y: Expr(cas.function_of(y, symbol))}
    for order in range(1, _MAX_ODE_ORDER + 1):
        derivative_of_y = cas.derivative_of_function(y, symbol, order)
        bindings[y + "'" * order] = Expr(derivative_of_y)
    with host.bound(bindings):
        conditions = raw_of(host.expr(args[0]))
    solution = cas.solve_ode(conditions, symbol, y)
    if solution is None:
        raise TIError(errors.NO_SOLUTION)
    return Expr(solution)
