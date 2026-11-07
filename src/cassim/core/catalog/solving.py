"""Solving: `solve`, `cSolve`, `zeros`, `cZeros`, `polyRoots` and `polyEval`."""

from collections.abc import Callable

from cassim.core import angles, ast, errors
from cassim.core.catalog.registry import Host, eager, lazy
from cassim.core.compat import sympy_adapter as cas
from cassim.core.errors import TIError
from cassim.core.settings import variable_key
from cassim.core.valueops import list_of, raw_list, raw_of
from cassim.core.values import Bool, Expr, ListValue, Raw, Value


def _unknowns(host: Host, node: ast.Expr) -> list[str]:
    """The variable or `{x,y}` list named in the second argument, as it was typed."""
    nodes = node.items if isinstance(node, ast.ListLit) else (node,)
    if not nodes or not all(isinstance(n, ast.Name) for n in nodes):
        raise TIError(errors.SYNTAX)
    return [variable_key(host.settings, n.text) for n in nodes if isinstance(n, ast.Name)]


def _radian_converter(host: Host) -> Callable[[Raw], Raw] | None:
    unit = host.settings.angle
    return lambda raw: angles.to_radians(raw, unit)


def _equations(host: Host, node: ast.Expr, names: list[str]) -> list[Raw]:
    """Evaluate the equation(s) with the unknowns left symbolic, even if they hold a value."""
    symbols: dict[str, Value] = {name: Expr(cas.symbol(name)) for name in names}
    with host.bound(symbols):
        value = host.expr(node)
    items = list(value.items) if isinstance(value, ListValue) else [value]
    return [raw_of(item) for item in items]


def _unevaluated(name: str, equations: list[Raw], symbols: list[Raw]) -> Value:
    """Echo a call that could not be solved, built from the equation as it was understood."""
    if len(equations) != 1 or len(symbols) != 1:
        raise TIError(errors.DOMAIN)
    return Expr(cas.undefined_function(name, (equations[0], symbols[0])))


def _answer(condition: Raw) -> Value:
    decided = cas.truth(condition)
    return Bool(decided) if decided is not None else Expr(condition)


def _solve(host: Host, args: tuple[ast.Expr, ...], *, complex_roots: bool) -> Value:
    equation_node, unknown_node = args
    names = _unknowns(host, unknown_node)
    equations = _equations(host, equation_node, names)
    symbols = [cas.symbol(name) for name in names]
    if len(symbols) > 1:  # `solve(eq1 and eq2, {x,y})` is the same system as `{eq1, eq2}`
        equations = [part for equation in equations for part in cas.conjuncts(equation)]
    if len(equations) == 1 and len(symbols) == 1:
        condition = cas.solve_equation(
            equations[0],
            symbols[0],
            host.constraints,
            _radian_converter(host),
            complex_roots=complex_roots,
        )
    else:
        condition = cas.solve_system(equations, symbols)
    if condition is None:
        return _unevaluated("cSolve" if complex_roots else "solve", equations, symbols)
    return _answer(condition)


@lazy("solve", 2, cas=True)
def solve(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    return _solve(host, args, complex_roots=False)


@lazy("cSolve", 2, cas=True)
def c_solve(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    return _solve(host, args, complex_roots=True)


def _single_unknown(host: Host, node: ast.Expr) -> str:
    names = _unknowns(host, node)
    if len(names) != 1:
        raise TIError(errors.SYNTAX)
    return names[0]


def _zeros(host: Host, args: tuple[ast.Expr, ...], *, complex_roots: bool) -> Value:
    expression_node, unknown_node = args
    name = _single_unknown(host, unknown_node)
    (expression,) = _equations(host, expression_node, [name])
    symbol = cas.symbol(name)
    roots = cas.roots_of(expression, symbol, _radian_converter(host), complex_roots=complex_roots)
    if roots is None:
        return _unevaluated("cZeros" if complex_roots else "zeros", [expression], [symbol])
    return list_of(roots)


@lazy("zeroes", 2, cas=True)
@lazy("zeros", 2, cas=True)
def zeros(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    return _zeros(host, args, complex_roots=False)


@lazy("cZeros", 2, cas=True)
def c_zeros(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    return _zeros(host, args, complex_roots=True)


@lazy("polyRoots", 2, cas=True)
def poly_roots(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    polynomial_node, unknown_node = args
    name = _single_unknown(host, unknown_node)
    (polynomial,) = _equations(host, polynomial_node, [name])
    return list_of(cas.polynomial_roots(polynomial, cas.symbol(name)) or [])


@eager("polyEval", 2)
def poly_eval(host: Host, args: list[Value]) -> Value:
    return Expr(cas.polynomial_value(raw_list(args[0]), raw_of(args[1])))
