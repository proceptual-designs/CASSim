"""Dialogs for confidence intervals and significance tests."""

from collections.abc import Mapping

from cassim.device.wizard import Field, Wizard

FREQUENCY = Field("freq", "Frequency List", "1")
CONFIDENCE_LEVEL = Field("level", "C-Level", "0.95")
ALTERNATIVE = Field(
    "alternative",
    "Alternate Hyp",
    "0",
    choices=(("0", "Ha: ≠"), ("-1", "Ha: <"), ("1", "Ha: >")),
)
POOLED = Field("pooled", "Pooled", "0", choices=(("0", "No"), ("1", "Yes")))

INTERVALS = (
    (
        "z Interval",
        "zInterval",
        "1",
        (
            Field("sigma", "σ", "1"),
            Field("mean", "x̄"),
            Field("n", "n"),
            CONFIDENCE_LEVEL,
        ),
    ),
    (
        "t Interval",
        "tInterval",
        "2",
        (Field("mean", "x̄"), Field("sd", "sx"), Field("n", "n"), CONFIDENCE_LEVEL),
    ),
    (
        "2-Sample z Interval",
        "zInterval_2Samp",
        "3",
        (
            Field("sigma1", "σ1"),
            Field("sigma2", "σ2"),
            Field("mean1", "x̄1"),
            Field("n1", "n1"),
            Field("mean2", "x̄2"),
            Field("n2", "n2"),
            CONFIDENCE_LEVEL,
        ),
    ),
    (
        "2-Sample t Interval",
        "tInterval_2Samp",
        "4",
        (
            Field("x1", "X1 List"),
            Field("x2", "X2 List"),
            Field("freq1", "Frequency List 1", "1"),
            Field("freq2", "Frequency List 2", "1"),
            CONFIDENCE_LEVEL,
            POOLED,
        ),
    ),
    (
        "1-Prop z Interval",
        "zInterval_1Prop",
        "5",
        (Field("successes", "Successes, x"), Field("n", "n"), CONFIDENCE_LEVEL),
    ),
    (
        "2-Prop z Interval",
        "zInterval_2Prop",
        "6",
        (
            Field("successes1", "Successes 1, x1"),
            Field("n1", "n1"),
            Field("successes2", "Successes 2, x2"),
            Field("n2", "n2"),
            CONFIDENCE_LEVEL,
        ),
    ),
    (
        "Linear Reg t Intervals",
        "LinRegtIntervals",
        "7",
        (
            Field("x", "X List"),
            Field("y", "Y List"),
            FREQUENCY,
            Field("slope", "Slope", "0"),
            CONFIDENCE_LEVEL,
        ),
    ),
)

TESTS = (
    (
        "z Test",
        "zTest",
        "1",
        (
            Field("null", "μ0"),
            Field("sigma", "σ", "1"),
            Field("mean", "x̄"),
            Field("n", "n"),
            ALTERNATIVE,
        ),
    ),
    (
        "t Test",
        "tTest",
        "2",
        (
            Field("null", "μ0"),
            Field("mean", "x̄"),
            Field("sd", "sx"),
            Field("n", "n"),
            ALTERNATIVE,
        ),
    ),
    (
        "2-Sample z Test",
        "zTest_2Samp",
        "3",
        (
            Field("sigma1", "σ1", "1"),
            Field("sigma2", "σ2", "1"),
            Field("x1", "X1 List"),
            Field("x2", "X2 List"),
            Field("freq1", "Frequency List 1", "1"),
            Field("freq2", "Frequency List 2", "1"),
            ALTERNATIVE,
        ),
    ),
    (
        "2-Sample t Test",
        "tTest_2Samp",
        "4",
        (
            Field("x1", "X1 List"),
            Field("x2", "X2 List"),
            Field("freq1", "Frequency List 1", "1"),
            Field("freq2", "Frequency List 2", "1"),
            POOLED,
            ALTERNATIVE,
        ),
    ),
    (
        "1-Prop z Test",
        "zTest_1Prop",
        "5",
        (
            Field("p0", "p0"),
            Field("successes", "Successes, x"),
            Field("n", "n"),
            ALTERNATIVE,
        ),
    ),
    (
        "2-Prop z Test",
        "zTest_2Prop",
        "6",
        (
            Field("successes1", "Successes 1, x1"),
            Field("n1", "n1"),
            Field("successes2", "Successes 2, x2"),
            Field("n2", "n2"),
            ALTERNATIVE,
        ),
    ),
    (
        "χ² GOF",
        "χ²GOF",
        "7",
        (
            Field("observed", "Observed List"),
            Field("expected", "Expected List"),
            Field("df", "df"),
        ),
    ),
    ("χ² 2-Way Test", "χ²2way", "8", (Field("observed", "Observed Matrix"),)),
    (
        "2-Sample F Test",
        "FTest_2Samp",
        "9",
        (
            Field("x1", "X1 List"),
            Field("x2", "X2 List"),
            Field("freq1", "Frequency List 1", "1"),
            Field("freq2", "Frequency List 2", "1"),
            ALTERNATIVE,
        ),
    ),
    (
        "Linear Reg t Test",
        "LinRegtTest",
        "A",
        (
            Field("x", "X List"),
            Field("y", "Y List"),
            FREQUENCY,
            Field("slope", "Slope", "0"),
            ALTERNATIVE,
        ),
    ),
)


def command_wizard(title: str, name: str, fields: tuple[Field, ...]) -> Wizard:
    names = [field.name for field in fields]
    return Wizard(
        title,
        fields,
        run=True,
        build=lambda values: f"{name} " + ",".join(values[field] for field in names),
    )


def build_command(name: str, fields: tuple[Field, ...], values: Mapping[str, str]) -> str:
    return f"{name} " + ",".join(values[field.name] for field in fields)
