"""The colour theme every app shares: one choice for the whole of CASSim, saved shell-wide, and
the one Appearance dialog that changes it (SDD-15 section 7; FR-THEME-001, FR-THEME-002)."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from typing import NamedTuple

import flet as ft

from cassim.app.sizes import dialog_width
from cassim.app.theme import (
    DEFAULT_THEME,
    PALETTE,
    THEME_FIELDS,
    THEME_NAMES,
    THEMES,
    Theme,
    theme_colours,
    themed,
    valid_theme_overrides,
)

APPEARANCE_KEY = "cassim.appearance"  # shell-wide: Home and every app read the same text
LEGACY_KEY = "cassim.system"  # the Nspire's System Settings, which held the theme until SDD-15
INVALID = "Saved theme settings are invalid; Dark defaults are in use."
CUSTOMISE_HINT = "Tap a swatch or type #RRGGBB. Custom colours may reduce contrast."


@dataclass
class Appearance:
    """The chosen preset and the colours changed in each preset (only the changes)."""

    theme_name: str = DEFAULT_THEME
    theme_overrides: dict[str, dict[str, str]] = field(default_factory=dict)

    @property
    def theme(self) -> Theme:
        return themed(self.theme_name, self.theme_overrides.get(self.theme_name, {}))

    @property
    def mode(self) -> ft.ThemeMode:
        return theme_mode(self.theme_name)

    def dumps(self) -> str:
        return json.dumps({"theme_name": self.theme_name, "theme_overrides": self.theme_overrides})

    @classmethod
    def from_data(cls, data: object) -> Appearance | None:
        """The appearance `data` describes, or None when any part of it is not valid."""
        if not isinstance(data, dict):
            return None
        name = data.get("theme_name", DEFAULT_THEME)
        overrides = data.get("theme_overrides", {})
        if not (
            isinstance(name, str)
            and name in THEMES
            and isinstance(overrides, dict)
            and all(
                isinstance(key, str) and key in THEMES and valid_theme_overrides(value)
                for key, value in overrides.items()
            )
        ):
            return None
        return cls(name, {key: dict(value) for key, value in overrides.items() if value})


def theme_mode(name: str) -> ft.ThemeMode:
    """Flet's light or dark mode for a preset: only Light is light."""
    return ft.ThemeMode.LIGHT if name == "Light" else ft.ThemeMode.DARK


class Loaded(NamedTuple):
    appearance: Appearance
    error: str  # a message for the person, empty unless the saved text was unreadable
    saved: bool  # a theme was saved in this browser (so an app's own older choice is not used)
    migrated: bool = False  # it came from the Nspire's old settings and is not yet in its own key


async def load_appearance(read: Callable[[str], Awaitable[str | None]]) -> Loaded:
    """The saved appearance. Before SDD-15 the theme was kept in the Nspire's System Settings,
    so a browser that has nothing under `APPEARANCE_KEY` takes its theme from there."""
    text = await read(APPEARANCE_KEY)
    legacy = text is None
    if text is None:
        text = await read(LEGACY_KEY)
        if text is None:
            return Loaded(Appearance(), "", saved=False)
    try:
        data = json.loads(text)
    except ValueError:
        data = None
    if legacy and isinstance(data, dict) and "theme_name" not in data:
        return Loaded(Appearance(), "", saved=False)  # from before themes could be chosen
    found = Appearance.from_data(data)
    if found is None:
        return Loaded(Appearance(), INVALID, saved=True)
    return Loaded(found, "", saved=True, migrated=legacy)


def field_label(name: str) -> str:
    return name.replace(".", " ").replace("_", " ").capitalize()


def pick_colour(page: ft.Page, title: str, edge: str, selected: Callable[[str], None]) -> None:
    def choose(colour: str) -> None:
        page.pop_dialog()
        selected(colour)
        page.update()

    page.show_dialog(
        ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.CIRCLE,
                        icon_color=colour,
                        style=ft.ButtonStyle(side=ft.BorderSide(1, edge)),
                        tooltip=colour,
                        on_click=lambda _, value=colour: choose(value),
                    )
                    for colour in PALETTE
                ],
                wrap=True,
                width=220,
            ),
            actions=[ft.TextButton("Cancel", on_click=lambda _: page.pop_dialog())],
        )
    )


