"""Statistics and number theory for CASSim Scientific (FR-FX-STA-002 to -005, FR-FX-DSP-009).

Quartiles follow the school convention CASSim uses everywhere (AGENTS.md): Q1 and Q3 are the
medians of the lower and upper halves, leaving the median out when n is odd; numpy's interpolated
quartiles are not used. Sample sd divides by n-1 (sx), population sd by n (σx). Regressions are
least squares, on transformed data for the curved types (ln X, eˣ, A·Bˣ, A·X^B, 1/X), so r is the
correlation of the transformed data.

Pure Python: no Flet, no NumPy.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from cassim.devices.scientific.layout import Seq, Sup, Text
from cassim.devices.scientific.values import CalcError

FIRST_PRIME = 2
MAX_FACTOR_INPUT = 10**10

StatType = Literal["1-VAR", "A+BX", "_+CX2", "ln X", "e^X", "A·B^X", "A·X^B", "1/X"]
STAT_TYPES: tuple[StatType, ...] = (
    "1-VAR",
    "A+BX",
    "_+CX2",
    "ln X",
    "e^X",
    "A·B^X",
    "A·X^B",
    "1/X",
)
STAT_TYPE_LABELS: dict[StatType, str] = {
    "1-VAR": "1-VAR",
    "A+BX": "A+BX",
    "_+CX2": "_+CX²",
    "ln X": "ln X",
    "e^X": "e^X",
    "A·B^X": "A·B^X",
    "A·X^B": "A·X^B",
    "1/X": "1/X",
}


def _math() -> CalcError:
    return CalcError("Math")


# ---- prime factors --------------------------------------------------------------------------


def prime_factors(n: int) -> list[tuple[int, int]]:
    """The prime factorisation of n > 1 as (prime, exponent) pairs."""
    factors: list[tuple[int, int]] = []
    d = FIRST_PRIME
    rest = n
    while d * d <= rest:
        if rest % d == 0:
            count = 0
            while rest % d == 0:
                count += 1
                rest //= d
            factors.append((d, count))
        d += 1 if d == FIRST_PRIME else 2
    if rest > 1:
        factors.append((rest, 1))
    return factors


def factor_layout(n: int) -> Seq:
    """FACT: n as a product of prime powers, e.g. 2²×3²×5 (FR-FX-DSP-009). Only for whole numbers
    from 2 up to ten digits; others are a Math ERROR."""
    if n < FIRST_PRIME or n >= MAX_FACTOR_INPUT:
        raise _math()
    nodes: list[Text | Sup] = []
    for index, (p, exp) in enumerate(prime_factors(n)):
        if index:
            nodes.append(Text("×"))
        nodes.append(Text(str(p)))
        if exp > 1:
            nodes.append(Sup((Text(str(exp)),)))
    return tuple(nodes)


# ---- one variable ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OneVar:
    n: float
    mean: float
    sum_x: float
    sum_x2: float
    sx: float  # sample sd (n-1)
    sigma_x: float  # population sd (n)
    min_x: float
    q1: float
    median: float
    q3: float
    max_x: float


def _median(values: list[float]) -> float:
    m = len(values)
    mid = m // 2
    return values[mid] if m % 2 else (values[mid - 1] + values[mid]) / 2


def one_var(rows: list[tuple[float, float]]) -> OneVar:
    """Summary statistics of (x, frequency) rows. Frequencies must be whole and not negative."""
    expanded: list[float] = []
    for x, freq in rows:
        if freq < 0 or freq != int(freq):
            raise _math()
        expanded.extend([x] * int(freq))
    if not expanded:
        raise _math()
    expanded.sort()
    n = len(expanded)
    sum_x = math.fsum(expanded)
    mean = sum_x / n
    squares = math.fsum((x - mean) ** 2 for x in expanded)
    half = n // 2
    lower = expanded[:half]
    upper = expanded[half + (n % 2) :]
    return OneVar(
        n=float(n),
        mean=mean,
        sum_x=sum_x,
        sum_x2=math.fsum(x * x for x in expanded),
        sx=math.sqrt(squares / (n - 1)) if n > 1 else math.nan,
        sigma_x=math.sqrt(squares / n),
        min_x=expanded[0],
        q1=_median(lower) if lower else expanded[0],
        median=_median(expanded),
        q3=_median(upper) if upper else expanded[-1],
        max_x=expanded[-1],
    )


# ---- two variables --------------------------------------------------------------------------


@dataclass(frozen=True)
class TwoVar:
    n: float
    sum_x: float
    sum_x2: float
    sum_y: float
    sum_y2: float
    sum_xy: float
    mean_x: float
    mean_y: float
    sigma_x: float
    sigma_y: float
    sx: float
    sy: float
    min_x: float
    max_x: float
    min_y: float
    max_y: float


def two_var(rows: list[tuple[float, float, float]]) -> TwoVar:
    """Sums and spreads of (x, y, frequency) rows."""
    if not rows:
        raise _math()
    for _, _, f in rows:
        if f < 0 or f != int(f):
            raise _math()
    n = math.fsum(f for _, _, f in rows)
    if n <= 0:
        raise _math()
    sum_x = math.fsum(x * f for x, _, f in rows)
    sum_y = math.fsum(y * f for _, y, f in rows)
    mean_x, mean_y = sum_x / n, sum_y / n
    ssx = math.fsum(f * (x - mean_x) ** 2 for x, _, f in rows)
    ssy = math.fsum(f * (y - mean_y) ** 2 for _, y, f in rows)
    used = [(x, y) for x, y, f in rows if f > 0]
    return TwoVar(
        n=n,
        sum_x=sum_x,
        sum_x2=math.fsum(f * x * x for x, _, f in rows),
        sum_y=sum_y,
        sum_y2=math.fsum(f * y * y for _, y, f in rows),
        sum_xy=math.fsum(f * x * y for x, y, f in rows),
        mean_x=mean_x,
        mean_y=mean_y,
        sigma_x=math.sqrt(ssx / n),
        sigma_y=math.sqrt(ssy / n),
        sx=math.sqrt(ssx / (n - 1)) if n > 1 else math.nan,
        sy=math.sqrt(ssy / (n - 1)) if n > 1 else math.nan,
        min_x=min(x for x, _ in used),
        max_x=max(x for x, _ in used),
        min_y=min(y for _, y in used),
        max_y=max(y for _, y in used),
    )


@dataclass(frozen=True)
class Regression:
    """A fitted model of one of the STAT types. `r` is NaN for the quadratic, which has none."""

    kind: StatType
    a: float
    b: float
    c: float
    r: float

    def predict_y(self, x: float) -> float:  # noqa: PLR0911
        a, b, c = self.a, self.b, self.c
        match self.kind:
            case "A+BX":
                return a + b * x
            case "_+CX2":
                return a + b * x + c * x * x
            case "ln X":
                if x <= 0:
                    raise _math()
                return a + b * math.log(x)
            case "e^X":
                return a * math.exp(b * x)
            case "A·B^X":
                return a * b**x
            case "A·X^B":
                if x <= 0:
                    raise _math()
                return a * x**b
            case "1/X":
                if x == 0:
                    raise _math()
                return a + b / x
        raise _math()

    def predict_x(self, y: float, root: int = 1) -> float:  # noqa: PLR0911
        """x̂ for a value of y; for the quadratic, root 1 or 2 is x̂₁ or x̂₂."""
        a, b, c = self.a, self.b, self.c
        try:
            match self.kind:
                case "A+BX":
                    return (y - a) / b
                case "_+CX2":
                    disc = b * b - 4 * c * (a - y)
                    if c == 0 or disc < 0:
                        raise _math()
                    sign = 1 if root == 1 else -1
                    return (-b + sign * math.sqrt(disc)) / (2 * c)
                case "ln X":
                    return math.exp((y - a) / b)
                case "e^X":
                    return math.log(y / a) / b
                case "A·B^X":
                    return math.log(y / a) / math.log(b)
                case "A·X^B":
                    return (y / a) ** (1 / b)
                case "1/X":
                    return b / (y - a)
        except ZeroDivisionError, ValueError:
            raise _math() from None
        raise _math()


def _line(points: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    """Least-squares intercept, slope and r of weighted points."""
    stats = two_var(points)
    sxx = stats.sum_x2 - stats.sum_x**2 / stats.n
    syy = stats.sum_y2 - stats.sum_y**2 / stats.n
    sxy = stats.sum_xy - stats.sum_x * stats.sum_y / stats.n
    if sxx <= 0:
        raise _math()
    slope = sxy / sxx
    intercept = stats.mean_y - slope * stats.mean_x
    r = sxy / math.sqrt(sxx * syy) if syy > 0 else math.nan
    return intercept, slope, r


def _solve3(m: list[list[float]], rhs: list[float]) -> list[float]:
    """Gaussian elimination for the 3×3 normal equations of the quadratic."""
    size = 3
    a = [[*row, value] for row, value in zip(m, rhs, strict=True)]
    for col in range(size):
        pivot = max(range(col, size), key=lambda r: abs(a[r][col]))
        if abs(a[pivot][col]) < 1e-12:  # noqa: PLR2004
            raise _math()
        a[col], a[pivot] = a[pivot], a[col]
        for row in range(size):
            if row != col:
                factor = a[row][col] / a[col][col]
                a[row] = [x - factor * y for x, y in zip(a[row], a[col], strict=True)]
    return [a[i][size] / a[i][i] for i in range(size)]


def regression(kind: StatType, rows: list[tuple[float, float, float]]) -> Regression:
    """Fit a STAT type to (x, y, frequency) rows (FR-FX-MOD-002, FR-FX-STA-004)."""
    if kind == "_+CX2":
        n = math.fsum(f for _, _, f in rows)
        if n < 3:  # noqa: PLR2004
            raise _math()
        sums = [math.fsum(f * x**k for x, _, f in rows) for k in range(5)]
        ys = [math.fsum(f * y * x**k for x, y, f in rows) for k in range(3)]
        a, b, c = _solve3(
            [[sums[0], sums[1], sums[2]], [sums[1], sums[2], sums[3]], [sums[2], sums[3], sums[4]]],
            ys,
        )
        return Regression(kind, a, b, c, math.nan)
    try:
        match kind:
            case "A+BX":
                points = rows
            case "ln X":
                points = [(math.log(x), y, f) for x, y, f in rows]
            case "1/X":
                points = [(1 / x, y, f) for x, y, f in rows]
            case "e^X" | "A·B^X":
                points = [(x, math.log(y), f) for x, y, f in rows]
            case "A·X^B":
                points = [(math.log(x), math.log(y), f) for x, y, f in rows]
            case _:
                raise _math()
    except ValueError, ZeroDivisionError:
        raise _math() from None
    intercept, slope, r = _line(points)
    match kind:
        case "e^X":
            return Regression(kind, math.exp(intercept), slope, 0.0, r)
        case "A·B^X":
            return Regression(kind, math.exp(intercept), math.exp(slope), 0.0, r)
        case "A·X^B":
            return Regression(kind, math.exp(intercept), slope, 0.0, r)
    return Regression(kind, intercept, slope, 0.0, r)
