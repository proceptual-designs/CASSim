# Requirement traced here: FR-STAT-004
import pytest
from scipy import stats

from cassim.core.session import Session
from cassim.core.settings import Settings


def _session(*lines: str, digits: str = "float8") -> Session:
    session = Session(Settings(digits=digits))
    for line in lines:
        result = session.eval(line)
        assert result.error is None, (line, result.error)
    return session


def _number(session: Session, name: str) -> float:
    result = session.eval(f"stat.{name}")
    assert result.error is None, result.error
    return float(result.text.replace("ᴇ", "e"))


def test_t_interval_matches_the_captured_catalog_case():
    session = _session(
        "ly:={2.1,3.9,6.2,7.8,10.1,12.2}",
        "tInterval ly,1,.95",
    )
    assert _number(session, "CLower") == pytest.approx(3.0805522)
    assert _number(session, "CUpper") == pytest.approx(11.019448)
    assert _number(session, "ME") == pytest.approx(3.9694478)
    assert _number(session, "df") == 5


def test_two_sample_t_interval_matches_the_captured_catalog_case():
    session = _session(
        "lx:={1,2,3,4,5,6}",
        "ly:={2.1,3.9,6.2,7.8,10.1,12.2}",
        "tInterval_2Samp lx,ly,1,1,.95,0",
    )
    assert _number(session, "CLower") == pytest.approx(-7.5890631)
    assert _number(session, "CUpper") == pytest.approx(0.4890631)
    assert _number(session, "x̄Diff") == pytest.approx(-3.55)
    assert _number(session, "ME") == pytest.approx(4.0390631)
    assert _number(session, "df") == pytest.approx(7.3082162)


def test_regression_interval_and_test_match_the_captured_catalog_cases():
    session = _session(
        "lx:={1,2,3,4,5,6}",
        "ly:={2.1,3.9,6.2,7.8,10.1,12.2}",
        "LinRegtTest lx,ly,1,0",
    )
    assert _number(session, "t") == pytest.approx(47.238425)
    assert _number(session, "PVal") == pytest.approx(0.0000012, abs=1e-7)
    assert _number(session, "SESlope") == pytest.approx(0.0427618)

    session.eval("LinRegtIntervals lx,ly,1,0,.95")
    assert _number(session, "CLower") == pytest.approx(1.9012742)
    assert _number(session, "CUpper") == pytest.approx(2.1387258)
    assert _number(session, "ME") == pytest.approx(0.11872579)


def test_goodness_of_fit_matches_the_captured_catalog_case():
    session = _session("χ²GOF {10,20,30},{20,20,20},2")
    assert _number(session, "χ²") == 10
    assert _number(session, "PVal") == pytest.approx(0.00673795)
    assert _number(session, "df") == 2


def test_two_sample_f_test_matches_the_captured_catalog_case():
    session = _session(
        "lx:={1,2,3,4,5,6}",
        "ly:={2.1,3.9,6.2,7.8,10.1,12.2}",
        "FTest_2Samp lx,ly,1,1,0",
    )
    assert _number(session, "PVal") == pytest.approx(0.14844134)
    assert _number(session, "dfNumer") == 5
    assert _number(session, "dfDenom") == 5


def test_one_proportion_interval_and_test_use_the_standard_vce_formula():
    session = _session("zInterval_1Prop 12,20,.95")
    assert _number(session, "p̂") == pytest.approx(0.6)
    assert _number(session, "CLower") == pytest.approx(0.3853, abs=1e-3)
    assert _number(session, "CUpper") == pytest.approx(0.8147, abs=1e-3)

    session.eval("zTest_1Prop .5,12,20,0")
    assert _number(session, "z") == pytest.approx(0.89442719)
    assert _number(session, "PVal") == pytest.approx(0.37109337)


def test_mean_interval_and_tests_accept_list_inputs():
    session = _session(
        "xs:={1,2,3,4}",
        "zInterval 1,xs,1,.95",
    )
    assert _number(session, "x̄") == pytest.approx(2.5)
    assert _number(session, "CLower") == pytest.approx(1.520018, abs=1e-6)
    assert _number(session, "CUpper") == pytest.approx(3.479982, abs=1e-6)

    session.eval("tTest 0,xs,1,0")
    assert _number(session, "df") == 3
    assert _number(session, "t") == pytest.approx(3.87298335)

    session.eval("zTest 0,1,xs,1,0")
    assert _number(session, "z") == pytest.approx(5)


