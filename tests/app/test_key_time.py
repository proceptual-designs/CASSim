# Requirements traced here: NFR-PERF-006
"""`#/debug/keytime`: the status line shows what each redraw cost, so typing can be measured on a
Chromebook or a phone with no tools (decision 0035 stage 4)."""

import re

from tests.app.test_splitter_drag import handheld_app


def test_off_by_default() -> None:
    app, _ = handheld_app()
    app.press("1")
    assert app.status.value == ""


def test_each_key_reports_its_build_and_send_time() -> None:
    app, _ = handheld_app()
    app.keytime = True
    app.press("1")
    assert re.fullmatch(r"build \d+ ms, send \d+ ms", app.status.value or "")
