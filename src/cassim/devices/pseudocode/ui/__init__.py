"""A shell-owned placeholder until the full Pseudocode editor is implemented."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from cassim.app import about
from cassim.app.theme import DARK

if TYPE_CHECKING:
    from cassim.app.shell import Shell


class App:
    """Minimal Pseudocode destination with a CASSim menu that can return Home."""

    def __init__(self, shell: Shell) -> None:
        self.shell = shell
        self.page = shell.page

    async def start(self, **_options: object) -> None:
        page = self.page
        page.title = "CASSim — Pseudocode & Python"
        page.bgcolor = DARK.background
        page.padding = 0
        page.on_keyboard_event = None
        page.on_resize = None
        page.on_app_lifecycle_state_change = None
        page.controls.clear()
        page.add(
            ft.Column(
                [
                    ft.Container(
                        ft.Row(
                            [
                                ft.Text(
                                    "Pseudocode & Python",
                                    size=16,
                                    weight=ft.FontWeight.W_600,
                                    color=DARK.title_text,
                                    expand=True,
                                ),
                                ft.TextButton(
                                    content=ft.Row(
                                        [
                                            ft.Icon(ft.Icons.MENU, color=DARK.title_text),
                                            ft.Text(
                                                about.product_name(),
                                                color=DARK.title_text,
                                            ),
                                        ],
                                        tight=True,
                                        spacing=5,
                                    ),
                                    tooltip="CASSim menu",
                                    on_click=lambda _: self.open_menu(),
                                ),
                            ]
                        ),
                        height=48,
                        bgcolor=DARK.title_bar,
                        padding=ft.Padding.symmetric(horizontal=16),
                    ),
                    ft.Container(
                        ft.Column(
                            [
                                ft.Text(
                                    "</>",
                                    size=54,
                                    weight=ft.FontWeight.W_700,
                                    color=DARK.panel_accent,
                                ),
                                ft.Text(
                                    "Pseudocode & Python are coming next.",
                                    size=24,
                                    weight=ft.FontWeight.W_600,
                                    color=DARK.panel_text,
                                ),
                                ft.Text(
                                    "This placeholder confirms device switching and lazy loading.",
                                    size=14,
                                    color=DARK.menu_disabled,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=12,
                        ),
                        expand=True,
                        alignment=ft.Alignment.CENTER,
                    ),
                ],
                expand=True,
                spacing=0,
            )
        )
        page.update()
        print("CASSIM: PSEUDOCODE READY", flush=True)

    def unmount(self) -> None:
        self.page.controls.clear()

    def open_menu(self) -> None:
        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text(about.product_name()),
                content=ft.Column(
                    [
                        ft.TextButton("Home", on_click=lambda _: self.home()),
                        ft.TextButton("Help (wiki)…", on_click=lambda _: self.shell.help()),
                        ft.TextButton(
                            f"About {about.product_name()}…",
                            on_click=lambda _: self.shell.about(),
                        ),
                    ],
                    tight=True,
                ),
                actions=[ft.TextButton("Close", on_click=lambda _: self.page.pop_dialog())],
            )
        )

    def home(self) -> None:
        self.page.pop_dialog()
        if self.shell.home is not None:
            self.shell.home()


def mount(shell: Shell) -> App:
    """Mount the Pseudocode placeholder behind the shell lifecycle."""
    return App(shell)
