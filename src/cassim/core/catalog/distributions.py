"""Probability distributions: normal, t, chi-square, F, binomial, geometric and Poisson."""

import math
from collections.abc import Callable

from cassim.core import errors
from cassim.core.catalog.registry import Host, eager
from cassim.core.compat import distributions as dist
from cassim.core.compat import sympy_adapter as cas
from cassim.core.errors import TIError
from cassim.core.valueops import list_of, map_value, raw_of
from cassim.core.values import Expr, MatrixValue, Raw, Value

type Continuous = Callable[..., float]
type Entry = Callable[[Host, list[Value]], Value]

# A tolerance for deciding that a cumulative probability has reached a given area.
_AREA_TOLERANCE = 1e-12


def _real(value: Value) -> float:
    number = cas.real_float(raw_of(value))
    if number is None:
        raise TIError(errors.DATA_TYPE)
    return number


def _bound(value: Value) -> float:
    """A limit of integration, which may be infinite."""
    number = cas.bound_float(raw_of(value))
    if number is None:
        raise TIError(errors.DATA_TYPE)
    return number


def _decimal(function: Continuous, *numbers: float) -> Value:
    try:
        return Expr(cas.from_float(function(*numbers)))
    except ValueError:
        raise TIError(errors.DOMAIN) from None


def _parameters(args: list[Value], used: int, defaults: tuple[float, ...]) -> list[float]:
    """The numbers after the first `used` arguments, with defaults for those left out."""
    given = [_real(arg) for arg in args[used:]]
    return [*given, *defaults[len(given) :]]


def _pdf(function: Continuous, defaults: tuple[float, ...]) -> Entry:
    """`f(x, parameters...)`, where trailing parameters may be left out and x may be a list."""

    def run(host: Host, args: list[Value]) -> Value:
        extra = _parameters(args, 1, defaults)
        return map_value(lambda x: _decimal(function, _real(x), *extra), args[0])

    return run


def _cdf(function: Continuous, defaults: tuple[float, ...]) -> Entry:
    """`F(lower, upper, parameters...)`."""

    def run(host: Host, args: list[Value]) -> Value:
        extra = _parameters(args, 2, defaults)
        return _decimal(function, _bound(args[0]), _bound(args[1]), *extra)

    return run


def _inverse(function: Continuous, defaults: tuple[float, ...]) -> Entry:
    """`F^-1(area, parameters...)`."""

    def run(host: Host, args: list[Value]) -> Value:
        return _decimal(function, _real(args[0]), *_parameters(args, 1, defaults))

    return run


_STANDARD = (0.0, 1.0)
eager("normPdf", 1, 3)(_pdf(dist.norm_pdf, _STANDARD))
eager("normCdf", 2, 4)(_cdf(dist.norm_cdf, _STANDARD))
eager("invNorm", 1, 3)(_inverse(dist.inv_norm, _STANDARD))
eager("tPdf", 2)(_pdf(dist.t_pdf, ()))
eager("tCdf", 3)(_cdf(dist.t_cdf, ()))
eager("invT", 2)(_inverse(dist.inv_t, ()))
for _prefix in ("chi2", "χ²"):
    eager(f"{_prefix}Pdf", 2)(_pdf(dist.chi2_pdf, ()))
    eager(f"{_prefix}Cdf", 3)(_cdf(dist.chi2_cdf, ()))
eager("invChi2", 2)(_inverse(dist.inv_chi2, ()))
eager("invχ²", 2)(_inverse(dist.inv_chi2, ()))
eager("fPdf", 3)(_pdf(dist.f_pdf, ()))
eager("fCdf", 4)(_cdf(dist.f_cdf, ()))
eager("invF", 3)(_inverse(dist.inv_f, ()))


# Discrete distributions are worked out exactly where the inputs are exact.


def _count(value: Value) -> int:
    number = cas.integer_value(raw_of(value))
    if number is None or number < 0:
        raise TIError(errors.DOMAIN)
    return number


def _probability(value: Value) -> Raw:
    raw = raw_of(value)
    number = cas.real_float(raw)
    if number is None:
        raise TIError(errors.DATA_TYPE)
    if not 0 <= number <= 1:
        raise TIError(errors.DOMAIN)
    return raw


def _binomial_term(n: int, p: Raw, k: int) -> Raw:
    if k > n:
        return cas.integer(0)
    return cas.combinations(cas.integer(n), cas.integer(k)) * p**k * (1 - p) ** (n - k)


def _as_decimal(raw: Raw) -> Raw:
    """binomPdf and binomCdf give decimals even for exact arguments: `binomPdf(10,1/2,5)` is
    0.24609375 on the handheld (emulator check 6, D20)."""
    return cas.approximate(raw)


def _cumulative(term: Callable[[int], Raw], lower: int, upper: int) -> Raw:
    return cas.add_all([term(k) for k in range(lower, upper + 1)])


@eager("binomPdf", 2, 3)
def binom_pdf(host: Host, args: list[Value]) -> Value:
    """`binomPdf(n, p)` lists P(X=k) for every k; `binomPdf(n, p, x)` is P(X=x)."""
    n, p, *rest = args
    count, chance = _count(n), _probability(p)
    if not rest:
        return list_of([_as_decimal(_binomial_term(count, chance, k)) for k in range(count + 1)])
    return map_value(lambda x: Expr(_as_decimal(_binomial_term(count, chance, _count(x)))), rest[0])


