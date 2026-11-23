"""Headless calculation engine for CASSim fx (Scientific Calculator).

Handles exact fractions, mixed numbers, powers, roots, scientific/engineering notation,
DMS (degrees, minutes, seconds), trigonometry, coordinate conversions, number theory (GCD, LCM,
prime factorisation), combinatorics, and Australian curriculum statistics (median-split quartiles,
sample sx vs population σx, Pearson's r, and linear regression).

Pure Python: zero Flet imports. Tested headless.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Literal

AngleUnit = Literal["DEG", "RAD", "GRA"]
FIRST_PRIME = 2
MIN_PAIRS = 2
SECONDS_PER_MINUTE = 60
MINUTES_PER_DEGREE = 60


def to_degrees(val: float, unit: AngleUnit) -> float:
    """Convert an angle from the active unit to degrees."""
    if unit == "DEG":
        return val
    if unit == "RAD":
        return math.degrees(val)
    if unit == "GRA":
        return val * 0.9
    return val


def from_degrees(deg: float, unit: AngleUnit) -> float:
    """Convert degrees to the active angle unit."""
    if unit == "DEG":
        return deg
    if unit == "RAD":
        return math.radians(deg)
    if unit == "GRA":
        return deg / 0.9
    return deg


def to_radians(val: float, unit: AngleUnit) -> float:
    """Convert an angle from the active unit to radians."""
    if unit == "RAD":
        return val
    if unit == "DEG":
        return math.radians(val)
    if unit == "GRA":
        return math.radians(val * 0.9)
    return val


# ---------------------------------------------------------------------------
# Number Theory & Combinatorics
# ---------------------------------------------------------------------------


def prime_factors(n: int) -> list[tuple[int, int]]:
    """Prime factorisation of positive integer n as list of (prime, exponent) pairs."""
    if n <= 1:
        return []
    factors: list[tuple[int, int]] = []
    d = 2
    temp = n
    while d * d <= temp:
        if temp % d == 0:
            count = 0
            while temp % d == 0:
                count += 1
                temp //= d
            factors.append((d, count))
        d += 1 if d == FIRST_PRIME else 2
    if temp > 1:
        factors.append((temp, 1))
    return factors


def format_prime_factors(n: int) -> str:
    """Format prime factorisation string (e.g. '2×3×5²×7')."""
    if n <= 1:
        return str(n)
    sup = {
        "0": "⁰",
        "1": "¹",
        "2": "²",
        "3": "³",
        "4": "⁴",
        "5": "⁵",
        "6": "⁶",
        "7": "⁷",
        "8": "⁸",
        "9": "⁹",
    }
    parts: list[str] = []
    for p, exp in prime_factors(n):
        if exp == 1:
            parts.append(str(p))
        else:
            exp_str = "".join(sup.get(ch, ch) for ch in str(exp))
            parts.append(f"{p}{exp_str}")
    return "×".join(parts)


def gcd(a: int, b: int) -> int:
    return math.gcd(a, b)


def lcm(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // math.gcd(a, b)


def nPr(n: int, r: int) -> int:
    if r < 0 or r > n:
        return 0
    return math.perm(n, r)


def nCr(n: int, r: int) -> int:
    if r < 0 or r > n:
        return 0
    return math.comb(n, r)


def factorial(n: int) -> int:
    return math.factorial(n)


# ---------------------------------------------------------------------------
# Sexagesimal (Degrees, Minutes, Seconds)
# ---------------------------------------------------------------------------


def to_dms(decimal_deg: float) -> tuple[int, int, float]:
    """Convert decimal degrees to (degrees, minutes, seconds)."""
    sign = -1 if decimal_deg < 0 else 1
    val = abs(decimal_deg)
    d = int(val)
    val = (val - d) * 60.0
    m = int(val)
    s = (val - m) * 60.0
    return sign * d, m, round(s, 5)


def from_dms(d: float, m: float = 0.0, s: float = 0.0) -> float:
    """Convert (degrees, minutes, seconds) to decimal degrees."""
    sign = -1 if d < 0 else 1
    return sign * (abs(d) + m / 60.0 + s / 3600.0)


def format_dms(decimal_deg: float) -> str:
    """Format as D°M'S\"."""
    d, m, s = to_dms(decimal_deg)
    s_int = round(s)
    if s_int == SECONDS_PER_MINUTE:
        s_int = 0
        m += 1
    if m == MINUTES_PER_DEGREE:
        m = 0
        d += 1
    return f"{d}°{m}'{s_int}\""


