# Requirements traced here: FID-1, FID-3, FID-4
"""The corpus as a regression net: reviewed cases must pass, and nothing may crash the engine.

A case is held to its result once its status moves from `pending` to `pass` or `xfail`.
"""

import re
from functools import cache

import pytest
from tools.replay import Outcome, case_settings, load_cases, run_case

CASES = list(load_cases())
# SymPy's own spelling, which must never reach a result: roots, relations, logic, powers.
SYMPY_TEXT = re.compile(r"CRootOf|RootOf|Eq\(|Ne\(|\*\*|\bTrue\b|\bFalse\b|Piecewise|~\(")
REVIEWED = {case["id"]: case for case in CASES if case["status"] != "pending"}


@pytest.mark.corpus
@pytest.mark.parametrize("case_id", REVIEWED)
def test_reviewed_case(request, case_id):
    case = REVIEWED[case_id]
    if case["status"] == "xfail":
        request.applymarker(pytest.mark.xfail(reason=case["xfail_reason"], strict=True))
    outcome = run_case(case)
    assert outcome.passed, outcome.reason


@cache
def _every_outcome() -> tuple[Outcome, ...]:
    return tuple(map(run_case, CASES))


@pytest.mark.corpus
def test_no_case_crashes_the_engine():
    crashes = [o for o in _every_outcome() if o.crashed]
    assert not crashes, crashes


@pytest.mark.corpus
@pytest.mark.xfail(strict=True, reason="SymPy text still leaks (emulator check 6 run 5, plan B1)")
def test_no_sympy_text_in_any_result():
    """Results are TI text: no `CRootOf`, `Eq(`, `**`, `True` or `Piecewise` (plan A)."""
    leaks = [
        (o.case_id, text) for o in _every_outcome() for text in o.texts if SYMPY_TEXT.search(text)
    ]
    assert not leaks, leaks


def test_every_case_has_valid_settings():
    for case in CASES:
        case_settings(case)
