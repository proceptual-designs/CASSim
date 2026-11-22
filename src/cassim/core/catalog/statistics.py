"""Statistics commands: OneVar, TwoVar and the regressions. Results go to the `stat.` variables."""

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from fractions import Fraction

from cassim.core import ast, errors
from cassim.core.catalog.registry import Host, command
from cassim.core.compat import inference as infer
from cassim.core.compat import statistics as stats
from cassim.core.compat import sympy_adapter as cas
from cassim.core.compat.statistics import REGRESSIONS as _REGRESSIONS
from cassim.core.compat.statistics import Regression
from cassim.core.errors import TIError
from cassim.core.parser import parse_expression
from cassim.core.scope import Function
from cassim.core.valueops import list_of
from cassim.core.values import Cell, Empty, Expr, ListValue, MatrixValue, Str, Value, Void


def _fraction(value: Value) -> Fraction:
    if isinstance(value, Expr):
        number = cas.to_fraction(value.raw)
        if number is not None:
            return number
    raise TIError(errors.DATA_TYPE)


def _numbers(value: Value) -> list[Fraction]:
    if not isinstance(value, ListValue):
        raise TIError(errors.DATA_TYPE)
    if not value.items:
        raise TIError(errors.INVALID_LIST_OR_MATRIX)
    return [_fraction(item) for item in value.items]


def _frequencies(value: Value, length: int) -> list[int]:
    """A frequency list, or a single number meaning that frequency for every value."""
    counts = (
        [_fraction(item) for item in value.items]
        if isinstance(value, ListValue)
        else [_fraction(value)] * length
    )
    if len(counts) != length:
        raise TIError(errors.DIMENSION_MISMATCH)
    if any(count < 0 or count.denominator != 1 for count in counts):
        raise TIError(errors.DOMAIN)
    return [int(count) for count in counts]


def _read(
    host: Host, args: tuple[ast.Expr, ...], lists: int
) -> tuple[list[list[Fraction]], list[int] | None]:
    """`[count,] X[, Y][, Freq[, Category, Include]]`: the data lists, and the frequencies if
    there are any. A leading number is TI's count of lists and is ignored. A frequency of 1
    changes nothing. With a category list and the categories to include, only those rows count:
    `OneVar d1,1,cat,{"a"}` (emulator check 6, S9).
    """
    values = [host.expr(arg) for arg in args]
    if values and isinstance(values[0], Expr) and cas.to_fraction(values[0].raw) is not None:
        values = values[1:]
    if len(values) < lists:
        raise TIError(errors.TOO_FEW_ARGUMENTS)
    values = _in_categories(values[: lists + 1], values[lists + 1 : lists + 3])
    values = _without_empty_rows(values)
    data = [_numbers(value) for value in values[:lists]]
    if len({len(column) for column in data}) != 1:
        raise TIError(errors.DIMENSION_MISMATCH)
    if len(values) == lists:
        return data, None
    return data, _frequencies(values[lists], len(data[0]))


def _category_key(item: Value) -> object:
    if isinstance(item, Str):
        return ("text", item.value)
    if isinstance(item, Expr):
        return ("number", item.raw)
    return ("other", repr(item))


# A category run takes the category list and the categories to include.
_CATEGORY_ARGUMENTS = 2


def _in_categories(values: list[Value], categories: list[Value]) -> list[Value]:
    """Keep the rows whose category is one of those to include."""
    if len(categories) < _CATEGORY_ARGUMENTS:
        return values
    category, include = categories
    if not isinstance(category, ListValue) or not isinstance(include, ListValue):
        raise TIError(errors.DATA_TYPE)
    wanted = {_category_key(item) for item in include.items}
    rows = [i for i, item in enumerate(category.items) if _category_key(item) in wanted]
    lists = [value for value in values if isinstance(value, ListValue)]
    if any(len(value.items) != len(category.items) for value in lists):
        raise TIError(errors.DIMENSION_MISMATCH)
    return [
        ListValue(tuple(value.items[i] for i in rows)) if isinstance(value, ListValue) else value
        for value in values
    ]


