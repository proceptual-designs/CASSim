"""Time value of money, on plain floats, as the TI finance functions define it.

A payment period's interest rate is worked out from the nominal annual rate `i` (in percent), the
payments per year `pp` and the compounding periods per year `cp`. Money paid out is negative.
`at` is 0 for payments at the end of each period and 1 for the beginning.
"""

import math
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

# Rates tried, in turn, to bracket the interest rate of a payment period.
_RATE_SCAN = (
    -0.9,
    -0.5,
    -0.1,
    -0.01,
    -0.001,
    1e-6,
    0.001,
    0.005,
    0.01,
    0.02,
    0.05,
    0.1,
    0.25,
    1,
    3,
)
_BISECTIONS = 200
_TINY = 1e-12


def period_rate(percent: float, pp: float, cp: float) -> float:
    """Interest per payment period, as a fraction."""
    if pp <= 0 or cp <= 0:
        raise ValueError(pp)
    return (1 + percent / (100 * cp)) ** (cp / pp) - 1


def nominal_percent(rate: float, pp: float, cp: float) -> float:
    """The inverse of `period_rate`: the annual nominal percentage for a period's rate."""
    return 100 * cp * ((1 + rate) ** (pp / cp) - 1)


def _annuity(n: float, rate: float, at: int) -> float:
    """The factor that turns a regular payment into its value at the end of `n` periods."""
    if abs(rate) < _TINY:
        return n
    return (1 + rate * at) * ((1 + rate) ** n - 1) / rate


def future_value(n: float, rate: float, pv: float, pmt: float, at: int) -> float:
    return -(pv * (1 + rate) ** n + pmt * _annuity(n, rate, at))


def present_value(n: float, rate: float, pmt: float, fv: float, at: int) -> float:
    return -(fv + pmt * _annuity(n, rate, at)) / (1 + rate) ** n


def payment(n: float, rate: float, pv: float, fv: float, at: int) -> float:
    factor = _annuity(n, rate, at)
    if factor == 0:
        raise ValueError(n)
    return -(pv * (1 + rate) ** n + fv) / factor


def periods(rate: float, pv: float, pmt: float, fv: float, at: int) -> float:
    if abs(rate) < _TINY:
        if pmt == 0:
            raise ValueError(pmt)
        return -(pv + fv) / pmt
    paid = pmt * (1 + rate * at)
    ratio = (paid - fv * rate) / (paid + pv * rate)
    if ratio <= 0:
        raise ValueError(ratio)
    return math.log(ratio) / math.log(1 + rate)


@dataclass(frozen=True, slots=True)
class _Flows:
    """The money in a time-value problem: present value, regular payment, future value, timing."""

    pv: float
    pmt: float
    fv: float
    at: int

    def residual(self, n: float, rate: float) -> float:
        """Zero when the flows balance."""
        return self.pv * (1 + rate) ** n + self.pmt * _annuity(n, rate, self.at) + self.fv


def interest_rate(n: float, pv: float, pmt: float, fv: float, at: int) -> float:
    """The rate per period that balances the cash flows, by bisection between sign changes."""
    flows = _Flows(pv, pmt, fv, at)
    previous = _RATE_SCAN[0]
    for current in _RATE_SCAN[1:]:
        before, after = flows.residual(n, previous), flows.residual(n, current)
        if before == 0:
            return previous
        if before * after < 0:
            low, high = previous, current
            for _ in range(_BISECTIONS):
                middle = (low + high) / 2
                if flows.residual(n, low) * flows.residual(n, middle) <= 0:
                    high = middle
                else:
                    low = middle
            return (low + high) / 2
        previous = current
    raise ValueError(n)


def effective_percent(nominal: float, cp: float) -> float:
    if cp <= 0:
        raise ValueError(cp)
    return 100 * ((1 + nominal / (100 * cp)) ** cp - 1)


def nominal_from_effective(effective: float, cp: float) -> float:
    if cp <= 0:
        raise ValueError(cp)
    return 100 * cp * ((1 + effective / 100) ** (1 / cp) - 1)


def _rounded(value: float, places: int) -> float:
    step = Decimal(1).scaleb(-places)
    return float(Decimal(repr(value)).quantize(step, ROUND_HALF_UP))


@dataclass(frozen=True, slots=True)
class Loan:
    """The inputs of the TI loan functions. `pmt` is worked out if it is left as None."""

    n: float
    percent: float
    pv: float
    pmt: float | None = None
    fv: float = 0.0
    pp: float = 1.0
    cp: float = 1.0
    at: int = 0
    places: int = 2


def amortization(loan: Loan, payments: int) -> list[tuple[int, float, float, float]]:
    """Rows of (payment number, interest, principal, balance), starting with payment 0.

    The payment and every amount in a row are rounded to `places` decimals, as the calculator's
    table does, so a row is what the bank would print.
    """
    rate = period_rate(loan.percent, loan.pp, loan.cp)
    owed = payment(loan.n, rate, loan.pv, loan.fv, loan.at) if loan.pmt is None else loan.pmt
    paid = _rounded(owed, loan.places)
    balance = loan.pv
    rows = [(0, 0.0, 0.0, balance)]
    for number in range(1, payments + 1):
        # With payments at the beginning of the period the first one earns no interest.
        first_at_start = loan.at == 1 and number == 1
        interest = 0.0 if first_at_start else _rounded(-balance * rate, loan.places)
        principal = _rounded(paid - interest, loan.places)
        balance = _rounded(balance + principal, loan.places)
        rows.append((number, interest, principal, balance))
    return rows
