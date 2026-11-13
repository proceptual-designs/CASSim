"""Lists: building (`seq`), summarising (`sum`, `mean`, ...) and sorting (`SortA`, `SortD`)."""

from collections.abc import Callable

from cassim.core import ast, errors
from cassim.core.catalog.registry import Host, command, eager, lazy
from cassim.core.compat import sympy_adapter as cas
from cassim.core.errors import TIError
from cassim.core.settings import variable_key
from cassim.core.valueops import as_expr, list_of, raw_list, raw_of
from cassim.core.values import (
    Bool,
    Empty,
    Expr,
    ListValue,
    MatrixValue,
    Raw,
    Str,
    Value,
    Void,
)

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
        with host.bound({variable_key(host.settings, name.text): Expr(current)}):
            items.append(host.expr(body))
        current = current + step_raw
    return ListValue(tuple(items))


def _whole(host: Host, node: ast.Expr) -> int:
    number = cas.integer_value(_number(host.expr(node)))
    if number is None:
        raise TIError(errors.DOMAIN)
    return number


@lazy("seqgen", 4, 7)
def seqgen(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    """`seqgen(expr, var, depVar, {var0, varMax}[, initialTerms[, varStep[, ceiling]]])`: a
    sequence where `expr` may use earlier terms as `depVar(var-1)`. The initial terms give the
    first values; an empty element there is left out (the template's empty box, check 6 E14).
    Terms stop past varMax, or before the first whose size exceeds the ceiling."""
    body, var, dependent, bounds, *rest = args
    if not isinstance(var, ast.Name) or not isinstance(dependent, ast.Name):
        raise TIError(errors.SYNTAX)
    if not isinstance(bounds, ast.ListLit) or len(bounds.items) != 2:  # noqa: PLR2004
        raise TIError(errors.DIMENSION_MISMATCH)
    first, last = (_whole(host, item) for item in bounds.items)
    initial: list[Raw] = []
    if rest:
        given = host.expr(rest[0])
        items = given.items if isinstance(given, ListValue) else (given,)
        initial = [raw_of(item) for item in items if not isinstance(item, Empty)]
    step = _whole(host, rest[1]) if len(rest) > 1 else 1
    if step <= 0:
        raise TIError(errors.DOMAIN)
    ceiling = cas.number_value(_number(host.expr(rest[2]))) if len(rest) > 2 else None  # noqa: PLR2004
    name = variable_key(host.settings, dependent.text)
    terms: dict[int, Raw] = {}

    def term(position: Raw) -> Raw | None:
        index = cas.integer_value(position)
        return None if index is None else terms.get(index)

    items_out: list[Value] = []
    for count, n in enumerate(range(first, last + 1, step)):
        if count >= _MAX_LIST_LENGTH:
            raise TIError(errors.MEMORY)
        if count < len(initial):
            raw = initial[count]
        else:
            with host.bound({variable_key(host.settings, var.text): Expr(cas.integer(n))}):
                raw = raw_of(host.expr(body))
            raw = cas.replace_calls(raw, name, term)
            if cas.calls(raw, name):
                raise TIError(errors.DOMAIN)  # a term before the first one
        size = cas.number_value(raw)
        if ceiling is not None and size is not None and abs(size) > abs(ceiling):
            break
        terms[n] = raw
        items_out.append(Expr(raw))
    return ListValue(tuple(items_out))


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
    """Running sums; an empty element stays empty and adds nothing: {1,2,_,4} gives {1,3,_,7}."""
    if not isinstance(args[0], ListValue):
        raise TIError(errors.DATA_TYPE)
    items = args[0].items
    sums = iter(cas.running_sums([raw_of(item) for item in items if not isinstance(item, Empty)]))
    return ListValue(tuple(item if isinstance(item, Empty) else Expr(next(sums)) for item in items))


@eager("isVoid", 1)
def is_void(host: Host, args: list[Value]) -> Value:
    """Whether a value is an empty element; for a list, element by element."""
    value = args[0]
    if isinstance(value, ListValue):
        return ListValue(tuple(Bool(isinstance(item, Empty)) for item in value.items))
    return Bool(isinstance(value, Empty))


@eager("delVoid", 1)
def del_void(host: Host, args: list[Value]) -> Value:
    """The list without its empty elements."""
    if not isinstance(args[0], ListValue):
        raise TIError(errors.DATA_TYPE)
    return ListValue(tuple(item for item in args[0].items if not isinstance(item, Empty)))


def _take(args: list[Value], *, from_left: bool) -> Value:
    """The first (`left`) or last (`right`) n items of a list, or characters of a string."""
    source = args[0]
    count = cas.integer_value(raw_of(args[1])) if len(args) > 1 else None
    if len(args) > 1 and (count is None or count < 0):
        raise TIError(errors.DOMAIN)
    if isinstance(source, Str):
        letters = source.value
        n = len(letters) if count is None else min(count, len(letters))
        return Str(letters[:n] if from_left else letters[len(letters) - n :])
    items = raw_list(source)
    n = len(items) if count is None else min(count, len(items))
    return list_of(items[:n] if from_left else items[len(items) - n :])


@eager("left", 1, 2)
def left(host: Host, args: list[Value]) -> Value:
    return _take(args, from_left=True)


@eager("right", 1, 2)
def right(host: Host, args: list[Value]) -> Value:
    return _take(args, from_left=False)


@eager("dim", 1)
def dim(host: Host, args: list[Value]) -> Value:
    value = args[0]
    if isinstance(value, ListValue):
        return Expr(cas.integer(len(value.items)))
    if isinstance(value, MatrixValue):
        return list_of([cas.integer(len(value.rows)), cas.integer(len(value.rows[0]))])
    raise TIError(errors.DATA_TYPE)


def _stored_list(host: Host, node: ast.Expr) -> tuple[str, tuple[Value, ...]]:
    if not isinstance(node, ast.Name):
        raise TIError(errors.VARIABLE_NAME_NEEDED)
    name = variable_key(host.settings, node.text)
    stored = host.scope.get(name)
    if not isinstance(stored, ListValue):
        raise TIError(errors.DATA_TYPE)
    return name, stored.items


def sorted_order(items: tuple[Value, ...], *, descending: bool) -> list[int]:
    """The positions of `items` in sorted order, with the empty elements last (Reference Guide,
    Empty (Void) Elements). The rest must be numbers or expressions."""
    filled = [i for i, item in enumerate(items) if not isinstance(item, Empty)]
    order = cas.sort_order([raw_of(items[i]) for i in filled], descending=descending)
    empty = [i for i, item in enumerate(items) if isinstance(item, Empty)]
    return [filled[i] for i in order] + empty


def _sort(host: Host, args: tuple[ast.Expr, ...], *, descending: bool) -> Value:
    """Sort the first list, and reorder any others to match it."""
    if not args:
        raise TIError(errors.TOO_FEW_ARGUMENTS)
    lists = [_stored_list(host, arg) for arg in args]
    order = sorted_order(lists[0][1], descending=descending)
    if any(len(items) != len(order) for _, items in lists):
        raise TIError(errors.DIMENSION_MISMATCH)
    for name, items in lists:
        host.scope.define(name, ListValue(tuple(items[i] for i in order)))
    return Void()


@command("SortA")
def sort_ascending(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    return _sort(host, args, descending=False)


@command("SortD")
def sort_descending(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    return _sort(host, args, descending=True)
