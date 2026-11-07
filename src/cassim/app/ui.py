"""The Flet views (FR-DEV-002, FR-DEV-004, FR-DEV-006) over one `AppState`."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from enum import StrEnum

import flet as ft

from cassim.app.entry import EntryLine
from cassim.app.state import MATH_SIZES, AppState, Mode
from cassim.app.theme import DARK, Theme
from cassim.core.format import latex_for_markdown
from cassim.core.settings import Angle, Ascii, Calc, Case, Domain, updated
from cassim.device.editor import format_target
from cassim.device.keys import Key
from cassim.device.menu import MenuView
from cassim.device.screen import Line, Screen, thumbnail

SCREEN_WIDTH, SCREEN_HEIGHT = 320, 240  # the handheld's pixels (FR-DEV-004)
# Arrows and shapes are not in the default font, and the browser's fallback font comes from a
# Google server, which the offline build cannot reach (FR-PWA-002). They are set in a vendored font.
SYMBOL_FONT = "Symbols"
SYMBOL_FONT_FILE = "fonts/NotoSansSymbols2-Regular.ttf"
SYMBOLS = frozenset("◀▶▲▼")


def label_text(text: str, **style: object) -> ft.Text:
    """Text whose arrow glyphs use the vendored symbols font; `style` is `ft.Text` keywords."""
    if not SYMBOLS.intersection(text):
        return ft.Text(text, **style)  # ty: ignore[invalid-argument-type]
    spans: list[ft.TextSpan] = []
    run = ""
    for ch in text:
        if (ch in SYMBOLS) == (run[:1] in SYMBOLS) or not run:
            run += ch
            continue
        spans.append(_span(run))
        run = ch
    spans.append(_span(run))
    return ft.Text(spans=spans, **style)  # ty: ignore[invalid-argument-type]


def _span(run: str) -> ft.TextSpan:
    style = ft.TextStyle(font_family=SYMBOL_FONT) if run[0] in SYMBOLS else None
    return ft.TextSpan(run, style=style)


ENTRY_ROOM = 28  # the blank line kept below the entry


def math(latex: str, theme: Theme, size: int = 20) -> ft.Markdown:
    """LaTeX drawn on the Flutter canvas (decision 0014)."""
    return ft.Markdown(
        f"${latex_for_markdown(latex)}$" if latex else " ",
        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
        fit_content=True,
        latex_style=ft.TextStyle(color=theme.screen_text, size=size),
    )


class CalculatorView:
    """The screen: title bar, history, entry line and the error dialog."""

    def __init__(
        self,
        state: AppState,
        theme: Theme = DARK,
        on_action: Callable[[str, str], None] = lambda action, arg: None,
        shift: Callable[[], bool] = lambda: False,
    ) -> None:
        self.state = state
        self.theme = theme
        self.on_action = on_action
        self.shift = shift
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
        self.entry.content = self._entry(screen)
        self.history.controls = [
            *(self._line(line, number) for number, line in enumerate(screen.lines)),
            self.entry,
            ft.Container(height=ENTRY_ROOM),
        ]
        self._error(screen)
        self._menu(screen.menu)

    def _entry(self, screen: Screen) -> ft.Control:
        """The entry line as clickable controls; a page without a calculator shows its LaTeX."""
        calculator = self.state.document.current.calculator
        if calculator is None:
            return math(screen.entry, self.theme, self.state.system.math_size)
        return EntryLine(
            self.theme,
            self.state.system.math_size,
            self._click,
            calculator.session.is_function,
        ).build(calculator.editor)

    def _click(self, path: Sequence[tuple[int, int]], pos: int) -> None:
        """A click in the entry: place the cursor, or extend the selection with shift held."""
        self.on_action("extend" if self.shift() else "place", format_target(path, pos))

    def _line(self, line: Line, number: int) -> ft.Control:
        right = line.kind == "result"
        spec = f"{number // 2}:{line.kind}"  # history rows come in entry, result pairs
        return ft.Container(
            math(line.latex, self.theme, self.state.system.math_size),
            on_click=lambda _: self.on_action("recall_at", spec),
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
                    label_text(key.ctrl or key.shift, size=9, color=self.theme.key_label),
                    label_text(
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


def chip(text: str, on_click: Callable[[], None], theme: Theme, *, on: bool = False) -> ft.Control:
    """A small text button for toolbars."""
    return ft.Container(
        label_text(text, color="#ffffff" if on else theme.key_text, size=13),
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
        rows: list[ft.Control] = [
            ft.Text("Pages", weight=ft.FontWeight.BOLD, color=theme.key_text),
            ft.Row(
                [
                    chip(label, lambda a=action, g=arg: self._act(a, g), theme)
                    for label, action, arg in (
                        ("▲", "move_page", "-1"),
                        ("▼", "move_page", "1"),
                        ("undo", "undo_pages", ""),
                        ("redo", "redo_pages", ""),
                    )
                ],
                spacing=4,
                wrap=True,
            ),
        ]
        for problem, page, kind in document.sorter():
            rows.append(
                ft.Container(
                    label_text(
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

    def _act(self, action: str, arg: str) -> None:
        self.state.run_action(action, arg)
        self.on_change()

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


def system_settings_dialog(
    page: ft.Page, state: AppState, on_change: Callable[[], None], theme: Theme = DARK
) -> None:
    """System Settings: the view the app starts in and the size of the maths."""
    system = state.system
    start = ft.Dropdown(
        label="Start in",
        value=system.start_mode.value,
        options=[ft.DropdownOption(key=m.value, text=m.name.title()) for m in Mode],
        width=240,
    )
    size = ft.Dropdown(
        label="Maths size",
        value=next(name for name, px in MATH_SIZES.items() if px == system.math_size),
        options=[ft.DropdownOption(key=name, text=name) for name in MATH_SIZES],
        width=240,
    )

    def apply() -> None:
        system.start_mode = Mode(start.value or system.start_mode)
        system.math_size = MATH_SIZES.get(size.value or "", system.math_size)
        page.pop_dialog()
        on_change()

    page.show_dialog(
        ft.AlertDialog(
            title=ft.Text("System Settings"),
            content=ft.Column([start, size], tight=True, spacing=12),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: page.pop_dialog()),
                ft.TextButton("OK", on_click=apply),
            ],
        )
    )


def sorter_dialog(
    page: ft.Page, state: AppState, on_change: Callable[[], None], theme: Theme = DARK
) -> None:
    """The page sorter: every page as a tile, grouped by Problem. Click a tile to go to it, then
    move or delete it with the buttons."""
    document = state.document
    body = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, width=520, height=360)

    def act(action: str, arg: str = "") -> None:
        state.run_action(action, arg)
        build()
        on_change()

    def go(problem: int, index: int) -> None:
        document.go(problem, index)
        build()
        on_change()

    def tile(problem: int, index: int) -> ft.Control:
        here = (problem, index) == (document.problem, document.page)
        shown = document.problems[problem].pages[index]
        return ft.Container(
            ft.Column(
                [
                    ft.Text(f"{problem + 1}.{index + 1}", size=11, color=theme.key_label),
                    *(ft.Text(line, size=11, color=theme.screen_text) for line in thumbnail(shown)),
                ],
                spacing=1,
            ),
            width=110,
            height=84,
            padding=6,
            bgcolor=theme.selection if here else theme.screen,
            border=ft.Border.all(2, theme.accent if here else theme.title_bar),
            border_radius=6,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            on_click=lambda _, p=problem, q=index: go(p, q),
        )

    def build() -> None:
        body.controls = [
            ft.Row(
                [
                    ft.Text(f"Problem {p + 1}", color=theme.key_text, width=70),
                    ft.Row([tile(p, q) for q in range(len(problem.pages))], wrap=True, expand=True),
                ],
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
            for p, problem in enumerate(document.problems)
        ]
        page.update()

    build()
    buttons = [
        ("◀ earlier", "move_page", "-1"),
        ("later ▶", "move_page", "1"),
        ("delete", "delete_page", ""),
        ("undo", "undo_pages", ""),
        ("redo", "redo_pages", ""),
    ]
    page.show_dialog(
        ft.AlertDialog(
            title=ft.Text("Page Sorter"),
            content=ft.Column(
                [
                    ft.Row(
                        [chip(label, lambda a=a, g=g: act(a, g), theme) for label, a, g in buttons],
                        spacing=4,
                        wrap=True,
                    ),
                    body,
                ],
                tight=True,
            ),
            actions=[ft.TextButton("Close", on_click=lambda _: page.pop_dialog())],
        )
    )