def _without_empty_rows(values: list[Value]) -> list[Value]:
    """Leave out every position where one of the lists has an empty element, as the handheld
    does for a void in X, Y or the frequencies (Reference Guide, Empty (Void) Elements)."""
    lists = [value for value in values if isinstance(value, ListValue)]
    if not lists or len({len(value.items) for value in lists}) != 1:
        return values
    gaps = {i for value in lists for i, item in enumerate(value.items) if isinstance(item, Empty)}
    if not gaps:
        return values
    return [
        ListValue(tuple(item for i, item in enumerate(value.items) if i not in gaps))
        if isinstance(value, ListValue)
        else value
        for value in values
    ]


def _decimal(number: float | Fraction) -> Expr:
    return Expr(cas.from_float(float(number)))


def _store(host: Host, name: str, value: Value | Function) -> None:
    host.scope.define(f"stat.{name}".casefold(), value)


def _equation(equation: str, coefficients: Mapping[str, float | Fraction]) -> Function:
    """`stat.RegEqn` as a function of x with the fitted numbers in it, so `stat.RegEqn(x)`
    gives the equation and a fitted line can be copied to `f1` (emulator check 6, run 4, S2,
    S3)."""

    def number(match: re.Match[str]) -> str:
        shown = format(float(coefficients[match.group()]), ".15g").replace("e", "ᴇ")
        return f"({shown})"

    names = "|".join(re.escape(name) for name in sorted(coefficients, key=len, reverse=True))
    text = re.sub(rf"(?<![A-Za-z]){names}(?![A-Za-z])", number, equation)
    return Function(("x",), parse_expression(text))


# ---- OneVar and TwoVar -----------------------------------------------------------------------

# TI's labels, letter for letter: a combining macron, subscript digits and Greek sigmas.
_MEAN_X, _MEAN_Y = "x̄", "ȳ"
_SUM, _SIGMA = "Σ", "σ"
_GOF_ARGUMENT_COUNT = 3


@dataclass(slots=True)
class _Results:
    """Statistics in the order TI lists them: (label, short stat. name, value)."""

    title: str
    rows: list[tuple[str, str, float | Fraction]] = field(default_factory=list)

    def add(self, label: str, name: str, value: float | Fraction) -> None:
        self.rows.append((label, name, value))

    def store(self, host: Host) -> None:
        cells: list[tuple[Cell, ...]] = [(Str("Title"), Str(self.title))]
        for label, name, value in self.rows:
            cells.append((Str(label), _decimal(value)))
            _store(host, name, _decimal(value))
        _store(host, "results", MatrixValue(tuple(cells)))
        values: tuple[Cell, ...] = (Str(self.title), *(_decimal(v) for _, _, v in self.rows))
        # One column, title first, so element k is `stat.values[k,1]` (emulator check 6, D24).
        _store(host, "values", MatrixValue(tuple((value,) for value in values)))


def _single_variable_rows(results: _Results, summary: stats.Summary, axis: str) -> None:
    mean = _MEAN_X if axis == "x" else _MEAN_Y
    results.add(mean, "v" if axis == "x" else "w", summary.mean)
    results.add(f"{_SUM}{axis}", f"sum{axis}", summary.total)
    results.add(f"{_SUM}{axis}²", f"sum{axis}2", summary.total_squares)
    results.add(f"s{axis} := sn-1{axis}", f"s{axis}", summary.sample_deviation)
    results.add(
        f"{_SIGMA}{axis} := {_SIGMA}n{axis}", f"{_SIGMA}{axis}", summary.population_deviation
    )


def _spread_rows(results: _Results, summary: stats.Summary, axis: str) -> None:
    upper = axis.upper()
    results.add(f"Min{upper}", f"min{axis}", summary.minimum)
    results.add(f"Q₁{upper}", f"q1{axis}", summary.q1)
    results.add(f"Median{upper}", f"med{axis}", summary.median)
    results.add(f"Q₃{upper}", f"q3{axis}", summary.q3)
    results.add(f"Max{upper}", f"max{axis}", summary.maximum)


