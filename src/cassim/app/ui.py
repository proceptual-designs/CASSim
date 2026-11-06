"""The Flet views (FR-DEV-002, FR-DEV-004, FR-DEV-006) over one `AppState`."""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum

import flet as ft

from cassim.app.state import AppState
from cassim.app.theme import DARK, Theme
from cassim.core.format import latex_for_markdown
from cassim.core.settings import Angle, Ascii, Calc, Case, Domain, updated
from cassim.device.keys import Key
from cassim.device.menu import MenuView
from cassim.device.screen import Line, Screen

SCREEN_WIDTH, SCREEN_HEIGHT = 320, 240  # the handheld's pixels (FR-DEV-004)
ENTRY_ROOM = 28  # the blank line kept below the entry


def math(latex: str, theme: Theme) -> ft.Markdown:
    """LaTeX drawn on the Flutter canvas (decision 0014)."""
    return ft.Markdown(
        f"${latex_for_markdown(latex)}$" if latex else " ",
        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
        fit_content=True,
        latex_style=ft.TextStyle(color=theme.screen_text, size=20),
    )


class CalculatorView:
    """The screen: title bar, history, entry line and the error dialog."""

    def __init__(self, state: AppState, theme: Theme = DARK) -> None:
        self.state = state
        self.theme = theme
        self.status = ft.Text(size=12, color="#ffffff", weight=ft.FontWeight.BOLD)
        self.title = ft.Text(size=12, color="#ffffff")
        # The entry line sits in the list with a blank line under it, so the end of the list always
        # leaves room below the entry. No animation: it lagged when the page was full.
        self.history = ft.ListView(
            expand=True, auto_scroll=True, auto_scroll_animation=ft.Animation(duration=0), spacing=2
        )
        self.entry = ft.Container(padding=ft.Padding.symmetric(horizontal=6, vertical=2))
        self.error = ft.Container(visible=False, alignment=ft.Alignment.CENTER, expand=True)
        self.menu = ft.Container(visible=False, alignment=ft.Alignment.TOP_LEFT, expand=True)
        title_bar = ft.Container(
            ft.Row([self.title, self.status], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=theme.title_bar,
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
        )
        body = ft.Column([self.history], expand=True, spacing=0)
        self.control = ft.Container(
            ft.Column([title_bar, ft.Stack([body, self.error, self.menu], expand=True)], spacing=0),
            bgcolor=theme.screen,
            border_radius=6,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

    def refresh(self) -> None:
        screen = self.state.screen()
        self.title.value = screen.title
        self.status.value = screen.status
        self.entry.content = math(screen.entry, self.theme)
        self.history.controls = [
            *(self._line(line) for line in screen.lines),
            self.entry,
            ft.Container(height=ENTRY_ROOM),
        ]
        self._error(screen)
        self._menu(screen.menu)

    def _line(self, line: Line) -> ft.Control:
        right = line.kind == "result"
        return ft.Container(
            math(line.latex, self.theme),
            alignment=ft.Alignment.CENTER_RIGHT if right else ft.Alignment.CENTER_LEFT,
            bgcolor=self.theme.selection if line.selected else None,
            padding=ft.Padding.symmetric(horizontal=6),
        )

    def _menu(self, view: MenuView | None) -> None:
        """The open menu: a list over the page, the chosen row highlighted (FR-DEV-001)."""
        self.menu.visible = view is not None
        if view is None:
            return
        theme = self.theme
        rows: list[ft.Control] = [
            ft.Text(view.title, size=12, weight=ft.FontWeight.BOLD, color=theme.key_label)
        ]
        rows.extend(
            ft.Container(
                ft.Text(
                    f"{row.key}  {row.label}{'  ▸' if row.submenu else ''}",
                    size=13,
                    color="#ffffff" if row.selected else theme.key_text,
                ),
                bgcolor=theme.accent if row.selected else None,
                padding=ft.Padding.symmetric(horizontal=6, vertical=1),
            )
            for row in view.rows
        )
        self.menu.content = ft.Container(
            ft.Column(rows, spacing=0, tight=True, scroll=ft.ScrollMode.AUTO),
            bgcolor=theme.title_bar,
            padding=6,
            border_radius=6,
            margin=4,
            width=230,
        )

    def _error(self, screen: Screen) -> None:
        self.error.visible = screen.error is not None
        if screen.error is None:
            return
        self.error.content = ft.Container(
            ft.Column(
                [
                    ft.Text("Error", weight=ft.FontWeight.BOLD, color="#ffffff"),
                    ft.Text(screen.error, color="#ffffff"),
                    ft.Text("press any key", size=11, color="#ffd0cc"),
                ],
                spacing=4,
                tight=True,
            ),
            bgcolor=self.theme.error,
            padding=12,
            border_radius=6,
        )


class Keypad:
    """The on-screen keys. The pending modifier lights up and shows its layer's labels."""

    def __init__(self, state: AppState, on_key: Callable[[str], None], theme: Theme = DARK) -> None:
        self.state = state
        self.on_key = on_key
        self.theme = theme
        self.control = ft.Column(spacing=4)
        self.refresh()

    def refresh(self) -> None:
        self.control.controls = [
            ft.Row(
                [self._key(key) for key in row], spacing=4, alignment=ft.MainAxisAlignment.CENTER
            )
            for row in self.state.profile.keypad
        ]

    def _key(self, key: Key) -> ft.Control:
        pending = self.state.pending
        layer = {"ctrl": key.ctrl, "shift": key.shift}.get(pending, "")
        return ft.Container(
            ft.Column(
                [
                    ft.Text(key.ctrl or key.shift, size=9, color=self.theme.key_label),
                    ft.Text(
                        layer or key.label,
                        size=15,
                        color=self.theme.key_text,
                        weight=ft.FontWeight.W_600,
                    ),
                ],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            width=58,
            height=44,
            bgcolor=self.theme.modifier_on if pending == key.name else self.theme.key,
            border_radius=8,
            ink=True,
            on_click=lambda _, name=key.name: self.on_key(name),
        )


def chip(label: str, on_click: Callable[[], None], theme: Theme, *, on: bool = False) -> ft.Control:
    """A small text button for toolbars."""
    return ft.Container(
        ft.Text(label, color="#ffffff" if on else theme.key_text, size=13),
        bgcolor=theme.accent if on else theme.key,
        padding=ft.Padding.symmetric(horizontal=10, vertical=5),
        border_radius=6,
        ink=True,
        on_click=lambda _: on_click(),
    )


class Sidebar:
    """The page sorter and the variable list of the current Problem (FR-DOC-001)."""

    def __init__(self, state: AppState, on_change: Callable[[], None], theme: Theme = DARK) -> None:
        self.state = state
        self.on_change = on_change
        self.theme = theme
        self.control = ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO)

    def refresh(self) -> None:
        document = self.state.document
        theme = self.theme
        here = (document.problem, document.page)
        rows: list[ft.Control] = [ft.Text("Pages", weight=ft.FontWeight.BOLD, color=theme.key_text)]
        for problem, page, kind in document.sorter():
            rows.append(
                ft.Container(
                    ft.Text(
                        f"{problem + 1}.{page + 1}  {kind}",
                        color=theme.accent if (problem, page) == here else theme.key_text,
                    ),
                    padding=ft.Padding.symmetric(vertical=2),
                    on_click=lambda _, p=problem, q=page: self._go(p, q),
                )
            )
        rows.append(ft.Text("Variables", weight=ft.FontWeight.BOLD, color=theme.key_text))
        session = document.problems[document.problem].session
        variables = session.variables()
        if not variables:
            rows.append(ft.Text("none", color=theme.key_label, size=12))
        rows.extend(
            ft.Text(f"{row.name} = {row.text}" if not row.is_function else row.text, size=12)
            for row in variables
        )
        self.control.controls = rows

    def _go(self, problem: int, page: int) -> None:
        self.state.document.go(problem, page)
        self.on_change()


def settings_dialog(
    page: ft.Page, state: AppState, on_change: Callable[[], None], theme: Theme = DARK
) -> None:
    """Document Settings (FR-DOC-002): choices apply to every Problem when OK is pressed."""
    current = state.document.settings
    fields: dict[str, ft.Dropdown] = {}

    def dropdown(label: str, name: str, options: list[tuple[str, str]], value: str) -> ft.Control:
        dropdown = ft.Dropdown(
            label=label,
            value=value,
            options=[ft.DropdownOption(key=key, text=text) for key, text in options],
            width=240,
        )
        fields[name] = dropdown
        return dropdown

    def enum_options(enum: type[StrEnum]) -> list[tuple[str, str]]:
        return [(member.value, member.name.title()) for member in enum]

    digits = [f"float{n}" for n in range(1, 13)] + [f"fix{n}" for n in range(0, 10)]
    controls = [
        dropdown("Angle", "angle", enum_options(Angle), current.angle),
        dropdown("Calculation mode", "calc", enum_options(Calc), current.calc),
        dropdown("Real or complex", "domain", enum_options(Domain), current.domain),
        dropdown("Display digits", "digits", [(d, d.title()) for d in digits], current.digits),
        dropdown("Letter case", "case", enum_options(Case), current.case),
        dropdown("Results as keyboard text", "ascii", enum_options(Ascii), current.ascii),
    ]

    def apply() -> None:
        changes = {name: field.value for name, field in fields.items() if field.value}
        state.document.use(updated(current, changes))
        page.pop_dialog()
        on_change()

    page.show_dialog(
        ft.AlertDialog(
            title=ft.Text("Document Settings"),
            content=ft.Column(controls, tight=True, spacing=12),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: page.pop_dialog()),
                ft.TextButton("OK", on_click=apply),
            ],
        )
    )
