"""Statistics commands: OneVar, TwoVar and the regressions. Results go to the `stat.` variables."""

import math
from collections.abc import Callable
from dataclasses import dataclass, field
from fractions import Fraction

from cassim.core import ast, errors
from cassim.core.catalog.registry import Host, command
from cassim.core.compat import statistics as stats
from cassim.core.compat import sympy_adapter as cas
from cassim.core.errors import TIError
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


def _store(host: Host, name: str, value: Value) -> None:
    host.scope.define(f"stat.{name}".casefold(), value)


# ---- OneVar and TwoVar -----------------------------------------------------------------------

# TI's labels, letter for letter: a combining macron, subscript digits and Greek sigmas.
_MEAN_X, _MEAN_Y = "x̄", "ȳ"
_SUM, _SIGMA = "Σ", "σ"


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


# ---- regressions -----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Fit:
    """What a regression found: named coefficients, a model to predict with, and how well."""

    coefficients: dict[str, float]
    predict: Callable[[float], float]
    r_squared: float | None = None
    r: float | None = None
    transformed: bool = False  # y = a*b^x and the like also report residuals of the straight line


@dataclass(frozen=True, slots=True)
class Regression:
    title: str
    equation: str
    r_squared_label: str  # "r²" for straight-line fits, "R²" for polynomials
    fit: Callable[[list[Fraction], list[Fraction]], Fit]


def _line(xs: list[Fraction], ys: list[Fraction], names: tuple[str, str]) -> Fit:
    line = stats.line_fit(xs, ys)
    first, second = names
    values = {first: line.intercept, second: line.slope}
    if names == ("m", "b"):
        values = {"m": line.slope, "b": line.intercept}
    return Fit(values, lambda x: line.intercept + line.slope * x, line.r_squared, line.r)


def _polynomial(xs: list[Fraction], ys: list[Fraction], degree: int) -> Fit:
    coefficients = stats.polynomial_fit(xs, ys, degree)
    names = "abcde"[: degree + 1]
    exact = stats.evaluate_polynomial

    def predict(x: float) -> float:
        return float(exact(coefficients, Fraction(x)))

    predicted = [predict(float(x)) for x in xs]
    r_squared = stats.coefficient_of_determination(ys, predicted)
    return Fit(dict(zip(names, (float(c) for c in coefficients), strict=True)), predict, r_squared)


def _exponential(xs: list[Fraction], ys: list[Fraction]) -> Fit:
    a, b, line = stats.exponential_fit(xs, ys)
    return Fit({"a": a, "b": b}, lambda x: a * b**x, line.r_squared, line.r, transformed=True)


def _power(xs: list[Fraction], ys: list[Fraction]) -> Fit:
    a, b, line = stats.power_fit(xs, ys)
    return Fit({"a": a, "b": b}, lambda x: a * x**b, line.r_squared, line.r, transformed=True)


def _logarithmic(xs: list[Fraction], ys: list[Fraction]) -> Fit:
    a, b, line = stats.logarithmic_fit(xs, ys)
    return Fit(
        {"a": a, "b": b}, lambda x: a + b * math.log(x), line.r_squared, line.r, transformed=True
    )


def _median_median(xs: list[Fraction], ys: list[Fraction]) -> Fit:
    slope, intercept = stats.median_median_line(xs, ys)
    m, b = float(slope), float(intercept)
    return Fit({"m": m, "b": b}, lambda x: m * x + b)


def _logistic(xs: list[Fraction], ys: list[Fraction], *, shifted: bool) -> Fit:
    found = stats.logistic_fit(xs, ys, shifted=shifted)
    a, b, c = found[:3]
    d = found[3] if shifted else 0.0
    names = dict(zip("abcd", found, strict=False))
    return Fit(names, lambda x: c / (1 + a * math.exp(-b * x)) + d)


def _sinusoid(xs: list[Fraction], ys: list[Fraction]) -> Fit:
    a, b, c, d = stats.sine_fit(xs, ys)
    return Fit({"a": a, "b": b, "c": c, "d": d}, lambda x: a * math.sin(b * x + c) + d)


_REGRESSIONS = {
    "LinRegBx": Regression(
        "Linear Regression (a+bx)", "a+b*x", "r²", lambda x, y: _line(x, y, ("a", "b"))
    ),
    "LinRegMx": Regression(
        "Linear Regression (mx+b)", "m*x+b", "r²", lambda x, y: _line(x, y, ("m", "b"))
    ),
    "QuadReg": Regression(
        "Quadratic Regression", "a*x^2+b*x+c", "R²", lambda x, y: _polynomial(x, y, 2)
    ),
    "CubicReg": Regression(
        "Cubic Regression", "a*x^3+b*x^2+c*x+d", "R²", lambda x, y: _polynomial(x, y, 3)
    ),
    "QuartReg": Regression(
        "Quartic Regression", "a*x^4+b*x^3+c*x^2+d*x+e", "R²", lambda x, y: _polynomial(x, y, 4)
    ),
    "ExpReg": Regression("Exponential Regression", "a*b^x", "r²", _exponential),
    "PowerReg": Regression("Power Regression", "a*x^b", "r²", _power),
    "LnReg": Regression("Logarithmic Regression", "a+b*ln(x)", "r²", _logarithmic),
    "MedMed": Regression("Median-Median Line", "m*x+b", "r²", _median_median),
    "Logistic": Regression(
        "Logistic Regression (d=0)",
        "c/(1+a*ⅇ^(-b*x))",
        "r²",
        lambda x, y: _logistic(x, y, shifted=False),
    ),
    "LogisticD": Regression(
        "Logistic Regression (d≠0)",
        "c/(1+a*ⅇ^(-b*x))+d",
        "r²",
        lambda x, y: _logistic(x, y, shifted=True),
    ),
    "SinReg": Regression("Sinusoidal Regression", "a*sin(b*x+c)+d", "r²", _sinusoid),
}


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
    stored: dict[str, Value] = {"regeqn": Str(kind.equation)}
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
