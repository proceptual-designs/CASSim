# Requirements traced here: FR-THEME-001, FR-THEME-002, NFR-USE-003
"""The shared theme (SDD-15 section 7): presets, editable colours, one Appearance dialog for
every app, persistence shell-wide, and contrast."""

import asyncio
import json
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import patch

import flet as ft
import flet.canvas as cv
import pytest
from tests.app.test_keypad_shapes import keys_named
from tests.app.test_splitter_drag import handheld_app

from cassim.app.appearance import (
    APPEARANCE_KEY,
    INVALID,
    LEGACY_KEY,
    Appearance,
    AppearanceDialog,
    appearance_dialog,
    load_appearance,
)
from cassim.app.shell import Shell
from cassim.app.theme import DEFAULT_THEME, THEME_NAMES, THEMES, contrast, theme_colours, themed
from cassim.devices.nspire.ui.keypad import Keypad
from cassim.devices.nspire.ui.state import AppState, System


class DialogPage(SimpleNamespace):
    def __init__(self) -> None:
        super().__init__(height=700, width=1000, dialogs=[])

    def show_dialog(self, dialog: ft.AlertDialog) -> None:
        self.dialogs.append(dialog)

    def pop_dialog(self) -> None:
        self.dialogs.pop()

    def update(self) -> None:
        pass


def open_dialog(
    appearance: Appearance | None = None, **options: Any
) -> tuple[AppearanceDialog, DialogPage, list[Appearance]]:
    page = DialogPage()
    saved: list[Appearance] = []
    dialog = appearance_dialog(
        cast("ft.Page", page), appearance or Appearance(), saved.append, **options
    )
    return dialog, page, saved


def click(button: ft.TextButton) -> None:
    cast("Any", button).on_click(None)


def read_from(store: dict[str, str]):
    async def read(key: str) -> str | None:
        return store.get(key)

    return read


def test_dark_is_the_default_theme():
    assert Appearance().theme_name == DEFAULT_THEME == "Dark"
    assert THEME_NAMES == ("Dark", "Light", "High contrast")


def test_edits_are_kept_separately_for_each_preset_and_round_trip():
    dialog, _page, saved = open_dialog()
    dialog.boxes["key_outline"].value = "#112233"
    dialog.select("Light")
    dialog.boxes["key_outline"].value = "#445566"
    click(dialog.save)
    (appearance,) = saved
    assert appearance.theme_name == "Light"
    assert appearance.theme_overrides["Dark"]["key_outline"] == "#112233"
    assert appearance.theme_overrides["Light"]["key_outline"] == "#445566"
    assert Appearance.from_data(json.loads(appearance.dumps())) == appearance
    assert themed("Dark", appearance.theme_overrides["Dark"]).key_outline == "#112233"


def test_the_colours_are_folded_away_until_asked_for():
    dialog, page, _saved = open_dialog()
    assert not dialog.colours.visible
    click(dialog.customise)
    assert dialog.colours.visible
    assert dialog.content.height is not None  # the long list scrolls inside the window
    assert page.dialogs == [dialog.dialog]


def test_invalid_colour_is_reported_and_cannot_be_saved():
    dialog, page, saved = open_dialog()
    dialog.boxes["key_outline"].value = "not a colour"
    click(dialog.save)
    assert dialog.boxes["key_outline"].error == "Use #RRGGBB"
    assert dialog.colours.visible  # the mistake is shown, not left folded away
    assert page.dialogs == [dialog.dialog]
    assert saved == []


def test_swatch_chooses_a_colour_without_typing():
    dialog, page, saved = open_dialog()
    cast("Any", dialog.swatches["key_outline"]).on_click(None)
    palette = page.dialogs[-1]
    palette.content.controls[0].on_click(None)
    assert dialog.boxes["key_outline"].value == "#000000"
    assert page.dialogs == [dialog.dialog]
    click(dialog.save)
    assert saved[0].theme_overrides["Dark"]["key_outline"] == "#000000"