# ---------------------------------------------------------------------------
# Coordinate Conversions
# ---------------------------------------------------------------------------


def pol_to_rec(r: float, theta: float, unit: AngleUnit = "DEG") -> tuple[float, float]:
    """Rec(r, θ) -> (x, y)."""
    rad = to_radians(theta, unit)
    x = r * math.cos(rad)
    y = r * math.sin(rad)
    return round(x, 10), round(y, 10)


def rec_to_pol(x: float, y: float, unit: AngleUnit = "DEG") -> tuple[float, float]:
    """Pol(x, y) -> (r, θ)."""
    r = math.hypot(x, y)
    rad = math.atan2(y, x)
    deg = math.degrees(rad)
    theta = from_degrees(deg, unit)
    return round(r, 10), round(theta, 10)


to_polar = rec_to_pol
to_rectangular = pol_to_rec


# ---------------------------------------------------------------------------
# Australian School Statistics Engine
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Stat1VarSummary:
    n: int
    mean: float
    sum_x: float
    sum_x2: float
    sx: float  # sample SD (n-1)
    sigma_x: float  # population SD (n)
    min_x: float
    q1: float
    median: float
    q3: float
    max_x: float

    @property
    def med(self) -> float:
        return self.median


def calculate_1var_stats(rows: list[tuple[float, int]]) -> Stat1VarSummary:
    """Calculate single-variable summary statistics under Australian curriculum rules.

    Quartiles follow the TI/school convention:
    - Sort values.
    - Median is middle element (or mean of two middle elements).
    - If n is odd, median is excluded when splitting into lower and upper halves.
    - If n is even, lower half is first n/2, upper half is last n/2.
    - Q1 is median of lower half; Q3 is median of upper half.
    - Sample SD uses (n - 1) divisor; population SD uses n divisor.
    """
    expanded: list[float] = []
    for x, freq in rows:
        if freq > 0:
            expanded.extend([float(x)] * freq)

    if not expanded:
        return Stat1VarSummary(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    expanded.sort()
    n = len(expanded)
    sum_x = sum(expanded)
    sum_x2 = sum(x * x for x in expanded)
    mean = sum_x / n

    if n > 1:
        var_sample = sum((x - mean) ** 2 for x in expanded) / (n - 1)
        sx = math.sqrt(max(0.0, var_sample))
    else:
        sx = 0.0

    var_pop = sum((x - mean) ** 2 for x in expanded) / n
    sigma_x = math.sqrt(max(0.0, var_pop))

    def _median_of(vals: list[float]) -> float:
        m = len(vals)
        if m == 0:
            return 0.0
        mid = m // 2
        if m % 2 != 0:
            return vals[mid]
        return (vals[mid - 1] + vals[mid]) / 2.0

    median = _median_of(expanded)
    half = n // 2
    if n % 2 == 0:
        lower_half = expanded[:half]
        upper_half = expanded[half:]
    else:
        lower_half = expanded[:half]
        upper_half = expanded[half + 1 :]

    q1 = _median_of(lower_half) if lower_half else expanded[0]
    q3 = _median_of(upper_half) if upper_half else expanded[-1]

    return Stat1VarSummary(
        n=n,
        mean=round(mean, 10),
        sum_x=round(sum_x, 10),
        sum_x2=round(sum_x2, 10),
        sx=round(sx, 10),
        sigma_x=round(sigma_x, 10),
        min_x=expanded[0],
        q1=q1,
        median=median,
        q3=q3,
        max_x=expanded[-1],
    )


@dataclass(frozen=True)
class LinearRegressionSummary:
    n: int
    mean_x: float
    mean_y: float
    sum_x: float
    sum_x2: float
    sum_y: float
    sum_y2: float
    sum_xy: float
    sx: float
    sy: float
    a: float  # y-intercept
    b: float  # slope
    r: float  # Pearson correlation coefficient

    def predict_y(self, x: float) -> float:
        """Estimate y for given x."""
        return self.a + self.b * x

    def predict_x(self, y: float) -> float:
        """Estimate x for given y."""
        if self.b == 0.0:
            return 0.0
        return (y - self.a) / self.b

    estimate_y = predict_y
    estimate_x = predict_x


def calculate_linear_regression(pairs: list[tuple[float, float]]) -> LinearRegressionSummary:
    """Calculate bivariate linear regression y = A + Bx and Pearson's r."""
    n = len(pairs)
    if n < MIN_PAIRS:
        return LinearRegressionSummary(
            n, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        )

    sum_x = sum(p[0] for p in pairs)
    sum_y = sum(p[1] for p in pairs)
    sum_x2 = sum(p[0] ** 2 for p in pairs)
    sum_y2 = sum(p[1] ** 2 for p in pairs)
    sum_xy = sum(p[0] * p[1] for p in pairs)

    mean_x = sum_x / n
    mean_y = sum_y / n

    denom_b = n * sum_x2 - sum_x**2
    if denom_b != 0:
        b = (n * sum_xy - sum_x * sum_y) / denom_b
        a = mean_y - b * mean_x
    else:
        b = 0.0
        a = mean_y

    denom_r_sq = (n * sum_x2 - sum_x**2) * (n * sum_y2 - sum_y**2)
    r = (n * sum_xy - sum_x * sum_y) / math.sqrt(denom_r_sq) if denom_r_sq > 0 else 0.0

    var_sx = sum((p[0] - mean_x) ** 2 for p in pairs) / (n - 1)
    var_sy = sum((p[1] - mean_y) ** 2 for p in pairs) / (n - 1)

    return LinearRegressionSummary(
        n=n,
        mean_x=round(mean_x, 10),
        mean_y=round(mean_y, 10),
        sum_x=round(sum_x, 10),
        sum_x2=round(sum_x2, 10),
        sum_y=round(sum_y, 10),
        sum_y2=round(sum_y2, 10),
        sum_xy=round(sum_xy, 10),
        sx=round(math.sqrt(max(0.0, var_sx)), 10),
        sy=round(math.sqrt(max(0.0, var_sy)), 10),
        a=round(a, 10),
        b=round(b, 10),
        r=round(r, 10),
    )


# ---------------------------------------------------------------------------
# General Expression Evaluator (Safe mathematical parsing)
# ---------------------------------------------------------------------------


def safe_eval(
    expr: str,
    angle_unit: AngleUnit = "DEG",
    variables: dict[str, float] | None = None,
) -> float | str:
    """Evaluate a mathematical expression string within an isolated math namespace."""
    vars_map = variables or {}
    clean = expr.replace("×", "*").replace("÷", "/").replace("−", "-").replace("·", ".")
    clean = clean.replace("^", "**")

    # Safe math namespace
    ns: dict[str, object] = {
        "pi": math.pi,
        "e": math.e,
        "sin": lambda x: math.sin(to_radians(x, angle_unit)),
        "cos": lambda x: math.cos(to_radians(x, angle_unit)),
        "tan": lambda x: math.tan(to_radians(x, angle_unit)),
        "asin": lambda x: from_degrees(math.degrees(math.asin(x)), angle_unit),
        "acos": lambda x: from_degrees(math.degrees(math.acos(x)), angle_unit),
        "atan": lambda x: from_degrees(math.degrees(math.atan(x)), angle_unit),
        "sinh": math.sinh,
        "cosh": math.cosh,
        "tanh": math.tanh,
        "sqrt": math.sqrt,
        "log": math.log10,
        "ln": math.log,
        "abs": abs,
        "gcd": gcd,
        "lcm": lcm,
        "nPr": nPr,
        "nCr": nCr,
    }
    ns.update(vars_map)

    try:
        res = eval(clean, {"__builtins__": {}}, ns)
        if isinstance(res, (int, float)):
            return float(res)
        return str(res)
    except Exception as exc:
        return f"Error: {exc}"


def to_exact_or_decimal(val: float) -> tuple[str, str]:
    """Return a tuple of (exact_string, decimal_string).

    For example, 0.75 -> ('3/4', '0.75').
    """
    dec_str = f"{val:.10g}"
    try:
        frac = Fraction(dec_str).limit_denominator(10000)
        if frac.denominator != 1:
            exact_str = f"{frac.numerator}/{frac.denominator}"
            return exact_str, dec_str
    except ValueError, OverflowError:
        pass
    return dec_str, dec_str


def to_mixed_fraction(frac_str: str) -> str:
    """Convert an improper fraction like '7/4' to mixed fraction '1 3/4'."""
    if "/" not in frac_str:
        return frac_str
    try:
        parts = frac_str.split("/")
        num, den = int(parts[0]), int(parts[1])
        if den == 0:
            return frac_str
        sign = "-" if (num < 0) ^ (den < 0) else ""
        abs_num = abs(num)
        abs_den = abs(den)
        whole = abs_num // abs_den
        rem = abs_num % abs_den
        if whole != 0 and rem != 0:
            return f"{sign}{whole} {rem}/{abs_den}"
        return frac_str
    except ValueError:
        return frac_str
