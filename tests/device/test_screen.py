"""The screen buffer (FR-DEV-001)."""

from cassim.device.document import Document, PageKind
from cassim.device.keys import Binding, Keyboard
from cassim.device.screen import render
from cassim.profiles import nspire


def test_screen_shows_history_entry_and_status() -> None:
    document = Document()
    page = document.current.calculator
    assert page is not None
    for char in "1+2":
        page.perform(Binding("insert", char))
    page.perform(Binding("enter"))
    page.perform(Binding("insert", "x"))
    screen = render(document, nspire.status_line(document.settings))
    assert screen.title == "1.1"
    assert screen.status == "RAD AUTO REAL"
    assert [(line.kind, line.text) for line in screen.lines] == [("entry", "1+2"), ("result", "3")]
    assert "x" in screen.entry


def test_recalled_row_is_marked_selected() -> None:
    document = Document()
    page = document.current.calculator
    assert page is not None
    page.perform(Binding("insert", "5"))
    page.perform(Binding("enter"))
    page.perform(Binding("up"))
    assert [line.selected for line in render(document).lines] == [False, True]


def test_page_without_a_model_is_blank() -> None:
    document = Document()
    document.add_page(PageKind.NOTES)
    screen = render(document)
    assert screen.title == "1.2"
    assert screen.lines == ()


def test_keypad_keys_resolve() -> None:
    """Every keypad key is a modifier, has a binding, or types its own character (FR-DEV-005)."""
    keyboard = Keyboard(nspire.HANDHELD, nspire.MODIFIERS)
    for row in nspire.KEYPAD:
        for key in row:
            assert key.name in nspire.MODIFIERS or keyboard.press(key.name) is not None, key.name
