# Requirements traced here: FR-DOC-003
"""Autosave in the built site: kept in IndexedDB after a pause, and an older build's copy in
localStorage is still found (decision 0031)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from playwright.sync_api import Browser
from test_flows_browser import AppPage

from cassim.device.keys import Binding
from cassim.devices.nspire.document import Document
from cassim.devices.nspire.pages.calculator import calculator_on
from cassim.doc.serialize import dumps

pytestmark = pytest.mark.e2e


def evaluate(app: AppPage, text: str) -> str:
    before = len(app.results)
    app.type_text(text)
    app.press("Enter")
    app.wait(lambda: len(app.results) > before, f"the result of {text!r}")
    return app.results[-1]


def reopen(app: AppPage, url: str) -> None:
    app.logs.clear()
    app.page.goto("about:blank")
    app.page.goto(url + "#/debug", wait_until="load")
    app.wait(lambda: "CASSIM: READY" in app.logs, "READY")
    app.page.mouse.click(600, 150)


def test_the_document_comes_back_after_a_reload(browser: Browser, site: tuple[Path, str]) -> None:
    url = site[1]
    context = browser.new_context(viewport={"width": 1100, "height": 700})
    app = AppPage(context.new_page(), url)
    assert evaluate(app, "a:=7") == "7"
    app.page.wait_for_timeout(1500)  # past the autosave delay
    stored = app.page.evaluate(
        "() => Object.keys(localStorage).filter(k => k.includes('autosave'))"
    )
    assert stored == []  # the document is in IndexedDB, not localStorage
    reopen(app, url)
    assert any("RECOVERED 1 pages" in line for line in app.logs), app.logs
    assert evaluate(app, "a+1") == "8"  # the variable was rebuilt by replaying the entry
    context.close()


def test_an_autosave_left_in_local_storage_is_still_opened(
    browser: Browser, site: tuple[Path, str]
) -> None:
    """A document autosaved by a build before IndexedDB is not lost."""
    url = site[1]
    document = Document()
    calculator = calculator_on(document.current)
    for char in "b:=5":
        calculator.perform(Binding("insert", char))
    calculator.perform(Binding("enter"))
    document.add_page()
    context = browser.new_context(viewport={"width": 1100, "height": 700})
    # shared_preferences on the web keeps `flutter.<key>` holding the JSON-encoded value.
    value = json.dumps(json.dumps(dumps(document)))
    context.add_init_script(f"localStorage.setItem('flutter.cassim.autosave', {value});")
    app = AppPage(context.new_page(), url)
    assert any("RECOVERED 2 pages" in line for line in app.logs), app.logs
    context.close()