def _sum_of_squares_row(results: _Results, summary: stats.Summary, axis: str) -> None:
    mean = _MEAN_X if axis == "x" else _MEAN_Y
    label = f"SS{axis.upper()} := {_SUM}({axis}-{mean})²"
    results.add(label, f"ss{axis}", summary.sum_squared_deviations)


@command("OneVar")
def one_var(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    """`OneVar x[, freq]`."""
    (column,), frequencies = _read(host, args, 1)
    summary = stats.summarise(stats.expand(column, frequencies))
    results = _Results("One-Variable Statistics")
    _single_variable_rows(results, summary, "x")
    results.add("n", "n", summary.n)
    _spread_rows(results, summary, "x")
    _sum_of_squares_row(results, summary, "x")
    results.store(host)
    return Void()


@command("TwoVar")
def two_var(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    """`TwoVar x, y[, freq]`."""
    (xs, ys), frequencies = _read(host, args, 2)
    xs, ys = stats.expand(xs, frequencies), stats.expand(ys, frequencies)
    x, y = stats.summarise(xs), stats.summarise(ys)
    results = _Results("Two-Variable Statistics")
    _single_variable_rows(results, x, "x")
    results.add("n", "n", x.n)
    _single_variable_rows(results, y, "y")
    results.add(f"{_SUM}xy", "sumxy", stats.cross_total(xs, ys))
    results.add("r", "r", stats.correlation(xs, ys))
    _spread_rows(results, x, "x")
    _spread_rows(results, y, "y")
    _sum_of_squares_row(results, x, "x")
    _sum_of_squares_row(results, y, "y")
    results.store(host)
    return Void()


def _run_regression(host: Host, args: tuple[ast.Expr, ...], kind: Regression) -> Value:
    (xs, ys), frequencies = _read(host, args, 2)
    xs, ys = stats.expand(xs, frequencies), stats.expand(ys, frequencies)
    try:
        fit = kind.fit(xs, ys)
    except ValueError, ZeroDivisionError, OverflowError:
        raise TIError(errors.DOMAIN) from None
    residuals = [float(y) - fit.predict(float(x)) for x, y in zip(xs, ys, strict=True)]
    cells: list[tuple[Cell, ...]] = [
        (Str("Title"), Str(kind.title)),
        (Str("RegEqn"), Str(kind.equation)),
    ]
    stored: dict[str, Value | Function] = {"regeqn": _equation(kind.equation, fit.coefficients)}
    for name, number in fit.coefficients.items():
        cells.append((Str(name), _decimal(number)))
        stored[name] = _decimal(number)
    if fit.r_squared is not None:
        cells.append((Str(kind.r_squared_label), _decimal(fit.r_squared)))
        stored[kind.r_squared_label] = _decimal(fit.r_squared)
    if fit.r is not None:
        cells.append((Str("r"), _decimal(fit.r)))
        stored["r"] = _decimal(fit.r)
    cells.append((Str("Resid"), Str("{...}")))
    if fit.transformed:
        cells.append((Str("ResidTrans"), Str("{...}")))
    stored["resid"] = list_of([cas.from_float(r) for r in residuals])
    stored["results"] = MatrixValue(tuple(cells))
    for name, value in stored.items():
        _store(host, name, value)
    return Void()


def _register(name: str, kind: Regression) -> None:
    @command(name)
    def run(host: Host, args: tuple[ast.Expr, ...]) -> Value:
        return _run_regression(host, args, kind)


for _name, _kind in _REGRESSIONS.items():
    _register(_name, _kind)


def _number_at(host: Host, args: tuple[ast.Expr, ...], index: int, default: float) -> float:
    return default if index >= len(args) else float(_fraction(host.expr(args[index])))


def _integer_at(host: Host, args: tuple[ast.Expr, ...], index: int, default: int) -> int:
    if index >= len(args):
        return default
    value = _fraction(host.expr(args[index]))
    if value.denominator != 1:
        raise TIError(errors.DOMAIN)
    return int(value)


def _list_argument(
    host: Host, args: tuple[ast.Expr, ...], index: int, frequency_index: int | None = None
) -> list[Fraction]:
    if index >= len(args):
        raise TIError(errors.TOO_FEW_ARGUMENTS)
    values = [host.expr(args[index])]
    if frequency_index is not None and frequency_index < len(args):
        values.append(host.expr(args[frequency_index]))
    values = _without_empty_rows(values)
    data = _numbers(values[0])
    frequencies = _frequencies(values[1], len(data)) if len(values) > 1 else None
    expanded = stats.expand(data, frequencies)
    if not expanded:
        raise TIError(errors.INVALID_LIST_OR_MATRIX)
    return expanded


def _inference_result(
    host: Host, title: str, rows: list[tuple[str, str, float | Fraction]]
) -> Value:
    results = _Results(title)
    for label, name, value in rows:
        results.add(label, name, value)
    results.store(host)
    return Void()


@dataclass(frozen=True, slots=True)
class _IntervalResult:
    estimate_label: str
    estimate_name: str
    estimate: float
    lower: float
    upper: float
    margin: float
    degrees: float | None = None
    count: int | None = None


def _interval_rows(interval: _IntervalResult) -> list[tuple[str, str, float | Fraction]]:
    rows = [
        (interval.estimate_label, interval.estimate_name, interval.estimate),
        ("CLower", "CLower", interval.lower),
        ("CUpper", "CUpper", interval.upper),
        ("ME", "ME", interval.margin),
    ]
    if interval.degrees is not None:
        rows.append(("df", "df", interval.degrees))
    if interval.count is not None:
        rows.append(("n", "n", interval.count))
    return rows


@dataclass(frozen=True, slots=True)
class _TestResult:
    statistic_label: str
    statistic_name: str
    statistic: float
    p_value: float
    degrees: float | None = None
    rows: tuple[tuple[str, str, float | Fraction], ...] = ()


def _test_rows(test: _TestResult) -> list[tuple[str, str, float | Fraction]]:
    result = [
        (test.statistic_label, test.statistic_name, test.statistic),
        ("PVal", "PVal", test.p_value),
    ]
    if test.degrees is not None:
        result.append(("df", "df", test.degrees))
    return [*result, *test.rows]


def _has_list(host: Host, args: tuple[ast.Expr, ...], index: int) -> bool:
    return index < len(args) and isinstance(host.expr(args[index]), ListValue)


def _sample_summary(
    host: Host, args: tuple[ast.Expr, ...], list_index: int, frequency_index: int | None
) -> tuple[stats.Summary, list[Fraction]]:
    values = _list_argument(host, args, list_index, frequency_index)
    return stats.summarise(values), values


def _two_samples(
    host: Host,
    args: tuple[ast.Expr, ...],
    *,
    first_frequency: int = 2,
    second_frequency: int = 3,
) -> tuple[list[Fraction], list[Fraction]]:
    return (
        _list_argument(host, args, 0, first_frequency),
        _list_argument(host, args, 1, second_frequency),
    )


@command("tInterval")
def t_interval(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    """One-sample t interval from a list and frequency, or summary statistics."""
    if _has_list(host, args, 0):
        summary, _ = _sample_summary(host, args, 0, 1)
        level = _number_at(host, args, 2, 0.95)
        mean, deviation, count = float(summary.mean), summary.sample_deviation, summary.n
    else:
        mean, deviation = _number_at(host, args, 0, 0), _number_at(host, args, 1, 0)
        count, level = _integer_at(host, args, 2, 0), _number_at(host, args, 3, 0.95)
    try:
        lower, upper, margin = infer.mean_interval(mean, deviation, count, level, degrees=count - 1)
    except ValueError:
        raise TIError(errors.DOMAIN) from None
    return _inference_result(
        host,
        "t Interval",
        _interval_rows(_IntervalResult("x̄", "x̄", mean, lower, upper, margin, count - 1, count)),
    )


@command("zInterval")
def z_interval(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    sigma = _number_at(host, args, 0, 0)
    if _has_list(host, args, 1):
        summary, _ = _sample_summary(host, args, 1, 2)
        level = _number_at(host, args, 3, 0.95)
        mean, count = float(summary.mean), summary.n
    else:
        mean, count = _number_at(host, args, 1, 0), _integer_at(host, args, 2, 0)
        level = _number_at(host, args, 3, 0.95)
    if sigma <= 0:
        raise TIError(errors.DOMAIN)
    try:
        lower, upper, margin = infer.mean_interval(mean, sigma, count, level)
    except ValueError:
        raise TIError(errors.DOMAIN) from None
    return _inference_result(
        host,
        "z Interval",
        _interval_rows(_IntervalResult("x̄", "x̄", mean, lower, upper, margin, count=count)),
    )


@command("tInterval_2Samp")
def t_interval_two_samples(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    first, second = _two_samples(host, args)
    summary1, summary2 = stats.summarise(first), stats.summarise(second)
    sample1 = infer.Sample(float(summary1.mean), summary1.sample_deviation, len(first))
    sample2 = infer.Sample(float(summary2.mean), summary2.sample_deviation, len(second))
    level = _number_at(host, args, 4, 0.95)
    pooled = _integer_at(host, args, 5, 0) != 0
    try:
        lower, upper, margin, degrees = infer.two_sample_mean_interval(
            sample1, sample2, level, pooled=pooled
        )
    except ValueError:
        raise TIError(errors.DOMAIN) from None
    difference = sample1.mean - sample2.mean
    return _inference_result(
        host,
        "2-Sample t Interval",
        _interval_rows(
            _IntervalResult("x̄Diff", "x̄Diff", difference, lower, upper, margin, degrees)
        ),
    )


@command("zInterval_1Prop")
def z_interval_one_proportion(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    successes = _integer_at(host, args, 0, -1)
    count = _integer_at(host, args, 1, 0)
    level = _number_at(host, args, 2, 0.95)
    try:
        lower, upper, margin = infer.proportion_interval(successes, count, level)
    except ValueError:
        raise TIError(errors.DOMAIN) from None
    estimate = successes / count if count else 0.0
    return _inference_result(
        host,
        "1-Prop z Interval",
        _interval_rows(_IntervalResult("p̂", "p̂", estimate, lower, upper, margin, count=count)),
    )


@command("zInterval_2Prop")
def z_interval_two_proportions(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    successes1, count1 = _integer_at(host, args, 0, -1), _integer_at(host, args, 1, 0)
    successes2, count2 = _integer_at(host, args, 2, -1), _integer_at(host, args, 3, 0)
    level = _number_at(host, args, 4, 0.95)
    try:
        lower, upper, margin = infer.two_proportion_interval(
            successes1, count1, successes2, count2, level
        )
    except ValueError:
        raise TIError(errors.DOMAIN) from None
    difference = successes1 / count1 - successes2 / count2 if count1 and count2 else 0.0
    return _inference_result(
        host,
        "2-Prop z Interval",
        _interval_rows(_IntervalResult("p̂Diff", "p̂Diff", difference, lower, upper, margin)),
    )


@command("zTest_1Prop")
def z_test_one_proportion(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    null = _number_at(host, args, 0, 0)
    successes, count = _integer_at(host, args, 1, -1), _integer_at(host, args, 2, 0)
    alternative = _integer_at(host, args, 3, 0)
    try:
        statistic, p_value = infer.proportion_test(successes, count, null, alternative=alternative)
    except ValueError:
        raise TIError(errors.DOMAIN) from None
    estimate = successes / count if count else 0.0
    return _inference_result(
        host,
        "1-Prop z Test",
        _test_rows(
            _TestResult(
                "z",
                "z",
                statistic,
                p_value,
                rows=(("p̂", "p̂", estimate), ("n", "n", count)),
            )
        ),
    )


@command("zTest_2Prop")
def z_test_two_proportions(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    successes1, count1 = _integer_at(host, args, 0, -1), _integer_at(host, args, 1, 0)
    successes2, count2 = _integer_at(host, args, 2, -1), _integer_at(host, args, 3, 0)
    alternative = _integer_at(host, args, 4, 0)
    try:
        statistic, p_value = infer.two_proportion_test(
            successes1, count1, successes2, count2, alternative=alternative
        )
    except ValueError:
        raise TIError(errors.DOMAIN) from None
    return _inference_result(
        host, "2-Prop z Test", _test_rows(_TestResult("z", "z", statistic, p_value))
    )


@command("tTest")
def t_test(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    null = _number_at(host, args, 0, 0)
    if _has_list(host, args, 1):
        summary, _ = _sample_summary(host, args, 1, 2)
        sample = infer.Sample(float(summary.mean), summary.sample_deviation, summary.n)
        alternative = _integer_at(host, args, 3, 0)
    else:
        sample = infer.Sample(
            _number_at(host, args, 1, 0),
            _number_at(host, args, 2, 0),
            _integer_at(host, args, 3, 0),
        )
        alternative = _integer_at(host, args, 4, 0)
    try:
        statistic, p_value = infer.mean_test(
            sample, null, degrees=sample.count - 1, alternative=alternative
        )
    except ValueError:
        raise TIError(errors.DOMAIN) from None
    return _inference_result(
        host,
        "t Test",
        _test_rows(
            _TestResult(
                "t",
                "t",
                statistic,
                p_value,
                sample.count - 1,
                (("x̄", "x̄", sample.mean), ("n", "n", sample.count)),
            )
        ),
    )


@command("zTest")
def z_test(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    null, sigma = _number_at(host, args, 0, 0), _number_at(host, args, 1, 0)
    if _has_list(host, args, 2):
        summary, _ = _sample_summary(host, args, 2, 3)
        sample = infer.Sample(float(summary.mean), sigma, summary.n)
        alternative = _integer_at(host, args, 4, 0)
    else:
        sample = infer.Sample(_number_at(host, args, 2, 0), sigma, _integer_at(host, args, 3, 0))
        alternative = _integer_at(host, args, 4, 0)
    try:
        statistic, p_value = infer.mean_test(sample, null, alternative=alternative)
    except ValueError:
        raise TIError(errors.DOMAIN) from None
    return _inference_result(
        host,
        "z Test",
        _test_rows(
            _TestResult(
                "z",
                "z",
                statistic,
                p_value,
                rows=(("x̄", "x̄", sample.mean), ("n", "n", sample.count)),
            )
        ),
    )


@command("tTest_2Samp")
def t_test_two_samples(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    first, second = _two_samples(host, args)
    first_summary, second_summary = stats.summarise(first), stats.summarise(second)
    sample1 = infer.Sample(float(first_summary.mean), first_summary.sample_deviation, len(first))
    sample2 = infer.Sample(float(second_summary.mean), second_summary.sample_deviation, len(second))
    pooled = _integer_at(host, args, 4, 0) != 0
    alternative = _integer_at(host, args, 5, 0)
    try:
        statistic, p_value, degrees = infer.two_sample_mean_test(
            sample1, sample2, 0, pooled=pooled, alternative=alternative
        )
    except ValueError:
        raise TIError(errors.DOMAIN) from None
    return _inference_result(
        host,
        "2-Sample t Test",
        _test_rows(_TestResult("t", "t", statistic, p_value, degrees)),
    )


@command("zInterval_2Samp")
def z_interval_two_samples(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    sigma1, sigma2 = _number_at(host, args, 0, 0), _number_at(host, args, 1, 0)
    if _has_list(host, args, 2):
        first = _list_argument(host, args, 2, 4)
        second = _list_argument(host, args, 3, 5)
        mean1, mean2 = float(stats.summarise(first).mean), float(stats.summarise(second).mean)
        count1, count2 = len(first), len(second)
        level_index = 6
    else:
        mean1, count1 = _number_at(host, args, 2, 0), _integer_at(host, args, 3, 0)
        mean2, count2 = _number_at(host, args, 4, 0), _integer_at(host, args, 5, 0)
        level_index = 6
    level = _number_at(host, args, level_index, 0.95)
    difference = mean1 - mean2
    if sigma1 <= 0 or sigma2 <= 0 or count1 < 1 or count2 < 1:
        raise TIError(errors.DOMAIN)
    standard_error = math.sqrt(sigma1**2 / count1 + sigma2**2 / count2)
    try:
        _, _, margin = infer.mean_interval(0, standard_error, 1, level)
    except ValueError:
        raise TIError(errors.DOMAIN) from None
    return _inference_result(
        host,
        "2-Sample z Interval",
        _interval_rows(
            _IntervalResult(
                "x̄Diff", "x̄Diff", difference, difference - margin, difference + margin, margin
            )
        ),
    )


@command("zTest_2Samp")
def z_test_two_samples(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    sigma1, sigma2 = _number_at(host, args, 0, 0), _number_at(host, args, 1, 0)
    first = _list_argument(host, args, 2, 4)
    second = _list_argument(host, args, 3, 5)
    summary1, summary2 = stats.summarise(first), stats.summarise(second)
    count1, count2 = len(first), len(second)
    standard_error = math.sqrt(sigma1**2 / count1 + sigma2**2 / count2)
    try:
        statistic, p_value = infer.mean_test(
            infer.Sample(float(summary1.mean) - float(summary2.mean), standard_error, 1),
            0,
            alternative=_integer_at(host, args, 6, 0),
        )
    except ValueError:
        raise TIError(errors.DOMAIN) from None
    return _inference_result(
        host, "2-Sample z Test", _test_rows(_TestResult("z", "z", statistic, p_value))
    )


@command("FTest_2Samp")
def f_test_two_samples(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    first, second = _two_samples(host, args)
    summary1, summary2 = stats.summarise(first), stats.summarise(second)
    sample1 = infer.Sample(float(summary1.mean), summary1.sample_deviation, len(first))
    sample2 = infer.Sample(float(summary2.mean), summary2.sample_deviation, len(second))
    alternative = _integer_at(host, args, 4, 0)
    try:
        statistic, p_value, df1, df2 = infer.f_test(sample1, sample2, alternative=alternative)
    except ValueError:
        raise TIError(errors.DOMAIN) from None
    return _inference_result(
        host,
        "2-Sample F Test",
        _test_rows(
            _TestResult(
                "F",
                "F",
                statistic,
                p_value,
                rows=(("dfNumer", "dfNumer", df1), ("dfDenom", "dfDenom", df2)),
            )
        ),
    )


@command("χ²GOF")
def chi_square_goodness_of_fit(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    if len(args) < _GOF_ARGUMENT_COUNT:
        raise TIError(errors.TOO_FEW_ARGUMENTS)
    observed, expected = host.expr(args[0]), host.expr(args[1])
    if not isinstance(observed, ListValue) or not isinstance(expected, ListValue):
        raise TIError(errors.DATA_TYPE)
    try:
        statistic, p_value = infer.chi_square_goodness(
            [float(_fraction(item)) for item in observed.items],
            [float(_fraction(item)) for item in expected.items],
            float(_fraction(host.expr(args[2]))),
        )
    except ValueError:
        raise TIError(errors.DOMAIN) from None
    degrees = float(_fraction(host.expr(args[2])))
    return _inference_result(
        host,
        "χ² GOF",
        _test_rows(_TestResult("χ²", "χ²", statistic, p_value, degrees)),
    )


@command("χ²2way")
def chi_square_two_way(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    if not args:
        raise TIError(errors.TOO_FEW_ARGUMENTS)
    observed_value = host.expr(args[0])
    if not isinstance(observed_value, MatrixValue) or not observed_value.rows:
        raise TIError(errors.DATA_TYPE)
    rows = [[float(_fraction(cell)) for cell in row] for row in observed_value.rows]
    width = len(rows[0])
    if width == 0 or any(len(row) != width for row in rows):
        raise TIError(errors.DIMENSION_MISMATCH)
    row_totals = [sum(row) for row in rows]
    column_totals = [sum(row[column] for row in rows) for column in range(width)]
    total = sum(row_totals)
    degrees = (len(rows) - 1) * (width - 1)
    if total <= 0 or degrees <= 0:
        raise TIError(errors.DOMAIN)
    expected = [
        [row_total * column_total / total for column_total in column_totals]
        for row_total in row_totals
    ]
    try:
        statistic, p_value = infer.chi_square_goodness(
            [value for row in rows for value in row],
            [value for row in expected for value in row],
            degrees,
        )
    except ValueError:
        raise TIError(errors.DOMAIN) from None
    _store(
        host,
        "expected",
        MatrixValue(tuple(tuple(_decimal(value) for value in row) for row in expected)),
    )
    return _inference_result(
        host, "χ² 2-Way Test", _test_rows(_TestResult("χ²", "χ²", statistic, p_value, degrees))
    )


@command("LinRegtTest")
def linear_regression_t_test(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    xs = [float(value) for value in _list_argument(host, args, 0, 2)]
    ys = [float(value) for value in _list_argument(host, args, 1, 2)]
    null_slope = _number_at(host, args, 3, 0)
    alternative = _integer_at(host, args, 4, 0)
    try:
        statistic, p_value, degrees, intercept, slope, residual_deviation = (
            infer.regression_slope_test(xs, ys, null_slope, alternative=alternative)
        )
    except ValueError:
        raise TIError(errors.DOMAIN) from None
    slope_error = residual_deviation / math.sqrt(sum((x - sum(xs) / len(xs)) ** 2 for x in xs))
    rows = _test_rows(
        _TestResult(
            "t",
            "t",
            statistic,
            p_value,
            degrees,
            (
                ("a", "a", intercept),
                ("b", "b", slope),
                ("s", "s", residual_deviation),
                ("SESlope", "SESlope", slope_error),
            ),
        )
    )
    result = _inference_result(host, "Linear Regression t Test", rows)
    # The fitted line, so the sheet's `CopyVar stat.RegEqn,f1` can graph it (plan B11).
    _store(host, "regeqn", _equation("a+b*x", {"a": intercept, "b": slope}))
    return result


@command("LinRegtIntervals")
def linear_regression_t_interval(host: Host, args: tuple[ast.Expr, ...]) -> Value:
    xs = [float(value) for value in _list_argument(host, args, 0, 2)]
    ys = [float(value) for value in _list_argument(host, args, 1, 2)]
    null_slope = _number_at(host, args, 3, 0)
    level = _number_at(host, args, 4, 0.95)
    try:
        statistic, _, degrees, intercept, slope, residual_deviation = infer.regression_slope_test(
            xs, ys, null_slope
        )
        slope_error = residual_deviation / math.sqrt(sum((x - sum(xs) / len(xs)) ** 2 for x in xs))
        _, _, margin = infer.mean_interval(0, slope_error, 1, level, degrees=degrees)
    except ValueError:
        raise TIError(errors.DOMAIN) from None
    return _inference_result(
        host,
        "Linear Regression t Intervals",
        [
            *_interval_rows(
                _IntervalResult(
                    "b", "b", slope, slope - margin, slope + margin, margin, degrees=degrees
                )
            ),
            ("a", "a", intercept),
            ("s", "s", residual_deviation),
            ("t", "t", statistic),
        ],
    )


# The commands that leave their results in `stat.results`, a (label, value) matrix: what a
# spreadsheet's Stat Calculations run and lay out in two columns (slice 3c).
RESULT_COMMANDS = (
    "OneVar",
    "TwoVar",
    *_REGRESSIONS,
    "tInterval",
    "zInterval",
    "tInterval_2Samp",
    "zInterval_1Prop",
    "zInterval_2Prop",
    "tTest",
    "zTest",
    "tTest_2Samp",
    "zInterval_2Samp",
    "zTest_2Samp",
    "FTest_2Samp",
    "zTest_1Prop",
    "zTest_2Prop",
    "χ²GOF",
    "χ²2way",
    "LinRegtTest",
    "LinRegtIntervals",
)