def test_reset_affects_only_the_selected_preset():
    start = Appearance(
        "Dark", {"Dark": {"key_outline": "#112233"}, "Light": {"key_outline": "#445566"}}
    )
    dialog, _page, saved = open_dialog(start)
    click(dialog.reset)
    assert dialog.boxes["key_outline"].value == theme_colours(THEMES["Dark"])["key_outline"]
    click(dialog.save)
    assert "Dark" not in saved[0].theme_overrides
    assert saved[0].theme_overrides["Light"]["key_outline"] == "#445566"


def test_material_button_order():
    """SDD-15 section 9.1: Reset preset at the left; Cancel, then Save, at the right."""
    dialog, _page, _saved = open_dialog()
    left, right = dialog.dialog.actions
    assert left is dialog.reset
    assert isinstance(right, ft.Row)
    assert [b.content for b in right.controls] == ["Cancel", "Save"]  # ty: ignore[unresolved-attribute]
    assert dialog.dialog.actions_alignment == ft.MainAxisAlignment.SPACE_BETWEEN


def test_a_preset_is_previewed_and_cancel_puts_the_saved_one_back():
    seen: list[str] = []
    dialog, page, saved = open_dialog(on_preview=lambda a: seen.append(a.theme_name))
    dialog.select("High contrast")
    dialog.select("Light")
    click(dialog.cancel)
    assert seen == ["High contrast", "Light", "Dark"]
    assert saved == []
    assert page.dialogs == []


def test_cancel_without_a_preview_redraws_nothing():
    seen: list[str] = []
    dialog, _page, _saved = open_dialog(on_preview=lambda a: seen.append(a.theme_name))
    click(dialog.cancel)
    assert seen == []


def test_the_app_can_add_its_own_controls():
    """Scientific adds its calculator model (SDD-15 section 7.3, item 2)."""
    extra = ft.Dropdown(label="Calculator")
    dialog, _page, _saved = open_dialog(extra=[extra])
    assert extra in dialog.content.controls


def test_the_shared_key_wins_and_round_trips():
    store = {
        APPEARANCE_KEY: Appearance(
            "High contrast", {"High contrast": {"accent": "#123456"}}
        ).dumps(),
        LEGACY_KEY: json.dumps({"theme_name": "Light"}),
    }
    loaded = asyncio.run(load_appearance(read_from(store)))
    assert loaded.appearance.theme_name == "High contrast"
    assert loaded.appearance.theme.accent == "#123456"
    assert loaded.saved
    assert loaded.error == ""


def test_a_theme_chosen_before_sdd_15_is_read_from_the_nspire_settings():
    store = {LEGACY_KEY: json.dumps({"theme_name": "Light", "theme_overrides": {}})}
    loaded = asyncio.run(load_appearance(read_from(store)))
    assert loaded.appearance.theme_name == "Light"
    assert loaded.saved
    assert loaded.migrated


def test_a_theme_from_the_nspire_settings_is_saved_under_the_shared_key():
    """The Nspire's settings no longer keep the theme, so the first load must copy it across."""
    store = {LEGACY_KEY: json.dumps({"theme_name": "Light", "theme_overrides": {}})}
    shell = SimpleNamespace(read_global=read_from(store), write_global=store.__setitem__)
    assert asyncio.run(Shell.load_appearance(shell)) == ""  # ty: ignore[invalid-argument-type]
    assert json.loads(store[APPEARANCE_KEY])["theme_name"] == "Light"
    # A later load reads the shared key, even after the Nspire rewrites its own settings.
    store[LEGACY_KEY] = System().dumps()
    again = asyncio.run(load_appearance(read_from(store)))
    assert again.appearance.theme_name == "Light"
    assert not again.migrated


def test_a_theme_already_under_the_shared_key_is_not_written_again():
    store = {APPEARANCE_KEY: Appearance(theme_name="Light").dumps()}
    written: dict[str, str] = {}
    shell = SimpleNamespace(read_global=read_from(store), write_global=written.__setitem__)
    asyncio.run(Shell.load_appearance(shell))  # ty: ignore[invalid-argument-type]
    assert written == {}


