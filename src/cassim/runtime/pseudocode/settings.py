"""Run settings (docs/pseudocode/dialect.md section 8; SRS FR-SET-*)."""

from dataclasses import dataclass, replace
from typing import Literal

type NumberMode = Literal["approx", "auto", "exact"]
type AngleMode = Literal["radian", "degree"]


@dataclass(frozen=True, slots=True)
class Settings:
    number: NumberMode = "approx"
    angle: AngleMode = "radian"
    display: int | Literal["full"] = 6  # significant digits, or full precision
    complex_domain: bool = False  # Real by default
    euler_e: bool = False  # an unassigned `e` is Euler's number (FR-SET-008)
    index_base: int = 1
    seed: int | None = None
    max_iterations: int = 10_000  # loop passes across all loops (FR-SET-009)
    max_depth: int = 100  # recursion depth
    max_events: int = 200_000  # recorded steps; the cap is reported, not silent


def updated(base: Settings, changes: dict[str, object]) -> Settings:
    """`base` with the entries of `changes` applied (the corpus `settings:` blocks)."""
    return replace(base, **changes)  # type: ignore[arg-type]
