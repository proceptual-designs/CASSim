"""The Flet views (FR-DEV-002, FR-DEV-004, FR-DEV-006) over one `AppState`."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from enum import StrEnum
from typing import Any, cast

import flet as ft

from cassim.app import about
from cassim.app.entry import EntryLine
from cassim.app.layout import KEY_GAP, KEY_H, SCREEN_H, key_span
from cassim.app.state import MATH_SIZES, AppState, Mode
from cassim.app.theme import DARK, Theme
from cassim.core.results import latex_for_markdown
from cassim.core.settings import Angle, Ascii, Calc, Case, Domain, updated
from cassim.device.editor import format_target
from cassim.device.keys import Key
from cassim.device.menu import MenuView, Panel, Row
from cassim.device.screen import Line, Screen, thumbnail
from cassim.device.wizard import Field, Wizard

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


SELECTED_KEY = "picked-line"


def _scroll_key() -> ft.ScrollKey:
    """The key `scroll_to` finds the picked line by (Flet's stubs hide ScrollKey's argument)."""
    return cast("Any", ft.ScrollKey)(value=SELECTED_KEY)


ENTRY_ROOM = 56  # blank space kept below the entry: the list scrolls once 3/4 of the screen is used
MENU_W, MENU_W_WIDE = 200, 400  # a menu panel, in Handheld and in Computer mode
GRID_CELL = 26  # a grid menu's cell (11 fit the handheld's 320 px)
SHORT_CELL = 2  # characters that fit a grid cell at full size
MENU_ROWS_WIDE = 16  # rows of a menu shown at once in Computer mode; the rest follow the highlight
# Handheld menus must fit the 240 px screen, so their rows are counted from what is left of it
# (all in handheld pixels): the title bar, a panel's padding, header, hint line and ▲ ▼ rows.
TITLE_H, PANEL_PAD, HEADER_H, HINT_H, ARROW_H, LIST_ROW_H = 20, 8, 18, 16, 14, 19.5
MENU_STEP_Y = 6  # each submenu sits this far lower than its parent


def math(latex: str, theme: Theme, size: float = 20) -> ft.Markdown:
    """LaTeX drawn on the Flutter canvas (decision 0014)."""
    return ft.Markdown(
        f"${latex_for_markdown(latex)}$" if latex else " ",
        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
        fit_content=True,
        latex_style=ft.TextStyle(color=theme.screen_text, size=size),
    )


STATUS_FIELDS = ("angle", "calc", "domain")  # the order of the words in the status line


class CalculatorView:
    """The screen: title bar, history, entry line and the error dialog."""

    def __init__(
        self,
        state: AppState,
        theme: Theme = DARK,
        on_action: Callable[[str, str], None] = lambda action, arg: None,
        shift: Callable[[], bool] = lambda: False,
        on_setting: Callable[[str], None] = lambda name: None,
    ) -> None:
        self.state = state
        self.on_setting = on_setting
        self.theme = theme
        self.on_action = on_action
        self.shift = shift
        self._follow = False
        self.status = ft.Row(spacing=8, tight=True)
        self.title = ft.Text(size=12, color="#ffffff")
        # The entry line sits in the list with a blank line under it, so the end of the list always
        # leaves room below the entry. No animation: it lagged when the page was full.
        # A Column, not a ListView: it builds every line, so `scroll_to` can find a line by key
        # (Up selects a line to recall, and the view follows it).
        self.history = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            auto_scroll=True,
            auto_scroll_animation=ft.Animation(duration=0),
            spacing=2,
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
        size = self.state.px(12)
        self.status.controls = [
            self._status_field(word, size, number)
            for number, word in enumerate(screen.status.split())
        ]
        self.title.size = size
        self.entry.content = self._entry(screen)
        pairs = [
            self._pair(screen.lines[number], screen.lines[number + 1], number)
            for number in range(0, len(screen.lines) - 1, 2)
        ]
        picked = next((n for n, line in enumerate(screen.lines) if line.selected), None)
        self.history.controls = [
            ft.Container(height=self.state.px(6)),  # the first line is not cut off by the title bar
            *pairs,
            self.entry,
            ft.Container(height=self.state.px(ENTRY_ROOM)),
        ]
        # While a line is picked the view follows it; otherwise it stays at the entry line
        self.history.auto_scroll = picked is None
        self._follow = picked is not None
        self._error(screen)
        self._menu(screen.menu)

    def follow_selection(self) -> None:
        """Scroll the history to the picked line. Called after the page has been updated."""
        if self._follow and self.history.page is not None:
            self.history.page.run_task(self.history.scroll_to, scroll_key=_scroll_key())

    def _status_field(self, word: str, size: float, number: int) -> ft.Control:
        """One word of the status; angle, calculation mode and real/complex cycle when clicked."""
        text = ft.Text(word, size=size, color="#ffffff", weight=ft.FontWeight.BOLD)
        if number >= len(STATUS_FIELDS):
            return text
        name = STATUS_FIELDS[number]
        return ft.Container(text, on_click=lambda _: self.on_setting(name), ink=True, tooltip=name)

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
            self._hold,
        ).build(calculator.editor)

    def _click(self, path: Sequence[tuple[int, int]], pos: int) -> None:
        """A click in the entry: place the cursor, or extend the selection with shift held (the
        keyboard's Shift, or the keypad's shift key waiting for its next key)."""
        extend = self.shift() or self.state.pending == "shift"
        if extend:
            self.state.clear_pending()
        self.on_action("extend" if extend else "place", format_target(path, pos))

    def _hold(self, path: Sequence[tuple[int, int]], pos: int) -> None:
        """A long press: the touch screen's shift+click."""
        self.on_action("extend", format_target(path, pos))

    def _fits(self, entry: Line, result: Line) -> bool:
        """Whether an entry and its result are short enough to share a line. LaTeX cannot be
        measured here, so this counts characters (fractions, powers and roots weigh double)
        against the screen width, with room to spare."""

        def width(text: str) -> int:
            return len(text) + sum(text.count(char) for char in "/^√[")

        room = self.state.px(300) / (0.62 * self.state.math_size)
        return width(entry.text) + width(result.text) + 3 <= room

    def _pair(self, entry: Line, result: Line, number: int) -> ft.Control:
        """An entry and its result with a thin rule under them: one line if both are short."""
        first = self._line(entry, number)
        second = self._line(result, number + 1)
        if self._fits(entry, result):
            second.expand = True  # takes the rest of the line, result at the right edge
            body: ft.Control = ft.Row([first, second], spacing=0)
        else:
            body = ft.Column([first, second], spacing=0)
        rule = ft.BorderSide(1, "#40" + self.theme.screen_text[1:])
        return ft.Container(
            body, border=ft.Border(bottom=rule), padding=ft.Padding.only(bottom=self.state.px(2))
        )

    def _line(self, line: Line, number: int) -> ft.Container:
        """One history row. A picked row is highlighted as TI does: only the item, same size and
        place as before; once moved into, its own LaTeX draws the cursor and the selected part."""
        right = line.kind == "result"
        spec = f"{number // 2}:{line.kind}"  # history rows come in entry, result pairs
        shown = ft.Container(
            math(line.latex, self.theme, self.state.math_size),
            bgcolor=self.theme.selection if line.selected and not line.part else None,
        )
        return ft.Container(
            shown,
            on_click=lambda _: self.on_action("recall_at", spec),
            alignment=ft.Alignment.CENTER_RIGHT if right else ft.Alignment.CENTER_LEFT,
            padding=ft.Padding.only(left=6, right=6, top=self.state.px(3)),  # air above each line
            key=_scroll_key() if line.selected else None,
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
        step_x, step_y = (
            (px(MENU_W_WIDE) / 2, px(MENU_STEP_Y)) if wide else (px(22), px(MENU_STEP_Y))
        )
        panels = [
            ft.Container(
                self._panel(view, depth, panel, wide=wide),
                left=px(4)
                + (0 if panel.columns else depth * step_x),  # a wide grid stays on screen
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
        columns = panel.columns or 1
        shown = (
            MENU_ROWS_WIDE if wide else self._rows_that_fit(depth, panel, last=last, hint=view.hint)
        )
        lines = -(-len(panel.rows) // columns)  # rows of the list or the grid
        chosen = selected_index(panel) // columns
        start = max(0, min(chosen - shown // 2, lines - shown))
        window = range(start, min(lines, start + shown))
        items: list[ft.Control] = [self._header(view, depth, panel)]
        if start:
            items.append(self._more("▲", -shown * columns, active=last))
        if panel.columns:
            items.extend(self._grid_line(depth, panel, line, active=last) for line in window)
        else:
            items.extend(self._menu_row(depth, panel, n, wide=wide, active=last) for n in window)
        if window.stop < lines:
            items.append(self._more("▼", shown * columns, active=last))
        if last and view.hint and (not wide or panel.columns):
            items.append(
                ft.Container(
                    ft.Text(view.hint, size=px(10), color=theme.menu_hint, italic=True),
                    padding=ft.Padding.only(left=px(4), top=px(3), right=px(4)),
                    border=ft.Border.only(top=ft.BorderSide(1, theme.key_label)),
                )
            )
        box = ft.Container(
            ft.Column(items, spacing=0, tight=True),
            bgcolor=theme.title_bar,
            padding=px(4),
            border_radius=px(6),
            width=None if panel.columns else px(MENU_W_WIDE if wide else MENU_W),
            shadow=ft.BoxShadow(blur_radius=8, color="#80000000"),
            on_click=lambda _: None,  # a click between rows is not a click outside the menu
        )
        if not last:
            return box

        def wheel(
            event: ft.ScrollEvent,
        ) -> None:  # the mouse wheel moves the highlight, which scrolls
            self.on_action("menu_page", str((1 if event.scroll_delta.y > 0 else -1) * columns))

        return ft.GestureDetector(box, on_scroll=wheel)

    def _rows_that_fit(self, depth: int, panel: Panel, *, last: bool, hint: str) -> int:
        """How many lines of a handheld panel fit on the screen under it, leaving room for its
        header, the ▲ and ▼ rows and (on the deepest panel) the syntax hint."""
        height = LIST_ROW_H if not panel.columns else GRID_CELL - 3
        taken = TITLE_H + 4 + depth * MENU_STEP_Y + 4 + PANEL_PAD + HEADER_H + 2 * ARROW_H
        taken += HINT_H if last and hint else 0
        return max(3, int((SCREEN_H - taken) / height))

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
        """The ▲ or ▼ that says there is more above or below; a click pages that way."""
        return ft.Container(
            label_text(text, size=self.state.px(11), color=self.theme.accent),
            alignment=ft.Alignment.CENTER,
            height=self.state.px(ARROW_H),
            on_click=(lambda _: self.on_action("menu_page", str(step))) if active else None,
        )

    def _grid_line(self, depth: int, panel: Panel, line: int, *, active: bool) -> ft.Control:
        """One row of a grid menu (trig, templates, symbols): cells without keys."""
        first = line * panel.columns
        cells = [
            self._grid_cell(depth, n, panel.rows[n], active=active)
            for n in range(first, min(first + panel.columns, len(panel.rows)))
        ]
        return ft.Row(cells, spacing=self.state.px(1), tight=True)

    def _grid_cell(self, depth: int, index: int, row: Row, *, active: bool) -> ft.Control:
        theme, px = self.theme, self.state.px
        on = row.selected
        colour = theme.menu_disabled if not row.enabled else "#ffffff" if on else theme.key_text
        return ft.Container(
            label_text(
                row.label, size=px(12 if len(row.label) <= SHORT_CELL else 10), color=colour
            ),
            width=px(GRID_CELL),
            height=px(GRID_CELL - 4),
            alignment=ft.Alignment.CENTER,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            bgcolor=(theme.accent if active and row.enabled else theme.key) if on else None,
            border_radius=px(3),
            tooltip=row.hint or None,
            ink=True,
            on_click=lambda _: self.on_action("menu_pick", f"{depth}:{index}"),
        )

    def _menu_row(
        self, depth: int, panel: Panel, index: int, *, wide: bool, active: bool
    ) -> ft.Control:
        theme, px = self.theme, self.state.px
        row, keys = panel.rows[index], not panel.keyless
        on = row.selected
        colour = "#ffffff" if on else theme.key_text
        if not row.enabled:  # a placeholder keeps the device's numbering, greyed out
            colour = theme.menu_disabled
        parts: list[ft.Control] = [
            ft.Text(
                row.key if keys else "",
                size=px(12),
                color=colour if on or not row.enabled else theme.key_label,
                width=px(14) if keys else 0,
            ),
            label_text(row.label, size=px(12), color=colour, expand=True, no_wrap=True),
        ]
        if wide and row.hint:
            hint_colour = colour if on else theme.menu_hint
            parts.append(ft.Text(row.hint, size=px(11), color=hint_colour, no_wrap=True))
        if row.submenu:
            parts.append(label_text("▶", size=px(10), color=colour))
        return ft.Container(
            ft.Row(parts, spacing=px(4)),
            bgcolor=(theme.accent if active and row.enabled else theme.key) if on else None,
            padding=ft.Padding.symmetric(horizontal=px(4), vertical=px(1)),
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

    def __init__(
        self,
        state: AppState,
        on_key: Callable[[str], None],
        theme: Theme = DARK,
        install: Callable[[], None] | None = None,
    ) -> None:
        self.state = state
        self.on_key = on_key
        self.install = install  # set while the browser offers to install; None otherwise
        self.theme = theme
        self.control = ft.Column(spacing=KEY_GAP, tight=True)
        self._look: tuple[object, ...] | None = None
        self.refresh()

    def refresh(self) -> None:
        state = self.state
        # Everything that changes how a key looks. Rebuilding ~40 controls costs far more on a
        # phone than the unchanged diff, so an unchanged keypad is left alone.
        look = (
            id(state.keypad),
            state.pending,
            state.pad_scale,
            self.install is not None,
            self.theme,
        )
        if look == self._look:
            return
        self._look = look
        gap = self.state.kpx(KEY_GAP)
        self.control.spacing = gap
        keypad = self.state.keypad
        rows: list[ft.Control] = []
        for number, row in enumerate(keypad):
            keys = [self._key(key) for key in row]
            # Install takes the empty cell at the top right of the keypad, so it needs no row
            if number == 0 and self.install is not None and not row[-1].name:
                keys[-1] = self._install_key(row[-1])
            rows.append(ft.Row(keys, spacing=gap, tight=True))
        self.control.controls = rows

    def _install_key(self, cell: Key) -> ft.Control:
        install = self.install
        assert install is not None
        return ft.Container(
            label_text("Install", size=self.state.kpx(12), color="#ffffff"),
            width=self.state.kpx(key_span(cell.width)),
            height=self.state.kpx(key_span(cell.height, KEY_H)),
            alignment=ft.Alignment.CENTER,
            bgcolor=self.theme.accent,
            border_radius=self.state.kpx(7),
            ink=True,
            tooltip="Install CASSim",
            on_click=lambda _: install(),
        )

    def _key(self, key: Key) -> ft.Control:
        state, theme = self.state, self.theme
        width = state.kpx(key_span(key.width))
        height = state.kpx(key_span(key.height, KEY_H))
        if not key.name:
            return ft.Container(width=width, height=height)
        pending = state.pending
        layer = {"ctrl": key.ctrl, "shift": key.shift}.get(pending, "")
        fill, text = theme.key_colours(key.style)
        small = state.kpx(8 if key.width < 1 else 9)
        labels = ft.Row(
            [
                label_text(key.ctrl, size=small, color=theme.key_label, no_wrap=True),
                label_text(key.shift, size=small, color=theme.shift_label, no_wrap=True),
            ],
            spacing=state.kpx(3),
            alignment=ft.MainAxisAlignment.CENTER,
            tight=True,
        )
        main = label_text(
            layer or key.label,
            size=state.kpx(13 if key.height < 1 or key.width < 1 else 15),
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
            border_radius=height / 2 if key.style == "pad" else state.kpx(7),
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

    def __init__(
        self,
        state: AppState,
        on_change: Callable[[], None],
        theme: Theme = DARK,
        on_menu: Callable[[], None] | None = None,
    ) -> None:
        self.state = state
        self.on_change = on_change
        self.theme = theme
        self.on_menu = on_menu  # the large Menu button above the page list
        self.control = ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO)

    def refresh(self) -> None:
        document = self.state.document
        theme = self.theme
        here = (document.problem, document.page)
        rows: list[ft.Control] = []
        if self.on_menu is not None:
            menu = self.on_menu
            rows.append(
                ft.Container(
                    label_text("Menu", size=16, color="#ffffff"),
                    height=48,
                    alignment=ft.Alignment.CENTER,
                    bgcolor=theme.accent,
                    border_radius=8,
                    ink=True,
                    on_click=lambda _: menu(),
                )
            )
        rows += [
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
        dropdown(
            "Join conditions with",
            "logic",
            [("words", "and, or"), ("symbols", "∧, ∨")],
            current.logic,
        ),
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


def about_dialog(page: ft.Page) -> None:
    """About CASSim: disclaimer, privacy, licence, notices and versions (NFR-LEG-002, -003)."""

    def heading(text: str) -> ft.Text:
        return ft.Text(text, weight=ft.FontWeight.BOLD)

    notices = [ft.Text(f"{n.name}: {n.licence}, {n.use}", size=12) for n in about.NOTICES]
    body = ft.Column(
        [
            ft.Text(about.DISCLAIMER),
            heading("Privacy"),
            ft.Text(about.PRIVACY),
            heading("Licence"),
            ft.Text(about.LICENCE),
            ft.Text(about.SOURCE_URL, selectable=True),
            ft.Text(f"Help: {about.WIKI_URL}", selectable=True),
            heading("Third-party notices"),
            *notices,
            heading("Version"),
            ft.Text(about.build_info(), selectable=True, size=12),
        ],
        tight=True,
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
        width=420,
    )
    page.show_dialog(
        ft.AlertDialog(
            title=ft.Text("About CASSim"),
            content=body,
            actions=[ft.TextButton("OK", on_click=lambda _: page.pop_dialog())],
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

    zoom = ft.Slider(
        min=50, max=200, divisions=30, value=round(system.zoom * 100), label="{value}%", width=240
    )
    zoom_row = ft.Column([ft.Text("Zoom (everything on screen)"), zoom], spacing=0, tight=True)

    layouts = list(state.profile.keypads)
    letters = ft.Dropdown(
        label="Keypad letters",
        value=system.letters if system.letters in layouts else (layouts or [""])[0],
        options=[ft.DropdownOption(key=name, text=name) for name in layouts],
        width=240,
        visible=bool(layouts),
    )

    def apply() -> None:
        system.start_mode = Mode(start.value or system.start_mode)
        system.letters = letters.value or system.letters
        system.math_size = MATH_SIZES.get(size.value or "", system.math_size)
        system.zoom = round((zoom.value or 100) / 100, 2)
        page.pop_dialog()
        on_change()

    page.show_dialog(
        ft.AlertDialog(
            title=ft.Text("System Settings"),
            content=ft.Column([start, size, zoom_row, letters], tight=True, spacing=12),
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


type TextHandler = Callable[[ft.Event[ft.TextField]], None]


def field_box(
    field: Field, on_focus: TextHandler, on_submit: TextHandler, on_change: TextHandler | None
) -> ft.TextField | ft.Dropdown:
    """One box of a command dialog: a drop-down for a choice, else a text box."""
    if field.choices:
        return ft.Dropdown(
            label=field.label,
            value=field.default,
            options=[ft.DropdownOption(key=value, text=text) for value, text in field.choices],
            width=280,
        )
    return ft.TextField(
        label=field.label,
        value=field.default,
        width=280,
        dense=True,
        on_focus=on_focus,
        on_submit=on_submit,
        on_change=on_change,
    )


def wizard_dialog(
    page: ft.Page, state: AppState, wizard: Wizard, on_change: Callable[[], None]
) -> ft.AlertDialog:
    """A command's dialog (FR-CALC-005): a box per field, OK pastes the command. A field that
    will not do is reported in the dialog, which stays open.

    A live dialog (`wizard.calculate`, the Finance Solver) works out the box the cursor is in when
    Enter is pressed there or Calculate is clicked, and keeps the other values."""
    live = wizard.calculate
    boxes: dict[str, ft.TextField | ft.Dropdown] = {}
    extra: dict[str, str] = {}  # values the dialog keeps that have no box (the field solved last)
    focused = [""]  # the text box the cursor is in, or was in last

    def on_focus(name: str) -> Callable[[ft.Event[ft.TextField]], None]:
        def focus(_: ft.Event[ft.TextField]) -> None:
            focused[0] = name

        return focus

    copies = dict(wizard.copies)  # PpY sets CpY in the Finance Solver

    def copier(name: str) -> Callable[[ft.Event[ft.TextField]], None] | None:
        target = copies.get(name)
        if target is None:
            return None

        def copy(event: ft.Event[ft.TextField]) -> None:
            boxes[target].value = event.control.value
            boxes[target].update()

        return copy

    def on_submit(name: str) -> Callable[[ft.Event[ft.TextField]], None]:
        return lambda _: calculate(name) if live is not None else ok()

    for field in wizard.fields:
        boxes[field.name] = field_box(
            field, on_focus(field.name), on_submit(field.name), copier(field.name)
        )
    problems = ft.Text("", color="#ff8a80", size=12)

    def values() -> dict[str, str]:
        return {**extra, **{name: str(box.value or "") for name, box in boxes.items()}}

    def report(message: str) -> None:
        problems.value = message
        problems.update()

    def calculate(name: str) -> None:
        assert live is not None
        try:
            found = live(values(), name)
        except ValueError as error:
            report(str(error))
            return
        extra.update({key: value for key, value in found.items() if key not in boxes})
        for key in boxes.keys() & found.keys():
            boxes[key].value = found[key]
        report("")
        state.store_wizard(wizard, values())
        page.update()

    def ok() -> None:
        found = wizard.problems(values())
        if found:
            report("\n".join(found))
            return
        page.pop_dialog()
        state.finish_wizard(wizard, values())
        on_change()

    first = next((box for box in boxes.values() if isinstance(box, ft.TextField)), None)
    if first is not None:
        first.autofocus = True
    hint = (
        [ft.Text("Press ENTER in a box to calculate it.", size=12, italic=True)]
        if live is not None
        else []
    )
    actions: list[ft.Control] = [
        ft.TextButton("OK", on_click=lambda _: ok()),
        ft.TextButton("Cancel", on_click=lambda _: page.pop_dialog()),
    ]
    if live is not None:
        actions.insert(0, ft.TextButton("Calculate", on_click=lambda _: calculate(focused[0])))
    dialog = ft.AlertDialog(
        title=ft.Text(wizard.title),
        content=ft.Column([*hint, *boxes.values(), problems], tight=True, spacing=10),
        actions=actions,
    )
    page.show_dialog(dialog)
    return dialog
