"""The corpus as a regression net: reviewed cases must pass, and nothing may crash the engine.

A case is held to its result once its status moves from `pending` to `pass` or `xfail`.
"""

import pytest
from tools.replay import case_settings, load_cases, run_case

CASES = list(load_cases())
REVIEWED = {case["id"]: case for case in CASES if case["status"] != "pending"}


@pytest.mark.corpus
@pytest.mark.parametrize("case_id", REVIEWED)
def test_reviewed_case(request, case_id):
    case = REVIEWED[case_id]
    if case["status"] == "xfail":
        request.applymarker(pytest.mark.xfail(reason=case["xfail_reason"], strict=True))
    outcome = run_case(case)
    assert outcome.passed, outcome.reason


@pytest.mark.corpus
def test_no_case_crashes_the_engine():
    crashes = [o for o in map(run_case, CASES) if o.crashed]
    assert not crashes, crashes


def test_every_case_has_valid_settings():
    for case in CASES:
        case_settings(case)