@eager("binomCdf", 2, 4)
def binom_cdf(host: Host, args: list[Value]) -> Value:
    """`binomCdf(n,p)` lists P(X<=k); `binomCdf(n,p,x)` is P(X<=x); with `lower,upper` a range."""
    n, p, *rest = args
    count, chance = _count(n), _probability(p)

    def term(k: int) -> Raw:
        return _binomial_term(count, chance, k)

    if not rest:
        sums = cas.running_sums([term(k) for k in range(count + 1)])
        return list_of([_as_decimal(total) for total in sums])
    if len(rest) == 1:
        return map_value(
            lambda x: Expr(_as_decimal(_cumulative(term, 0, min(_count(x), count)))), rest[0]
        )
    lower, upper = _count(rest[0]), _count(rest[1])
    return Expr(_as_decimal(_cumulative(term, lower, min(upper, count))))


def _matrix_form(args: list[Value], index: int) -> bool:
    """The optional last argument of invBinom and invBinomN: 1 is the dialog's Matrix Form."""
    if len(args) <= index:
        return False
    flag = _count(args[index])
    if flag not in (0, 1):
        raise TIError(errors.DOMAIN)
    return flag == 1


def _neighbours(rows: list[tuple[int, float]]) -> MatrixValue:
    """Matrix Form: the value before the answer and the answer, each with its cumulative
    probability as a decimal (emulator run 6, R6-D1: `invBinom(0.9,10,0.5,1)` is
    `[[6,0.828125],[7,0.9453125]]`)."""
    return MatrixValue(
        tuple((Expr(cas.integer(k)), Expr(cas.from_float(chance))) for k, chance in rows)
    )


@eager("invBinom", 3, 4)
def inv_binom(host: Host, args: list[Value]) -> Value:
    """The smallest k with P(X<=k) at least the given area. With Matrix Form, the k before it
    too (with no k before 0, only the answer's row: a guess)."""
    area, n, p = _real(args[0]), _count(args[1]), _probability(args[2])
    matrix = _matrix_form(args, 3)
    if not 0 <= area <= 1:
        raise TIError(errors.DOMAIN)
    total = cas.integer(0)
    cumulative: list[float] = []
    answer = n
    for k in range(n + 1):
        total = total + _binomial_term(n, p, k)
        cumulative.append(cas.real_float(total) or 0.0)
        if cumulative[-1] >= area - _AREA_TOLERANCE:
            answer = k
            break
    if not matrix:
        return Expr(cas.integer(answer))
    return _neighbours([(k, cumulative[k]) for k in range(max(answer - 1, 0), answer + 1)])


_MOST_TRIALS = 100_000  # invBinomN stops looking here


@eager("invBinomN", 3, 4)
def inv_binom_n(host: Host, args: list[Value]) -> Value:
    """`invBinomN(area, p, x)`: the fewest trials n for which P(X<=x) is below the area. On the
    device an exact tie moves on, so invBinomN(0.5,0.5,5) is 12, not 11 (P(X<=5) is 0.5 at 11).
    With Matrix Form, the n before it too: `invBinomN(0.9,0.5,5,1)` is
    `[[7,0.9375],[8,0.85546875]]` (emulator run 6, R6-D1)."""
    area, chance, successes = _real(args[0]), _real(args[1]), _count(args[2])
    matrix = _matrix_form(args, 3)
    if not (0 < area < 1 and 0 < chance < 1):
        raise TIError(errors.DOMAIN)

    def below(trials: int) -> float:
        return sum(
            math.comb(trials, k) * chance**k * (1 - chance) ** (trials - k)
            for k in range(successes + 1)
        )

    for trials in range(successes, _MOST_TRIALS):
        if below(trials) < area - _AREA_TOLERANCE:
            if not matrix:
                return Expr(cas.integer(trials))
            first = max(trials - 1, successes)
            return _neighbours([(n, below(n)) for n in range(first, trials + 1)])
    raise TIError(errors.DOMAIN)


def _geometric_term(p: Raw, k: int) -> Raw:
    return cas.integer(0) if k < 1 else p * (1 - p) ** (k - 1)


@eager("geomPdf", 2)
def geom_pdf(host: Host, args: list[Value]) -> Value:
    chance = _probability(args[0])
    return map_value(lambda x: Expr(_geometric_term(chance, _count(x))), args[1])


@eager("geomCdf", 2, 3)
def geom_cdf(host: Host, args: list[Value]) -> Value:
    """`geomCdf(p, x)` is P(X<=x); `geomCdf(p, lower, upper)` is P(lower<=X<=upper)."""
    p, *bounds = args
    chance = _probability(p)
    lower, upper = (1, _count(bounds[0])) if len(bounds) == 1 else map(_count, bounds)
    return Expr(_cumulative(lambda k: _geometric_term(chance, k), lower, upper))


def _poisson_term(rate: Raw, k: int) -> Raw:
    exponential = cas.FUNCTIONS["exp"](-rate)
    return cas.approximate(rate**k * exponential / cas.factorial(cas.integer(k)))


def _rate(value: Value) -> Raw:
    raw = raw_of(value)
    number = cas.real_float(raw)
    if number is None:
        raise TIError(errors.DATA_TYPE)
    if number <= 0:
        raise TIError(errors.DOMAIN)
    return raw


@eager("poissPdf", 2)
def poiss_pdf(host: Host, args: list[Value]) -> Value:
    rate = _rate(args[0])
    return map_value(lambda x: Expr(_poisson_term(rate, _count(x))), args[1])


@eager("poissCdf", 2, 3)
def poiss_cdf(host: Host, args: list[Value]) -> Value:
    """`poissCdf(λ, x)` is P(X<=x); `poissCdf(λ, lower, upper)` is P(lower<=X<=upper)."""
    lam, *bounds = args
    rate = _rate(lam)
    lower, upper = (0, _count(bounds[0])) if len(bounds) == 1 else map(_count, bounds)
    return Expr(_cumulative(lambda k: _poisson_term(rate, k), lower, upper))
