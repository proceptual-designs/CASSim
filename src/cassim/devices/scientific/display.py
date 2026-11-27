"""How answers are shown (FR-FX-CFG-003, FR-FX-CFG-004, FR-FX-DSP-005 to -009).

Decimals have ten significant digits. Norm 1 switches to ×10ⁿ below 0.01, Norm 2 below 10⁻⁹, and
both at 10¹⁰ and above; Fix n shows n decimal places; Sci n shows n significant digits (Sci 0 is
ten). Exact answers are fractions and mixed numbers while they fit in ten digits; otherwise the
decimal is shown. Surds and multiples of π are shown exactly only with the `surds` extra on (the
four calculators behind the keys show them as decimals). Pure Python: no Flet.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from typing import Literal

from cassim.devices.scientific import values as v
from cassim.devices.scientific.layout import Frac, Node, Seq, Sqrt, Sup, Text, to_text
from cassim.devices.scientific.parser import AngleUnit, Pair, Percent, Value
from cassim.devices.scientific.values import Exact, Number

SIGNIFICANT = 10
MAX_EXACT_DIGITS = 10
SCI_ABOVE = Decimal("1e10")

Form = Literal["auto", "decimal", "exact", "dms", "eng"]


@dataclass
class Setup:
    """The SETUP settings, with the device's defaults."""

    input: Literal["math", "line"] = "math"  # MthIO or LineIO
    output: Literal["math", "line"] = "line"  # MathO or LineO (LineIO always shows LineO)
    angle: AngleUnit = "DEG"
    disp: Literal["Norm", "Fix", "Sci", "Eng"] = "Norm"  # Eng: the EL-531's ENG display mode
    digits: int = 1  # Norm 1 or 2, Fix 0-9, Sci 0-9, Eng 0-9 (decimal places)
    fraction: Literal["d/c", "ab/c"] = "d/c"
    frequency: bool = False
    comma: bool = False  # Disp: a decimal comma in answers (a dot is always typed)
    # CASSim's own extra, off by default: exact surds and multiples of π in MathO, as the
    # fx-8200 AU, fx-991ES PLUS, HP 300s+ and TI MultiView models give (decision 0041)
    surds: bool = False

    @property
    def natural_output(self) -> bool:
        return self.input == "math" and self.output == "math"

    def to_dict(self) -> dict[str, object]:
        return {
            "input": self.input,
            "output": self.output,
            "angle": self.angle,
            "disp": self.disp,
            "digits": self.digits,
            "fraction": self.fraction,
            "frequency": self.frequency,
            "comma": self.comma,
            "surds": self.surds,
        }

    @classmethod
    def from_dict(cls, data: object) -> Setup:
        setup = cls()
        if not isinstance(data, dict):
            return setup
        if data.get("input") in ("math", "line"):
            setup.input = data["input"]
        if data.get("output") in ("math", "line"):
            setup.output = data["output"]
        if data.get("angle") in ("DEG", "RAD", "GRA"):
            setup.angle = data["angle"]
        if data.get("disp") in ("Norm", "Fix", "Sci", "Eng"):
            setup.disp = data["disp"]
        digits = data.get("digits")
        if isinstance(digits, int) and 0 <= digits <= 9:  # noqa: PLR2004
            setup.digits = digits
        if setup.disp == "Norm" and setup.digits not in (1, 2):
            setup.digits = 1
        if data.get("fraction") in ("d/c", "ab/c"):
            setup.fraction = data["fraction"]
        setup.frequency = data.get("frequency") is True
        setup.comma = data.get("comma") is True
        setup.surds = data.get("surds") is True
        return setup


# ---- decimals -----------------------------------------------------------------------------------


def _significant(d: Decimal, n: int) -> Decimal:
    if d == 0:
        return Decimal(0)
    quantum = Decimal(1).scaleb(d.adjusted() - n + 1)
    rounded = d.quantize(quantum, rounding=ROUND_HALF_UP)
    if rounded.adjusted() != d.adjusted():  # 9.99… rounded up to 10.0…
        quantum = Decimal(1).scaleb(rounded.adjusted() - n + 1)
        rounded = d.quantize(quantum, rounding=ROUND_HALF_UP)
    return rounded


def _plain(d: Decimal, *, trim: bool = True) -> str:
    text = f"{d:f}"
    if trim and "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text.replace("-", "−")


def _scientific(d: Decimal, digits: int, *, trim: bool, exponent: int | None = None) -> Seq:
    """Mantissa ×10^exponent. `exponent` forces the exponent (ENG); otherwise one digit before
    the point."""
    if d == 0:
        return (Text("0"),)
    rounded = _significant(d, digits)
    exp = rounded.adjusted() if exponent is None else exponent
    mantissa = rounded.scaleb(-exp)
    text = _plain(mantissa, trim=trim)
    return (Text(text), Text("×10"), Sup((Text(str(exp).replace("-", "−")),)))


