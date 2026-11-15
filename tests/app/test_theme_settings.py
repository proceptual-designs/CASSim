# Requirements traced here: FR-THEME-001, FR-THEME-002, NFR-USE-003
"""Theme presets, editable colours, persistence and keypad contrast."""

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import patch

import flet as ft
import flet.canvas as cv
import pytest
from tests.app.test_keypad_shapes import keys_named
from tests.app.test_splitter_drag import handheld_app

from cassim.app.theme import THEMES, contrast, theme_colours, themed
from cassim.devices.nspire.ui.keypad import Keypad
from cassim.devices.nspire.ui.state import AppState, System
from cassim.devices.nspire.ui.theme_settings import theme_settings_dialog


class DialogPage(SimpleNamespace):
    def __init__(self) -> None:
        super().__init__(height=700, dialogs=[])

    def show_dialog(self, dialog: ft.AlertDialog) -> None:
        self.dialogs.append(dialog)

    def pop_dialog(self) -> None:
        self.dialogs.pop()

    def update(self) -> None:
        pass


def test_dark_is_the_default_theme():
    assert System().theme_name == "Dark"


def fields(dialog: ft.AlertDialog) -> dict[str, Any]:
    return {
        row.controls[0].label: row.controls[0]
        for row in dialog.content.controls[3:]  # ty: ignore[unresolved-attribute]
    }


def action(dialog: ft.AlertDialog, index: int) -> None:
    button = cast("Any", dialog.actions[index])
    button.on_click(None)


def test_edits_are_kept_separately_and_round_trip():
    page = DialogPage()
    system = System()
    changes: list[str] = []
    dialog = theme_settings_dialog(cast("ft.Page", page), system, lambda: changes.append("saved"))
    choice = dialog.content.controls[1]  # ty: ignore[unresolved-attribute]
    boxes = fields(dialog)
    boxes["Key Outline"].value = "#112233"
    choice.value = "Light"
    choice.on_select(None)
    boxes["Key Outline"].value = "#445566"
    action(dialog, -1)
    assert changes == ["saved"]
    assert system.theme_name == "Light"
    assert system.theme_overrides["Dark"]["key_outline"] == "#112233"
    assert system.theme_overrides["Light"]["key_outline"] == "#445566"
    assert System.loads(system.dumps()) == system
    assert themed("Dark", system.theme_overrides["Dark"]).key_outline == "#112233"


def test_invalid_colour_is_reported_and_cannot_be_saved():
    page = DialogPage()
    system = System()
    dialog = theme_settings_dialog(cast("ft.Page", page), system, lambda: None)
    boxes = fields(dialog)
    boxes["Key Outline"].value = "not a colour"
    action(dialog, -1)
    assert boxes["Key Outline"].error == "Use #RRGGBB"
    assert page.dialogs == [dialog]
    assert system.theme_overrides == {}


def test_swatch_chooses_a_colour_without_typing():
    page = DialogPage()
    system = System()
    dialog = theme_settings_dialog(cast("ft.Page", page), system, lambda: None)
    row = next(
        row
        for row in dialog.content.controls[3:]  # ty: ignore[unresolved-attribute]
        if row.controls[0].label == "Key Outline"
    )
    row.controls[1].on_click(None)
    palette = page.dialogs[-1]
    palette.content.controls[0].on_click(None)
    assert fields(dialog)["Key Outline"].value == "#000000"
    assert page.dialogs == [dialog]
    action(dialog, -1)
    assert system.theme_overrides["Dark"]["key_outline"] == "#000000"


def test_reset_affects_only_selected_preset_and_cancel_does_not_save():
    system = System(
        theme_overrides={
            "Dark": {"key_outline": "#112233"},
            "Light": {"key_outline": "#445566"},
        }
    )
    page = DialogPage()
    dialog = theme_settings_dialog(cast("ft.Page", page), system, lambda: None)
    action(dialog, 0)
    assert fields(dialog)["Key Outline"].value == theme_colours(THEMES["Dark"])["key_outline"]
    action(dialog, 1)
    assert system.theme_overrides["Dark"]["key_outline"] == "#112233"
    dialog = theme_settings_dialog(cast("ft.Page", page), system, lambda: None)
    action(dialog, 0)
    action(dialog, -1)
    assert "Dark" not in system.theme_overrides
    assert system.theme_overrides["Light"]["key_outline"] == "#445566"


