"""Descriptive statistics and least-squares fits on plain numbers, with no SymPy or NumPy.

Data arrive as `Fraction`s, so a sum or a fit to exact data is exact and only the final square
roots, logarithms and nonlinear fits are floating point. Quartiles follow the TI and school
convention: the median of the lower and upper halves, with the median left out when n is odd.
"""

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from fractions import Fraction

type Vector = Sequence[Fraction]

_NAN = float("nan")
_MIN_POINTS = 3  # the median-median line needs a point for each of its three groups
_SINGULAR = 1e-300
_NEGLIGIBLE_COST = 1e-30
_LM_STEPS = 400
_LM_TOLERANCE = 1e-26
_FREQUENCY_GRID = 4000
_REFINEMENTS = 200
_GOLDEN = (math.sqrt(5) - 1) / 2


# ---- one and two variables ------------------------------------------------------------------


def expand(values: Vector, frequencies: Sequence[int] | None) -> list[Fraction]:
    """Repeat each value by its frequency; no frequencies means once each."""
    if frequencies is None:
        return list(values)
    if len(frequencies) != len(values) or any(f < 0 for f in frequencies):
        raise ValueError(frequencies)
    return [v for v, f in zip(values, frequencies, strict=True) for _ in range(f)]


def median(sorted_values: Sequence[Fraction]) -> Fraction:
    middle, odd = divmod(len(sorted_values), 2)
    return sorted_values[middle] if odd else (sorted_values[middle - 1] + sorted_values[middle]) / 2


def quartiles(values: Sequence[Fraction]) -> tuple[Fraction, Fraction, Fraction]:
    """(Q1, median, Q3) by the median-of-halves rule."""
    ordered = sorted(values)
    half = len(ordered) // 2
    lower, upper = ordered[:half], ordered[half + len(ordered) % 2 :]
    if not lower:  # one value: every quartile is that value
        return ordered[0], ordered[0], ordered[0]
    return median(lower), median(ordered), median(upper)


@dataclass(frozen=True, slots=True)
class Summary:
    """One-variable statistics. Square roots are floats; everything else stays exact."""

    n: int
    total: Fraction
    total_squares: Fraction
    mean: Fraction
    sum_squared_deviations: Fraction
    minimum: Fraction
    q1: Fraction
    median: Fraction
    q3: Fraction
    maximum: Fraction

    @property
    def sample_deviation(self) -> float:
        return math.sqrt(self.sum_squared_deviations / (self.n - 1)) if self.n > 1 else _NAN

    @property
    def population_deviation(self) -> float:
        return math.sqrt(self.sum_squared_deviations / self.n)


def summarise(values: Sequence[Fraction]) -> Summary:
    if not values:
        raise ValueError(values)
    n = len(values)
    total = sum(values, Fraction(0))
    mean = total / n
    q1, mid, q3 = quartiles(values)
    return Summary(
        n=n,
        total=total,
        total_squares=sum((v * v for v in values), Fraction(0)),
        mean=mean,
        sum_squared_deviations=sum(((v - mean) ** 2 for v in values), Fraction(0)),
        minimum=min(values),
        q1=q1,
        median=mid,
        q3=q3,
        maximum=max(values),
    )


def cross_total(xs: Vector, ys: Vector) -> Fraction:
    return sum((x * y for x, y in zip(xs, ys, strict=True)), Fraction(0))


def correlation(xs: Vector, ys: Vector) -> float:
    """Pearson's r, or nan if either variable does not vary."""
    x, y = summarise(xs), summarise(ys)
    covariance = cross_total(xs, ys) - x.total * y.total / x.n
    spread = x.sum_squared_deviations * y.sum_squared_deviations
    return float(covariance) / math.sqrt(spread) if spread else _NAN


# ---- linear least squares -------------------------------------------------------------------


def solve_linear(matrix: list[list[Fraction]], constants: list[Fraction]) -> list[Fraction]:
    """Solve a square system exactly by Gauss-Jordan elimination."""
    size = len(constants)
    rows = [[*row, constant] for row, constant in zip(matrix, constants, strict=True)]
    for column in range(size):
        pivot = next((r for r in range(column, size) if rows[r][column] != 0), None)
        if pivot is None:
            raise ValueError(column)
        rows[column], rows[pivot] = rows[pivot], rows[column]
        scale = rows[column][column]
        rows[column] = [value / scale for value in rows[column]]
        for other in range(size):
            if other != column and rows[other][column] != 0:
                factor = rows[other][column]
                rows[other] = [
                    a - factor * b for a, b in zip(rows[other], rows[column], strict=True)
                ]
    return [rows[i][size] for i in range(size)]


def polynomial_fit(xs: Vector, ys: Vector, degree: int) -> list[Fraction]:
    """Coefficients from the highest power down, by the normal equations."""
    if len(xs) != len(ys) or len(xs) <= degree:
        raise ValueError(degree)
    powers = [sum((x**p for x in xs), Fraction(0)) for p in range(2 * degree + 1)]
    matrix = [[powers[row + column] for column in range(degree + 1)] for row in range(degree + 1)]
    constants = [
        sum((y * x**row for x, y in zip(xs, ys, strict=True)), Fraction(0))
        for row in range(degree + 1)
    ]
    return solve_linear(matrix, constants)[::-1]