@pytest.mark.parametrize(
    "store",
    [{}, {LEGACY_KEY: json.dumps({"start_mode": "computer", "math_size": 20})}],
    ids=["nothing saved", "settings from before themes"],
)
def test_nothing_saved_is_dark_without_a_message(store: dict[str, str]):
    loaded = asyncio.run(load_appearance(read_from(store)))
    assert loaded == (Appearance(), "", False, False)  # nothing saved, nothing to move


@pytest.mark.parametrize(
    "text",
    [
        "not json",
        json.dumps({"theme_name": "unknown"}),
        json.dumps({"theme_name": "Dark", "theme_overrides": {"Dark": {"accent": "red"}}}),
        json.dumps({"theme_name": "Dark", "theme_overrides": {"Dark": {"no_such": "#000000"}}}),
    ],
)
def test_bad_saved_theme_falls_back_to_dark_with_a_message(text: str):
    loaded = asyncio.run(load_appearance(read_from({APPEARANCE_KEY: text})))
    assert loaded.appearance == Appearance()
    assert loaded.error == INVALID


def test_the_nspire_no_longer_keeps_a_theme_of_its_own():
    assert "theme_name" not in json.loads(System().dumps())


def test_theme_changes_rebuild_all_views_even_when_only_a_key_style_changes():
    app, _page = handheld_app()
    old_view = app.view
    app.shell.appearance = Appearance("Dark", {"Dark": {"digit.fill": "#333333"}})
    app.apply_theme()
    assert app.view is not old_view
    assert app.view.theme.key_styles["digit"][0] == "#333333"
    assert app.keypad.theme == app.sidebar.theme == app.shell.theme == app.view.theme


def test_the_nspire_saves_the_theme_shell_wide_without_replacing_the_document():
    app, page = handheld_app()
    document = app.state.document
    shown: list[ft.AlertDialog] = []
    cast("Any", page).show_dialog = shown.append
    with patch.object(app.shell, "write_global") as write, patch.object(app, "refresh"):
        app.open_appearance()
        (dialog,) = shown
        assert app.typing_dialog is dialog  # its colour boxes take the keyboard
        assert cast("ft.Text", dialog.title).value == "Appearance"
        app.shell.save_appearance(Appearance("Light", {"Light": {"background": "#e7e8e9"}}))
        app.on_appearance_change()
    key, saved = write.call_args.args
    assert key == APPEARANCE_KEY
    assert json.loads(saved)["theme_overrides"]["Light"]["background"] == "#e7e8e9"
    assert page.bgcolor == "#e7e8e9"
    assert page.theme_mode == ft.ThemeMode.LIGHT
    assert app.view.theme == app.keypad.theme == app.shell.theme
    assert app.state.document is document


@pytest.mark.parametrize("name", list(THEMES))
def test_shared_status_colours_contrast(name: str):
    """SDD-15 section 7.2: the tokens that replaced literal colours are readable in each
    preset: feedback text on a panel, the attention dot and chip edges against the page."""
    theme = THEMES[name]
    for colour in (theme.success, theme.warning):
        assert contrast(colour, theme.home_card) >= 4.5, colour
    assert contrast(theme.attention, theme.background) >= 3
    assert contrast(theme.chip_edge, theme.background) >= 3
    assert contrast(theme.panel_text, theme.line_highlight) >= 4.5


@pytest.mark.parametrize("name", list(THEMES))
def test_the_tokens_that_replaced_literal_colours_contrast(name: str):
    """SDD-15 gap 17: an error message's text on its colour, a dialog's problem text on a
    panel, and the pointer's arrow against its outline, in each preset."""
    theme = THEMES[name]
    assert contrast(theme.on_error, theme.error) >= 4.5
    assert contrast(theme.on_error_muted, theme.error) >= 3
    assert contrast(theme.problem_text, theme.home_card) >= 4.5
    assert contrast(theme.pointer_fill, theme.pointer_edge) >= 4.5


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
