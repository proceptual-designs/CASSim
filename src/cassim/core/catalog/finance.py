"""Finance: the time value of money (`tvm*`), `eff`, `nom` and loan tables."""

from collections.abc import Callable

from cassim.core import errors
from cassim.core.catalog.registry import Host, eager
from cassim.core.compat import finance as fin
from cassim.core.compat import sympy_adapter as cas
from cassim.core.errors import TIError
from cassim.core.valueops import matrix_of, raw_of
from cassim.core.values import Empty, Expr, Raw, Value

# What the TI functions assume for the optional PpY, CpY and PmtAt arguments of `tvm*`.
_TIMING_DEFAULTS = (1.0, 1.0, 0.0)
# `tvmN(I, PV, Pmt, FV[, PpY, CpY, PmtAt])` and its relatives take four values and then timing.
_TVM_FIXED = 4
_TVM_MAXIMUM = 7


def _real(value: Value) -> float:
    number = cas.real_float(raw_of(value))
    if number is None:
        raise TIError(errors.DATA_TYPE)
    return number


def _numbers(args: list[Value]) -> list[float]:
    return [_real(arg) for arg in args]


def _answer(compute: Callable[[], float]) -> Value:
    try:
        return Expr(cas.from_float(compute()))
    except ValueError, ZeroDivisionError, OverflowError:
        raise TIError(errors.DOMAIN) from None


def _tvm(
    args: list[Value], compute: Callable[[float, float, float, float, float, float, int], float]
) -> Value:
    """Read four values and the optional timing, then call `compute(a, b, c, d, pp, cp, at)`."""
    numbers = _numbers(args)
    fixed, optional = numbers[:_TVM_FIXED], numbers[_TVM_FIXED:]
    pp, cp, at = [*optional, *_TIMING_DEFAULTS[len(optional) :]]
    if at not in (0, 1):
        raise TIError(errors.DOMAIN)
    a, b, c, d = fixed
    return _answer(lambda: compute(a, b, c, d, pp, cp, int(at)))


@eager("tvmN", _TVM_FIXED, _TVM_MAXIMUM)
def tvm_n(host: Host, args: list[Value]) -> Value:
    """`tvmN(I, PV, Pmt, FV[, PpY, CpY, PmtAt])`."""
    return _tvm(
        args,
        lambda i, pv, pmt, fv, pp, cp, at: fin.periods(fin.period_rate(i, pp, cp), pv, pmt, fv, at),
    )


@eager("tvmI", _TVM_FIXED, _TVM_MAXIMUM)
def tvm_i(host: Host, args: list[Value]) -> Value:
    """`tvmI(N, PV, Pmt, FV[, PpY, CpY, PmtAt])`."""
    return _tvm(
        args,
        lambda n, pv, pmt, fv, pp, cp, at: fin.nominal_percent(
            fin.interest_rate(n, pv, pmt, fv, at), pp, cp
        ),
    )


@eager("tvmPV", _TVM_FIXED, _TVM_MAXIMUM)
def tvm_pv(host: Host, args: list[Value]) -> Value:
    """`tvmPV(N, I, Pmt, FV[, PpY, CpY, PmtAt])`."""
    return _tvm(
        args,
        lambda n, i, pmt, fv, pp, cp, at: fin.present_value(
            n, fin.period_rate(i, pp, cp), pmt, fv, at
        ),
    )


@eager("tvmPmt", _TVM_FIXED, _TVM_MAXIMUM)
def tvm_pmt(host: Host, args: list[Value]) -> Value:
    """`tvmPmt(N, I, PV, FV[, PpY, CpY, PmtAt])`."""
    return _tvm(
        args,
        lambda n, i, pv, fv, pp, cp, at: fin.payment(n, fin.period_rate(i, pp, cp), pv, fv, at),
    )


@eager("tvmFV", _TVM_FIXED, _TVM_MAXIMUM)
def tvm_fv(host: Host, args: list[Value]) -> Value:
    """`tvmFV(N, I, PV, Pmt[, PpY, CpY, PmtAt])`."""
    return _tvm(
        args,
        lambda n, i, pv, pmt, pp, cp, at: fin.future_value(
            n, fin.period_rate(i, pp, cp), pv, pmt, at
        ),
    )


