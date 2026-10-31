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


@dataclass(frozen=True, slots=True)
class Settings:
    """Document settings. `digits` is `floatN` or `fixN`, as in the corpus."""

    angle: Angle = Angle.RADIAN
    calc: Calc = Calc.AUTO
    domain: Domain = Domain.REAL
    digits: str = "float8"
    cas_mode: CasMode = CasMode.ON


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
    )