def test_bad_saved_theme_falls_back_with_an_error():
    saved = System().dumps().replace('"theme_name": "Dark"', '"theme_name": "unknown"')
    system = System.loads(saved)
    assert system.theme_name == "Dark"
    assert system.theme_error
    assert "theme_error" not in system.dumps()


def test_theme_changes_rebuild_all_views_even_when_only_a_key_style_changes():
    app, _page = handheld_app()
    old_view = app.view
    app.state.system.theme_overrides = {"Dark": {"digit.fill": "#333333"}}
    app.apply_theme()
    assert app.view is not old_view
    assert app.view.theme.key_styles["digit"][0] == "#333333"
    assert app.keypad.theme == app.sidebar.theme == app.shell.theme == app.view.theme


def test_app_applies_and_saves_the_new_theme_without_replacing_the_document():
    app, page = handheld_app()
    document = app.state.document
    app.state.system.theme_name = "Light"
    app.state.system.theme_overrides = {"Light": {"background": "#e7e8e9"}}
    with patch.object(app.shell, "write") as write, patch.object(app, "refresh"):
        app.on_system_change()
    key, saved = write.call_args.args
    assert key == "system"
    assert System.loads(saved).theme_overrides["Light"]["background"] == "#e7e8e9"
    assert page.bgcolor == "#e7e8e9"
    assert page.theme_mode == ft.ThemeMode.LIGHT
    assert app.view.theme == app.keypad.theme == app.shell.theme
    assert app.state.document is document


@pytest.mark.parametrize("modifier", ["ctrl", "shift"])
def test_active_modifier_has_a_non_colour_indicator(modifier: str):
    state = AppState()
    state.press_keypad(modifier)
    keypad = Keypad(state, lambda _: None)
    ((_, control),) = keys_named(keypad, modifier)
    assert control.content.controls[-1].value == f"{modifier} •"


@pytest.mark.parametrize("name", list(THEMES))
@pytest.mark.parametrize("pending", ["", "ctrl", "shift"])
@pytest.mark.parametrize("layout", ["ABC", "QWERTY"])
def test_keypad_text_and_secondary_legends_have_aa_contrast(name: str, pending: str, layout: str):
    state = AppState()
    state.system.letters = layout
    if pending:
        state.press_keypad(pending)
    theme = THEMES[name]
    keypad = Keypad(state, lambda _: None, theme)
    for row in state.keypad:
        for key in row:
            if not key.name or key.join:
                continue
            ((_, control),) = keys_named(keypad, key.name)
            for part in control.content.controls:
                children = part.controls if isinstance(part, ft.Row) else [part]
                for child in children:
                    if isinstance(child, ft.Text) and (child.value or child.spans):
                        assert contrast(child.color, control.bgcolor) >= 4.5, (
                            name,
                            pending,
                            key.name,
                        )
                    elif isinstance(child, cv.Canvas):
                        assert contrast(child.shapes[0].paint.color, control.bgcolor) >= 3, (
                            name,
                            pending,
                            key.name,
                        )


@pytest.mark.parametrize("name", list(THEMES))
def test_green_and_orange_outlines_contrast_with_their_keys_and_background(name: str):
    theme = THEMES[name]
    for colour, fill in (
        (theme.key_outline, theme.key_colours("alpha")[0]),
        (theme.key_outline, theme.key_colours("enter")[0]),
        (theme.shift_outline, theme.key_colours("nav")[0]),
    ):
        assert contrast(colour, fill) >= 3
        assert contrast(colour, theme.background) >= 3


@pytest.mark.parametrize("name", list(THEMES))
def test_theme_panel_and_menu_text_contrasts(name: str):
    theme = THEMES[name]
    for colour in (theme.panel_text, theme.panel_accent, theme.status_text):
        assert contrast(colour, theme.background) >= 4.5
    for colour in (theme.key_text, theme.key_label, theme.menu_accent, theme.menu_hint):
        assert contrast(colour, theme.title_bar) >= 4.5
    assert contrast(theme.title_text, theme.title_bar) >= 4.5
    assert contrast(theme.accent_text, theme.accent) >= 4.5
    assert contrast(theme.sheet_grid, theme.screen) >= 3
    assert contrast(theme.sheet_axis, theme.sheet_header) >= 4.5
