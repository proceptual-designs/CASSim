"""The About dialog's content and its menu entry (NFR-LEG-002, NFR-LEG-003, NFR-SEC-001)."""

from __future__ import annotations

import tomllib

import sympy
from tools import publish

from cassim.app import about
from cassim.devices.nspire.ui.state import AppState


def test_disclaimer_says_what_nfr_leg_002_requires() -> None:
    """NFR-LEG-002 and NFR-LEG-005: not affiliated with or endorsed by any company (TI, Casio, HP
    included); not an approved exam calculator."""
    text = about.DISCLAIMER
    assert text.startswith(
        "CASSim is a simulator of handheld Computer Algebra Systems (CAS), made for educational "
        "purposes."
    )
    assert "not affiliated with, endorsed by or sponsored by any company" in text
    assert "curriculum authority" in text
    assert "not an approved exam calculator" in text


def test_privacy_and_licence_statements() -> None:
    """NFR-SEC-001: no telemetry. NFR-LEG-003: the Unlicense."""
    assert "no telemetry" in about.PRIVACY
    assert "vibe-coded" in about.LICENCE
    assert "Unlicense" in about.LICENCE


def test_every_version_is_known() -> None:
    """The About box names a real version for CASSim, Python, Flet, SymPy and mpmath, and CASSim's
    and SymPy's are the ones this checkout uses."""
    shown = dict(about.versions())
    assert list(shown) == ["CASSim", "Python", "Flet", "SymPy", "mpmath"]
    assert about.UNKNOWN not in shown.values(), shown
    pyproject = tomllib.loads((publish.ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert shown["CASSim"] == pyproject["project"]["version"]
    assert shown["SymPy"] == sympy.__version__


def test_a_build_shows_the_versions_it_ships() -> None:
    """In the browser the versions come from the build's `bundle.VERSIONS`, which `tools.publish`
    takes from pyproject.toml and Pyodide's lock file."""
    lock = {"packages": {"sympy": {"version": "1.14.0"}, "mpmath": {"version": "1.4.1"}}}
    shipped = publish.shipped_versions(lock, "0.29.0", publish.bundles()["all"])
    assert shipped == {
        "CASSim": publish.project_version(),
        "Pyodide": "0.29.0",
        "Flet": publish.flet_version(),
        "SymPy": "1.14.0",
        "mpmath": "1.4.1",
    }
    shown = dict(about.versions(shipped))
    assert list(shown) == ["CASSim", "Python", "Pyodide", "Flet", "SymPy", "mpmath"]
    assert (shown["SymPy"], shown["Pyodide"]) == ("1.14.0", "0.29.0")


def test_notices_cover_the_shipped_third_party_parts() -> None:
    """NFR-LEG-003: Flet, Pyodide, SymPy, SciPy and the vendored font are named with a licence."""
    names = {notice.name for notice in about.NOTICES}
    assert {"Flet", "Pyodide", "SymPy", "SciPy", "Noto Sans, Math, Symbols 2 and SC"} <= names
    assert all(notice.licence for notice in about.NOTICES)


def test_versions_include_cassim_and_python() -> None:
    names = [name for name, _ in about.versions()]
    assert names[:2] == ["CASSim", "Python"]
    assert "CASSim " in about.build_info()
    assert "SymPy " in about.build_info()


def test_about_is_in_the_doc_menu() -> None:
    """Doc > 8 About CASSim asks for the about dialog."""
    state = AppState()
    asked: list[str] = []
    state.show_dialog = asked.append
    for key in ("F4", "8"):
        state.key_event(key)
    assert asked == ["about"]


def test_help_menu_item_opens_the_wiki() -> None:
    """Doc > 9 Help asks for the help dialog, which opens the wiki."""
    assert about.WIKI_URL == "https://cassim-wiki.pages.dev/"
    state = AppState()
    asked: list[str] = []
    state.show_dialog = asked.append
    for key in ("F4", "9"):
        state.key_event(key)
    assert asked == ["help"]
