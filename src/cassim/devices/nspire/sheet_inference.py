"""Confidence interval and stat test dialogs on a Lists & Spreadsheet page (FR-STAT-004).

From the emulator (stats4, R5-I2): a test or interval with a data and a summary form first asks
for the Data Input Method (Data first); the Data form's first list is the cursor's column (`a[]`),
the 1st Result Column is the column after it, and a z or t test ends with Draw: Shade P Value,
unticked. Linear Reg t Test has Save RegEqn to and no Draw. The Ha choices name the parameter
(`Ha: μ > μ0`, `Ha: prop ≠ p0`, the regression's slope), > first and ≠ the default.

The dialog's fields are in the device's order; `args` puts their values in the engine command's
order. Alternatives use TI's numbering (0 ≠, -1 <, 1 >). The Calculator's own dialogs stay
in `statistics.py`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from cassim.device.wizard import Field

RHO = chr(0x3C1)  # Greek rho, as the device writes it
LIST = "{list}"  # a list field whose default is the cursor's column


def hypotheses(left: str, right: str) -> Field:
    return Field(
        "alternative",
        "Alternate Hyp",
        "0",
        choices=(
            ("1", f"Ha: {left} > {right}"),
            ("0", f"Ha: {left} ≠ {right}"),
            ("-1", f"Ha: {left} < {right}"),
        ),
    )


_FREQ = Field("freq", "Frequency List", "1")
_LEVEL = Field("level", "C Level", "0.95")
_POOLED = Field("pooled", "Pooled", "0", choices=(("0", "No"), ("1", "Yes")))
_MU = hypotheses("μ", "μ0")
_TWO_MU = hypotheses("μ1", "μ2")


@dataclass(frozen=True)
class Form:
    fields: tuple[Field, ...]
    args: tuple[str, ...]  # field names in the command's order; a literal starts with "="

    def command(self, name: str, values: Mapping[str, str]) -> str:
        parts = [arg[1:] if arg.startswith("=") else values[arg].strip() for arg in self.args]
        return f"{name} " + ",".join(parts)


@dataclass(frozen=True)
class Inference:
    title: str
    command: str
    key: str
    data: Form
    stats: Form | None = None  # the summary form, when there is a Data Input Method box
    shade: str = ""  # "z" or "t": the statistic a Draw: Shade P Value pane shows
    save: bool = False  # Save RegEqn to
    method: bool = False  # a Data Input Method box comes first (Data, and Stats if `stats`)


def _form(*fields: Field, order: tuple[str, ...] = ()) -> Form:
    return Form(fields, order or tuple(field.name for field in fields))


def _two_lists() -> tuple[Field, ...]:
    return (
        Field("x1", "List 1", LIST),
        Field("x2", "List 2"),
        Field("freq1", "Frequency 1", "1"),
        Field("freq2", "Frequency 2", "1"),
    )


INTERVALS = (
    Inference(
        "z Interval",
        "zInterval",
        "1",
        _form(Field("sigma", "σ"), Field("x", "List", LIST), _FREQ, _LEVEL),
        _form(Field("sigma", "σ"), Field("mean", "x̄"), Field("n", "n"), _LEVEL),
        method=True,
    ),
    Inference(
        "t Interval",
        "tInterval",
        "2",
        _form(Field("x", "List", LIST), _FREQ, _LEVEL),
        _form(Field("mean", "x̄"), Field("sd", "sx"), Field("n", "n"), _LEVEL),
        method=True,
    ),
    Inference(
        "2-Sample z Interval",
        "zInterval_2Samp",
        "3",
        _form(
            Field("sigma1", "σ1"),
            Field("sigma2", "σ2"),
            *_two_lists(),
            _LEVEL,
            order=("sigma1", "sigma2", "x1", "x2", "freq1", "freq2", "level"),
        ),
        _form(
            Field("sigma1", "σ1"),
            Field("sigma2", "σ2"),
            Field("mean1", "x̄1"),
            Field("n1", "n1"),
            Field("mean2", "x̄2"),
            Field("n2", "n2"),
            _LEVEL,
        ),
        method=True,
    ),
    Inference(
        "2-Sample t Interval",
        "tInterval_2Samp",
        "4",
        _form(*_two_lists(), _LEVEL, _POOLED),
        method=True,
    ),
    Inference(
        "1-Prop z Interval",
        "zInterval_1Prop",
        "5",
        _form(Field("successes", "Successes, x"), Field("n", "n"), _LEVEL),
    ),
    Inference(
        "2-Prop z Interval",
        "zInterval_2Prop",
        "6",
        _form(
            Field("successes1", "Successes 1, x1"),
            Field("n1", "n1"),
            Field("successes2", "Successes 2, x2"),
            Field("n2", "n2"),
            _LEVEL,
        ),
    ),
    Inference(
        "Linear Reg t Intervals",
        "LinRegtIntervals",
        "7",
        _form(
            Field("x", "X List", LIST),
            Field("y", "Y List"),
            _FREQ,
            _LEVEL,
            order=("x", "y", "freq", "=0", "level"),
        ),
    ),
)

TESTS = (
    Inference(
        "z Test",
        "zTest",
        "1",
        _form(Field("null", "μ0"), Field("sigma", "σ"), Field("x", "List", LIST), _FREQ, _MU),
        _form(Field("null", "μ0"), Field("sigma", "σ"), Field("mean", "x̄"), Field("n", "n"), _MU),
        shade="z",
        method=True,
    ),
    Inference(
        "t Test",
        "tTest",
        "2",
        _form(Field("null", "μ0"), Field("x", "List", LIST), _FREQ, _MU),
        _form(Field("null", "μ0"), Field("mean", "x̄"), Field("sd", "sx"), Field("n", "n"), _MU),
        shade="t",
        method=True,
    ),
    Inference(
        "2-Sample z Test",
        "zTest_2Samp",
        "3",
        _form(Field("sigma1", "σ1"), Field("sigma2", "σ2"), *_two_lists(), _TWO_MU),
        shade="z",
        method=True,
    ),
    Inference(
        "2-Sample t Test",
        "tTest_2Samp",
        "4",
        _form(
            *_two_lists(),
            _TWO_MU,
            _POOLED,
            order=("x1", "x2", "freq1", "freq2", "pooled", "alternative"),
        ),
        shade="t",
        method=True,
    ),
    Inference(
        "1-Prop z Test",
        "zTest_1Prop",
        "5",
        _form(
            Field("p0", "P0"),
            Field("successes", "Successes, x"),
            Field("n", "n"),
            hypotheses("prop", "p0"),
        ),
        shade="z",
    ),
    Inference(
        "2-Prop z Test",
        "zTest_2Prop",
        "6",
        _form(
            Field("successes1", "Successes 1, x1"),
            Field("n1", "n1"),
            Field("successes2", "Successes 2, x2"),
            Field("n2", "n2"),
            hypotheses("p1", "p2"),
        ),
        shade="z",
    ),
    Inference(
        "χ² GOF",
        "χ²GOF",
        "7",
        _form(
            Field("observed", "Observed List", LIST),
            Field("expected", "Expected List"),
            Field("df", "Deg of Freedom, df"),
        ),
    ),
    Inference("χ² 2-way Test", "χ²2way", "8", _form(Field("observed", "Observed Matrix"))),
    Inference(
        "2-Sample F Test",
        "FTest_2Samp",
        "9",
        _form(*_two_lists(), hypotheses("σ1", "σ2")),
    ),
    Inference(
        "Linear Reg t Test",
        "LinRegtTest",
        "A",
        _form(
            Field("x", "X List", LIST),
            Field("y", "Y List"),
            _FREQ,
            hypotheses(f"β & {RHO}", "0"),
            order=("x", "y", "freq", "=0", "alternative"),
        ),
        save=True,
    ),
)


def inference(command: str) -> Inference | None:
    return next((item for item in (*INTERVALS, *TESTS) if item.command == command), None)