class AppearanceDialog:
    """CASSim > Appearance…: the preset, the app's own look (`extra`, such as Scientific's
    calculator model) and, folded away, every colour of the preset. A change of preset is shown
    at once through `on_preview`; Cancel puts the saved look back. Buttons in Material order:
    Reset preset on the left, then Cancel and Save on the right (SDD-15 sections 7.3, 9.1)."""

    def __init__(
        self,
        page: ft.Page,
        appearance: Appearance,
        on_save: Callable[[Appearance], None],
        *,
        extra: Sequence[ft.Control] = (),
        on_preview: Callable[[Appearance], None] | None = None,
    ) -> None:
        self.page = page
        self.saved = appearance
        self.on_save = on_save
        self.on_preview = on_preview
        self.previewed = False
        self.drafts = {name: dict(v) for name, v in appearance.theme_overrides.items()}
        self.selected = appearance.theme_name
        self.edge = appearance.theme.chip_edge
        width = dialog_width(page, 300)
        self.boxes = {
            name: ft.TextField(label=field_label(name), value=value, width=width - 80, dense=True)
            for name, value in theme_colours(THEMES[self.selected]).items()
        }
        self.swatches: dict[str, ft.IconButton] = {}
        rows = [self._row(name) for name in THEME_FIELDS]
        self.choice = ft.SegmentedButton(
            selected=[self.selected],
            segments=[ft.Segment(value=name, label=name) for name in THEME_NAMES],
            show_selected_icon=False,
            on_change=self._choose,
        )
        self.colours = ft.Column(
            [ft.Text(CUSTOMISE_HINT, size=12), *rows], spacing=8, visible=False
        )
        self.customise = ft.TextButton(
            "Customise colours", icon=ft.Icons.EXPAND_MORE, on_click=self._fold
        )
        self.reset = ft.TextButton("Reset preset", on_click=self._reset)
        self.cancel = ft.TextButton("Cancel", on_click=self._cancel)
        self.save = ft.TextButton("Save", on_click=self._save)
        self.content = ft.Column(
            [
                ft.Text("Theme", size=13, weight=ft.FontWeight.W_600),
                self.choice,
                *extra,
                self.customise,
                self.colours,
            ],
            scroll=ft.ScrollMode.AUTO,
            tight=True,
            width=width,
            spacing=10,
        )
        self.dialog = ft.AlertDialog(
            title=ft.Text("Appearance"),
            content=self.content,
            actions=[self.reset, ft.Row([self.cancel, self.save], tight=True, spacing=4)],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        self._show(self.selected)
        page.show_dialog(self.dialog)

    # ---- what a tap does ----------------------------------------------------------------------

    def select(self, name: str) -> None:
        """Choose a preset, as a tap on its segment does."""
        self.choice.selected = [name]
        self._choose(None)

    def _choose(self, _: object) -> None:
        name = self.choice.selected[0] if self.choice.selected else self.selected
        if name not in THEMES or not self._collect():
            self.choice.selected = [self.selected]
            self.page.update()
            return
        self.selected = name
        self._show(name)
        self._preview()
        self.page.update()

    def _fold(self, _: object) -> None:
        self._unfold(not self.colours.visible)
        self.page.update()

    def _reset(self, _: object) -> None:
        self.drafts.pop(self.selected, None)
        self._show(self.selected)
        self._preview()
        self.page.update()

    def _cancel(self, _: object) -> None:
        self.page.pop_dialog()
        if self.previewed and self.on_preview is not None:
            self.on_preview(self.saved)  # the saved look again

    def _save(self, _: object) -> None:
        if not self._collect():
            return
        self.page.pop_dialog()
        self.on_save(self.draft())

    # ---- the colours --------------------------------------------------------------------------

    def draft(self) -> Appearance:
        return Appearance(self.selected, {name: dict(v) for name, v in self.drafts.items() if v})

    def _preview(self) -> None:
        if self.on_preview is not None:
            self.previewed = True
            self.on_preview(self.draft())

    def _row(self, name: str) -> ft.Control:
        box = self.boxes[name]
        swatch = ft.IconButton(
            icon=ft.Icons.CIRCLE,
            icon_color=box.value,
            style=ft.ButtonStyle(side=ft.BorderSide(1, self.edge)),
            tooltip=f"Choose {box.label}",
            on_click=lambda _, key=name: self._pick(key),
        )
        self.swatches[name] = swatch
        box.on_change = lambda _, key=name: self._typed(key)
        return ft.Row([box, swatch], spacing=8, tight=True)

    def _show(self, name: str) -> None:
        values = theme_colours(THEMES[name])
        values.update(self.drafts.get(name, {}))
        for key, box in self.boxes.items():
            box.value = values[key]
            box.error = None
            self.swatches[key].icon_color = values[key]

    def _unfold(self, shown: bool) -> None:
        self.colours.visible = shown
        self.customise.icon = ft.Icons.EXPAND_LESS if shown else ft.Icons.EXPAND_MORE
        # the open list scrolls inside the dialog, so the dialog keeps to the window
        room = min(450, max(180, (self.page.height or 700) - 200))
        self.content.height = room if shown else None

    def _collect(self) -> bool:
        values = {key: (box.value or "").strip() for key, box in self.boxes.items()}
        if not valid_theme_overrides(values):
            for name, box in self.boxes.items():
                box.error = None if valid_theme_overrides({name: values[name]}) else "Use #RRGGBB"
            self._unfold(True)  # the mistake is in the folded colours: show them
            self.page.update()
            return False
        defaults = theme_colours(THEMES[self.selected])
        self.drafts[self.selected] = {
            name: value for name, value in values.items() if value != defaults[name]
        }
        return True

    def _pick(self, name: str) -> None:
        def set_colour(colour: str) -> None:
            self.boxes[name].value = colour
            self.boxes[name].error = None
            self.swatches[name].icon_color = colour

        pick_colour(self.page, field_label(name), self.edge, set_colour)

    def _typed(self, name: str) -> None:
        value = (self.boxes[name].value or "").strip()
        if valid_theme_overrides({name: value}):
            self.swatches[name].icon_color = value
            self.page.update()


def appearance_dialog(
    page: ft.Page,
    appearance: Appearance,
    on_save: Callable[[Appearance], None],
    *,
    extra: Sequence[ft.Control] = (),
    on_preview: Callable[[Appearance], None] | None = None,
) -> AppearanceDialog:
    """Open the Appearance dialog (see `AppearanceDialog`)."""
    return AppearanceDialog(page, appearance, on_save, extra=extra, on_preview=on_preview)