def decimal(x: float, setup: Setup, eng: int | None = None) -> Seq:  # noqa: PLR0911
    """x in the current Norm, Fix or Sci setting; `eng` is the ENG exponent when ENG was pressed."""
    d = Decimal(repr(x))
    if eng is not None:
        return _scientific(d, SIGNIFICANT, trim=True, exponent=eng)
    if d == 0 and setup.disp != "Norm":
        places = setup.digits if setup.disp == "Fix" else (setup.digits or SIGNIFICANT) - 1
        return (Text(_fixed(Decimal(0), places)),)
    if setup.disp == "Sci":
        return _scientific(d, setup.digits or SIGNIFICANT, trim=False)
    if setup.disp == "Eng":
        return _engineering(d, setup.digits)
    rounded = _significant(d, SIGNIFICANT)
    low = Decimal("0.01") if setup.digits == 1 else Decimal("1e-9")
    if d != 0 and (abs(rounded) >= SCI_ABOVE or (setup.disp == "Norm" and abs(rounded) < low)):
        return _scientific(d, SIGNIFICANT, trim=True)
    if setup.disp == "Fix":
        return (Text(_fixed(d, setup.digits)),)
    return (Text(_plain(rounded)),)


def _engineering(d: Decimal, places: int) -> Seq:
    """The EL-531's ENG display: a power of ten that is a multiple of 3, `places` decimals."""
    if d == 0:
        return (Text(_fixed(Decimal(0), places)),)
    exp = math.floor(d.adjusted() / 3) * 3
    mantissa = d.scaleb(-exp).quantize(Decimal(1).scaleb(-places), ROUND_HALF_UP)
    if abs(mantissa) >= 1000:  # noqa: PLR2004  rounded up into the next group
        exp += 3
        mantissa = d.scaleb(-exp).quantize(Decimal(1).scaleb(-places), ROUND_HALF_UP)
    return (
        Text(_plain(mantissa, trim=False)),
        Text("×10"),
        Sup((Text(str(exp).replace("-", "−")),)),
    )


def with_comma(seq: Seq) -> Seq:
    """An answer with a decimal comma (SETUP Disp: Comma)."""
    return tuple(
        Text(node.text.replace(".", ",")) if isinstance(node, Text) else node for node in seq
    )


def _fixed(d: Decimal, places: int) -> str:
    return _plain(d.quantize(Decimal(1).scaleb(-places), ROUND_HALF_UP), trim=False)


def engineering_exponent(x: float) -> int:
    """The largest multiple of 3 not above x's exponent."""
    if x == 0:
        return 0
    return math.floor(_significant(Decimal(repr(x)), SIGNIFICANT).adjusted() / 3) * 3


def rnd(value: Number, setup: Setup) -> Number:
    """Rnd(: the value rounded as the display shows it (FR-FX-FNC-009)."""
    x = float(value)
    d = Decimal(repr(x))
    if setup.disp == "Fix":
        rounded = d.quantize(Decimal(1).scaleb(-setup.digits), ROUND_HALF_UP)
    elif setup.disp == "Sci":
        rounded = _significant(d, setup.digits or SIGNIFICANT)
    elif setup.disp == "Eng":
        exp = math.floor(d.adjusted() / 3) * 3 if d else 0
        rounded = (
            d.scaleb(-exp).quantize(Decimal(1).scaleb(-setup.digits), ROUND_HALF_UP).scaleb(exp)
        )
    else:
        rounded = _significant(d, SIGNIFICANT)
    return v.rational(Fraction(rounded))


# ---- exact forms --------------------------------------------------------------------------------


def _ndigits(*numbers: int) -> int:
    return sum(len(str(abs(n))) for n in numbers)


def fraction(q: Fraction, setup: Setup, *, mixed: bool) -> Seq | None:  # noqa: PLR0911
    """q as an integer, a fraction or a mixed number, or None when it needs more than ten digits."""
    sign = "−" if q < 0 else ""
    a = abs(q)
    if a.denominator == 1:
        if _ndigits(a.numerator) > MAX_EXACT_DIGITS:
            return None
        return (Text(f"{sign}{a.numerator}"),)
    whole, rest = divmod(a.numerator, a.denominator)
    natural = setup.input == "math"  # MthIO draws fractions stacked, in MathO and LineO alike
    if mixed and whole:
        if _ndigits(whole, rest, a.denominator) > MAX_EXACT_DIGITS:
            return None
        if natural:
            part = Frac((Text(str(rest)),), (Text(str(a.denominator)),))
            return (Text(f"{sign}{whole} "), part)
        return (Text(f"{sign}{whole}⌟{rest}⌟{a.denominator}"),)
    if _ndigits(a.numerator, a.denominator) > MAX_EXACT_DIGITS:
        return None
    if natural:
        head: tuple[Node, ...] = (Text(sign),) if sign else ()
        return (*head, Frac((Text(str(a.numerator)),), (Text(str(a.denominator)),)))
    return (Text(f"{sign}{a.numerator}⌟{a.denominator}"),)


