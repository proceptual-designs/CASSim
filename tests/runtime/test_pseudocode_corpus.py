"""Replay corpus/pseudocode/seed.yaml against the tree interpreter (M7b; FR-PSE-*, FR-SET-*).

Every case runs with display=full, Approx, Radian and the Euler toggle on (case q3 writes `2e^x`)
unless the case says otherwise. Comparison modes are those named in the file header.
"""

import math
import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from cassim.runtime.pseudocode import RunResult, Settings, run

SEED = Path(__file__).parents[2] / "corpus" / "pseudocode" / "seed.yaml"
CASES: list[dict[str, Any]] = yaml.safe_load(SEED.read_text(encoding="utf-8"))["cases"]
ALL = pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])

# The corpus marks these as not desk-checkable although each has exactly one un-nested loop;
# the rule in docs/pseudocode/trace-tables.md section 3 says they qualify. Awaiting Simon's call.
ELIGIBILITY_DISAGREES = {
    "book.u1.linear-search.x4-10x-2": "101 passes",
    "vcaa.2024.nov.mm2.q17.integer-roots": "18 passes with two ifs per pass",
}


def settings_for(case: dict[str, Any], extra: dict[str, Any] | None = None) -> Settings:
    changes: dict[str, Any] = {"display": "full", "euler_e": True, **case.get("settings", {})}
    changes.update(extra or {})
    return Settings(**changes)


def as_number(token: str) -> float | None:
    try:
        return float(token.replace("ᴇ", "e"))
    except ValueError:
        return None


def tolerance(compare: str) -> float:
    m = re.fullmatch(r"numeric\(([^)]+)\)|tokens-numeric\(([^)]+)\)", compare)
    return float(m.group(1) or m.group(2)) if m else 1e-9


def lines_match(got: str, want: str, compare: str, *, noise: bool) -> bool:
    if compare == "exact":
        return got == want
    tol = max(tolerance(compare), 1e-9 if noise else 0.0)
    g, w = got.split(), want.split()
    if len(g) != len(w):
        return False
    for a, b in zip(g, w, strict=True):
        x, y = as_number(a), as_number(b)
        if x is None or y is None:
            if a != b:
                return False
        elif not math.isclose(x, y, rel_tol=tol, abs_tol=tol):
            return False
    return True


def check(result: RunResult, expect: dict[str, Any]) -> None:
    compare = expect.get("compare", "numeric")
    noise = bool(expect.get("float_noise"))
    if "halt" in expect:
        assert result.halt == expect["halt"], result.error
    else:
        assert result.halt == "finished", result.error
    if "output" in expect:
        assert len(result.output) == len(expect["output"]), result.output
        for got, want in zip(result.output, expect["output"], strict=True):
            assert lines_match(got, want, compare, noise=noise), (got, want)
    if "output_count" in expect:
        assert len(result.output) == expect["output_count"]
    for nth, want in expect.get("output_nth", {}).items():
        assert lines_match(result.output[nth - 1], want, compare, noise=noise), (nth, want)


@ALL
def test_golden_output(case: dict[str, Any]) -> None:
    """FR-PSE-001 to -007: the program's printed output matches the reference Python."""
    if "expect" not in case or not case["expect"]:
        pytest.skip("expectations are in expect_by_settings")
    result = run(case["pseudocode"], settings_for(case), case.get("inputs", []))
    check(result, case["expect"])


BY_SETTINGS = [
    pytest.param(c, v, id=f"{c['id']}[{i}]")
    for c in CASES
    for i, v in enumerate(c.get("expect_by_settings", []))
]


@pytest.mark.parametrize(("case", "variant"), BY_SETTINGS)
def test_golden_output_by_settings(case: dict[str, Any], variant: dict[str, Any]) -> None:
    """FR-SET-001 to -006: number mode, angle and display precision change the printed values."""
    result = run(
        case["pseudocode"], settings_for(case, variant["settings"]), case.get("inputs", [])
    )
    check(result, variant)


@ALL
def test_horizontal_eligibility(case: dict[str, Any]) -> None:
    """FR-TRC-003: one un-nested loop makes the desk-check layout available."""
    if "trace" not in case:
        pytest.skip("no trace expectation")
    if case["id"] in ELIGIBILITY_DISAGREES:
        pytest.xfail(f"corpus flag disagrees with the rule: {ELIGIBILITY_DISAGREES[case['id']]}")
    result = run(case["pseudocode"], settings_for(case), case.get("inputs", []))
    assert result.horizontal_eligible == case["trace"]["horizontal_eligible"]


@ALL
def test_loop_iterations(case: dict[str, Any]) -> None:
    """FR-TRC-001: the recorded passes match the corpus count (body passes, all loops)."""
    iterations = case.get("trace", {}).get("loop_iterations")
    if iterations is None or case.get("expect", {}).get("halt"):
        pytest.skip("no iteration count")
    result = run(case["pseudocode"], settings_for(case), case.get("inputs", []))
    assert result.loop_body_runs == iterations
