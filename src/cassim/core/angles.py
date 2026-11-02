"""Conversions between the document's angle unit and radians."""

from cassim.core.compat import sympy_adapter as cas
from cassim.core.settings import Angle
from cassim.core.values import Raw

# How many of each unit make a half turn.
_HALF_TURN = {Angle.DEGREE: 180, Angle.GRADIAN: 200}


def to_radians(raw: Raw, unit: Angle) -> Raw:
    half_turn = _HALF_TURN.get(unit)
    return raw if half_turn is None else raw * cas.pi / half_turn


def from_radians(raw: Raw, unit: Angle) -> Raw:
    half_turn = _HALF_TURN.get(unit)
    return raw if half_turn is None else raw * half_turn / cas.pi


def convert(raw: Raw, unit: Angle, target: Angle) -> Raw:
    """Convert an angle typed in `unit` to `target`."""
    return raw if unit == target else from_radians(to_radians(raw, unit), target)
