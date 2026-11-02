"""Lists: building (`seq`), summarising (`sum`, `mean`, ...) and sorting (`SortA`, `SortD`)."""

from collections.abc import Callable

from cassim.core import ast, errors
from cassim.core.catalog.registry import Host, command, eager, lazy
from cassim.core.compat import sympy_adapter as cas
from cassim.core.errors import TIError
from cassim.core.valueops import as_expr, list_of, raw_list, raw_of
from cassim.core.values import Expr, ListValue, MatrixValue, Raw, Value, Void

# A list this long would not fit in the calculator's memory either.
_MAX_LIST_LENGTH = 100_000
# A sample standard deviation or variance needs at least two values.
_SAMPLE_MINIMUM = 2


def _number(value: Value) -> Raw:
    raw = raw_of(value)
    if cas.number_value(raw) is None:
        raise TIError(errors.DATA_TYPE)
    return raw


@lazy("seq", 4, 5)
def seq(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    """`seq(expr, var, low, high[, step])`: evaluate `expr` with `var` at each value."""
    body, name, *bounds = args
    if not isinstance(name, ast.Name):
        raise TIError(errors.SYNTAX)
    low, high, *step = (_number(host.expr(bound)) for bound in bounds)
    step_raw: Raw = step[0] if step else cas.integer(1)
    direction = cas.number_value(step_raw)
    if direction is None or direction == 0:
        raise TIError(errors.DOMAIN)
    last = cas.number_value(high)
    assert last is not None
    ascending = direction.real > 0

    def within(value: Raw) -> bool:
        number = cas.number_value(value)
        assert number is not None
        return number.real <= last.real if ascending else number.real >= last.real

    items: list[Value] = []
    current = low
    while within(current):
        if len(items) >= _MAX_LIST_LENGTH:
            raise TIError(errors.MEMORY)
        with host.bound({name.text.casefold(): Expr(current)}):
            items.append(host.expr(body))
        current = current + step_raw
    return ListValue(tuple(items))


def _slice(host: Host, args: list[Value]) -> list[Raw]:
    """The list in `args[0]`, cut to the optional 1-based start and end in `args[1:]`."""
    items = raw_list(args[0])
    first, *rest = args[1:] or [Expr(cas.integer(1))]
    start = cas.integer_value(raw_of(first))
    end = cas.integer_value(raw_of(rest[0])) if rest else len(items)
    if start is None or end is None or not 1 <= start <= end <= len(items):
        raise TIError(errors.DOMAIN)
    return items[start - 1 : end]


@eager("sum", 1, 3)
def total(host: Host, args: list[Value]) -> Value:
    return Expr(cas.add_all(_slice(host, args)))


@eager("product", 1, 3)
def product(host: Host, args: list[Value]) -> Value:
    return Expr(cas.multiply_all(_slice(host, args)))


def _extreme(pick: Callable[[list[Raw]], Raw]) -> Callable[[Host, list[Value]], Value]:
    def run(host: Host, args: list[Value]) -> Value:
        if len(args) == 1:
            return Expr(pick(raw_list(args[0])))
        return Expr(pick([as_expr(arg).raw for arg in args]))

    return run


eager("min", 1, 2)(_extreme(cas.smallest))
eager("max", 1, 2)(_extreme(cas.largest))


def _summary(function: Callable[[list[Raw]], Raw]) -> Callable[[Host, list[Value]], Value]:
    def run(host: Host, args: list[Value]) -> Value:
        items = raw_list(args[0])
        if not items:
            raise TIError(errors.DOMAIN)
        return Expr(function(items))

    return run


def _sample(function: Callable[..., Raw], *, sample: bool) -> Callable[[list[Raw]], Raw]:
    def run(items: list[Raw]) -> Raw:
        if sample and len(items) < _SAMPLE_MINIMUM:
            raise TIError(errors.DOMAIN)
        return function(items, sample=sample)

    return run


eager("mean", 1)(_summary(cas.mean))
eager("median", 1)(_summary(cas.median))
eager("varSamp", 1)(_summary(_sample(cas.variance, sample=True)))
eager("varPop", 1)(_summary(_sample(cas.variance, sample=False)))
eager("stDevSamp", 1)(_summary(_sample(cas.standard_deviation, sample=True)))
eager("stDevPop", 1)(_summary(_sample(cas.standard_deviation, sample=False)))


@eager("cumulativeSum", 1)
def cumulative_sum(host: Host, args: list[Value]) -> Value:
    return list_of(cas.running_sums(raw_list(args[0])))


@eager("dim", 1)
def dim(host: Host, args: list[Value]) -> Value:
    value = args[0]
    if isinstance(value, ListValue):
        return Expr(cas.integer(len(value.items)))
    if isinstance(value, MatrixValue):
        return list_of([cas.integer(len(value.rows)), cas.integer(len(value.rows[0]))])
    raise TIError(errors.DATA_TYPE)


def _stored_list(host: Host, node: ast.Expr) -> tuple[str, list[Raw]]:
    if not isinstance(node, ast.Name):
        raise TIError(errors.VARIABLE_NAME_NEEDED)
    name = node.text.casefold()
    stored = host.scope.get(name)
    if not isinstance(stored, ListValue):
        raise TIError(errors.DATA_TYPE)
    return name, raw_list(stored)


def _sort(host: Host, args: tuple[ast.Expr, ...], *, descending: bool) -> Value:
    """Sort the first list, and reorder any others to match it."""
    if not args:
        raise TIError(errors.TOO_FEW_ARGUMENTS)
    lists = [_stored_list(host, arg) for arg in args]
    order = cas.sort_order(lists[0][1], descending=descending)
    if any(len(items) != len(order) for _, items in lists):
        raise TIError(errors.DIMENSION_MISMATCH)
    for name, items in lists:
        host.scope.define(name, list_of([items[i] for i in order]))
    return Void()


@command("SortA")
def sort_ascending(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    return _sort(host, args, descending=False)


@command("SortD")
def sort_descending(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    return _sort(host, args, descending=True)
