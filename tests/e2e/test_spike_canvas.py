"""Spike 3: Flet canvas drawing speed (decision 0004)."""

import re

import pytest
from tools import webharness

pytestmark = pytest.mark.e2e


def _fps(line: str) -> float:
    match = re.search(r"fps=([\d.]+)", line)
    assert match, line
    return float(match.group(1))


def test_points_polygon_is_fast_and_per_segment_lines_are_not(browser, build) -> None:
    dist = build("spike3_web")
    with webharness.serve(dist) as url:
        run = webharness.visit(browser.new_context(), url, timeout=240)
    assert run.finished, run.markers()
    points = _fps(run.find("RESULT points pan"))
    lines = _fps(run.find("RESULT lines pan"))
    # Loose bounds, far from the measured 120 fps and 1 fps, so CI noise cannot trip them.
    assert points > 30, run.markers()
    assert lines < 5, run.markers()
    assert points > 10 * lines
