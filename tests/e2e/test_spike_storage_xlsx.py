"""Spikes 4 and 5: IndexedDB persistence and openpyxl inside Pyodide (decision 0003)."""

import pytest
from tools import webharness

pytestmark = pytest.mark.e2e


def test_indexeddb_persists_across_visits(browser, build) -> None:
    dist = build("spike2_web")
    ctx = browser.new_context()
    with webharness.serve(dist) as url:
        first = webharness.visit(ctx, url)
        second = webharness.visit(ctx, url)
    assert "counter=1" in first.find("IDB ok"), first.markers()
    assert "counter=2" in second.find("IDB ok"), second.markers()
    assert "roundtrip_len=2000075" in second.find("IDB ok")


def test_openpyxl_roundtrip(browser, build) -> None:
    dist = build("spike2_web")
    with webharness.serve(dist) as url:
        run = webharness.visit(browser.new_context(), url)
    line = run.find("XLSX ok")
    assert "B6=25" in line
    assert "C2==A2+B2" in line  # formulas survive a save/load cycle