def coefficient_of_determination(observed: Vector, predicted: Sequence[float]) -> float:
    """1 - SSE/SST, for any model."""
    mean = float(sum(observed, Fraction(0)) / len(observed))
    total = sum((float(y) - mean) ** 2 for y in observed)
    error = sum((float(y) - p) ** 2 for y, p in zip(observed, predicted, strict=True))
    return 1 - error / total if total else _NAN


def evaluate_polynomial(coefficients: Sequence[Fraction], x: Fraction) -> Fraction:
    total = Fraction(0)
    for coefficient in coefficients:
        total = total * x + coefficient
    return total


# ---- fits that are linear after a transformation ---------------------------------------------


@dataclass(frozen=True, slots=True)
class LineFit:
    """y = intercept + slope * x, with r and r-squared of the (possibly transformed) data."""

    intercept: float
    slope: float
    r_squared: float

    @property
    def r(self) -> float:
        return (
            math.copysign(math.sqrt(self.r_squared), self.slope)
            if self.r_squared == self.r_squared
            else _NAN
        )


def line_fit(xs: Vector, ys: Vector) -> LineFit:
    slope, intercept = polynomial_fit(xs, ys, 1)
    predicted = [float(slope * x + intercept) for x in xs]
    return LineFit(float(intercept), float(slope), coefficient_of_determination(ys, predicted))


def _logs(values: Vector) -> list[Fraction]:
    if any(v <= 0 for v in values):
        raise ValueError(values)
    return [Fraction(math.log(float(v))) for v in values]


def exponential_fit(xs: Vector, ys: Vector) -> tuple[float, float, LineFit]:
    """y = a * b**x, from a line through (x, ln y). Returns a, b and that line."""
    fit = line_fit(xs, _logs(ys))
    return math.exp(fit.intercept), math.exp(fit.slope), fit


def power_fit(xs: Vector, ys: Vector) -> tuple[float, float, LineFit]:
    """y = a * x**b, from a line through (ln x, ln y). Returns a, b and that line."""
    fit = line_fit(_logs(xs), _logs(ys))
    return math.exp(fit.intercept), fit.slope, fit


def logarithmic_fit(xs: Vector, ys: Vector) -> tuple[float, float, LineFit]:
    """y = a + b * ln(x), from a line through (ln x, y). Returns a, b and that line."""
    fit = line_fit(_logs(xs), ys)
    return fit.intercept, fit.slope, fit


