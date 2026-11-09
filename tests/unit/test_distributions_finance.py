# Requirements traced here: FR-STAT-004, FR-FIN-001
"""Distributions and finance (M1d slice 4). Reference values for the continuous distributions
were computed with SciPy once and are fixed here, so the tests need no SciPy."""

import pytest

from cassim.core.compat import distributions as dist
from cassim.core.compat import finance as fin
from cassim.core.session import Session, same_value
from cassim.core.settings import CasMode, Settings

CAS_OFF = Settings(cas_mode=CasMode.OFF)
INF = float("inf")


def run(*lines, settings=None):
    session = Session(settings)
    result = None
    for line in lines:
        result = session.eval(line)
    assert result is not None
    return result


def text(*lines, settings=None):
    result = run(*lines, settings=settings)
    assert result.error is None, result.error
    return result.text


def error(*lines, settings=None):
    return run(*lines, settings=settings).error


def number(line, settings=None):
    result = run(line, settings=settings)
    assert result.error is None, result.error
    return float(result.text)


def same(line, wanted, tolerance=None):
    got = run(line).value
    expected = run(wanted).value
    assert got is not None
    assert expected is not None
    assert same_value(got, expected, tolerance), f"{line} gave {text(line)}"


@pytest.mark.parametrize(
    ("value", "reference"),
    [
        (dist.norm_cdf(-1, 1, 0, 1), 0.682689492137),
        (dist.norm_cdf(1.96, INF, 0, 1), 0.0249978951482),
        (dist.norm_pdf(1, 0, 1), 0.241970724519),
        (dist.norm_pdf(12, 10, 2), 0.12098536226),
        (dist.inv_norm(0.975, 0, 1), 1.95996398454),
        (dist.inv_norm(0.9, 50, 10), 62.8155156554),
        (dist.inv_norm(1e-10, 0, 1), -6.3613409024),
        (dist.t_cdf(-INF, 1, 5), 0.818391266175),
        (dist.t_cdf(-1, 1, 5), 0.636782532351),
        (dist.t_cdf(-INF, -2.5, 3.5), 0.0378473219047),
        (dist.t_pdf(0.7, 5), 0.286765457577),
        (dist.inv_t(0.975, 5), 2.57058183564),
        (dist.inv_t(0.01, 3), -4.54070285857),
        (dist.inv_t(0.9, 1), 3.07768353718),
        (dist.chi2_cdf(0, 3, 2), 0.776869839852),
        (dist.chi2_cdf(1, 4, 5), 0.413149821895),
        (dist.chi2_pdf(2, 3), 0.20755374871),
        (dist.inv_chi2(0.95, 2), 5.99146454711),
        (dist.inv_chi2(0.5, 10), 9.34181776559),
        (dist.f_cdf(0, 2, 3, 4), 0.743612802472),
        (dist.f_pdf(1, 3, 4), 0.343550031275),
        (dist.inv_f(0.95, 3, 4), 6.59138211643),
    ],
)
def test_continuous_distributions_agree_with_scipy(value, reference):
    assert value == pytest.approx(reference, rel=1e-11)


@pytest.mark.parametrize(
    "call",
    [
        lambda: dist.norm_pdf(0, 0, 0),
        lambda: dist.inv_norm(0, 0, 1),
        lambda: dist.inv_norm(1, 0, 1),
        lambda: dist.inv_t(0.5, 0),
        lambda: dist.chi2_cdf(0, 1, -1),
        lambda: dist.f_cdf(0, 1, 0, 1),
    ],
)
def test_arguments_outside_the_domain_raise(call):
    with pytest.raises(ValueError, match=r"."):
        call()


def test_median_of_t_is_exactly_zero():
    assert dist.inv_t(0.5, 7) == 0.0


