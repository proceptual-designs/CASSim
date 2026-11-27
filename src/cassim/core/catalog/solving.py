"""Solving: `solve`, `cSolve`, `zeros`, `cZeros`, `polyRoots` and `polyEval`."""

from collections.abc import Callable

from cassim.core import angles, ast, errors
from cassim.core.catalog.registry import Host, eager, lazy
from cassim.core.compat import sympy_adapter as cas
from cassim.core.errors import TIError
from cassim.core.settings import variable_key
from cassim.core.valueops import list_of, raw_list, raw_of
from cassim.core.values import Bool, Expr, ListValue, MatrixValue, Raw, Value


def _unknowns(host: Host, node: ast.Expr, *more: ast.Expr) -> list[str]:
    """The variable, `{x,y}` list or `x, y` named after the equation, as it was typed."""
    nodes = node.items if isinstance(node, ast.ListLit) else (node, *more)
    if not nodes or not all(isinstance(n, ast.Name) for n in nodes):
        raise TIError(errors.SYNTAX)
    names = [variable_key(host.settings, n.text) for n in nodes if isinstance(n, ast.Name)]
    if len(set(names)) != len(names):
        raise TIError(errors.TOO_MANY_ARGUMENTS)
    return names


def _radian_converter(host: Host) -> Callable[[Raw], Raw] | None:
    unit = host.settings.angle
    return lambda raw: angles.to_radians(raw, unit)


def _equations(host: Host, node: ast.Expr, names: list[str]) -> list[Raw]:
    """Evaluate the equation(s) with the unknowns left symbolic, even if they hold a value."""
    symbols: dict[str, Value] = {name: Expr(cas.symbol(name)) for name in names}
    with host.bound(symbols):
        vectors = _vector_equation(host, node)
        if vectors is not None:
            return vectors
        value = host.expr(node)
    items = list(value.items) if isinstance(value, ListValue) else [value]
    return [raw_of(item) for item in items]


def _vector_equation(host: Host, node: ast.Expr) -> list[Raw] | None:
    """`u=v` between two vectors or matrices is one equation per element (emulator check 6,
    K5 and K6: `solve(l1(t)=l2(s),s,t)`). None if `node` is not such an equation."""
    if not (isinstance(node, ast.Compare) and len(node.rest) == 1 and node.rest[0][0] == "="):
        return None
    left, right = host.expr(node.first), host.expr(node.rest[0][1])
    if not isinstance(left, ListValue | MatrixValue) or not isinstance(right, type(left)):
        return None
    left_parts, right_parts = _elements(left), _elements(right)
    if len(left_parts) != len(right_parts):
        raise TIError(errors.DIMENSION_MISMATCH)
    pairs = zip(left_parts, right_parts, strict=True)
    return [cas.relation("=", a, b) for a, b in pairs]


def _elements(value: ListValue | MatrixValue) -> list[Raw]:
    if isinstance(value, ListValue):
        return raw_list(value)
    return [raw_of(cell) for row in value.rows for cell in row]


def _require_relations(equations: list[Raw]) -> None:
    if not equations or not all(cas.is_boolean(equation) for equation in equations):
        raise TIError(errors.SYNTAX)


def _unevaluated(name: str, equations: list[Raw], symbols: list[Raw]) -> Value:
    """Echo a call that could not be solved, built from the equation as it was understood."""
    if len(equations) != 1 or len(symbols) != 1:
        raise TIError(errors.DOMAIN)
    return Expr(cas.undefined_function(name, (equations[0], symbols[0])))


def _answer(condition: Raw) -> Value:
    decided = cas.truth(condition)
    return Bool(decided) if decided is not None else Expr(condition)


def _solve(host: Host, args: tuple[ast.Expr, ...], *, complex_roots: bool) -> Value:
    equation_node, *unknown_nodes = args
    names = _unknowns(host, *unknown_nodes)
    equations = _equations(host, equation_node, names)
    _require_relations(equations)
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
    if condition is None and not complex_roots:
        condition = _numeric_fallback(host, equations, symbols)
    if condition is None:
        host.warn(errors.MORE_SOLUTIONS)  # emulator run 7, R7-A1c
        return _unevaluated("cSolve" if complex_roots else "solve", equations, symbols)
    return _answer(condition)


def _numeric_fallback(host: Host, equations: list[Raw], symbols: list[Raw]) -> Raw | None:
    """Decimal roots of one equation in one unknown that has no exact answer, with a warning,
    as TI gives `solve(ⅇ^(-2x)-2ⅇ^(-x)+1=x+2,x)` as `x=-0.750403` (FR-CALC-007)."""
    if len(equations) != 1 or len(symbols) != 1:
        return None
    if any(symbols[0] in constraint.free_symbols for constraint in host.constraints):
        return None  # a domain to respect: left to the exact solver
    unit = host.settings.angle
    equation = cas.with_trig_in_radians(equations[0], lambda raw: angles.to_radians(raw, unit))
    found = cas.numeric_solutions(equation, symbols[0])
    if found is not None:
        host.warn(errors.NUMERIC_SOLUTION)
    return found


@lazy("solve", 2, None, cas=True)
def solve(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    return _solve(host, args, complex_roots=False)


@lazy("cSolve", 2, None, cas=True)
def c_solve(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    return _solve(host, args, complex_roots=True)


@lazy("linSolve", 2, cas=True)
def lin_solve(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    """`linSolve(system, {x,y})`: the values of the unknowns as a list, `{2,1}`. The system is a
    list, the system template, or equations joined with `and`."""
    equation_node, unknown_node = args
    names = _unknowns(host, unknown_node)
    equations = _equations(host, equation_node, names)
    equations = [part for equation in equations for part in cas.conjuncts(equation)]
    values = cas.linear_solve(equations, [cas.symbol(name) for name in names])
    if values is None:
        raise TIError(errors.NO_SOLUTION)
    return list_of(values)


def _single_unknown(host: Host, node: ast.Expr) -> str:
    names = _unknowns(host, node)
    if len(names) != 1:
        raise TIError(errors.SYNTAX)
    return names[0]


def _zeros(host: Host, args: tuple[ast.Expr, ...], *, complex_roots: bool) -> Value:
    expression_node, unknown_node = args
    name = _single_unknown(host, unknown_node)
    (expression,) = _equations(host, expression_node, [name])
    if cas.is_boolean(expression):
        raise TIError(errors.SYNTAX)
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