def median_median_line(xs: Vector, ys: Vector) -> tuple[Fraction, Fraction]:
    """The median-median line (slope, intercept): split the points by x into three groups, take
    the median point of each, and join the outer two with the average offset of all three."""
    if len(xs) < _MIN_POINTS:
        raise ValueError(len(xs))
    points = sorted(zip(xs, ys, strict=True))
    third, extra = divmod(len(points), 3)
    # 3k points split k,k,k; 3k+1 split k,k+1,k; 3k+2 split k+1,k,k+1.
    sizes = (third + extra // 2, third + extra % 2, third + extra // 2)
    groups, start = [], 0
    for size in sizes:
        groups.append(points[start : start + size])
        start += size
    centres = [(median(sorted(p[0] for p in g)), median(sorted(p[1] for p in g))) for g in groups]
    slope = (centres[2][1] - centres[0][1]) / (centres[2][0] - centres[0][0])
    offset = sum((y - slope * x for x, y in centres), Fraction(0)) / 3
    return slope, offset


# ---- nonlinear fits ---------------------------------------------------------------------------


def _solve_floats(matrix: list[list[float]], constants: list[float]) -> list[float] | None:
    size = len(constants)
    rows = [[*row, constant] for row, constant in zip(matrix, constants, strict=True)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda r: abs(rows[r][column]))
        if abs(rows[pivot][column]) < _SINGULAR:
            return None
        rows[column], rows[pivot] = rows[pivot], rows[column]
        for other in range(column + 1, size):
            factor = rows[other][column] / rows[column][column]
            rows[other] = [a - factor * b for a, b in zip(rows[other], rows[column], strict=True)]
    solution = [0.0] * size
    for row in range(size - 1, -1, -1):
        known = sum(rows[row][c] * solution[c] for c in range(row + 1, size))
        solution[row] = (rows[row][size] - known) / rows[row][row]
    return solution


def levenberg_marquardt(
    model: Callable[[Sequence[float], float], float],
    start: Sequence[float],
    xs: Sequence[float],
    ys: Sequence[float],
) -> list[float]:
    """Minimise the sum of squared errors of `model(parameters, x)` from a starting point."""
    parameters = list(start)

    def cost(values: Sequence[float]) -> float:
        try:
            return sum((y - model(values, x)) ** 2 for x, y in zip(xs, ys, strict=True))
        except OverflowError, ZeroDivisionError:
            return math.inf

    current, damping = cost(parameters), 1e-3
    for _ in range(_LM_STEPS):
        jacobian = []
        for x in xs:
            row = []
            for index in range(len(parameters)):
                step = 1e-7 * max(1.0, abs(parameters[index]))
                bumped = list(parameters)
                bumped[index] += step
                row.append((model(bumped, x) - model(parameters, x)) / step)
            jacobian.append(row)
        residuals = [y - model(parameters, x) for x, y in zip(xs, ys, strict=True)]
        size = len(parameters)
        normal = [[sum(r[i] * r[j] for r in jacobian) for j in range(size)] for i in range(size)]
        gradient = [
            sum(r[i] * e for r, e in zip(jacobian, residuals, strict=True)) for i in range(size)
        ]
        improved = False
        for _attempt in range(30):
            damped = [
                [normal[i][j] + (damping * normal[i][i] if i == j else 0) for j in range(size)]
                for i in range(size)
            ]
            step_vector = _solve_floats(damped, gradient)
            if step_vector is not None:
                trial = [p + s for p, s in zip(parameters, step_vector, strict=True)]
                trial_cost = cost(trial)
                if trial_cost < current:
                    improvement = current - trial_cost
                    parameters, current, damping = trial, trial_cost, damping / 3
                    improved = True
                    break
            damping *= 4
        if not improved or improvement < _LM_TOLERANCE * current or current < _NEGLIGIBLE_COST:
            break
    return parameters


def logistic_fit(xs: Vector, ys: Vector, *, shifted: bool) -> list[float]:
    """c / (1 + a*e^(-b*x)), plus d if `shifted`. Returns [a, b, c] or [a, b, c, d]."""
    x_values, y_values = [float(x) for x in xs], [float(y) for y in ys]
    low, high = min(y_values), max(y_values)
    spread = (high - low) or 1.0
    floor = low - 0.05 * spread if shifted else 0.0
    top = (high - floor) * 1.1
    # Straighten ln(c/(y-d) - 1) = ln(a) - b*x to find a first guess.
    pairs = [
        (x, math.log(top / (y - floor) - 1))
        for x, y in zip(x_values, y_values, strict=True)
        if 0 < y - floor < top
    ]
    guess = line_fit([Fraction(x) for x, _ in pairs], [Fraction(z) for _, z in pairs])
    start = [math.exp(guess.intercept), -guess.slope, top]

    if shifted:

        def model(p: Sequence[float], x: float) -> float:
            return p[2] / (1 + p[0] * math.exp(-p[1] * x)) + p[3]

        return levenberg_marquardt(model, [*start, floor], x_values, y_values)

    def plain(p: Sequence[float], x: float) -> float:
        return p[2] / (1 + p[0] * math.exp(-p[1] * x))

    return levenberg_marquardt(plain, start, x_values, y_values)


def _sine_terms(
    frequency: float, xs: Sequence[float], ys: Sequence[float]
) -> tuple[list[float], float]:
    """Best A, B, d in y = A*sin(f*x) + B*cos(f*x) + d, and the squared error."""
    rows = [(math.sin(frequency * x), math.cos(frequency * x), 1.0) for x in xs]
    normal = [[sum(r[i] * r[j] for r in rows) for j in range(3)] for i in range(3)]
    constants = [sum(r[i] * y for r, y in zip(rows, ys, strict=True)) for i in range(3)]
    solution = _solve_floats(normal, constants)
    if solution is None:
        return [0.0, 0.0, sum(ys) / len(ys)], math.inf
    error = sum(
        (y - sum(c * v for c, v in zip(solution, r, strict=True))) ** 2
        for r, y in zip(rows, ys, strict=True)
    )
    return solution, error


def sine_fit(xs: Vector, ys: Vector) -> list[float]:
    """y = a*sin(b*x + c) + d, with b in radians per unit of x. Returns [a, b, c, d].

    For a fixed frequency the model is linear, so the frequency is found by a scan followed by a
    golden-section search, and a, c, d then follow from a linear fit.
    """
    x_values, y_values = [float(x) for x in xs], [float(y) for y in ys]
    spacing = min(
        b - a for a, b in zip(sorted(x_values), sorted(x_values)[1:], strict=False) if b > a
    )
    limit = math.pi / spacing
    grid = [limit * (i + 1) / _FREQUENCY_GRID for i in range(_FREQUENCY_GRID)]
    errors = [_sine_terms(f, x_values, y_values)[1] for f in grid]
    best = min(range(len(grid)), key=errors.__getitem__)
    low, high = grid[max(best - 1, 0)], grid[min(best + 1, len(grid) - 1)]
    for _ in range(_REFINEMENTS):
        a_point, b_point = high - _GOLDEN * (high - low), low + _GOLDEN * (high - low)
        if (
            _sine_terms(a_point, x_values, y_values)[1]
            < _sine_terms(b_point, x_values, y_values)[1]
        ):
            high = b_point
        else:
            low = a_point
    frequency = (low + high) / 2
    (sine, cosine, offset), _ = _sine_terms(frequency, x_values, y_values)
    return [math.hypot(sine, cosine), frequency, math.atan2(cosine, sine), offset]
