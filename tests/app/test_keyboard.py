"""Browser key events become key names (FR-DEV-001)."""

import pytest

from cassim.app.keyboard import key_name

# (key, modifiers as letters: s shift, c ctrl, a alt, m meta, expected name)
CASES = [
    ("A", "", "a"),
    ("A", "s", "A"),
    ("6", "s", "^"),
    ("9", "s", "("),
    ("Slash", "", "/"),
    ("Slash", "c", "ctrl+/"),
    ("Z", "c", "ctrl+z"),
    ("Z", "m", "ctrl+z"),
    ("Enter", "c", "ctrl+Enter"),
    ("Enter", "a", "alt+Enter"),
    ("Tab", "s", "shift+Tab"),
    ("Arrow Left", "", "ArrowLeft"),
    ("Space", "c", "ctrl+ "),
    ("Shift Left", "", None),
    ("Escape", "", None),
    ("F5", "", None),
]


@pytest.mark.parametrize(("key", "mods", "name"), CASES)
def test_key_name(key: str, mods: str, name: str | None) -> None:
    got = key_name(key, shift="s" in mods, ctrl="c" in mods, alt="a" in mods, meta="m" in mods)
    assert got == name