def test_two_sample_mean_tests_and_two_way_chi_square():
    session = _session("xs:={1,2,3,4}", "ys:={2,3,4,5}", "zTest_2Samp 1,1,xs,ys,1,1,0")
    assert _number(session, "z") == pytest.approx(-1.41421356)
    session.eval("tTest_2Samp xs,ys,1,1,0,0")
    assert _number(session, "PVal") == pytest.approx(0.3153336)

    session.eval("χ²2way [10,20;20,10]")
    assert _number(session, "χ²") == pytest.approx(6.66666667)
    assert _number(session, "df") == 1
    assert _number(session, "PVal") == pytest.approx(0.00982327, abs=1e-7)


def test_invalid_confidence_levels_are_domain_errors():
    session = Session()
    assert session.eval("zInterval_1Prop 12,20,1").error == "Domain error"


def test_any_positive_or_negative_hypothesis_picks_the_tail():
    """TI's Hypoth: 0 is ≠, below 0 is <, above 0 is > (plan B10)."""
    greater, also_greater = _session("zTest_1Prop .5,12,20,1"), _session("zTest_1Prop .5,12,20,3")
    assert _number(greater, "PVal") == pytest.approx(_number(also_greater, "PVal"))
    less, also_less = _session("zTest_1Prop .5,12,20,-1"), _session("zTest_1Prop .5,12,20,-5")
    assert _number(less, "PVal") == pytest.approx(_number(also_less, "PVal"))


@pytest.mark.parametrize(("alternative", "tail"), [(0, 0), (-1, 1), (1, 2)])
def test_summary_mean_tests_use_the_selected_tail(alternative, tail):
    session = _session(f"tTest 0,2,2,16,{alternative}")
    expected_tails = (
        2 * stats.t.sf(4, 15),
        stats.t.cdf(4, 15),
        stats.t.sf(4, 15),
    )
    assert _number(session, "t") == pytest.approx(4)
    assert _number(session, "df") == 15
    assert _number(session, "PVal") == pytest.approx(expected_tails[tail], abs=1e-8)

    session = _session(f"zTest 0,2,2,16,{alternative}")
    expected_tails = (2 * stats.norm.sf(4), stats.norm.cdf(4), stats.norm.sf(4))
    assert _number(session, "z") == pytest.approx(4)
    assert _number(session, "PVal") == pytest.approx(expected_tails[tail], abs=1e-8)


def test_two_sample_z_interval_from_summary_and_frequency_lists():
    standard_error = (2**2 / 4 + 3**2 / 9) ** 0.5
    margin = stats.norm.ppf(0.975) * standard_error
    summary = _session("zInterval_2Samp 2,3,5,4,3,9,.95")
    assert _number(summary, "x̄Diff") == pytest.approx(2)
    assert _number(summary, "CLower") == pytest.approx(2 - margin)
    assert _number(summary, "CUpper") == pytest.approx(2 + margin)

    lists = _session(
        "xs:={4,6}",
        "ys:={2,4}",
        "zInterval_2Samp 2,3,xs,ys,{2,2},{5,4},.95",
    )
    difference = 5 - 26 / 9
    assert _number(lists, "x̄Diff") == pytest.approx(difference)
    assert _number(lists, "CLower") == pytest.approx(difference - margin)
    assert _number(lists, "CUpper") == pytest.approx(difference + margin)


def test_two_proportion_interval_and_test():
    session = _session("zInterval_2Prop 12,20,8,20,.95")
    margin = stats.norm.ppf(0.975) * (2 * 0.6 * 0.4 / 20) ** 0.5
    assert _number(session, "p̂Diff") == pytest.approx(0.2)
    assert _number(session, "CLower") == pytest.approx(0.2 - margin)
    assert _number(session, "CUpper") == pytest.approx(0.2 + margin)

    session = _session("zTest_2Prop 12,20,8,20,2")
    z = 0.2 / (0.5 * 0.5 * (1 / 20 + 1 / 20)) ** 0.5
    assert _number(session, "z") == pytest.approx(z)
    assert _number(session, "PVal") == pytest.approx(stats.norm.sf(z))