@pytest.mark.parametrize(
    ("line", "wanted", "tolerance"),
    [
        ("normCdf(-1,1,0,1)", "0.68268948", 1e-7),
        ("normCdf(-1,1)", "0.68268949", 1e-7),
        ("normCdf(-∞,0)", "0.5", 1e-12),
        ("normCdf(1.96,∞)", "0.024997895", 1e-7),
        ("normCdf(8,12,10,2)", "0.68268949", 1e-7),
        ("normPdf(0,0,1)", "0.39894228", 1e-7),
        ("normPdf({0,1})", "{0.39894228,0.24197072}", 1e-7),
        ("invNorm(0.975,0,1)", "1.959964", 1e-7),
        ("invNorm(0.9,50,10)", "62.815516", 1e-7),
        ("invNorm(0.5,10,2)", "10", 1e-12),
        ("tCdf(-1,1,5)", "0.63678253", 1e-7),
        ("invT(0.975,5)", "2.5705818", 1e-7),
        ("chi2Cdf(0,3,2)", "0.77686984", 1e-7),
        ("χ²Cdf(0,3,2)", "0.77686984", 1e-7),
        ("invChi2(0.95,2)", "5.9914645", 1e-7),
        ("fCdf(0,2,3,4)", "0.7436128", 1e-7),
    ],
)
def test_continuous_functions(line, wanted, tolerance):
    same(line, wanted, tolerance)


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("normCdf(1)", "Too few arguments"),
        ("tCdf(1,2)", "Too few arguments"),
        ("normPdf(0,0,1,2)", "Too many arguments"),
        ("invNorm(0)", "Domain error"),
        ("invNorm(1.5)", "Domain error"),
        ("normPdf(0,0,-1)", "Domain error"),
        ("normPdf(x)", "Data type"),
        ("tCdf(0,1,0)", "Domain error"),
    ],
)
def test_distribution_errors(line, message):
    assert error(line) == message


def test_continuous_functions_work_in_cas_off():
    assert number("normCdf(-1,1,0,1)", CAS_OFF) == pytest.approx(0.68268949, abs=1e-8)
    assert number("invNorm(0.975,0,1)", CAS_OFF) == pytest.approx(1.959964, abs=1e-6)


@pytest.mark.parametrize(
    ("line", "wanted"),
    [
        ("binomPdf(10,0.5,5)", "0.24609375"),
        ("binomPdf(10,1/2,5)", "63/256"),  # exact inputs stay exact
        ("binomPdf(3,1/2)", "{1/8,3/8,3/8,1/8}"),
        ("binomPdf(3,1/2,{0,3})", "{1/8,1/8}"),
        ("binomPdf(3,1/2,4)", "0"),
        ("binomCdf(10,0.5,3,5)", "0.56835938"),
        ("binomCdf(20,0.3,0,5)", "0.41637082"),
        ("binomCdf(10,0.5,4)", "0.376953125"),
        ("binomCdf(3,1/2)", "{1/8,1/2,7/8,1}"),
        ("invBinom(0.5,10,0.5)", "5"),
        ("invBinom(0.95,20,0.3)", "9"),
        ("geomPdf(0.3,3)", "0.147"),
        ("geomPdf(1/2,3)", "1/8"),
        ("geomCdf(0.5,3)", "0.875"),
        ("geomCdf(1/2,2,3)", "3/8"),
        ("poissPdf(2,3)", "0.18044704"),
        ("poissCdf(2,3)", "0.85712346"),
        ("poissCdf(2,1,3)", "0.72178818"),
    ],
)
def test_discrete_distributions(line, wanted):
    same(line, wanted, 1e-7)


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("binomPdf(3,2,1)", "Domain error"),
        ("binomPdf(3.5,0.5,1)", "Domain error"),
        ("binomPdf(-1,0.5,1)", "Domain error"),
        ("binomPdf(3,0.5,-1)", "Domain error"),
        ("binomPdf(n,0.5,1)", "Domain error"),
        ("binomPdf(3,p,1)", "Data type"),
        ("invBinom(1.5,10,0.5)", "Domain error"),
        ("poissPdf(0,1)", "Domain error"),
        ("geomPdf(2,1)", "Domain error"),
    ],
)
def test_discrete_errors(line, message):
    assert error(line) == message


def test_binomial_probabilities_add_to_one():
    assert text("sum(binomPdf(10,1/3))") == "1"
    assert text("sum(binomPdf(7,0.2))") == "1."


