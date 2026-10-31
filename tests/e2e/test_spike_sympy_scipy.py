"""Spike 1: SymPy + SciPy run inside the Flet static build (decision 0002)."""

import pytest
from tools import webharness

pytestmark = pytest.mark.e2e


def test_sympy_and_scipy_run_in_browser(browser, build) -> None:
    dist = build("spike1_web")
    with webharness.serve(dist) as url:
        run = webharness.visit(browser.new_context(), url)
    assert run.finished, run.lines[-10:]
    assert "-2, 2" in run.find("solve x^2-4")
    assert run.find("import sympy").endswith("1.14.0")
    assert "x/2 - sin(x)*cos(x)/2" in run.find("integrate")
    assert "0.975" in run.find("norm.cdf")
    assert run.seconds < 120, f"cold start too slow: {run.seconds:.0f}s"


def test_python_runs_in_a_worker(browser, build) -> None:
    dist = build("spike1_web")
    with webharness.serve(dist) as url:
        run = webharness.visit(browser.new_context(), url)
    assert any("Starting up Python worker" in x for x in run.lines)