@pytest.mark.parametrize(
    "command",
    [
        "tInterval 5,2,1,.95",
        "zInterval 0,5,10,.95",
        "zInterval 1,5,0,.95",
        "tInterval_2Samp {1,1},{2,2},1,1,.95,0",
        "zInterval_2Prop 21,20,8,20,.95",
        "zTest_2Prop 0,20,0,20,0",
        "tTest 0,5,0,10,0",
        "zTest 0,0,5,10,0",
        "tTest_2Samp {1,1},{2,2},1,1,1,0",
        "zInterval_2Samp 1,0,5,4,3,9,.95",
        "zInterval_2Samp 1,1,5,4,3,9,1",
        "zTest_2Samp 0,0,{1,2},{2,3},1,1,0",
        "FTest_2Samp {1,1},{2,3},1,1,0",
        "χ²GOF {10,20},{10,0},1",
        "χ²2way [0,0;0,0]",
        "χ²2way [1,0;0,0]",
        "LinRegtTest {1,1,1},{1,2,3}",
        "LinRegtIntervals {1,1,1},{1,2,3}",
        "zInterval_1Prop 1.5,20,.95",
    ],
)
def test_invalid_inference_inputs_report_domain_errors(command):
    assert Session().eval(command).error == "Domain error"


def test_linear_regression_t_test_stores_the_regression_equation():
    """The sheet's Linear Reg t Test appends `CopyVar stat.RegEqn,f1` (plan B11)."""
    session = _session("LinRegtTest {1,2,3,4},{3,5,7,9.5}")
    assert session.eval("stat.RegEqn(x)").text == "2.15*x+0.75"
    assert session.eval("stat.RegEqn(2)").text == "5.05"


def _rows(session: Session) -> list[tuple[str, str]]:
    result = session.eval("stat.results")
    assert result.error is None, result.error
    rows = result.text.removeprefix("[").removesuffix("]").split(";")
    return [(label, value) for label, _, value in (row.partition(",") for row in rows)]


def test_t_test_rows_match_the_run_6_sheet():
    """Emulator run 6, R6-C2: eight rows, the Alternate Hyp and sx among them."""
    session = _session("d1:={2,4,4,4,5,5,7,9}", "tTest 4,d1,1,0")
    assert [label for label, _ in _rows(session)] == [
        '"Title"',
        '"Alternate Hyp"',
        '"t"',
        '"PVal"',
        '"df"',
        '"x̄"',
        '"sx := sn-1x"',
        '"n"',
    ]
    assert _rows(session)[1][1] == '"μ ≠ μ0"'
    assert _number(session, "t") == pytest.approx(1.3228757, abs=1e-7)
    assert _number(session, "PVal") == pytest.approx(0.22745282, abs=1e-8)
    assert _number(session, "df") == 7
    assert _number(session, "x̄") == 5
    assert _number(session, "sx") == pytest.approx(2.1380899, abs=1e-7)
    assert _number(session, "n") == 8


def test_two_sample_t_interval_from_summary_statistics_matches_run_6():
    """Emulator run 6, S2: Stats input, not pooled. The device's t quantile differs from
    SciPy's (and CASSim's, -0.601090895431) by about 2.4ᴇ-8, so the bounds are checked to 1ᴇ-7;
    df is the same to all 12 places."""
    session = _session("tInterval_2Samp 5.4,1.2,10,4.8,1.5,12,0.95,0", digits="float12")
    assert _number(session, "CLower") == pytest.approx(-0.601090871756, abs=1e-7)
    assert _number(session, "CUpper") == pytest.approx(1.80109087176, abs=1e-7)
    assert _number(session, "x̄Diff") == pytest.approx(0.6, abs=1e-12)
    assert _number(session, "ME") == pytest.approx(1.20109087176, abs=1e-7)
    assert _number(session, "df") == pytest.approx(19.9803265276, abs=1e-10)
    labels = [label.strip('"') for label, _ in _rows(session)]
    assert labels == [
        "Title",
        "CLower",
        "CUpper",
        "x̄Diff",
        "ME",
        "df",
        "x̄1",
        "x̄2",
        "sx1",
        "sx2",
        "n1",
        "n2",
    ]


