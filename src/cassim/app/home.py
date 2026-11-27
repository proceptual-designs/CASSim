"""The all-in-one bundle's Home screen (FR-PROF-010 to FR-PROF-013, FR-PROF-017)."""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

import flet as ft

from cassim.app import about
from cassim.app.appearance import Appearance, appearance_dialog
from cassim.app.cassim_menu import HOME_MENU, fill_cassim_menu
from cassim.app.shell import BrowserOffers

if TYPE_CHECKING:
    from cassim.app.shell import Shell
    from cassim.app.theme import Theme

WELCOME = "Hi! Choose a CAS Calculator or other tool to start"
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
        self.appearance = shell.appearance  # the shared theme, or a preview of another
        self.symbol_font = "Symbols"
        self.control: ft.Control | None = None
        self.cassim_menu = ft.SubmenuButton(content="CASSim")
        shell.changed = self.on_bridge

    async def start(self) -> None:
        error = await self.shell.load_appearance()
        self.appearance = self.shell.appearance
        self.draw()
        if error:
            self.shell.notice("Appearance", error)
        print("CASSIM: HOME", flush=True)

    @property
    def theme(self) -> Theme:
        return self.appearance.theme

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
        page.theme_mode = self.appearance.mode
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
                            ft.MenuBar(controls=[self.refresh_cassim_menu()]),
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

    @property
    def offers(self) -> BrowserOffers:
        return getattr(self.shell, "offers", None) or BrowserOffers()

    def refresh_cassim_menu(self) -> ft.SubmenuButton:
        """The CASSim menu, as in every app (SDD-15 section 4), with Home's subset."""
        fill_cassim_menu(self.cassim_menu, self.offers, HOME_MENU, self.cassim_action, self.theme)
        return self.cassim_menu

    def cassim_action(self, action: str) -> None:
        if action == "appearance":
            self.open_appearance()
        else:
            self.shell.menu_action(action)

    def on_bridge(self) -> None:
        """The page reported a change (an update, installing): redraw the menu."""
        self.refresh_cassim_menu()
        if self.control is not None:
            with contextlib.suppress(RuntimeError):  # not on the page yet
                self.cassim_menu.update()

    def open_appearance(self) -> None:
        """CASSim > Appearance…: the theme for Home and every app (SDD-15 section 7.3)."""

        def preview(appearance: Appearance) -> None:
            self.appearance = appearance
            self.draw()

        def save(appearance: Appearance) -> None:
            self.shell.save_appearance(appearance)
            preview(appearance)

        appearance_dialog(self.page, self.shell.appearance, save, on_preview=preview)
