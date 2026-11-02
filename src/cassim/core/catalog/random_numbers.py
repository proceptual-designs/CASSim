"""Random numbers: `rand`, `randInt`, `randNorm`, `randBin` and the `RandSeed` command."""

import random
from collections.abc import Callable

from cassim.core import ast, errors
from cassim.core.catalog.registry import Host, command, eager
from cassim.core.compat import sympy_adapter as cas
from cassim.core.errors import TIError
from cassim.core.valueops import list_of, raw_of
from cassim.core.values import Expr, Raw, Value, Void

# The most values one call may ask for.
_MAX_COUNT = 100_000
_generator = random.Random()


def _count(args: list[Value], position: int) -> int | None:
    """The optional number of values asked for, or None for a single one."""
    if len(args) <= position:
        return None
    number = cas.integer_value(raw_of(args[position]))
    if number is None or not 0 <= number <= _MAX_COUNT:
        raise TIError(errors.DOMAIN)
    return number


def _draw(count: int | None, make: Callable[[], float | int]) -> Value:
    if count is None:
        return Expr(_number(make()))
    return list_of([_number(make()) for _ in range(count)])


def _number(value: float | int) -> Raw:
    return cas.integer(value) if isinstance(value, int) else cas.from_float(value)


def _real(value: Value) -> float:
    number = cas.real_float(raw_of(value))
    if number is None:
        raise TIError(errors.DATA_TYPE)
    return number


@eager("rand", 0, 1)
def rand(host: Host, args: list[Value]) -> Value:
    return _draw(_count(args, 0), _generator.random)


@eager("randInt", 2, 3)
def rand_int(host: Host, args: list[Value]) -> Value:
    """`randInt(low, high[, count])`: whole numbers from low to high, both included."""
    low, high = (cas.integer_value(raw_of(arg)) for arg in args[:2])
    if low is None or high is None:
        raise TIError(errors.DOMAIN)
    low, high = min(low, high), max(low, high)
    return _draw(_count(args, 2), lambda: _generator.randint(low, high))


@eager("randNorm", 2, 3)
def rand_norm(host: Host, args: list[Value]) -> Value:
    """`randNorm(mean, deviation[, count])`."""
    mean, deviation = _real(args[0]), _real(args[1])
    if deviation < 0:
        raise TIError(errors.DOMAIN)
    return _draw(_count(args, 2), lambda: _generator.gauss(mean, deviation))


@eager("randBin", 2, 3)
def rand_bin(host: Host, args: list[Value]) -> Value:
    """`randBin(trials, probability[, count])`."""
    trials, chance = cas.integer_value(raw_of(args[0])), _real(args[1])
    if trials is None or trials < 0 or not 0 <= chance <= 1:
        raise TIError(errors.DOMAIN)
    return _draw(_count(args, 2), lambda: sum(_generator.random() < chance for _ in range(trials)))


@command("RandSeed")
def rand_seed(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    """`RandSeed n` makes the following random numbers repeatable."""
    if len(args) != 1:
        raise TIError(errors.TOO_FEW_ARGUMENTS if not args else errors.TOO_MANY_ARGUMENTS)
    _generator.seed(cas.integer_value(raw_of(host.expr(args[0]))))
    return Void()
