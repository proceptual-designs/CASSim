"""The Flet views (FR-DEV-002, FR-DEV-004, FR-DEV-006) over one `AppState`."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from enum import StrEnum

import flet as ft

from cassim.app.entry import EntryLine
from cassim.app.layout import KEY_GAP, KEY_H, key_span
from cassim.app.state import MATH_SIZES, AppState, Mode
from cassim.app.theme import DARK, Theme
from cassim.core.format import latex_for_markdown
from cassim.core.settings import Angle, Ascii, Calc, Case, Domain, updated
from cassim.device.editor import format_target
from cassim.device.keys import Key
from cassim.device.menu import MenuView, Panel, Row
from cassim.device.screen import Line, Screen, thumbnail
from cassim.device.wizard import Wizard

# Arrows and shapes are not in the default font, and the browser's fallback font comes from a
# Google server, which the offline build cannot reach (FR-PWA-002). They are set in a vendored font.
SYMBOL_FONT = "Symbols"
SYMBOL_FONT_FILE = "fonts/NotoSansSymbols2-Regular.ttf"
SYMBOLS = frozenset("◀▶▲▼␣●⏎▸□▮▦")


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
MENU_W, MENU_W_WIDE = 200, 400  # a menu panel, in Handheld and in Computer mode
MENU_ROWS, MENU_ROWS_WIDE = 5, 16  # rows shown at once; the rest follow the highlight


def math(latex: str, theme: Theme, size: float = 20) -> ft.Markdown:
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
        self.title.size = self.status.size = self.state.px(12)
        self.entry.content = self._entry(screen)
        self.history.controls = [
            *(self._line(line, number) for number, line in enumerate(screen.lines)),
            self.entry,
            ft.Container(height=self.state.px(ENTRY_ROOM)),
        ]
        self._error(screen)
        self._menu(screen.menu)

    def _entry(self, screen: Screen) -> ft.Control:
        """The entry line as clickable controls; a page without a calculator shows its LaTeX."""
        calculator = self.state.document.current.calculator
        if calculator is None:
            return math(screen.entry, self.theme, self.state.math_size)
        return EntryLine(
            self.theme,
            self.state.math_size,
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
            math(line.latex, self.theme, self.state.math_size),
            on_click=lambda _: self.on_action("recall_at", spec),
            alignment=ft.Alignment.CENTER_RIGHT if right else ft.Alignment.CENTER_LEFT,
            bgcolor=self.theme.selection if line.selected else None,
            padding=ft.Padding.symmetric(horizontal=6),
        )

    def _menu(self, view: MenuView | None) -> None:
        """The open menu (FR-DEV-001): each level is a panel, submenus cascading to the right as
        on the handheld. Every row is clickable; a tap outside the panels closes the menu. The
        highlighted row's syntax shows at the foot of the deepest panel (beside every row in
        Computer mode, where there is room)."""
        self.menu.visible = view is not None
        if view is None:
            return
        wide = self.state.mode is Mode.COMPUTER
        px = self.state.px
        # Submenus overlap their parent by half (Computer) or nearly all of it (Handheld).
        step_x, step_y = (px(MENU_W_WIDE) / 2, px(10)) if wide else (px(22), px(10))
        panels = [
            ft.Container(
                self._panel(view, depth, panel, wide=wide),
                left=px(4) + depth * step_x,
                top=px(4) + depth * step_y,
            )
            for depth, panel in enumerate(view.panels)
        ]
        outside = ft.Container(
            left=0,
            top=0,
            right=0,
            bottom=0,
            bgcolor="#30000000",
            on_click=lambda _: self.on_action("escape", ""),
        )
        self.menu.content = ft.Stack([outside, *panels])

    def _panel(self, view: MenuView, depth: int, panel: Panel, *, wide: bool) -> ft.Control:
        theme, px = self.theme, self.state.px
        last = depth == len(view.panels) - 1
        shown = MENU_ROWS_WIDE if wide else MENU_ROWS
        chosen = selected_index(panel)
        start = max(0, min(chosen - shown // 2, len(panel.rows) - shown))
        window = range(start, min(len(panel.rows), start + shown))
        items: list[ft.Control] = [self._header(view, depth, panel)]
        if start:
            items.append(self._more("▲ more", -shown, active=last))
        items.extend(
            self._menu_row(depth, n, panel.rows[n], wide=wide, active=last) for n in window
        )
        if window.stop < len(panel.rows):
            items.append(self._more("▼ more", shown, active=last))
        if last and view.hint and not wide:
            items.append(
                ft.Container(
                    ft.Text(view.hint, size=px(10), color=theme.menu_hint, italic=True),
                    padding=ft.Padding.only(left=px(4), top=px(3), right=px(4)),
                    border=ft.Border.only(top=ft.BorderSide(1, theme.key_label)),
                )
            )
        return ft.Container(
            ft.Column(items, spacing=0, tight=True),
            bgcolor=theme.title_bar,
            padding=px(4),
            border_radius=px(6),
            width=px(MENU_W_WIDE if wide else MENU_W),
            shadow=ft.BoxShadow(blur_radius=8, color="#80000000"),
            on_click=lambda _: None,  # a click between rows is not a click outside the menu
        )

    def _header(self, view: MenuView, depth: int, panel: Panel) -> ft.Control:
        """The panel's title; on a submenu it is a back button (it closes this level)."""
        back = f"{depth - 1}:{selected_index(view.panels[depth - 1])}" if depth else ""
        return ft.Container(
            label_text(
                ("◀ " if depth else "") + panel.title,
                size=self.state.px(12),
                weight=ft.FontWeight.BOLD,
                color=self.theme.key_label,
            ),
            padding=ft.Padding.symmetric(horizontal=self.state.px(4), vertical=self.state.px(2)),
            on_click=(lambda _: self.on_action("menu_pick", back)) if back else None,
        )

    def _more(self, text: str, step: int, *, active: bool) -> ft.Control:
        return ft.Container(
            label_text(text, size=self.state.px(11), color=self.theme.key_label),
            padding=ft.Padding.symmetric(horizontal=self.state.px(6)),
            on_click=(lambda _: self.on_action("menu_page", str(step))) if active else None,
        )

    def _menu_row(
        self, depth: int, index: int, row: Row, *, wide: bool, active: bool
    ) -> ft.Control:
        theme, px = self.theme, self.state.px
        on = row.selected
        colour = "#ffffff" if on else theme.key_text
        parts: list[ft.Control] = [
            ft.Text(row.key, size=px(12), color=colour if on else theme.key_label, width=px(14)),
            label_text(row.label, size=px(13), color=colour, expand=True, no_wrap=True),
        ]
        if wide and row.hint:
            hint_colour = colour if on else theme.menu_hint
            parts.append(ft.Text(row.hint, size=px(11), color=hint_colour, no_wrap=True))
        if row.submenu:
            parts.append(label_text("▶", size=px(10), color=colour))
        return ft.Container(
            ft.Row(parts, spacing=px(4)),
            bgcolor=(theme.accent if active else theme.key) if on else None,
            padding=ft.Padding.symmetric(horizontal=px(4), vertical=px(2)),
            border_radius=px(3),
            tooltip=row.hint or None,
            ink=True,
            on_click=lambda _: self.on_action("menu_pick", f"{depth}:{index}"),
        )

    def _error(self, screen: Screen) -> None:
        self.error.visible = screen.error is not None
        if screen.error is None:
            return
        self.error.content = ft.Container(
            ft.Column(
                [
                    ft.Text(
                        "Error", size=self.state.px(14), weight=ft.FontWeight.BOLD, color="#ffffff"
                    ),
                    ft.Text(screen.error, size=self.state.px(14), color="#ffffff"),
                    ft.Text("press any key", size=self.state.px(11), color="#ffd0cc"),
                ],
                spacing=4,
                tight=True,
            ),
            bgcolor=self.theme.error,
            padding=12,
            border_radius=6,
        )