def _term(coeff: int, radicand: int, pi: int) -> Seq:
    """|coeff|√radicand π, leaving out a coefficient of 1."""
    nodes: list[Node] = []
    magnitude = abs(coeff)
    if magnitude != 1 or (radicand == 1 and not pi):
        nodes.append(Text(str(magnitude)))
    if radicand != 1:
        nodes.append(Sqrt((Text(str(radicand)),)))
    if pi:
        nodes.append(Text("π"))
    return tuple(nodes)


def surd(value: Exact) -> Seq | None:
    """A surd or π form in natural display, or None if it is too long or not a known shape."""
    terms = value.terms
    denominator = math.lcm(*(c.denominator for _, _, c in terms))
    numerators = [(int(c * denominator), r, p) for r, p, c in terms]
    if _ndigits(denominator, *(n for n, _, _ in numerators), *(r for _, r, _ in numerators)) > (
        MAX_EXACT_DIGITS
    ):
        return None
    top: list[Node] = []
    for index, (n, r, p) in enumerate(numerators):
        if index == 0:
            if n < 0:
                top.append(Text("−"))
        else:
            top.append(Text("+" if n > 0 else "−"))
        top.extend(_term(n, r, p))
    if denominator == 1:
        return tuple(top)
    if len(numerators) == 1 and numerators[0][0] < 0:  # −√3/2 with the sign outside
        return (Text("−"), Frac(tuple(top[1:]), (Text(str(denominator)),)))
    return (Frac(tuple(top), (Text(str(denominator)),)),)


def exact(value: Number, setup: Setup, *, mixed: bool) -> Seq | None:
    """The exact form of a value, or None when there is none to show."""
    if isinstance(value, Exact):
        q = value.rational
        if q is not None:
            return fraction(q, setup, mixed=mixed)
        if not (setup.natural_output and setup.surds):
            return None  # the four calculators show surds and π as decimals
        return surd(value)
    q = v.recognise_fraction(value)
    return None if q is None else fraction(q, setup, mixed=mixed)


def dms(x: float) -> Seq:
    """Degrees, minutes and seconds (FR-FX-DSP-008)."""
    sign = "−" if x < 0 else ""
    total = Decimal(repr(abs(x))) * 3600
    seconds_total = _significant(total, 12) if total else Decimal(0)
    degrees, rest = divmod(seconds_total, 3600)
    minutes, seconds = divmod(rest, 60)
    seconds = seconds.quantize(Decimal("0.01"), ROUND_HALF_UP)
    if seconds >= 60:  # noqa: PLR2004
        seconds -= 60
        minutes += 1
    if minutes >= 60:  # noqa: PLR2004
        minutes -= 60
        degrees += 1
    return (Text(f"{sign}{int(degrees)}°{int(minutes)}°{_plain(seconds)}°"),)


def show(  # noqa: PLR0913
    value: Value,
    setup: Setup,
    form: Form = "auto",
    *,
    mixed: bool | None = None,
    eng: int | None = None,
    prefer_exact: bool = True,
) -> Seq:
    """The answer line for a value. `form` follows S⇔D, ° ' " and ENG; `mixed` follows
    SHIFT S⇔D (None means the SETUP fraction setting)."""
    if isinstance(value, bool):
        return (Text("TRUE" if value else "FALSE"),)
    if isinstance(value, Percent):
        value = value.share
    if isinstance(value, Pair):
        first = to_text(show(value.first, setup))
        second = to_text(show(value.second, setup))
        return (Text(f"{value.first_name}={first}, {value.second_name}={second}"),)
    as_mixed = setup.fraction == "ab/c" if mixed is None else mixed
    x = float(value)
    if form == "dms":
        return dms(x)
    if form == "eng":
        return decimal(x, setup, eng=eng if eng is not None else engineering_exponent(x))
    wants_exact = form == "exact" or (form == "auto" and prefer_exact and isinstance(value, Exact))
    whole = (
        isinstance(value, Exact) and value.rational is not None and value.rational.denominator == 1
    )
    if whole and setup.disp != "Norm":
        wants_exact = False  # Fix and Sci format whole numbers too; fractions and surds stay
    if wants_exact:
        shown = exact(value, setup, mixed=as_mixed)
        if shown is not None:
            return shown
    return decimal(x, setup)
