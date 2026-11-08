"""The exam-style flows, run key by key through the app's own state (M2 exit criterion).

`corpus/flows/exam.yaml` is the script; `tools/flows.py` plays it. The same flows marked
`browser: true` run in the built site in `tests/e2e/test_flows_browser.py`.
"""

import pytest
from tools.flows import Outcome, load_flows, matches, parse_keys, run_flow, split_text

from cassim.core.settings import Settings

FLOWS = {flow["id"]: flow for flow in load_flows()}


@pytest.mark.parametrize("flow_id", FLOWS)
def test_flow(flow_id: str) -> None:
    outcome = run_flow(FLOWS[flow_id])
    assert outcome.passed, outcome.reason


def test_the_flows_cover_every_course() -> None:
    assert {flow["course"] for flow in FLOWS.values()} >= {"methods", "specialist", "general"}


def test_a_wrong_expectation_fails() -> None:
    """The player is not waving everything through."""
    flow = {"id": "x", "course": "methods", "steps": [{"type": "2+2", "expect": "5"}]}
    assert run_flow(flow) == Outcome("x", False, "2+2: got 4, expected 5")


def test_an_expected_error_is_checked() -> None:
    flow = {"id": "x", "course": "methods", "steps": [{"type": "1+", "error": True}]}
    assert run_flow(flow).passed


def test_matches_reads_both_sides_as_maths() -> None:
    settings = Settings()
    assert matches("x=1 or x=3", "x=3 or x=1", settings, "canonical", 1e-7)
    assert matches("0.5", "1/2", settings, "numeric", 1e-7)
    assert not matches("0.5", "0.6", settings, "numeric", 1e-7)
    assert not matches("x=1", "x=2", settings, "canonical", 1e-7)
    assert not matches("1/2", "0.5", settings, "text", 1e-7)


def test_typed_text_and_key_specs() -> None:
    assert split_text("x^2{R}+1") == ["x", "^", "2", "{R}", "+", "1"]
    assert parse_keys("Up ctrl+Enter ctrl+/") == [
        ("Arrow Up", {}),
        ("Enter", {"ctrl": True}),
        ("/", {"ctrl": True}),
    ]


def test_flows_marked_for_the_browser_only_use_what_it_can_do() -> None:
    for flow in FLOWS.values():
        if not flow.get("browser"):
            continue
        assert flow["course"] == "methods", flow["id"]  # the site starts with the Methods defaults
        for step in flow["steps"]:
            assert not {"keypad", "action", "settings", "variable"} & step.keys(), flow["id"]