class Keypad:
    """The on-screen keys, laid out as on the handheld (FR-DEV-005). Each key shows its ctrl and
    shift labels small above it; the pending modifier lights up and its layer's labels move onto
    the keys."""

    def __init__(self, state: AppState, on_key: Callable[[str], None], theme: Theme = DARK) -> None:
        self.state = state
        self.on_key = on_key
        self.theme = theme
        self.control = ft.Column(spacing=KEY_GAP, tight=True)
        self.refresh()

    def refresh(self) -> None:
        gap = self.state.px(KEY_GAP)
        self.control.spacing = gap
        self.control.controls = [
            ft.Row([self._key(key) for key in row], spacing=gap, tight=True)
            for row in self.state.profile.keypad
        ]

    def _key(self, key: Key) -> ft.Control:
        state, theme = self.state, self.theme
        width = state.px(key_span(key.width))
        height = state.px(key_span(key.height, KEY_H))
        if not key.name:
            return ft.Container(width=width, height=height)
        pending = state.pending
        layer = {"ctrl": key.ctrl, "shift": key.shift}.get(pending, "")
        fill, text = theme.key_colours(key.style)
        small = state.px(8 if key.width < 1 else 9)
        labels = ft.Row(
            [
                label_text(key.ctrl, size=small, color=theme.key_label, no_wrap=True),
                label_text(key.shift, size=small, color=theme.shift_label, no_wrap=True),
            ],
            spacing=state.px(3),
            alignment=ft.MainAxisAlignment.CENTER,
            tight=True,
        )
        main = label_text(
            layer or key.label,
            size=state.px(13 if key.height < 1 or key.width < 1 else 15),
            color=text,
            weight=ft.FontWeight.W_600,
            no_wrap=True,
        )
        body: list[ft.Control] = [labels, main] if key.ctrl or key.shift else [main]
        return ft.Container(
            ft.Column(
                body,
                spacing=0,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            width=width,
            height=height,
            alignment=ft.Alignment.CENTER,
            bgcolor=theme.modifier_on if pending == key.name else fill,
            border_radius=height / 2 if key.style == "pad" else state.px(7),
            ink=True,
            tooltip=key_tip(key),
            on_click=lambda _, name=key.name: self.on_key(name),
        )


def key_tip(key: Key) -> str | None:
    """What the other layers of a key do, for a mouse hover or a long press."""
    layers = (("ctrl", key.ctrl), ("shift", key.shift))
    return ", ".join(f"{layer}: {label}" for layer, label in layers if label) or None


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


def selected_index(panel: Panel) -> int:
    return next((n for n, row in enumerate(panel.rows) if row.selected), 0)


def wizard_dialog(
    page: ft.Page, state: AppState, wizard: Wizard, on_change: Callable[[], None]
) -> ft.AlertDialog:
    """A command's dialog (FR-CALC-005): a box per field, OK pastes the command. A field that
    will not do is reported in the dialog, which stays open."""
    boxes: dict[str, ft.TextField | ft.Dropdown] = {}
    for field in wizard.fields:
        if field.choices:
            boxes[field.name] = ft.Dropdown(
                label=field.label,
                value=field.default,
                options=[ft.DropdownOption(key=value, text=text) for value, text in field.choices],
                width=280,
            )
        else:
            boxes[field.name] = ft.TextField(
                label=field.label,
                value=field.default,
                width=280,
                dense=True,
                on_submit=lambda _: ok(),
            )
    problems = ft.Text("", color="#ff8a80", size=12)

    def ok() -> None:
        values = {name: str(box.value or "") for name, box in boxes.items()}
        found = wizard.problems(values)
        if found:
            problems.value = "\n".join(found)
            problems.update()
            return
        page.pop_dialog()
        state.finish_wizard(wizard, values)
        on_change()

    first = next((box for box in boxes.values() if isinstance(box, ft.TextField)), None)
    if first is not None:
        first.autofocus = True
    dialog = ft.AlertDialog(
        title=ft.Text(wizard.title),
        content=ft.Column([*boxes.values(), problems], tight=True, spacing=10),
        actions=[
            ft.TextButton("OK", on_click=lambda _: ok()),
            ft.TextButton("Cancel", on_click=lambda _: page.pop_dialog()),
        ],
    )
    page.show_dialog(dialog)
    return dialog
