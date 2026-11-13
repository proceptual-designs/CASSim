"""The screen buffer (FR-DEV-001)."""

from cassim.device.calculator import calculator_of
from cassim.device.keys import Binding, Keyboard, keypad_units
from cassim.device.screen import render
from cassim.devices.nspire.document import Document, PageKind
from cassim.profiles import nspire


def test_screen_shows_history_entry_and_status() -> None:
    document = Document()
    page = calculator_of(document.current)
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
    page = calculator_of(document.current)
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
    """Every keypad key is a gap, a modifier, has a binding, or types its own character; every
    ctrl or shift label drawn on a key does something (FR-DEV-005)."""
    keyboard = Keyboard(nspire.HANDHELD, nspire.MODIFIERS)
    for row in (row for keypad in nspire.KEYPADS.values() for row in keypad):
        for key in row:
            if not key.name or key.name in nspire.MODIFIERS:
                continue
            assert keyboard.press(key.name) is not None, key.name
            for layer, label in (("ctrl", key.ctrl), ("shift", key.shift)):
                if label:
                    assert f"{layer}+{key.name}" in nspire.HANDHELD, (layer, key.name)


def test_keypad_rows_are_equally_wide() -> None:
    for keypad in nspire.KEYPADS.values():
        assert {round(sum(key.width for key in row), 6) for row in keypad} == {5.0}
    assert keypad_units(nspire.KEYPAD)[0] == 5.0


def test_both_letter_layouts_have_every_letter_once() -> None:
    for keypad in nspire.KEYPADS.values():
        names = [key.name for row in keypad for key in row if key.name]
        assert sorted(name for name in names if len(name) == 1 and name.isalpha()) == list(
            "abcdefghijklmnopqrstuvwxyz"
        )
        assert len(names) == len(set(names))