def test_linear_regression_t_test_matches_run_6():
    """Emulator run 6, S2: the dragged ys, the device's values and row order. The device's
    PVal differs from SciPy's (and CASSim's, 0.047039689277) by about 2.5ᴇ-10."""
    session = _session(
        "xs:={1,2,3,4,5,6}",
        "ys:={2,3,6.949,4,6,8}",
        "LinRegtTest xs,ys,1,0",
        digits="float12",
    )
    expected = {
        "t": 2.83638252595,
        "PVal": 0.047039689028,
        "df": 4,
        "a": 1.3864,
        "b": 1.03002857143,
        "s": 1.51915992293,
        "SESlope": 0.363148680407,
        "r²": 0.667913811739,
        "r": 0.817259941352,
    }
    for name, value in expected.items():
        tolerance = 1e-9 if name == "PVal" else 1e-11
        assert _number(session, name) == pytest.approx(value, abs=tolerance), name
    rows = _rows(session)
    assert [label.strip('"') for label, _ in rows] == [
        "Title",
        "Alternate Hyp",
        "RegEqn",
        "t",
        "PVal",
        "df",
        "a",
        "b",
        "s",
        "SESlope",
        "r²",
        "r",
        "Resid",
    ]
    assert rows[0][1] == '"Linear Reg t Test"'
    assert rows[1][1] == f'"β & {chr(0x3C1)} ≠ 0"'  # Greek rho


@pytest.mark.parametrize(("alternative", "relation"), [(0, "≠"), (1, ">"), (-1, "<")])
def test_the_alternate_hypothesis_row_names_the_relation(alternative, relation):
    session = _session(f"tTest_2Samp 5.4,1.2,10,4.8,1.5,12,{alternative},0")
    assert _rows(session)[1] == ('"Alternate Hyp"', f'"μ1 {relation} μ2"')


def test_two_sample_t_test_takes_the_hypothesis_before_pooled():
    """Reference Guide order: `tTest_2Samp List1,List2,Freq1,Freq2,Hypoth,Pooled`."""
    lists = _session("xs:={1,2,3,4}", "ys:={2,3,4,5}", "tTest_2Samp xs,ys,1,1,1,0")
    welch = stats.ttest_ind([1, 2, 3, 4], [2, 3, 4, 5], equal_var=False, alternative="greater")
    assert _number(lists, "PVal") == pytest.approx(welch.pvalue, abs=1e-8)
    pooled = _session("xs:={1,2,3,9}", "ys:={2,3,4,5}", "tTest_2Samp xs,ys,1,1,0,1")
    expected = stats.ttest_ind([1, 2, 3, 9], [2, 3, 4, 5], equal_var=True)
    assert _number(pooled, "PVal") == pytest.approx(expected.pvalue, abs=1e-8)
    assert _number(pooled, "df") == 6


def test_two_sample_t_test_from_summary_statistics():
    session = _session("tTest_2Samp 5.4,1.2,10,4.8,1.5,12,0,1")
    expected = stats.ttest_ind_from_stats(5.4, 1.2, 10, 4.8, 1.5, 12, equal_var=True)
    assert _number(session, "t") == pytest.approx(expected.statistic, abs=1e-7)
    assert _number(session, "PVal") == pytest.approx(expected.pvalue, abs=1e-8)
    assert _number(session, "df") == 20


def test_two_sample_z_test_from_summary_statistics():
    session = _session("zTest_2Samp 1.2,1.5,5.4,10,4.8,12,-1")
    z = 0.6 / (1.2**2 / 10 + 1.5**2 / 12) ** 0.5
    assert _number(session, "z") == pytest.approx(z, abs=1e-7)
    assert _number(session, "PVal") == pytest.approx(stats.norm.cdf(z), abs=1e-8)
