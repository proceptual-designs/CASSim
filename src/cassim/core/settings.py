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


PRESETS = {
    "none": Settings(),
    "general": Settings(angle=Angle.DEGREE, calc=Calc.APPROXIMATE),
    "methods": Settings(),
    "specialist": Settings(domain=Domain.RECTANGULAR),
}


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
    )


def variable_key(settings: Settings, name: str) -> str:
    """How a variable or user function name is stored: folded unless the case matters.

    The `stat.` results are the calculator's own names, so they are never case sensitive.
    """
    if settings.case is Case.SENSITIVE and not name.casefold().startswith("stat."):
        return name
    return name.casefold()
