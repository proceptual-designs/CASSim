# Requirements traced here: FR-DOC-003
"""The autosave waits for a pause in typing, then writes once (decision 0031)."""

import json
import time
from typing import Any

import pytest
from tests.app.test_splitter_drag import handheld_app

from cassim.device.keys import Binding
from cassim.devices.nspire.ui import app as nspire_app


def writes(app: Any, monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    monkeypatch.setattr(app.shell, "write", lambda key, text: found.append((key, text)))
    return found


def test_changes_close_together_are_saved_once(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(nspire_app, "AUTOSAVE_DELAY", 0.01)
    app, page = handheld_app()
    saved = writes(app, monkeypatch)
    app.state.run(Binding("insert", "1"))
    app.autosave()
    app.state.run(Binding("insert", "2"))
    app.autosave()
    assert len(page.tasks) == 1  # one waiting save, pushed back by the second change
    assert saved == []
    page.run_queued()
    assert len(saved) == 1
    assert saved[0][0] == "autosave"
    assert json.loads(saved[0][1])["problems"][0]["pages"][0]["entry"] == ["1", "2"]  # both keys


def test_nothing_is_written_when_nothing_changed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(nspire_app, "AUTOSAVE_DELAY", 0.0)
    app, page = handheld_app()
    saved = writes(app, monkeypatch)
    app.autosave()
    page.run_queued()
    app.autosave()
    page.run_queued()
    assert len(saved) == 1


def test_the_save_waits_for_the_last_change(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(nspire_app, "AUTOSAVE_DELAY", 0.05)
    app, page = handheld_app()
    writes(app, monkeypatch)
    start = time.monotonic()
    app.autosave()
    page.run_queued()
    assert time.monotonic() - start >= 0.05
    assert not app.save_waiting