@pytest.mark.parametrize(
    ("line", "wanted", "tolerance"),
    [
        ("tvmPmt(60,6,10000,0,12,12)", "-193.32802", 1e-7),
        ("tvmN(6,10000,-193.32802,0,12,12)", "60", 1e-6),
        ("tvmI(60,10000,-193.32802,0,12,12)", "6", 1e-6),
        ("tvmPV(60,6,-193.32802,0,12,12)", "10000", 1e-6),
        ("tvmFV(60,6,-200,0,12,12)", "269.77003", 1e-7),
        ("tvmFV(10,5,-5000,0,1,1)", "8144.4731", 1e-7),
        ("tvmFV(5,-15,-30000,0,1,1)", "13311.159", 1e-7),
        ("tvmFV(10,5,-5000,0)", "8144.4731", 1e-7),  # PpY and CpY default to 1
        ("tvmPmt(60,6,10000,0,12,12,1)", "-192.36618", 1e-7),  # payments at the start
        ("tvmFV(10,0,-5000,-100)", "6000", 1e-12),  # no interest
        ("tvmN(0,1000,-100,0)", "10", 1e-12),
        ("eff(5.4,12)", "5.5356752", 1e-8),
        ("nom(5.5356751950103,12)", "5.4", 1e-8),
        ("eff(12,1)", "12", 1e-12),
    ],
)
def test_finance(line, wanted, tolerance):
    same(line, wanted, tolerance)


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("tvmN(6,10000,0,0)", "Domain error"),  # no payment ever repays the loan
        ("tvmPmt(60,6,10000,0,0,12)", "Domain error"),
        ("tvmPmt(60,6,10000,0,12,12,2)", "Domain error"),
        ("tvmPmt(60,6,10000)", "Too few arguments"),
        ("tvmPmt(60,6,10000,0,12,12,0,1)", "Too many arguments"),
        ("tvmPmt(n,6,10000,0)", "Data type"),
    ],
)
def test_finance_errors(line, message):
    assert error(line) == message


def test_tvm_functions_invert_each_other():
    pmt = number("tvmPmt(60,6,10000,0,12,12)")
    assert number(f"tvmN(6,10000,{pmt!r},0,12,12)") == pytest.approx(60, abs=1e-5)
    assert number(f"tvmI(60,10000,{pmt!r},0,12,12)") == pytest.approx(6, abs=1e-5)
    assert number(f"tvmPV(60,6,{pmt!r},0,12,12)") == pytest.approx(10000, abs=1e-4)


def test_period_rate_and_nominal_rate_are_inverses():
    rate = fin.period_rate(7.5, 12, 4)
    assert fin.nominal_percent(rate, 12, 4) == pytest.approx(7.5)


def test_amortisation_table_matches_the_corpus():
    result = run("amortTbl(3,60,6,10000)")
    assert result.error is None
    expected = run(
        "[0,0.,0.,10000.;1,-600.,-18.76,9981.24;2,-598.87,-19.89,9961.35;3,-597.68,-21.08,9940.27]"
    )
    assert result.value is not None
    assert expected.value is not None
    assert same_value(result.value, expected.value, 0.01)


def test_loan_functions_agree_with_the_table():
    assert number("bal(3,60,6,10000)") == pytest.approx(9940.27)
    assert number("ΣInt(1,3,60,6,10000)") == pytest.approx(-600 - 598.87 - 597.68)
    assert number("ΣPrn(1,3,60,6,10000)") == pytest.approx(-18.76 - 19.89 - 21.08)
    assert number("bal(0,60,6,10000)") == 10000.0


def test_a_loan_can_be_repaid_exactly():
    rows = fin.amortization(fin.Loan(n=12, percent=12, pv=1200.0, pp=12, cp=12), 12)
    assert rows[-1][3] == pytest.approx(0, abs=0.1)
    assert rows[0] == (0, 0.0, 0.0, 1200.0)


def test_payments_at_the_start_pay_no_interest_the_first_time():
    rows = fin.amortization(fin.Loan(n=12, percent=12, pv=1200.0, pp=12, cp=12, at=1), 2)
    assert rows[1][1] == 0.0
    assert rows[2][1] != 0.0


def test_amortisation_arguments():
    assert error("amortTbl(3,60,6)") == "Too few arguments"
    assert error("bal(1,60,6,10000,0,0,1,1,0,2,9)") == "Too many arguments"
    assert error("ΣInt(3,1,60,6,10000)") == "Domain error"
