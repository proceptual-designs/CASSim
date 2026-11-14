# Requirements traced here: FR-DEV-005
"""The accent key (in the place of the handheld's flag key) cycles the letter before the cursor
through its accented forms, taken from Unicode's canonical decompositions."""

import unicodedata

from hypothesis import given
from hypothesis import strategies as st

from cassim.device.accents import accent_forms, next_accent
from cassim.device.editor import Editor
from cassim.devices.nspire.pages.calculator import calculator_of
from cassim.devices.nspire.ui.state import AppState


def test_a_letter_steps_through_its_forms_and_back():
    forms = accent_forms("e")
    assert forms[0] == "e"
    assert {"è", "é", "ê", "ë", "ệ"} <= set(forms)
    letter = "e"
    seen = []
    for _ in forms:
        letter = next_accent(letter) or ""
        seen.append(letter)
    assert seen[-1] == "e"  # round to the plain letter
    assert len(set(seen)) == len(forms)


def test_one_accent_comes_before_two():
    forms = accent_forms("e")
    marks = [len(unicodedata.normalize("NFD", form)) for form in forms]
    assert marks == sorted(marks)
    assert forms.index("é") < forms.index("ệ")


def test_capitals_have_their_own_forms():
    assert next_accent("E") == "È"
    assert all(form.isupper() for form in accent_forms("E"))


def test_an_accented_letter_carries_on_from_where_it_is():
    forms = accent_forms("a")
    middle = forms[3]
    assert next_accent(middle) == forms[4]


def test_characters_without_forms_are_left_alone():
    for char in ("1", "+", "π", "", "ab", "ⅇ"):
        assert next_accent(char) is None


@given(st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"))
def test_every_form_decomposes_to_its_letter(letter: str):
    for form in accent_forms(letter):
        assert unicodedata.normalize("NFD", form)[0] == letter


def test_the_editor_changes_only_the_letter_before_the_cursor():
    editor = Editor("2e")
    editor.cycle_accent()
    assert editor.linear() == "2è"
    editor.left()
    editor.cycle_accent()  # a digit: no change
    assert editor.linear() == "2è"
    editor.home()
    editor.cycle_accent()  # nothing before the cursor
    assert editor.linear() == "2è"


def test_the_key_on_the_calculator_and_in_a_sheet_cell():
    state = AppState()
    state.press_keypad("e")
    state.press_keypad("accent")
    state.press_keypad("accent")
    calculator = calculator_of(state.document.current)
    assert calculator is not None
    assert calculator.editor.linear() == "é"
    state.run_action("add_page", "spreadsheet")
    state.press_keypad("a")
    state.press_keypad("accent")
    sheet = state.sheet
    assert sheet is not None
    assert sheet.editing == "à"
