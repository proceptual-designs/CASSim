"""Spike 4: engine in a second Pyodide worker, cancelled by terminate (decision 0005)."""

import re

import pytest
from tools import webharness

pytestmark = pytest.mark.e2e


def test_engine_worker_cancel_and_restart(browser, build) -> None:
    dist = build("spike4_web")
    with webharness.serve(dist) as url:
        run = webharness.visit(browser.new_context(), url, timeout=360)  # slow on a loaded machine
    assert run.finished, run.markers()
    assert "[-2, 2]" in run.find("B solve1")
    alive = run.find("B flet_loop_alive_during_hang")
    match = re.search(r"ticks=(\d+)", alive)
    assert match, alive
    ticks = int(match.group(1))
    assert ticks > 20, alive  # Flet's own loop kept running while the engine was stuck
    assert "hang_done=False" in alive
    assert "hang_cancelled=True" in run.find("B terminate")
    assert "[-3, 3]" in run.find("B solve2")  # a fresh worker works after the cancel
