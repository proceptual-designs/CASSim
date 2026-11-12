"""The About dialog's content and its menu entry (NFR-LEG-002, NFR-LEG-003, NFR-SEC-001)."""

from __future__ import annotations

from cassim.app import about
from cassim.app.state import AppState


def test_disclaimer_says_what_nfr_leg_002_requires() -> None:
    """NFR-LEG-002: not affiliated with or endorsed by TI; not an approved exam calculator."""
    text = about.DISCLAIMER
    assert "not affiliated with, endorsed by" in text
    assert "Texas Instruments" in text
    assert "not an approved exam calculator" in text


def test_privacy_and_licence_statements() -> None:
    """NFR-SEC-001: no telemetry. NFR-LEG-003: the Unlicense."""
    assert "no telemetry" in about.PRIVACY
    assert "Unlicense" in about.LICENCE


def test_notices_cover_the_shipped_third_party_parts() -> None:
    """NFR-LEG-003: Flet, Pyodide, SymPy, SciPy and the vendored font are named with a licence."""
    names = {notice.name for notice in about.NOTICES}
    assert {"Flet", "Pyodide", "SymPy", "SciPy", "Noto Sans, Math, Symbols 2 and SC"} <= names
    assert all(notice.licence for notice in about.NOTICES)


def test_versions_include_cassim_and_python() -> None:
    names = [name for name, _ in about.versions()]
    assert names[:2] == ["CASSim", "Python"]
    assert "CASSim " in about.build_info()


def test_about_is_in_settings_and_status_menu() -> None:
    """Menu > Settings & Status > About CASSim asks for the about dialog."""
    state = AppState()
    asked: list[str] = []
    state.show_dialog = asked.append
    for key in ("F4", "7", "7"):
        state.key_event(key)
    assert asked == ["about"]


def test_help_menu_item_opens_the_wiki() -> None:
    """Menu > Settings & Status > Help asks for the help dialog, which opens the wiki."""
    assert about.WIKI_URL == "https://cassim-wiki.pages.dev/"
    state = AppState()
    asked: list[str] = []
    state.show_dialog = asked.append
    for key in ("F4", "7", "8"):
        state.key_event(key)
    assert asked == ["help"]
