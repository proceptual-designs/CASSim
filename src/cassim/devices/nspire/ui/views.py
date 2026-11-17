"""The Flet views (FR-DEV-002, FR-DEV-004, FR-DEV-006) over one `AppState`."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, cast

import flet as ft
import flet.canvas as cv

from cassim.app import scene_canvas
from cassim.app.theme import DARK, Theme
from cassim.app.warning import warning_mark
from cassim.core.results import latex_for_markdown
from cassim.core.settings import Angle, Ascii, Calc, Case, Domain, updated
from cassim.device.editor import format_target
from cassim.device.keys import Action
from cassim.device.menu import MenuView, Panel, Row
from cassim.device.pointer import Pointer
from cassim.device.wizard import Field, Wizard
from cassim.devices.nspire.pages.calculator import calculator_of
from cassim.devices.nspire.pages.spreadsheet import Spreadsheet
from cassim.devices.nspire.screen import Line, Screen, Tile
from cassim.devices.nspire.statistics_plot import p_value_scene
from cassim.devices.nspire.ui.entry import EntryLine
from cassim.devices.nspire.ui.layout import SCREEN_H
from cassim.devices.nspire.ui.sheet_view import SheetView
from cassim.devices.nspire.ui.state import MATH_SIZES, SORTER, AppState, Mode
from cassim.devices.nspire.ui.statistics_view import StatisticsView
from cassim.devices.nspire.ui.template_icons import HEIGHT as ICON_H
from cassim.devices.nspire.ui.template_icons import ICONS, Icon, Slot, Stroke
from cassim.devices.nspire.ui.template_icons import WIDTH as ICON_W

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


def icon_canvas(icon: Icon, scale: float, colour: str) -> cv.Canvas:
    """A template icon drawn at `scale` screen pixels per handheld pixel. Slots are thinner than
    the strokes, so the fixed parts of a template stand out from the places to type in."""

    def paint(width: float) -> ft.Paint:
        return ft.Paint(
            color=colour,
            stroke_width=width * scale,
            style=ft.PaintingStyle.STROKE,
            stroke_cap=ft.StrokeCap.ROUND,
            stroke_join=ft.StrokeJoin.ROUND,
        )

    shapes: list[cv.Shape] = []
    for shape in icon:
        if isinstance(shape, Stroke):
            (x, y), *rest = shape.points
            elements: list[cv.Path.PathElement] = [cv.Path.MoveTo(x * scale, y * scale)]
            elements.extend(cv.Path.LineTo(x * scale, y * scale) for x, y in rest)
            shapes.append(cv.Path(elements, paint=paint(1.1)))
        elif isinstance(shape, Slot):
            side = shape.side * scale
            shapes.append(cv.Rect(shape.x * scale, shape.y * scale, side, side, paint=paint(0.6)))
        else:
            shapes.append(
                cv.Text(
                    shape.x * scale,
                    shape.y * scale,
                    shape.text,
                    style=ft.TextStyle(size=shape.size * scale, color=colour, italic=shape.italic),
                    alignment=ft.Alignment.CENTER,
                )
            )
    return cv.Canvas(shapes, width=ICON_W * scale, height=ICON_H * scale)


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
DOC_NAME_WIDTH = 105  # handheld px reserved for the document name beside the page number
MENU_STEP_Y = 6  # each submenu sits this far lower than its parent


# The pointer's arrow in handheld pixels, tip at (0, 0): CASSim's own drawing
POINTER_SHAPE = ((0, 0), (0, 13), (3.5, 10), (6, 15.5), (8, 14.6), (5.6, 9.4), (10, 9.4))
POINTER_TICK = 1 / 30  # seconds between the pointer's moves


def pointer_mark(scale: float) -> ft.Container:
    """The pointer's arrow, hidden until the centre key moves it. Its tip is the place a click
    goes to; a short glide between steps keeps the motion smooth at a low step rate."""
    (x, y), *rest = POINTER_SHAPE
    outline: list[cv.Path.PathElement] = [cv.Path.MoveTo(x * scale, y * scale)]
    outline.extend(cv.Path.LineTo(x * scale, y * scale) for x, y in rest)
    outline.append(cv.Path.Close())
    canvas = cv.Canvas(
        [
            cv.Path(outline, paint=ft.Paint(color="#ffffff", style=ft.PaintingStyle.FILL)),
            cv.Path(
                outline,
                paint=ft.Paint(
                    color="#000000",
                    stroke_width=max(1.0, scale),
                    style=ft.PaintingStyle.STROKE,
                    stroke_join=ft.StrokeJoin.ROUND,
                ),
            ),
        ],
        width=11 * scale,
        height=16 * scale,
    )
    return ft.Container(
        canvas,
        left=0,
        top=0,
        visible=False,
        animate_position=ft.Animation(int(POINTER_TICK * 1000), ft.AnimationCurve.LINEAR),
    )


@dataclass(frozen=True)
class MenuBox:
    """Where one menu panel was drawn, in the body's pixels, and what its parts are: enough to
    turn a pointer click into the action a tap on that part sends."""

    depth: int
    left: float
    top: float
    width: float
    pad: float
    header: float
    arrow: float
    line: float  # a list row, or a grid line
    cell: float  # a grid cell and the space after it
    columns: int  # 0 for a list
    count: int  # rows (or cells) in the panel
    start: int  # the first line shown
    stop: int  # one past the last line shown
    lines: int
    step: int  # rows that ▲ and ▼ page by
    active: bool  # the deepest panel, the only one that pages
    back: str  # a submenu header's `menu_pick` target; "" on the top panel
    hint: float  # the hint line's height under the rows, or 0

    @property
    def shown(self) -> int:
        return self.stop - self.start

    @property
    def height(self) -> float:
        more = (self.start > 0) + (self.stop < self.lines)
        return 2 * self.pad + self.header + more * self.arrow + self.shown * self.line + self.hint

    def hit(self, x: float, y: float) -> tuple[Action, str] | None:
        """The action for a click at (`x`, `y`) inside this panel, or None for a dead part."""
        y -= self.top + self.pad
        up = self.arrow if self.start else 0.0
        rows = self.shown * self.line
        page = ("menu_page", str(self.step)) if self.active else None
        if y < 0:
            hit = None
        elif y < self.header:
            hit = ("menu_pick", self.back) if self.back else None
        elif y < self.header + up:
            hit = ("menu_page", str(-self.step)) if self.active else None
        elif y < self.header + up + rows:
            hit = self._row(x, int((y - self.header - up) // self.line))
        elif self.stop < self.lines and y < self.header + up + rows + self.arrow:
            hit = page
        else:
            hit = None
        return hit

    def _row(self, x: float, line: int) -> tuple[Action, str] | None:
        """A list row, or a grid cell found from `x`."""
        index = self.start + line
        if self.columns:
            column = int((x - self.left - self.pad) // self.cell)
            if not 0 <= column < self.columns:
                return None
            index = index * self.columns + column
        return ("menu_pick", f"{self.depth}:{index}") if index < self.count else None


def math(latex: str, theme: Theme, size: float = 20) -> ft.Markdown:
    """LaTeX drawn on the Flutter canvas (decision 0014)."""
    return ft.Markdown(
        f"${latex_for_markdown(latex)}$" if latex else " ",
        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
        fit_content=True,
        latex_style=ft.TextStyle(color=theme.screen_text, size=size),
    )


def window_start(line: int, lines: int, shown: int) -> int:
    """The first line a panel shows: the highlighted `line` is kept in the middle, except near
    the ends of the list."""
    return max(0, min(line - shown // 2, lines - shown))


def scroll_line(line: int, lines: int, shown: int, step: int) -> int:
    """Where the highlight goes so the window moves one line (`step` 1 down, -1 up). The
    highlight is first brought to the window's middle, since the window centres on it; at the
    end of the list it stops."""
    middle = window_start(line, lines, shown) + shown // 2
    target = max(line, middle) + 1 if step > 0 else min(line, middle) - 1
    return max(0, min(lines - 1, target))


class DragSteps:
    """Turns a vertical drag into whole-row steps: finger up (a negative delta) is a step down
    the list, as when a touch screen list follows the finger."""

    def __init__(self) -> None:
        self.travel = 0.0

    def reset(self) -> None:
        self.travel = 0.0

    def feed(self, delta: float, row: float) -> list[int]:
        """The steps (+1 down the list, -1 up) for a move of `delta` with rows `row` high."""
        self.travel += delta
        steps: list[int] = []
        while row > 0 and abs(self.travel) >= row:
            sign = 1 if self.travel > 0 else -1
            self.travel -= sign * row
            steps.append(-sign)
        return steps


STATUS_FIELDS = ("angle", "calc", "domain")  # the order of the words in the status line


STUB_NOTICE = "This page type is not built yet. CASSim has the Calculator page so far."
STUB_HELP = (
    "Doc > Insert adds a Calculator page; Doc > Page Layout > Delete Page removes this one; "
    "undo takes it away again."
)


class CalculatorView:
    """The screen: title bar, history, entry line and the error dialog."""

    def __init__(
        self,
        state: AppState,
        theme: Theme = DARK,
        on_action: Callable[[Action, str], None] = lambda action, arg: None,
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
        self.title = ft.Text(size=12, color=theme.title_text)
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
            on_scroll=self._scrolled,  # where it is scrolled to, for pointer clicks
        )
        self.entry = ft.Container(padding=ft.Padding.symmetric(horizontal=6, vertical=2))
        self.error = ft.Container(visible=False, alignment=ft.Alignment.CENTER, expand=True)
        self.menu = ft.Container(visible=False, alignment=ft.Alignment.TOP_LEFT, expand=True)
        # A one-finger drag on an open menu scrolls it (a CASSim touch feature; the device has
        # none). The detector wraps the lasting menu layer, so a drag outlives each redraw.
        self._drag = DragSteps()
        self._menu_view: MenuView | None = None
        self._boxes: list[MenuBox] = []  # where each open panel was drawn, for pointer clicks
        # While the pointer is in use the history reports its sizes (see `_measure`)
        self.measuring = False
        self._calculator_shown = False
        # history child (by identity: the entry line is the same control every redraw, and
        # Flet reports a size only when it changes) -> height
        self._heights: dict[int, float] = {}
        self._clicked = False  # the next pick came from a click: the line is in view already
        self._held: int | None = None  # the line a click picked, which the view does not follow
        self._keep: float | None = None  # the scroll offset when that click was made
        self._line_sizes: dict[str, tuple[float, float]] = {}  # "row:entry" -> width, height
        self._side_by_side: dict[int, bool] = {}  # history row -> entry and result on one line
        self._history_page: object | None = None
        self._history_rows: dict[
            int, tuple[tuple[Line, Line, float, float, Theme], ft.Control, bool]
        ] = {}
        self._scroll: float | None = None  # the history's scroll offset, once reported
        self._shown = 1  # lines the deepest open panel shows
        menu_layer = ft.GestureDetector(
            self.menu,
            on_vertical_drag_start=lambda _: self._drag.reset(),
            on_vertical_drag_update=self._drag_menu,
            on_vertical_drag_end=lambda _: self._drag.reset(),
        )
        # The page number and document name form one group on the left; settings stay right
        # (FR-DOC-010), leaving the centre clear for phone cutouts.
        self.doc_name = ft.Text(
            size=12,
            color=theme.title_text,
            no_wrap=True,
            overflow=ft.TextOverflow.ELLIPSIS,
            expand=True,
        )
        self.doc_box = ft.Container(
            self.doc_name,
            width=state.px(DOC_NAME_WIDTH),
        )
        page_number = ft.Container(
            self.title,
            on_click=lambda _: self.on_action("dialog", SORTER),
            ink=True,
            tooltip="Page Sorter",
        )
        title_bar = ft.Container(
            ft.Row(
                [
                    page_number,
                    self.doc_box,
                    ft.Container(expand=True),
                    self.status,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                expand=True,
            ),
            bgcolor=theme.title_bar,
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
        )
        # The Lists & Spreadsheet page draws here instead of the history (slice 3b)
        self.sheet_view = SheetView(theme, on_action, lambda: state.scale)
        self.statistics_view = StatisticsView(theme, on_action, lambda: state.scale)
        self.sheet_panes = ft.Row([], spacing=0, expand=True)
        self.pvalue_pane = ft.Container(expand=True)
        self.split_statistics_views: list[StatisticsView] = []
        self.body_size: Callable[[], tuple[float, float]] = lambda: (320.0, 200.0)  # set by the App
        body = ft.Column([self.history], expand=True, spacing=0)
        self.body = body
        # The pointer the keypad's centre key moves. Its place is in pixels of this layer, the
        # body's own frame under the title bar, which is also the sheet's frame.
        self._pointer_scale = state.px(1)
        self.pointer = pointer_mark(self._pointer_scale)
        self.control = ft.Container(
            ft.Column(
                [title_bar, ft.Stack([body, self.error, menu_layer, self.pointer], expand=True)],
                spacing=0,
            ),
            bgcolor=theme.screen,
            border_radius=6,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

    def refresh(self) -> None:
        screen = self.state.screen()
        self.title.value = screen.title
        size = self.state.px(12)
        self._refresh_status(screen.status, size)
        self.title.size = size
        self.set_doc_title(self.state.doc_title)
        self.doc_box.width = self.state.px(DOC_NAME_WIDTH)
        sheet = self.state.sheet
        self._prepare_history(screen)
        if sheet is not None and screen.sheet is not None:
            self._calculator_shown = False
            self._refresh_sheet(sheet)
            self._error(screen)
            self._menu(screen.menu)
            return
        if self._refresh_statistics(screen):
            return
        self.body.controls = [self.history]
        if screen.sorter is not None:  # the page sorter, in place of the page
            self.history.controls = [self._sorter_bar(), *map(self._sorter_row, screen.sorter)]
            self._calculator_shown = False
            self.history.auto_scroll = False
            self._follow = True  # the highlighted tile stays in view
            self._error(screen)
            self._menu(screen.menu)
            return

        if screen.stub is not None:  # a page type with nothing behind it yet
            self.history.controls = [stub_notice(screen.stub, self.theme, self.state.px)]
            self._calculator_shown = False
            self.history.auto_scroll = False
            self._follow = False
            self._error(screen)
            self._menu(screen.menu)
            return
        self.entry.content = self._entry(screen)
        self._side_by_side.clear()
        pairs = [
            self._history_pair(screen.lines[number], screen.lines[number + 1], number)
            for number in range(0, len(screen.lines) - 1, 2)
        ]
        self._history_rows = {
            n: row for n, row in self._history_rows.items() if n < len(screen.lines)
        }
        picked = next((n for n, line in enumerate(screen.lines) if line.selected), None)
        self.history.controls = [
            ft.Container(height=self.state.px(6)),  # the first line is not cut off by the title bar
            *pairs,
            self.entry,
            ft.Container(height=self.state.px(ENTRY_ROOM)),
        ]
        self._calculator_shown = True
        self._measure()
        # While a line is picked the view follows it; otherwise it stays at the entry line
        self.history.auto_scroll = picked is None
        if picked is None:  # the redraw takes the view to its end, which Flet may not report
            self._scroll = None
        # follow a picked line (Up, ctrl+7), but not one picked by a click: it is under the
        # finger or the pointer, and scrolling would move it away. A click is followed by more
        # than one redraw, so remember the line it picked until another line is picked.
        if self._clicked:
            self._clicked, self._held = False, picked
        elif picked != self._held:  # another line, or none: the click's line is let go
            self._held = self._keep = None
        self._follow = picked is not None and picked != self._held
        self._error(screen)
        self._menu(screen.menu)

    def _refresh_statistics(self, screen: Screen) -> bool:
        statistics = self.state.statistics
        if statistics is None:
            return False
        self._calculator_shown = False
        self.body.controls = [self.statistics_view.control]
        self.statistics_view.refresh(statistics, *self.body_size())
        self._follow = False
        self._error(screen)
        self._menu(screen.menu)
        return True

    def _refresh_sheet(self, sheet: Spreadsheet) -> None:
        width, height = self.body_size()
        if sheet.pvalue_plot is not None:
            pane_width = max((width - 1) / 2, 1)
            self.sheet_panes.controls = [self.sheet_view.control, self.pvalue_pane]
            self.sheet_view.refresh(sheet, pane_width, height)
            self.pvalue_pane.content = scene_canvas.canvas(
                p_value_scene(sheet.pvalue_plot, pane_width, height),
                {
                    "ink": self.theme.screen_text,
                    "axis": self.theme.sheet_axis,
                    "curve1": self.theme.accent,
                    "curve2": self.theme.selection,
                },
            )
        elif sheet.split_statistics:
            pane_width = max((width - 1) / 2, 1)
            self.sheet_view.refresh(sheet, pane_width, height)
            self.split_statistics_views = self.split_statistics_views[: len(sheet.split_statistics)]
            while len(self.split_statistics_views) < len(sheet.split_statistics):
                self.split_statistics_views.append(
                    StatisticsView(
                        self.theme, self._split_statistics_action, lambda: self.state.scale
                    )
                )
            panes = ft.Column([], spacing=0, expand=True)
            slot_height = height / len(sheet.split_statistics)
            for view, statistics in zip(
                self.split_statistics_views, sheet.split_statistics, strict=True
            ):
                view.refresh(statistics, pane_width, slot_height)
                panes.controls.append(ft.Container(view.control, expand=True))
            self.sheet_panes.controls = [self.sheet_view.control, panes]
        else:
            self.sheet_panes.controls = [self.sheet_view.control]
            self.sheet_view.refresh(sheet, width, height)
        self.body.controls = [self.sheet_panes]
        self._follow = False

    def _split_statistics_action(self, action: Action, arg: str) -> None:
        if action == "context_menu" or (action == "open_menu" and arg == "menu"):
            self.on_action("open_menu", "menu_statistics")
        else:
            self.on_action(action, arg)

    def _refresh_status(self, status: str, size: float) -> None:
        words = status.split()
        settings = [word for word in words if word != "CAPS"]
        self.status.controls = [
            *(
                [self._status_field("CAPS", size * 0.65, len(STATUS_FIELDS))]
                if "CAPS" in words
                else []
            ),
            *(self._status_field(word, size, number) for number, word in enumerate(settings)),
        ]

    def set_doc_title(self, title: str) -> None:
        """Append the unsaved marker to the displayed filename."""
        dirty = title.startswith("*")
        name = title[1:] if dirty else title
        self.doc_name.value = f"{name}*" if dirty else name
        self.doc_name.size = self.state.px(12)

    def _prepare_history(self, screen: Screen) -> None:
        page = self.state.document.current
        if (
            page is not self._history_page
            or self.measuring
            or screen.sorter is not None
            or screen.stub is not None
            or screen.sheet is not None
        ):
            self._history_rows.clear()
            self._history_page = page

    def _sorter_unit(self) -> float:
        """Pixels per sorter unit: the Handheld screen's scale, larger on the Computer screen."""
        return self.state.px(1) * (1.6 if self.state.mode is Mode.COMPUTER else 1)

    def _sorter_bar(self) -> ft.Control:
        """Move the highlighted page earlier or later, delete it, undo, redo, and close."""
        unit, theme, act = self._sorter_unit(), self.theme, self.on_action
        buttons = (
            (ft.Icons.ARROW_BACK, "Move page earlier", "move_page", "-1"),
            (ft.Icons.ARROW_FORWARD, "Move page later", "move_page", "1"),
            (ft.Icons.DELETE_OUTLINE, "Delete page (del)", "delete_page", ""),
            (ft.Icons.UNDO, "Undo (ctrl+Z)", "undo_pages", ""),
            (ft.Icons.REDO, "Redo (ctrl+Y)", "redo_pages", ""),
            (ft.Icons.CLOSE, "Close the sorter (enter or esc)", "dialog", SORTER),
        )
        return ft.Container(
            ft.Row(
                [
                    icon_chip(icon, tip, lambda a=a, g=g: act(a, g), theme, size=14 * unit)
                    for icon, tip, a, g in buttons
                ],
                spacing=4 * unit,
                wrap=True,
            ),
            padding=ft.Padding.only(left=4 * unit, top=4 * unit, right=4 * unit),
        )

    def _sorter_row(self, row: tuple[Tile, ...]) -> ft.Control:
        """One Problem: its name, then its pages as tiles."""
        unit, theme = self._sorter_unit(), self.theme
        return ft.Container(
            ft.Column(
                [
                    ft.Text(f"Problem {row[0].problem + 1}", size=9 * unit, color=theme.key_label),
                    ft.Row([self._tile(tile) for tile in row], spacing=4 * unit, wrap=True),
                ],
                spacing=2 * unit,
            ),
            padding=ft.Padding.symmetric(horizontal=4 * unit),
        )

    def _tile(self, tile: Tile) -> ft.Control:
        unit, theme = self._sorter_unit(), self.theme
        return ft.Container(
            ft.Column(
                [
                    ft.Text(
                        f"{tile.problem + 1}.{tile.page + 1}", size=8 * unit, color=theme.key_label
                    ),
                    *(
                        ft.Text(line, size=7 * unit, color=theme.screen_text, no_wrap=True)
                        for line in tile.lines
                    ),
                ],
                spacing=0,
            ),
            width=72 * unit,
            height=50 * unit,
            padding=3 * unit,
            bgcolor=theme.selection if tile.current else theme.screen,
            border=ft.Border.all(
                2 * unit if tile.current else 1, theme.accent if tile.current else theme.title_bar
            ),
            border_radius=4 * unit,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            key=_scroll_key() if tile.current else None,
            on_click=lambda _, t=tile: self.on_action("sorter_go", f"{t.problem}.{t.page}"),
        )

    def show_pointer(self, pointer: Pointer) -> None:
        """Put the arrow's tip at the pointer's place, or hide it."""
        mark = self.pointer
        scale = self.state.px(1)
        if pointer.visible and scale != self._pointer_scale:  # zoomed: redraw the arrow
            mark.content = pointer_mark(scale).content
            self._pointer_scale = scale
        mark.visible = pointer.visible
        mark.left, mark.top = pointer.x, pointer.y

    def click_at(self, x: float, y: float) -> bool:
        """A click by the keypad's pointer at (`x`, `y`) in the body's frame. Returns whether the
        page took it; a page that cannot place a click yet leaves it to the key's `select`.
        An open menu lies over the page and takes every click, as a tap would."""
        if self._menu_view is not None:
            hit = self.menu_click(x, y)
            if hit is not None:
                self.on_action(*hit)
            return True
        if self.state.sheet is not None and self.sheet_view.control in self.sheet_panes.controls:
            width, _ = self.body_size()
            split = self.state.sheet.pvalue_plot is not None or bool(
                self.state.sheet.split_statistics
            )
            pane_width = width / 2 if split else width
            if x <= pane_width:
                return self.sheet_view.click_at(x, y)
            if self.state.sheet.split_statistics:
                count = len(self.state.sheet.split_statistics)
                slot_height = self.body_size()[1] / count
                index = min(int(y / slot_height), count - 1)
                return self.split_statistics_views[index].click_at(
                    x - pane_width, y - index * slot_height
                )
            return True
        if self.state.statistics is not None and self.body.controls == [
            self.statistics_view.control
        ]:
            return self.statistics_view.click_at(x, y)
        return self.history_click(x, y)

    # ---- pointer clicks on the history: sizes reported by Flet while the pointer is in use --

    def _measure(self) -> None:
        """While the pointer is in use, ask Flet for the size of every history row and line, so
        a pointer click can find the row under it. Otherwise ask for nothing: each report is a
        message from the browser, too many to send on every key. The scroll offset is always
        followed (`_scrolled`): it is reported only while the history moves, and a redraw that
        scrolls to a picked line must not leave a stale offset behind."""
        here = {id(control) for control in self.history.controls}
        self._heights = {key: h for key, h in self._heights.items() if key in here}
        self._line_sizes.clear()
        on = self.measuring
        for control in self.history.controls:
            if isinstance(control, ft.LayoutControl):
                control.on_size_change = self._sized(control) if on else None

    def _sized(self, control: ft.Control) -> Callable[[ft.LayoutSizeChangeEvent], None]:
        key = id(control)

        def store(event: ft.LayoutSizeChangeEvent) -> None:
            self._heights[key] = event.height

        return store

    def _line_sized(self, spec: str) -> Callable[[ft.LayoutSizeChangeEvent], None]:
        def store(event: ft.LayoutSizeChangeEvent) -> None:
            self._line_sizes[spec] = (event.width, event.height)

        return store

    def _scrolled(self, event: ft.OnScrollEvent) -> None:
        self._scroll = event.pixels

    def history_click(self, x: float, y: float) -> bool:
        """A pointer click on the Calculator's history, as a tap there: a history line is picked
        (and a second click recalls it), and the entry line takes the cursor at its end. False
        when the page is not the Calculator or the sizes have not arrived yet."""
        controls = self.history.controls
        known = [self._heights.get(id(control)) for control in controls]
        if not self._calculator_shown or None in known:
            return False
        heights = [height or 0.0 for height in known]
        spacing = float(self.history.spacing or 0)
        content = sum(heights) + spacing * (len(heights) - 1)
        offset = self._scroll  # none yet: the history sits at its end, as it scrolls itself
        if offset is None:
            offset = max(0.0, content - self.body_size()[1])
        self._keep = offset  # where the view must stay if the click picks a line
        y += offset
        top = 0.0
        for index, height in enumerate(heights):
            if top <= y < top + height:
                return self._history_hit(index, x, y - top)
            top += height + spacing
        return True

    def _click_line(self, spec: str) -> None:
        """A tap on a history line picks it where it is, without scrolling."""
        self._clicked = True
        self._keep = self._scroll
        self.on_action("recall_at", spec)

    def _history_hit(self, index: int, x: float, y: float) -> bool:
        pairs = len(self._side_by_side)
        if 1 <= index <= pairs:
            row = index - 1
            entry = self._line_sizes.get(f"{row}:entry")
            if entry is None:
                return False
            width, height = entry
            in_entry = x < width if self._side_by_side[row] else y < height
            self._clicked = True
            self.on_action("recall_at", f"{row}:{'entry' if in_entry else 'result'}")
        elif index == pairs + 1:
            calculator = calculator_of(self.state.document.current)
            if calculator is not None:  # the end of the entry: the pointer cannot aim at a letter
                self.on_action("place", format_target([], len(calculator.editor.root)))
        return True

    def follow_selection(self) -> None:
        """Scroll the history to the picked line, or, for a line picked by a click, keep the
        view where it was: Flet resets the scroll position when the history stops keeping
        itself at its end, which is what picking a line does. Called after the page update."""
        keep = self._keep if self._held is not None and not self._follow else None
        if not self._follow and keep is None:
            return
        try:
            page = self.history.page
        except RuntimeError:  # not on a page yet (Flet raises rather than give None)
            return
        if keep is not None:
            self._scroll = keep
            page.run_task(self.history.scroll_to, offset=keep, duration=0)
        else:
            page.run_task(self.history.scroll_to, scroll_key=_scroll_key())

    def _status_field(self, word: str, size: float, number: int) -> ft.Control:
        """One word of the status; angle, calculation mode and real/complex cycle when clicked."""
        text = ft.Text(word, size=size, color=self.theme.title_text, weight=ft.FontWeight.BOLD)
        if number >= len(STATUS_FIELDS):
            return text
        name = STATUS_FIELDS[number]
        return ft.Container(text, on_click=lambda _: self.on_setting(name), ink=True, tooltip=name)

    def _entry(self, screen: Screen) -> ft.Control:
        """The entry line as clickable controls; a page without a calculator shows its LaTeX."""
        calculator = calculator_of(self.state.document.current)
        if calculator is None:
            return math(screen.entry, self.theme, self.state.math_size)
        return EntryLine(
            self.theme,
            self.state.math_size,
            self._click,
            calculator.session.is_defined,
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
        self._side_by_side[number // 2] = self._fits(entry, result)
        if self._fits(entry, result):
            second.expand = True  # takes the rest of the line, result at the right edge
            body: ft.Control = ft.Row([first, second], spacing=0)
        else:
            body = ft.Column([first, second], spacing=0)
        rule = ft.BorderSide(1, "#40" + self.theme.screen_text[1:])
        return ft.Container(
            body, border=ft.Border(bottom=rule), padding=ft.Padding.only(bottom=self.state.px(2))
        )

    def _history_pair(self, entry: Line, result: Line, number: int) -> ft.Control:
        if self.measuring:
            return self._pair(entry, result, number)
        key = (entry, result, self.state.scale, self.state.math_size, self.theme)
        old = self._history_rows.get(number)
        if old is not None and old[0] == key:
            self._side_by_side[number // 2] = old[2]
            return old[1]
        control = self._pair(entry, result, number)
        self._history_rows[number] = (key, control, self._side_by_side[number // 2])
        return control

    def _line(self, line: Line, number: int) -> ft.Container:
        """One history row. A picked row is highlighted as TI does: only the item, same size and
        place as before; once moved into, its own LaTeX draws the cursor and the selected part."""
        right = line.kind == "result"
        spec = f"{number // 2}:{line.kind}"  # history rows come in entry, result pairs
        shown: ft.Control = ft.Container(
            ft.Text(
                line.text,
                size=self.state.math_size,
                color=self.theme.screen_text,
                font_family="serif",
            )
            if line.error and not line.part
            else math(line.latex, self.theme, self.state.math_size),
            bgcolor=self.theme.selection if line.selected and not line.part else None,
        )
        if line.warnings:  # the triangle sits at the left of the entry (FR-CALC-007)
            mark = warning_mark(line.warnings, self.state.px(14))
            shown = ft.Row(
                [mark, shown],
                spacing=4,
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        return ft.Container(
            shown,
            on_click=lambda _: self._click_line(spec),
            on_size_change=self._line_sized(spec) if self.measuring else None,
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
        self._menu_view = view
        self._boxes = []
        if view is None:
            return
        wide = self.state.mode is Mode.COMPUTER
        px = self.state.px
        # Submenus overlap their parent by half (Computer) or nearly all of it (Handheld).
        step_x, step_y = (
            (px(MENU_W_WIDE) / 2, px(MENU_STEP_Y)) if wide else (px(22), px(MENU_STEP_Y))
        )
        places = [
            # a wide grid stays on screen
            (px(4) + (0 if panel.columns else depth * step_x), px(4) + depth * step_y)
            for depth, panel in enumerate(view.panels)
        ]
        panels = [
            ft.Container(
                self._panel(view, depth, panel, wide=wide, at=places[depth]),
                left=places[depth][0],
                top=places[depth][1],
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

    def _drag_menu(self, event: ft.DragUpdateEvent) -> None:
        """Scroll the deepest panel a row (a grid line) for each row's height the finger
        travels, so the list moves with the finger."""
        view = self._menu_view
        if view is None or not view.panels or event.primary_delta is None:
            return
        panel = view.panels[-1]
        row = self.state.px(GRID_CELL - 3 if panel.columns else LIST_ROW_H)
        for step in self._drag.feed(event.primary_delta, row):
            self._scroll_menu(panel, step)

    def _scroll_menu(self, panel: Panel, step: int) -> None:
        """Move the window a line down (`step` 1) or up (-1), taking the highlight with it."""
        columns = panel.columns or 1
        lines = -(-len(panel.rows) // columns)
        line = selected_index(panel) // columns
        moved = scroll_line(line, lines, self._shown, step)
        if moved != line:
            self.on_action("menu_page", str((moved - line) * columns))

    def menu_click(self, x: float, y: float) -> tuple[Action, str] | None:
        """What a click at (`x`, `y`) in the body's frame does to the open menu, worked out from
        the panels as drawn: pick a row, page with ▲ or ▼, go back with a submenu's header, or
        close the menu from outside it. None when no menu is open, or the click lands on a part
        of a panel that does nothing (its padding, the hint)."""
        if self._menu_view is None:
            return None
        for box in reversed(self._boxes):  # the deepest panel is drawn on top
            if box.left <= x < box.left + box.width and box.top <= y < box.top + box.height:
                return box.hit(x, y)
        return ("escape", "")

    def _panel(
        self,
        view: MenuView,
        depth: int,
        panel: Panel,
        *,
        wide: bool,
        at: tuple[float, float] = (0.0, 0.0),
    ) -> ft.Control:
        theme, px = self.theme, self.state.px
        last = depth == len(view.panels) - 1
        columns = panel.columns or 1
        shown = (
            MENU_ROWS_WIDE if wide else self._rows_that_fit(depth, panel, last=last, hint=view.hint)
        )
        lines = -(-len(panel.rows) // columns)  # rows of the list or the grid
        chosen = selected_index(panel) // columns
        start = window_start(chosen, lines, shown)
        if last:
            self._shown = shown
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
        hinted = last and view.hint and (not wide or panel.columns)
        pad, gap = px(4), px(1)
        self._boxes.append(
            MenuBox(
                depth=depth,
                left=at[0],
                top=at[1],
                width=2 * pad
                + (
                    columns * px(GRID_CELL) + (columns - 1) * gap
                    if panel.columns
                    else px(MENU_W_WIDE if wide else MENU_W) - 2 * pad
                ),
                pad=pad,
                header=px(HEADER_H),
                arrow=px(ARROW_H),
                line=px(GRID_CELL - 4) if panel.columns else px(LIST_ROW_H),
                cell=px(GRID_CELL) + gap,
                columns=panel.columns,
                count=len(panel.rows),
                start=start,
                stop=window.stop,
                lines=lines,
                step=shown * columns,
                active=last,
                back=f"{depth - 1}:{selected_index(view.panels[depth - 1])}" if depth else "",
                hint=px(HINT_H) if hinted else 0.0,
            )
        )
        if hinted:
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

        def wheel(event: ft.ScrollEvent) -> None:  # the mouse wheel scrolls, as a drag does
            self._scroll_menu(panel, 1 if event.scroll_delta.y > 0 else -1)

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
            padding=ft.Padding.symmetric(horizontal=self.state.px(4)),
            height=self.state.px(HEADER_H),  # fixed, so a pointer click can find the rows
            alignment=ft.Alignment.CENTER_LEFT,
            on_click=(lambda _: self.on_action("menu_pick", back)) if back else None,
        )

    def _more(self, text: str, step: int, *, active: bool) -> ft.Control:
        """The ▲ or ▼ that says there is more above or below; a click pages that way."""
        return ft.Container(
            label_text(text, size=self.state.px(11), color=self.theme.menu_accent),
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
        colour = (
            theme.menu_disabled if not row.enabled else theme.accent_text if on else theme.key_text
        )
        icon = ICONS.get(row.icon)
        return ft.Container(
            icon_canvas(icon, self.state.scale, colour)
            if icon
            else label_text(
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
        colour = theme.accent_text if on else theme.key_text
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
            padding=ft.Padding.symmetric(horizontal=px(4)),
            height=px(LIST_ROW_H),  # fixed, so a pointer click can find the row
            alignment=ft.Alignment.CENTER_LEFT,
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
                    ft.Text("click or press any key", size=self.state.px(11), color="#ffd0cc"),
                ],
                spacing=4,
                tight=True,
            ),
            bgcolor=self.theme.error,
            padding=12,
            border_radius=6,
            ink=True,
            on_click=lambda _: self.on_action("escape", ""),
        )


def stub_notice(name: str, theme: Theme, px: Callable[[float], float]) -> ft.Control:
    """What a page type without a model shows: its name and that it is still to be built."""
    return ft.Container(
        ft.Column(
            [
                label_text(name, size=px(18), color=theme.screen_text, weight=ft.FontWeight.BOLD),
                label_text(
                    STUB_NOTICE,
                    size=px(12),
                    color=theme.screen_text,
                    text_align=ft.TextAlign.CENTER,
                ),
                label_text(
                    STUB_HELP,
                    size=px(11),
                    color=theme.screen_text,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            spacing=px(8),
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=px(16), vertical=px(28)),
        alignment=ft.Alignment.CENTER,
    )


def icon_chip(
    icon: ft.IconData, tip: str, on_click: Callable[[], None], theme: Theme, *, size: float = 16
) -> ft.Control:
    """A small button with a standard icon, the same shape as a `chip`."""
    return ft.Container(
        ft.Icon(icon, size=size, color=theme.key_text),
        bgcolor=theme.key,
        padding=ft.Padding.symmetric(horizontal=size / 2, vertical=size / 4),
        border_radius=6,
        ink=True,
        tooltip=tip,
        on_click=lambda _: on_click(),
    )


def chip(text: str, on_click: Callable[[], None], theme: Theme, *, on: bool = False) -> ft.Control:
    """A small text button for toolbars."""
    return ft.Container(
        label_text(text, color=theme.accent_text if on else theme.key_text, size=13),
        bgcolor=theme.accent if on else theme.key,
        padding=ft.Padding.symmetric(horizontal=10, vertical=5),
        border_radius=6,
        ink=True,
        on_click=lambda _: on_click(),
    )


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


def system_settings_dialog(
    page: ft.Page,
    state: AppState,
    on_change: Callable[[], None],
    theme: Theme = DARK,
    on_appearance: Callable[[], None] | None = None,
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
    column_controls = ft.Checkbox(
        label="Show keyboard-accessible column controls",
        value=system.computer_column_controls,
    )

    def apply() -> None:
        system.start_mode = Mode(start.value or system.start_mode)
        system.letters = letters.value or system.letters
        system.math_size = MATH_SIZES.get(size.value or "", system.math_size)
        system.zoom = round((zoom.value or 100) / 100, 2)
        system.computer_column_controls = bool(column_controls.value)
        page.pop_dialog()
        on_change()

    page.show_dialog(
        ft.AlertDialog(
            title=ft.Text("System Settings"),
            content=ft.Column(
                [
                    start,
                    size,
                    zoom_row,
                    letters,
                    column_controls,
                    ft.TextButton("Appearance…", on_click=lambda _: on_appearance())
                    if on_appearance is not None
                    else ft.Container(),
                ],
                tight=True,
                spacing=12,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: page.pop_dialog()),
                ft.TextButton("OK", on_click=apply),
            ],
        )
    )


def selected_index(panel: Panel) -> int:
    return next((n for n, row in enumerate(panel.rows) if row.selected), 0)


type TextHandler = Callable[[ft.Event[ft.TextField]], None]
type WizardFieldControl = ft.TextField | ft.Dropdown | ft.Checkbox


def _wizard_value(box: WizardFieldControl) -> str:
    if isinstance(box, ft.Checkbox):
        return "1" if box.value else "0"
    return str(box.value or "")


def _set_wizard_value(box: WizardFieldControl, value: str, *, update: bool = False) -> None:
    if isinstance(box, ft.Checkbox):
        return
    box.value = value
    if update:
        box.update()


def field_box(
    field: Field, on_focus: TextHandler, on_submit: TextHandler, on_change: TextHandler | None
) -> WizardFieldControl:
    """One box of a command dialog: a drop-down for a choice, else a text box."""
    if field.toggle:
        return ft.Checkbox(label=field.label, value=field.default == "1")
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
    boxes: dict[str, WizardFieldControl] = {}
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
            _set_wizard_value(boxes[target], event.control.value, update=True)

        return copy

    def on_submit(name: str) -> Callable[[ft.Event[ft.TextField]], None]:
        return lambda _: calculate(name) if live is not None else ok()

    for field in wizard.fields:
        boxes[field.name] = field_box(
            field, on_focus(field.name), on_submit(field.name), copier(field.name)
        )
    problems = ft.Text("", color="#ff8a80", size=12)

    def values() -> dict[str, str]:
        return {**extra, **{name: _wizard_value(box) for name, box in boxes.items()}}

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
            _set_wizard_value(boxes[key], found[key])
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
