"""The all-in-one bundle's Home screen (FR-PROF-010 to FR-PROF-013, FR-PROF-017)."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

import flet as ft

from cassim.app import about
from cassim.app.theme import DARK, HIGH_CONTRAST, LIGHT

if TYPE_CHECKING:
    from cassim.app.shell import Shell

WELCOME = "Hi! Choose a CAS Calculator or other tool to start"
SYSTEM_KEY = "cassim.system"  # the Nspire shell's existing, device-prefixed system settings
APP_CHOICES = ("nspire", "classpad", "prime", "pseudocode", "scientific")
APP_NAMES = {
    "nspire": "Nspire",
    "classpad": "Classpad",
    "prime": "Prime",
    "pseudocode": "Pseudocode & Python",
    "scientific": "Scientific",
}
APP_HINTS = {
    "nspire": "Handheld graphing and CAS",
    "classpad": "ClassPad CAS calculator",
    "prime": "Prime calculator",
    "pseudocode": "Write and trace algorithms",
    "scientific": "Scientific calculator",
}
APP_GLYPHS = {
    "nspire": "ℕ",  # noqa: RUF001 - requested double-struck N
    "classpad": "ℂ",  # noqa: RUF001 - requested double-struck C
    "prime": "ℙ",  # noqa: RUF001 - requested double-struck P
}
APP_ICONS = {
    "pseudocode": ft.Icons.CODE,
    "scientific": ft.Icons.SCIENCE_OUTLINED,
}


@dataclass(frozen=True)
class HomeChoice:
    """One row on Home, including choices this build cannot open."""

    id: str
    title: str
    hint: str
    available: bool


def home_choices(available: tuple[str, ...]) -> tuple[HomeChoice, ...]:
    """Return every requested app in display order, enabling only apps in this bundle."""
    built = set(available)
    return tuple(
        HomeChoice(item, APP_NAMES[item], APP_HINTS[item], item in built) for item in APP_CHOICES
    )


class Home:
    """Render and operate the Home screen without importing any device UI."""

    def __init__(self, shell: Shell, choose: Callable[[str], object]) -> None:
        self.shell = shell
        self.choose = choose
        self.page = shell.page
        self.theme = DARK
        self.theme_name = "Dark"
        self.symbol_font = "Symbols"
        self.control: ft.Control | None = None
        self.update_button: ft.TextButton | None = None
        shell.changed = self.on_bridge

    async def start(self) -> None:
        saved = await self.shell.read_global(SYSTEM_KEY)
        if saved is not None:
            try:
                data = json.loads(saved)
                name = data.get("theme_name", "Dark") if isinstance(data, dict) else "Dark"
                self._set_theme(name if isinstance(name, str) else "Dark")
            except TypeError, ValueError:
                self._set_theme("Dark")
        self.draw()
        print("CASSIM: HOME", flush=True)

    def _set_theme(self, name: str) -> None:
        themes = {"Dark": DARK, "Light": LIGHT, "High contrast": HIGH_CONTRAST}
        self.theme_name = name if name in themes else "Dark"
        self.theme = themes[self.theme_name]

    def _card(self, choice: HomeChoice) -> ft.Control:
        title = self.theme.panel_text if choice.available else self.theme.menu_disabled
        hint = self.theme.panel_accent if choice.available else self.theme.menu_disabled
        content = ft.Row(
            [
                ft.Container(
                    (
                        ft.Text(
                            APP_GLYPHS[choice.id],
                            size=25,
                            weight=ft.FontWeight.W_600,
                            color=title,
                            font_family=self.symbol_font,
                            semantics_label="",
                        )
                        if choice.id in APP_GLYPHS
                        else ft.Icon(APP_ICONS[choice.id], color=title, size=27)
                    ),
                    width=48,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Column(
                    [
                        ft.Text(choice.title, size=17, weight=ft.FontWeight.W_600, color=title),
                        ft.Text(
                            choice.hint if choice.available else "Coming soon",
                            size=12,
                            color=hint,
                        ),
                    ],
                    spacing=2,
                    expand=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Icon(
                    ft.Icons.CHEVRON_RIGHT if choice.available else ft.Icons.LOCK_OUTLINE,
                    color=title,
                    size=20,
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        return ft.Button(
            content=content,
            width=self.card_width,
            height=72,
            disabled=not choice.available,
            tooltip=None if choice.available else f"{choice.title} is coming soon",
            style=ft.ButtonStyle(
                bgcolor=self.theme.home_card if choice.available else self.theme.background,
                color=title,
                side=ft.BorderSide(
                    1, self.theme.panel_accent if choice.available else self.theme.menu_disabled
                ),
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                elevation=0,
            ),
            on_click=(lambda _, item=choice: self.choose(item.id)) if choice.available else None,
        )

    @staticmethod
    def _mark() -> ft.Control:
        return ft.Image(
            src="icons/icon-192.png",
            width=66,
            height=66,
            fit=ft.BoxFit.CONTAIN,
            semantics_label=f"{about.product_name()} app icon",
        )

    def draw(self) -> None:
        page = self.page
        page_width = float(page.width or 800)
        self.content_width = min(740, max(320, page_width - 32))
        self.card_width = min(560, self.content_width)
        page.title = about.product_name()
        page.fonts = {self.symbol_font: "fonts/NotoSansSymbols2-Regular.ttf"}
        page.theme_mode = ft.ThemeMode.LIGHT if self.theme_name == "Light" else ft.ThemeMode.DARK
        page.bgcolor = self.theme.background
        page.padding = 0
        page.on_keyboard_event = None
        page.on_resize = None
        page.on_app_lifecycle_state_change = None

        choices = home_choices(self.shell.available_devices)
        content = ft.Column(
            [
                self._mark(),
                ft.Container(
                    ft.Text(
                        WELCOME,
                        size=22,
                        weight=ft.FontWeight.W_500,
                        color=self.theme.panel_text,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    width=self.card_width,
                    alignment=ft.Alignment.CENTER,
                    padding=ft.Padding.symmetric(horizontal=12),
                ),
                ft.Container(height=10),
                ft.Container(
                    ft.Row(
                        [
                            ft.Text(
                                "Choose an app",
                                size=15,
                                weight=ft.FontWeight.W_600,
                                color=self.theme.panel_accent,
                            ),
                            ft.TextButton(
                                content=ft.Row(
                                    [
                                        ft.Icon(
                                            ft.Icons.MENU,
                                            size=19,
                                            color=self.theme.panel_accent,
                                        ),
                                        ft.Text(
                                            about.product_name(),
                                            size=14,
                                            color=self.theme.panel_accent,
                                        ),
                                    ],
                                    tight=True,
                                    spacing=5,
                                ),
                                tooltip="CASSim menu",
                                on_click=lambda _: self.open_cassim_menu(),
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        width=self.card_width,
                    ),
                    width=self.card_width,
                ),
                ft.Column([self._card(choice) for choice in choices], spacing=8),
            ],
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.control = ft.Container(content, padding=ft.Padding.symmetric(vertical=42), expand=True)
        page.controls.clear()
        page.add(self.control)
        page.update()

    def open_cassim_menu(self) -> None:
        update = ft.TextButton(
            self.shell.update_label,
            on_click=self.activate_update,
        )
        self.update_button = update
        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("CASSim"),
                content=ft.Column(
                    [
                        ft.TextButton(
                            "Settings",
                            on_click=lambda _: self.page.run_task(self.open_settings),
                        ),
                        update,
                        ft.TextButton("Help (wiki)…", on_click=self.open_help),
                        ft.TextButton(f"About {about.product_name()}…", on_click=self.open_about),
                    ],
                    tight=True,
                ),
                actions=[ft.TextButton("Close", on_click=self.close_cassim_menu)],
            )
        )

    def on_bridge(self) -> None:
        if self.update_button is not None:
            self.update_button.content = self.shell.update_label
            self.update_button.update()

    def activate_update(self, _: ft.Event[ft.TextButton]) -> None:
        self.update_button = None
        self.shell.activate_update()

    def close_cassim_menu(self, _: ft.Event[ft.TextButton]) -> None:
        self.update_button = None
        self.page.pop_dialog()

    def open_help(self, _: ft.Event[ft.TextButton]) -> None:
        self.update_button = None
        self.shell.help()

    def open_about(self, _: ft.Event[ft.TextButton]) -> None:
        self.update_button = None
        self.shell.about()

    async def open_settings(self) -> None:
        self.update_button = None
        self.page.pop_dialog()
        saved = await self.shell.read_global(SYSTEM_KEY)
        data: dict[str, object] = {}
        if saved is not None:
            try:
                parsed = json.loads(saved)
                if isinstance(parsed, dict):
                    data = parsed
            except TypeError, ValueError:
                pass

        theme = ft.Dropdown(
            label="Appearance",
            value=self.theme_name,
            options=[ft.DropdownOption(name) for name in ("Dark", "Light", "High contrast")],
            width=280,
        )

        def save(_: object) -> None:
            value = theme.value if isinstance(theme.value, str) else "Dark"
            data.setdefault("start_mode", "computer")
            data.setdefault("math_size", 20)
            data["theme_name"] = value
            self.shell.write_global(SYSTEM_KEY, json.dumps(data))
            self._set_theme(value)
            self.page.pop_dialog()
            self.draw()

        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Settings"),
                content=ft.Column(
                    [
                        ft.Text("Appearance", size=13, weight=ft.FontWeight.W_600),
                        theme,
                        ft.Text("Each app opens directly on later visits.", size=12),
                    ],
                    tight=True,
                    spacing=12,
                ),
                actions=[
                    ft.TextButton("Save", on_click=save),
                    ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog()),
                ],
            )
        )
