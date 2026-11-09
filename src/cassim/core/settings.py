"""Angle, calc mode, Real/Rect/Polar, float digits, base; course presets."""

from dataclasses import dataclass
from enum import StrEnum


class Angle(StrEnum):
    RADIAN = "radian"
    DEGREE = "degree"
    GRADIAN = "gradian"


class Calc(StrEnum):
    AUTO = "auto"
    EXACT = "exact"
    APPROXIMATE = "approximate"


class Domain(StrEnum):
    REAL = "real"
    RECTANGULAR = "rectangular"
    POLAR = "polar"


class CasMode(StrEnum):
    ON = "on"
    EXACT_ARITHMETIC = "exact_arithmetic"
    OFF = "off"


class Case(StrEnum):
    """Whether `x` and `X` are one variable (the handheld) or two."""

    INSENSITIVE = "insensitive"
    SENSITIVE = "sensitive"


class Pretty(StrEnum):
    """Whether results are drawn in two dimensions as text (fractions, roots, powers)."""

    OFF = "off"
    ON = "on"


class Ascii(StrEnum):
    """Whether results use keyboard characters (`pi`, `sqrt(2)`), so they can be copied."""

    OFF = "off"
    ON = "on"


class Logic(StrEnum):
    """How a result joins conditions: the words `and`, `or` (as the handheld) or `∧`, `∨`."""

    WORDS = "words"
    SYMBOLS = "symbols"


@dataclass(frozen=True, slots=True)
class Settings:
    """Document settings. `digits` is `floatN` or `fixN`, as in the corpus."""

    angle: Angle = Angle.RADIAN
    calc: Calc = Calc.AUTO
    domain: Domain = Domain.REAL
    digits: str = "float8"
    cas_mode: CasMode = CasMode.ON
    exp_format: str = "normal"
    case: Case = Case.INSENSITIVE
    pretty: Pretty = Pretty.OFF
    ascii: Ascii = Ascii.OFF
    logic: Logic = Logic.WORDS


PRESETS = {
    "none": Settings(),
    "general": Settings(angle=Angle.DEGREE, calc=Calc.APPROXIMATE),
    "methods": Settings(),
    "specialist": Settings(domain=Domain.RECTANGULAR),
}


# What a click on the title-bar status cycles through; Grad and Exact stay in the settings dialog.
_CYCLES: dict[str, tuple[str, ...]] = {
    "angle": (Angle.RADIAN, Angle.DEGREE),
    "calc": (Calc.AUTO, Calc.APPROXIMATE),
    "domain": (Domain.REAL, Domain.RECTANGULAR, Domain.POLAR),
}


def next_choice(settings: Settings, name: str) -> str:
    """The value a click on `name` (angle, calc or domain) switches to; others go to the first."""
    cycle = _CYCLES[name]
    current = getattr(settings, name)
    return cycle[(cycle.index(current) + 1) % len(cycle)] if current in cycle else cycle[0]


def updated(settings: Settings, changes: dict[str, str]) -> Settings:
    """Apply changes spelled as in the corpus `settings` block."""
    return Settings(
        angle=Angle(changes.get("angle", settings.angle)),
        calc=Calc(changes.get("calc", settings.calc)),
        domain=Domain(changes.get("domain", settings.domain)),
        digits=changes.get("digits", settings.digits),
        cas_mode=CasMode(changes.get("cas_mode", settings.cas_mode)),
        exp_format=changes.get("exp_format", settings.exp_format),
        case=Case(changes.get("case", settings.case)),
        pretty=Pretty(changes.get("pretty", settings.pretty)),
        ascii=Ascii(changes.get("ascii", settings.ascii)),
        logic=Logic(changes.get("logic", settings.logic)),
    )


def variable_key(settings: Settings, name: str) -> str:
    """How a variable or user function name is stored: folded unless the case matters.

    The `stat.` results are the calculator's own names, so they are never case sensitive.
    """
    if settings.case is Case.SENSITIVE and not name.casefold().startswith("stat."):
        return name
    return name.casefold()