@eager("eff", 2)
def eff(host: Host, args: list[Value]) -> Value:
    """`eff(nominal, compoundings per year)`, in percent."""
    nominal, cp = _numbers(args)
    return _answer(lambda: fin.effective_percent(nominal, cp))


@eager("nom", 2)
def nom(host: Host, args: list[Value]) -> Value:
    """`nom(effective, compoundings per year)`, in percent."""
    effective, cp = _numbers(args)
    return _answer(lambda: fin.nominal_from_effective(effective, cp))


# Positions of the optional arguments after `N, I, PV` in the loan functions.
_PMT, _FV, _PP, _CP, _AT, _PLACES = range(6)
_LOAN_MAXIMUM = 6


def _nth(values: list[float | None], index: int, default: float) -> float:
    value = values[index] if index < len(values) else None
    return default if value is None else value


def _loan_numbers(args: list[Value]) -> list[float | None]:
    """The arguments of a loan function, with None for one left empty (`amortTbl(...,,0)`)."""
    return [None if isinstance(arg, Empty) else _real(arg) for arg in args]


def _given(value: float | None) -> float:
    if value is None:
        raise TIError(errors.DATA_TYPE)
    return value


def _loan(numbers: list[float | None]) -> fin.Loan:
    """A loan from `N, I, PV[, Pmt, FV, PpY, CpY, PmtAt, round]`; an empty Pmt is worked out."""
    n, percent, pv, *rest = numbers
    if len(rest) > _LOAN_MAXIMUM:
        raise TIError(errors.TOO_MANY_ARGUMENTS)
    return fin.Loan(
        n=_given(n),
        percent=_given(percent),
        pv=_given(pv),
        pmt=rest[_PMT] if len(rest) > _PMT else None,
        fv=_nth(rest, _FV, 0.0),
        pp=_nth(rest, _PP, 1.0),
        cp=_nth(rest, _CP, 1.0),
        at=int(_nth(rest, _AT, 0.0)),
        places=int(_nth(rest, _PLACES, 2.0)),
    )


def _rows(loan: fin.Loan, payments: int) -> list[tuple[int, float, float, float]]:
    try:
        return fin.amortization(loan, payments)
    except ValueError, ZeroDivisionError, OverflowError:
        raise TIError(errors.DOMAIN) from None


def _decimals(*numbers: float) -> list[Raw]:
    return [cas.from_float(number) for number in numbers]


@eager("amortTbl", 4, 10)
def amort_tbl(host: Host, args: list[Value]) -> Value:
    """`amortTbl(NPmt, N, I, PV[, Pmt, FV, PpY, CpY, PmtAt, round])`: payment number, interest,
    principal and balance, one row for each payment from 0."""
    numbers = _loan_numbers(args)
    rows = _rows(_loan(numbers[1:]), int(_given(numbers[0])))
    return matrix_of([[cas.integer(number), *_decimals(*row)] for number, *row in rows])


@eager("bal", 4, 10)
def bal(host: Host, args: list[Value]) -> Value:
    """`bal(NPmt, N, I, PV, ...)`: the balance after NPmt payments."""
    numbers = _loan_numbers(args)
    rows = _rows(_loan(numbers[1:]), int(_given(numbers[0])))
    return Expr(cas.from_float(rows[-1][3]))


def _total(args: list[Value], column: int) -> Value:
    numbers = _loan_numbers(args)
    first, last = int(_given(numbers[0])), int(_given(numbers[1]))
    if not 1 <= first <= last:
        raise TIError(errors.DOMAIN)
    rows = _rows(_loan(numbers[2:]), last)
    return Expr(cas.from_float(sum(row[column] for row in rows[first : last + 1])))


@eager("ΣInt", 5, 11)
def sum_interest(host: Host, args: list[Value]) -> Value:
    """`ΣInt(NPmt1, NPmt2, N, I, PV, ...)`: interest paid from payment NPmt1 to NPmt2."""
    return _total(args, 1)


@eager("ΣPrn", 5, 11)
def sum_principal(host: Host, args: list[Value]) -> Value:
    """`ΣPrn(NPmt1, NPmt2, N, I, PV, ...)`: principal paid from payment NPmt1 to NPmt2."""
    return _total(args, 2)
