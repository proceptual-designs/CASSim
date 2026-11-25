"""The CASSim Scientific view: top bar, calculator and tutorial panel (SDD-14 section 5).

The calculator is drawn from the key table in `keys.py` and the screen model of `state.py`; this
module only draws them and passes keys on. It scales to the window, so the whole keypad fits on a
Chromebook screen, and the tutorial panel moves under the calculator when there is no room beside
it. Keys come from the mouse, touch or the computer keyboard (`keys.COMPUTER`).
"""

from __future__ import annotations

import asyncio
import contextlib
import dataclasses
import json
from typing import TYPE_CHECKING

import flet as ft

from cassim.app.keyboard import key_name
from cassim.devices.scientific import HELP_PAGE, examples, layouts
from cassim.devices.scientific import keys as k
from cassim.devices.scientific.examples import EXAMPLES, load_example
from cassim.devices.scientific.layouts import LAYOUTS, LAYOUTS_BY_ID, Cell, Layout, LKey
from cassim.devices.scientific.state import Display, DocumentFileError, ScientificState
from cassim.devices.scientific.tutorials import (
    SPEEDS,
    Lesson,
    TutorialMode,
    TutorialSession,
    expected_screens,
    lessons_for,
    wording,
)
from cassim.devices.scientific.ui.render import FALLBACK, FONT, FONTS, Renderer
from cassim.devices.scientific.ui.skins import SKIN_NAMES, SKINS, Skin

if TYPE_CHECKING:
    from cassim.app.shell import Shell

AUTOSAVE_KEY = "autosave"
PREFS_KEY = "prefs"
BASE_WIDTH = 360.0  # the calculator at scale 1
BAR_HEIGHT = 48.0
PANEL_WIDTH = 330.0
MIN_SCALE = 0.7
MAX_SCALE = 1.3
SAVE_DELAY = 0.6
FLASH_TIME = 0.12
DEMO_STEP = 2.0  # seconds per key at 1×: slow enough to talk through
DEMO_NEW_STEP = 2.0  # extra seconds before a new step, to read its instruction
# The legends above a key, as in the design mockup: 8 px bold, inset 2 px from the key's edges.
LEGEND_SIZE = 8.0
LEGEND_MIN = 6.5
LEGEND_INSET = 2.0
LEGEND_GAP = 3.0
LEGEND_ADVANCE = 0.62  # a generous average character width of the legend font, in em


def legend_font_size(shift: str, alpha: str, width: float, scale: float) -> float:
    """The legend text size that keeps both labels inside the key: the design size, shrunk only
    when the pair (ab/c⇔d/c and Y) would otherwise run past the key's edge."""
    room = width - 2 * LEGEND_INSET * scale - (LEGEND_GAP * scale if shift and alpha else 0)
    chars = len(shift) + len(alpha)
    if not chars:
        return LEGEND_SIZE * scale
    fitted = room / (chars * LEGEND_ADVANCE)
    return max(LEGEND_MIN * scale, min(LEGEND_SIZE * scale, fitted))


def ink_on(fill: str) -> str:
    """Near-black or white text, whichever reads better on `fill` (a #rrggbb colour)."""
    hex_ = fill.lstrip("#")[:6]
    if len(hex_) != 6:  # noqa: PLR2004
        return "#ffffff"
    r, g, b = (int(hex_[i : i + 2], 16) / 255 for i in (0, 2, 4))
    return "#111111" if 0.299 * r + 0.587 * g + 0.114 * b > 0.55 else "#ffffff"  # noqa: PLR2004


def _safe_update(control: ft.Control) -> None:
    with contextlib.suppress(RuntimeError, AssertionError):
        control.update()


def _shortcut_names() -> dict[str, str]:
    """For tooltips: the keyboard key that presses each keypad key on its own."""
    found: dict[str, str] = {}
    for name, binding in k.COMPUTER.items():
        presses = k.sequence(binding)
        if len(presses) == 1 and presses[0] not in found:
            found[presses[0]] = name.replace("ctrl+", "Ctrl+")
    return found


SHORTCUTS = _shortcut_names()


class ScientificApp:
    """The mounted CASSim Scientific app."""

    def __init__(self, shell: Shell) -> None:
        self.shell = shell
        self.page = shell.page
        self.state = ScientificState()
        self.skin_name = "Dark"
        self.scale = 1.0
        self.menu_visible = True
        self.panel_open = True
        self.doc_name = "Untitled"
        self.key_controls: dict[str, ft.Container] = {}
        self.completed: set[str] = set()
        self.speed = 1.0
        self.session: TutorialSession | None = None  # a lesson in progress
        self.lesson_index = 0
        self.tutorial_mode: TutorialMode = "guide"
        self.saved_before_lesson: dict[str, object] | None = None
        self.demo_run = 0  # bumped to stop a Show me playback
        self.save_pending = False
        self.feedback = ""
        self.feedback_ok = True
        self.layout: Layout = layouts.DEFAULT  # the calculator chosen in Appearance
        self.shown_layout: Layout = layouts.DEFAULT  # the keypad drawn (a lesson may differ)
        self.pending: list[str] = []  # SHIFT or ALPHA pressed, waiting for the next key
        self.pressed_faces: list[str] = []  # the keys a lesson has seen, as labelled
        self._build()

    @property
    def skin(self) -> Skin:
        return SKINS[self.skin_name]

    # ------------------------------------------------------------------------------------------
    # building
    # ------------------------------------------------------------------------------------------

    def _build(self) -> None:
        self.update_item = ft.MenuItemButton(
            content=getattr(self.shell, "update_label", "Check for updates"),
            on_click=lambda _: self.shell.activate_update(),
        )
        home = (
            [ft.MenuItemButton(content="Home", on_click=lambda _: self._home())]
            if self.shell.home is not None
            else []
        )
        self.cassim_menu = ft.SubmenuButton(
            content="CASSim",
            controls=[
                *home,
                ft.MenuItemButton(content="Settings…", on_click=lambda _: self.open_settings()),
                ft.MenuItemButton(content="Appearance…", on_click=lambda _: self.open_appearance()),
                ft.MenuItemButton(
                    content="Keyboard shortcuts…", on_click=lambda _: self.open_shortcuts()
                ),
                self.update_item,
                ft.MenuItemButton(
                    content="Help (wiki)…", on_click=lambda _: self.shell.help(HELP_PAGE)
                ),
                ft.MenuItemButton(content="About CASSim…", on_click=lambda _: self.shell.about()),
            ],
        )
        self.doc_menu = ft.SubmenuButton(
            content="Doc",
            controls=[
                ft.MenuItemButton(content="Open…", on_click=self.open_file),
                ft.MenuItemButton(content="Save", on_click=self.save_file),
                ft.MenuItemButton(content="Save as…", on_click=lambda _: self.save_file_as()),
                ft.MenuItemButton(content="Share link…", on_click=lambda _: self.open_share_link()),
                ft.SubmenuButton(
                    content="Examples",
                    controls=[
                        ft.MenuItemButton(
                            content=title, on_click=lambda _, i=index: self.load_example(i)
                        )
                        for index, (title, _) in enumerate(EXAMPLES)
                    ],
                ),
                ft.MenuItemButton(content="Reset all…", on_click=lambda _: self.confirm_reset()),
            ],
        )
        self.open_menus: set[str] = set()  # the keyboard drives an open menu, not the keypad
        for menu in (self.cassim_menu, self.doc_menu, *self.doc_menu.controls):
            if isinstance(menu, ft.SubmenuButton):
                name = str(menu.content)
                menu.on_open = lambda _, name=name: self.open_menus.add(name)
                menu.on_close = lambda _, name=name: self.open_menus.discard(name)
        self.mode_chip = self._chip("COMP", "Calculation mode: click for the MODE menu (Ctrl+M)")
        self.mode_chip.on_click = lambda _: self.on_key(k.MODE)
        self.angle_chip = self._chip("Deg", "Angle unit: click to change")
        self.angle_chip.on_click = lambda _: self.cycle_angle()
        self.io_chip = self._chip(
            "Math", "Natural display (Math) or linear (Line): click to change"
        )
        self.io_chip.on_click = lambda _: self.toggle_io()
        self.panel_button = ft.TextButton(
            "Tutorials",
            icon=ft.Icons.SCHOOL_OUTLINED,
            on_click=lambda _: self.toggle_panel(),
            tooltip="Show or hide the tutorials",
        )
        self.hide_button = ft.IconButton(
            icon=ft.Icons.FULLSCREEN,
            tooltip="Hide the menu bar for presenting (Esc brings it back)",
            on_click=lambda _: self.toggle_menu_bar(),
        )
        self.top_bar = ft.Container(
            ft.Row(
                [
                    ft.MenuBar(controls=[self.cassim_menu, self.doc_menu]),
                    self.mode_chip,
                    self.angle_chip,
                    self.io_chip,
                    ft.Container(expand=True),
                    self.panel_button,
                    self.hide_button,
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            height=BAR_HEIGHT,
        )
        self.restore_button = ft.Container(
            ft.IconButton(
                icon=ft.Icons.FULLSCREEN_EXIT,
                tooltip="Show the menu bar (Esc)",
                on_click=lambda _: self.toggle_menu_bar(),
            ),
            top=6,
            right=6,
            visible=False,
        )
        self.calculator = ft.Container()
        self.panel = ft.Container(width=PANEL_WIDTH)
        self.body = ft.Row(
            [self.calculator, self.panel],
            wrap=True,
            spacing=20,
            run_spacing=16,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
        self.content = ft.Column(
            [ft.Container(self.body, padding=12)],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.root = ft.Stack(
            [ft.Column([self.top_bar, self.content], expand=True, spacing=0), self.restore_button],
            expand=True,
        )

    def _chip(self, text: str, tooltip: str) -> ft.Container:
        return ft.Container(
            ft.Text(text, size=12, weight=ft.FontWeight.W_600),
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            border_radius=6,
            tooltip=tooltip,
            ink=False,  # not focusable: Tab and Enter must not land on it
        )

    # ---- the calculator ----

    def _build_calculator(self) -> None:
        s = self.scale
        skin = self.skin
        layout = self.shown_layout
        self.key_controls = {}
        inner = (BASE_WIDTH - 28) * s
        self.lcd = ft.Container(
            height=112 * s,
            bgcolor=skin.lcd,
            border_radius=8 * s,
            border=ft.Border.all(3 * s, skin.lcd_edge),
            padding=ft.Padding.symmetric(horizontal=8 * s, vertical=4 * s),
            width=inner,
        )
        rows: list[ft.Control] = [self._top_block(inner)]
        rows.extend(self._key_row(row, inner) for row in layout.rows)
        subtitle = "TWO-LINE DISPLAY" if layout.linear else "NATURAL DISPLAY"
        badge = ft.Row(
            [
                ft.Text(
                    f"CASSim Scientific ({layout.series})",
                    size=13 * s,
                    weight=ft.FontWeight.BOLD,
                    color=skin.badge,
                ),
                ft.Text(subtitle, size=9 * s, weight=ft.FontWeight.W_600, color=skin.badge_sub),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            width=inner,
        )
        self.calculator.content = ft.Column(
            [badge, self.lcd, ft.Container(height=4 * s), *rows],
            spacing=6 * s,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.calculator.width = BASE_WIDTH * s
        self.calculator.padding = 14 * s
        self.calculator.bgcolor = skin.chassis
        self.calculator.border_radius = 22 * s
        self.calculator.border = ft.Border.all(1.5, skin.chassis_edge)
        self.calculator.shadow = ft.BoxShadow(spread_radius=1, blur_radius=14, color="#00000066")

    def _colours(self, key: LKey) -> tuple[str, str]:  # noqa: PLR0911
        skin = self.skin
        match key.style:
            case "num":
                return skin.num
            case "nav":
                return skin.nav
            case "del":
                return skin.delete
            case "ac":
                return skin.clear
            case "eq":
                return skin.equals
            case "mod_shift":
                return (skin.fn[0], self._legend_colours()[0] if self._dark() else skin.shift_key)
            case "mod_alpha":
                return (skin.fn[0], self._legend_colours()[1] if self._dark() else skin.alpha_key)
        return skin.fn

    def _dark(self) -> bool:
        return self.skin_name != "Light"

    def _legend_colours(self) -> tuple[str, str]:
        """SHIFT's and ALPHA's legend colours: the layout's own on a dark body, else the theme's."""
        layout = self.shown_layout
        skin = self.skin
        if self._dark() and layout.shift_colour:
            return layout.shift_colour, layout.alpha_colour or skin.alpha
        return skin.shift, skin.alpha

    def _key(self, key: LKey, w: float, h: float, *, legends: bool = True) -> ft.Control:
        s = self.scale
        skin = self.skin
        layout = self.shown_layout
        fill, text = self._colours(key)
        shortcut = SHORTCUTS.get(key.plain[0]) if len(key.plain) == 1 else None
        tip = key.spoken + (f" (keyboard: {shortcut})" if shortcut else "")
        tip += "".join(
            f"\n{layer}: {label}"
            for layer, label in (
                (layout.shift_name, key.shift_label),
                (layout.alpha_name, key.alpha_label),
            )
            if label
        )
        face = ft.Container(
            ft.Text(
                key.face,
                size=(12 if len(key.face) > 3 else 14) * s,  # noqa: PLR2004
                weight=ft.FontWeight.W_600,
                color=text,
                no_wrap=True,
                font_family=FONT if key.style in ("num", "eq") else None,
                style=ft.TextStyle(font_family_fallback=FALLBACK),
            ),
            width=w,
            height=h,
            alignment=ft.Alignment.CENTER,
            bgcolor=fill,
            border_radius=7 * s,
            border=ft.Border.all(1, skin.key_edge),
            on_click=lambda _, pressed=key: self.on_layout_key(pressed),
            ink=False,  # not focusable: Tab and Enter must not land on it
            tooltip=tip,
        )
        self.key_controls[key.id] = face
        spoken = ft.Semantics(content=face, label=key.spoken, button=True)
        if not legends:
            return spoken
        shift_colour, alpha_colour = self._legend_colours()
        # As in the design mockup: SHIFT's legend at the key's left and ALPHA's at its right (a
        # lone legend at the left), inset from the edges, bold, and clipped there so nothing runs
        # into the next key.
        size = legend_font_size(key.shift_label, key.alpha_label, w, s)
        legend = ft.Container(
            ft.Row(
                [
                    ft.Text(
                        label,
                        size=size,
                        color=colour,
                        weight=ft.FontWeight.BOLD,
                        no_wrap=True,
                        style=ft.TextStyle(font_family_fallback=FALLBACK),
                    )
                    for label, colour in (
                        ((key.shift_label, shift_colour), (key.alpha_label, alpha_colour))
                        if key.shift_label
                        else ((key.alpha_label, alpha_colour), ("", shift_colour))
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                spacing=LEGEND_GAP * s,
                vertical_alignment=ft.CrossAxisAlignment.END,
            ),
            width=w,
            height=12 * s,
            padding=ft.Padding.symmetric(horizontal=LEGEND_INSET * s),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            alignment=ft.Alignment.BOTTOM_LEFT,
        )
        return ft.Column([legend, spoken], spacing=1 * s, tight=True)

    def _cells(self, cells: tuple[Cell, ...], width: float, height: float) -> ft.Row:
        """A row of keys sharing `width`; a key may span columns, and None leaves a gap."""
        s = self.scale
        gap = 5 * s
        units = sum(cell.span if cell is not None else 1 for cell in cells)
        unit = (width - gap * (units - 1)) / units
        controls: list[ft.Control] = []
        for cell in cells:
            if cell is None:
                controls.append(ft.Container(width=unit))
                continue
            w = unit * cell.span + gap * (cell.span - 1)
            controls.append(self._key(cell, w, height))
        return ft.Row(controls, spacing=gap, width=width, tight=True)

    def _key_row(self, row: tuple[Cell, ...], inner: float) -> ft.Row:
        return self._cells(row, inner, 34 * self.scale)

    def _dpad(self) -> ft.Column:
        s = self.scale
        nav_w, nav_h = 40 * s, 24 * s
        up, left, right, down = layouts.DPAD_KEYS
        return ft.Column(
            [
                self._key(up, nav_w, nav_h, legends=False),
                ft.Row(
                    [
                        self._key(left, nav_w, nav_h, legends=False),
                        ft.Container(width=14 * s),
                        self._key(right, nav_w, nav_h, legends=False),
                    ],
                    spacing=2 * s,
                    tight=True,
                ),
                self._key(down, nav_w, nav_h, legends=False),
            ],
            spacing=2 * s,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _top_block(self, inner: float) -> ft.Row:
        """The keys beside the D-pad: either side of it, or all to its left."""
        s = self.scale
        layout = self.shown_layout
        h = 30 * s
        dpad_w = 100 * s
        gap = 6 * s
        if layout.dpad == "right":
            side = inner - dpad_w - gap
            block = ft.Column(
                [self._cells(row, side, h) for row in layout.top], spacing=6 * s, tight=True
            )
            return ft.Row(
                [block, self._dpad()],
                width=inner,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        side = (inner - dpad_w) / 2 - gap
        left_rows, right_rows = [], []
        for row in layout.top:
            half = len(row) // 2
            left_rows.append(self._cells(row[:half], side, h))
            right_rows.append(self._cells(row[half:], side, h))
        return ft.Row(
            [
                ft.Column(left_rows, spacing=6 * s, tight=True),
                self._dpad(),
                ft.Column(right_rows, spacing=6 * s, tight=True),
            ],
            width=inner,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def layout_height(self) -> float:
        """The calculator's height at scale 1 for the shown layout."""
        layout = self.shown_layout
        top = max(len(layout.top) * 49.0 - 6, 76.0)
        rows = len(layout.rows) * 47.0
        gaps = 6.0 * (3 + len(layout.rows))
        return 18 + 112 + 4 + top + rows + gaps + 28

    # ---- the screen ----

    def _draw_lcd(self) -> None:
        s = self.scale
        skin = self.skin
        state = self.state
        shown = state.display()
        lit = state.annunciators()
        ink = skin.lcd_text
        width = (BASE_WIDTH - 28) * s - 22 * s
        renderer = Renderer(ink, ink)
        ann_names = ("S", "A", "M", "STO", "RCL", "STAT", "D", "R", "G", "FIX", "SCI", "Math")
        marks = {"S": self.shown_layout.shift_mark, "A": self.shown_layout.alpha_mark}
        annunciators = ft.Row(
            [
                ft.Text(
                    marks.get(name, name),
                    size=9 * s,
                    weight=ft.FontWeight.BOLD,
                    color=ink if lit.get(name) else skin.lcd_dim,
                )
                for name in ann_names
                if name not in ("D", "R", "G") or lit.get(name)
            ]
            + [
                ft.Container(expand=True),
                ft.Text("▲", size=9 * s, color=ink if lit["▲"] else skin.lcd_dim),
                ft.Text("▼", size=9 * s, color=ink if lit["▼"] else skin.lcd_dim),
            ],
            spacing=5 * s,
            height=12 * s,
        )
        body: ft.Control
        if shown.kind == "off":
            self.lcd.bgcolor = skin.lcd_dim
            self.lcd.content = None
            _safe_update(self.lcd)
            return
        self.lcd.bgcolor = skin.lcd
        if shown.kind == "menu":
            body = self._menu_body(shown, ink)
        elif shown.kind == "grid":
            body = self._grid_body(shown, renderer, width)
        elif shown.kind == "message":
            body = ft.Column(
                [
                    ft.Text(shown.title, size=15 * s, color=ink, font_family=FONT),
                    ft.Text(shown.footer, size=11 * s, color=ink, font_family=FONT),
                ],
                spacing=6 * s,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                expand=True,
            )
        else:
            title = (
                [ft.Text(shown.title, size=11 * s, color=ink, font_family=FONT)]
                if shown.title
                else []
            )
            body = ft.Column(
                [
                    *title,
                    ft.Container(
                        renderer.line(shown.input, 17 * s, width),
                        expand=True,
                        alignment=ft.Alignment.TOP_LEFT,
                    ),
                    ft.Container(
                        renderer.line(shown.result, 22 * s, width, keep="shrink"),
                        alignment=ft.Alignment.BOTTOM_RIGHT,
                    ),
                ],
                spacing=0,
                expand=True,
            )
        self.lcd.content = ft.Column([annunciators, body], spacing=2 * s, expand=True)
        _safe_update(self.lcd)

    def _menu_body(self, shown: Display, ink: str) -> ft.Control:
        s = self.scale
        options = list(shown.options)
        half = (len(options) + 1) // 2 if len(options) > 4 else len(options)  # noqa: PLR2004
        columns = [options[:half], options[half:]] if len(options) > 4 else [options]  # noqa: PLR2004
        size = (12 if len(options) > 6 else 13) * s  # noqa: PLR2004
        title = (
            [ft.Text(shown.title, size=12 * s, color=ink, font_family=FONT)] if shown.title else []
        )
        return ft.Column(
            [
                *title,
                ft.Row(
                    [
                        ft.Column(
                            [ft.Text(o, size=size, color=ink, font_family=FONT) for o in column],
                            spacing=0,
                            expand=True,
                        )
                        for column in columns
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    expand=True,
                ),
            ],
            spacing=2 * s,
            expand=True,
        )

    def _grid_body(self, shown: Display, renderer: Renderer, width: float) -> ft.Control:
        s = self.scale
        skin = self.skin
        ink = skin.lcd_text
        grid = shown.grid
        assert grid is not None
        size = 12 * s
        number_w = 18 * s
        cell_w = (width - number_w) / max(1, len(grid.headers))

        def cell(text: str, *, selected: bool, bold: bool = False) -> ft.Container:
            return ft.Container(
                ft.Text(
                    text,
                    size=size,
                    color=skin.lcd if selected else ink,
                    font_family=FONT,
                    no_wrap=True,
                    weight=ft.FontWeight.BOLD if bold else None,
                ),
                width=cell_w,
                bgcolor=skin.lcd_select if selected else None,
                alignment=ft.Alignment.CENTER_RIGHT,
                padding=ft.Padding.only(right=3 * s),
            )

        lines: list[ft.Control] = [
            ft.Row(
                [ft.Container(width=number_w)]
                + [cell(h, selected=False, bold=True) for h in grid.headers],
                spacing=0,
            )
        ]
        for index, row in enumerate(grid.rows):
            lines.append(
                ft.Row(
                    [
                        ft.Text(
                            str(grid.first_row + index),
                            size=10 * s,
                            color=ink,
                            width=number_w,
                            font_family=FONT,
                        )
                    ]
                    + [
                        cell(text, selected=grid.cursor == (index, col))
                        for col, text in enumerate(row)
                    ],
                    spacing=0,
                )
            )
        if shown.input:
            lines.append(
                ft.Container(
                    renderer.line(shown.input, 13 * s, width), alignment=ft.Alignment.CENTER_RIGHT
                )
            )
        return ft.Column(lines, spacing=0, expand=True)

    def _paint_keys(self) -> None:
        """Modifier keys light up while waiting; the tutorial's next key glows."""
        target = self._target_key()
        skin = self.skin
        shift_colour, alpha_colour = self._legend_colours()
        for key, face in self.key_controls.items():
            spec = self._layout_key(key)
            fill, text = self._colours(spec)
            if spec.plain == (k.SHIFT,) and self.state.shift:
                fill = shift_colour
                text = ink_on(fill)
            elif spec.plain == (k.ALPHA,) and self.state.alpha:
                fill = alpha_colour
                text = ink_on(fill)
            face.bgcolor = fill
            if isinstance(face.content, ft.Text):
                face.content.color = text  # a lit modifier's own name must stay readable
            if key == target:
                face.border = ft.Border.all(3 * self.scale, skin.target)
                face.shadow = ft.BoxShadow(spread_radius=1, blur_radius=10, color=skin.target)
            else:
                face.border = ft.Border.all(1, skin.key_edge)
                face.shadow = None
            _safe_update(face)

    def _paint_bar(self) -> None:
        skin = self.skin
        self.top_bar.bgcolor = skin.bar
        self.top_bar.border = ft.Border(bottom=ft.BorderSide(1, skin.chassis_edge))
        state = self.state
        for chip, text in (
            (self.mode_chip, state.mode),
            (self.angle_chip, {"DEG": "Deg", "RAD": "Rad", "GRA": "Gra"}[state.setup.angle]),
            (self.io_chip, "Math" if state.setup.input == "math" else "Line"),
        ):
            chip.bgcolor = skin.chip
            chip.border = ft.Border.all(1, "#4d5563")
            label = chip.content
            assert isinstance(label, ft.Text)
            label.value = text
            label.color = skin.bar_text
            _safe_update(chip)
        for item in (self.panel_button, self.hide_button):
            if isinstance(item, ft.IconButton):
                item.icon_color = skin.bar_text
            else:
                item.style = ft.ButtonStyle(color=skin.bar_text)
            _safe_update(item)
        _safe_update(self.top_bar)

    def refresh(self) -> None:
        if not self.key_controls:
            self.fit()  # builds the calculator, then refreshes
            return
        self._draw_lcd()
        self._paint_keys()
        self._paint_bar()
        self._draw_panel()

    # ------------------------------------------------------------------------------------------
    # start, stop, size
    # ------------------------------------------------------------------------------------------

    async def start(self, **_options: object) -> None:
        self.page.title = "CASSim Scientific"
        self.page.fonts = {**(self.page.fonts or {}), **FONTS}
        self.page.padding = 0
        self.page.on_keyboard_event = self.on_keyboard
        self.page.on_resize = lambda _: self.fit()
        self.shell.changed = self.on_bridge
        await self._load_prefs()
        await self._load_state()
        layout = self.layout
        self.state.use_layout(
            layout.modes, linear=layout.linear, dialect=layout.dialect, switch_display=False
        )
        self.page.controls.clear()
        self.page.add(self.root)
        self.apply_skin(self.skin_name, save=False)

    def unmount(self) -> None:
        self.demo_run += 1
        self.page.on_keyboard_event = None
        self.page.on_resize = None
        self.shell.changed = lambda: None
        self.page.controls.clear()

    def on_bridge(self) -> None:
        self.update_item.content = getattr(self.shell, "update_label", "Check for updates")
        _safe_update(self.update_item)

    def fit(self) -> None:
        """Scale the calculator so all of it fits the window (FR-FX-DSP-001)."""
        page_w = float(getattr(self.page, "width", 0) or 1200)
        page_h = float(getattr(self.page, "height", 0) or 800)
        bar = BAR_HEIGHT if self.menu_visible else 0
        tall = (page_h - bar - 32) / self.layout_height()
        wide = (page_w - 28) / BASE_WIDTH
        scale = max(MIN_SCALE, min(MAX_SCALE, tall, wide))
        if abs(scale - self.scale) > 0.02 or not self.key_controls:  # noqa: PLR2004
            self.scale = scale
            self._build_calculator()
        self.panel.width = min(PANEL_WIDTH, page_w - 28)
        self.body.width = page_w - 24  # a wrapping row needs a width to centre and to wrap in
        self.refresh()
        _safe_update(self.body)

    def apply_skin(self, name: str, *, save: bool = True) -> None:
        self.skin_name = name if name in SKINS else "Dark"
        skin = self.skin
        self.page.bgcolor = skin.page
        self.page.theme_mode = (
            ft.ThemeMode.LIGHT if self.skin_name == "Light" else ft.ThemeMode.DARK
        )
        self.key_controls = {}
        self.fit()
        _safe_update(self.page)
        if save:
            self._save_prefs()

    # ------------------------------------------------------------------------------------------
    # keys
    # ------------------------------------------------------------------------------------------

    def _layout_key(self, key_id: str) -> LKey:
        return self.shown_layout.key(key_id)

    def on_layout_key(self, key: LKey, *, from_demo: bool = False) -> None:
        """A key of the drawn keypad: it sends the canonical keys of the layer that is waiting."""
        state = self.state
        produced = layouts.press(
            key, shift=state.shift, alpha=state.alpha, waiting=state.sto or state.rcl
        )
        self._feed(produced, key, from_demo=from_demo)

    def on_key(self, key: str, *, from_demo: bool = False) -> None:
        """A canonical key, from the computer keyboard or a status chip."""
        drawn = next((c for c in self.shown_layout.all_keys() if c.plain == (key,)), None)
        self._feed([key], drawn, from_demo=from_demo)

    def _feed(self, produced: list[str], key: LKey | None, *, from_demo: bool) -> None:
        """Send canonical keys to the calculator; in Guide me, first check that they are what the
        lesson asks for (FR-FX-TUT-001 to -003). A SHIFT or ALPHA on its own waits for the next
        key, because what it means depends on that key."""
        self.open_menus.clear()  # any key that got here means no menu is open
        session = self.session
        effect = layouts.normalize(layouts.expand(tuple(self.pending + produced)))
        only_modifiers = bool(effect) and all(c in (k.SHIFT, k.ALPHA) for c in effect)
        if session is not None and not from_demo and self.tutorial_mode == "show":
            self.stop_demo()
        checking = (
            session is not None
            and not session.is_complete
            and (from_demo or self.tutorial_mode == "guide")
        )
        if checking and session is not None and not only_modifiers:
            expected = session.remaining_keys()[: len(effect)]
            if effect != expected and not from_demo:
                for modifier in self.pending:
                    self.state.press(modifier)  # cancel the waiting SHIFT or ALPHA
                self.pending = []
                target = self._target_face()
                self.feedback = (
                    f"Not that one. Press [{target}] to continue, or use Show me."
                    if target
                    else "Not that one: use Show me to see the next key."
                )
                self.feedback_ok = False
                self.refresh()
                return
            for canonical in effect:
                session.press(canonical)
            self.feedback, self.feedback_ok = "", True
        if key is not None:
            self.pressed_faces.append(key.face)
        for canonical in produced:
            self.state.press(canonical)
        self.pending = list(effect) if only_modifiers else []
        if not (self.state.shift or self.state.alpha):
            self.pending = []
        if session is not None and session.is_complete and self.tutorial_mode != "test":
            self._lesson_done()
        self.refresh()
        if key is not None:
            self._flash(key.id)
        self._schedule_save()

    def _flash(self, key: str) -> None:
        face = self.key_controls.get(key)
        if face is None:
            return
        face.opacity = 0.55
        _safe_update(face)

        async def restore() -> None:
            await asyncio.sleep(FLASH_TIME)
            face.opacity = 1.0
            _safe_update(face)

        self.page.run_task(restore)

    def _dialog_open(self) -> bool:
        """A dialog or a menu has the keyboard (Flet's open-dialog stack, read defensively)."""
        if self.open_menus:
            return True
        stack = getattr(self.page, "_dialogs", None)
        return any(getattr(d, "open", False) for d in getattr(stack, "controls", []) or [])

    def on_keyboard(self, event: ft.KeyboardEvent) -> None:
        if self._dialog_open():
            return
        raw = event.key
        if raw.startswith("Numpad ") and raw[-1].isdigit():
            raw = raw[-1]
        name = key_name(raw, shift=event.shift, ctrl=event.ctrl, alt=event.alt, meta=event.meta)
        if name is None:
            return
        if name == "Escape" and not self.menu_visible:
            self.toggle_menu_bar()
            return
        if name == "=" and self.state.mode == "VERIFY":
            self.on_key(k.REL_EQ)
            return
        binding = k.COMPUTER.get(name)
        if binding is None:
            return
        if binding.action == "copy":
            self.shell.copy(self.state.answer_text())
            return
        for key in k.sequence(binding):
            self.on_key(key)

    def cycle_angle(self) -> None:
        order = ("DEG", "RAD", "GRA")
        self.state.set_angle(order[(order.index(self.state.setup.angle) + 1) % 3])
        self.refresh()
        self._schedule_save()

    def toggle_io(self) -> None:
        setup = self.state.setup
        setup.input = "line" if setup.input == "math" else "math"
        setup.output = setup.input
        self.refresh()
        self._schedule_save()

    def toggle_menu_bar(self) -> None:
        self.menu_visible = not self.menu_visible
        self.top_bar.visible = self.menu_visible
        self.restore_button.visible = not self.menu_visible
        _safe_update(self.top_bar)
        _safe_update(self.restore_button)
        self.fit()

    def toggle_panel(self) -> None:
        self.panel_open = not self.panel_open
        self._draw_panel()
        self._save_prefs()

    def _home(self) -> None:
        if self.shell.home is not None:
            self.shell.home()

    # ------------------------------------------------------------------------------------------
    # tutorials (FR-FX-TUT-001 to -006)
    # ------------------------------------------------------------------------------------------

    def _panel_text(
        self, text: str, *, size: float = 13, muted: bool = False, bold: bool = False
    ) -> ft.Text:
        skin = self.skin
        return ft.Text(
            text,
            size=size,
            color=skin.panel_muted if muted else skin.panel_text,
            weight=ft.FontWeight.BOLD if bold else None,
            selectable=True,
        )

    def _draw_panel(self) -> None:
        skin = self.skin
        self.panel.visible = self.panel_open
        if not self.panel_open:
            _safe_update(self.panel)
            return
        lessons = self.lessons
        lesson = self.lesson
        picker = ft.Dropdown(
            value=lesson.id,
            options=[
                ft.DropdownOption(
                    key=item.id,
                    text=("✓ " if item.key in self.completed else "")
                    + f"{item.category}: {item.title}",
                )
                for item in lessons
            ],
            on_select=self._pick_lesson,
            width=self.panel.width - 32 if self.panel.width else PANEL_WIDTH - 32,
            dense=True,
            disabled=self.session is not None,
            text_style=ft.TextStyle(color=skin.panel_text, size=13),
        )
        modes = ft.Row(
            [
                self._mode_button("guide", "Guide me"),
                self._mode_button("show", "Show me"),
                self._mode_button("test", "Test me"),
            ],
            spacing=6,
        )
        controls: list[ft.Control] = [
            ft.Row(
                [
                    ft.Icon(ft.Icons.SCHOOL_OUTLINED, size=18, color=skin.target),
                    self._panel_text("Tutorials", size=15, bold=True),
                    ft.Container(expand=True),
                    self._panel_text(
                        f"{sum(item.key in self.completed for item in lessons)} of "
                        f"{len(lessons)} done",
                        size=11,
                        muted=True,
                    ),
                    ft.IconButton(
                        ft.Icons.CLOSE,
                        icon_size=16,
                        icon_color=skin.panel_muted,
                        tooltip="Hide the tutorials",
                        on_click=lambda _: self.toggle_panel(),
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            picker,
            modes,
        ]
        if self.tutorial_mode == "show":
            controls.append(
                ft.Row(
                    [self._panel_text("Speed", size=12, muted=True)]
                    + [self._speed_button(speed) for speed in SPEEDS],
                    spacing=4,
                )
            )
        session = self.session
        if session is None:
            controls.append(self._panel_text(lesson.problem))
            label = {"guide": "Start lesson", "show": "Play lesson", "test": "Start test"}
            controls.append(
                ft.Button(
                    label[self.tutorial_mode],
                    icon=ft.Icons.PLAY_ARROW,
                    on_click=lambda _: self.start_lesson(),
                )
            )
            controls.append(
                self._panel_text(
                    "Your calculation is put aside during a lesson and comes back when it ends.",
                    size=11,
                    muted=True,
                )
            )
        elif self.tutorial_mode == "test":
            controls.extend(
                [
                    self._panel_text("Your problem", size=12, muted=True, bold=True),
                    self._panel_text(lesson.challenge.prompt, bold=True),
                    self._panel_text(
                        "No keys are highlighted. Work it out, then check.", size=12, muted=True
                    ),
                    ft.Row(
                        [
                            ft.Button("Check my answer", on_click=lambda _: self.check_test()),
                            ft.TextButton("End test", on_click=lambda _: self.stop_lesson()),
                        ]
                    ),
                ]
            )
        else:
            controls.extend(self._step_controls(session))
        if self.feedback:
            controls.append(
                ft.Text(
                    self.feedback,
                    size=12,
                    color="#22c55e" if self.feedback_ok else "#f59e0b",
                    weight=ft.FontWeight.W_600,
                )
            )
        self.panel.content = ft.Column(controls, spacing=10, tight=True)
        self.panel.padding = 16
        self.panel.bgcolor = skin.panel
        self.panel.border = ft.Border.all(1, skin.panel_edge)
        self.panel.border_radius = 12
        _safe_update(self.panel)

    def _step_controls(self, session: TutorialSession) -> list[ft.Control]:
        skin = self.skin
        lesson = session.lesson
        layout = self.shown_layout
        total = len(lesson.steps)
        notes: list[ft.Control] = []
        if session.is_complete:
            answer = self.state.answer_text()
            body: list[ft.Control] = [
                *notes,
                self._panel_text("Lesson complete", size=15, bold=True),
                self._panel_text(f"Answer: {answer}" if answer else "All steps done."),
            ]
        else:
            step = session.current_step
            assert step is not None
            target = self._target_face() if self.tutorial_mode != "test" else ""
            body = [
                *notes,
                self._panel_text(f"Step {session.step_index + 1} of {total}", size=12, muted=True),
                self._panel_text(wording(step.instruction, layout), size=14, bold=True),
            ]
            if step.why:
                body.append(self._panel_text(wording(step.why, layout), size=12, muted=True))
            if target:
                body.append(
                    ft.Row(
                        [
                            self._panel_text("Next key", size=12, muted=True),
                            ft.Container(
                                ft.Text(
                                    target,
                                    size=13,
                                    color=skin.target,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                border=ft.Border.all(1.5, skin.target),
                                border_radius=6,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                            ),
                        ]
                    )
                )
        expected = session.expected_screen()
        body.extend(
            [
                self._panel_text("The screen should then show", size=12, muted=True),
                ft.Container(
                    ft.Text(
                        expected or "(an empty entry line)",
                        size=12,
                        color=skin.lcd_text,
                        font_family=FONT,
                    ),
                    bgcolor=skin.lcd,
                    padding=8,
                    border_radius=6,
                    width=PANEL_WIDTH - 32,
                ),
                self._panel_text(
                    "Keys so far: " + (" ".join(self.pressed_faces[-8:]) or "none"),
                    size=11,
                    muted=True,
                ),
                ft.Row(
                    [
                        ft.TextButton("Back", on_click=lambda _: self.lesson_back()),
                        ft.TextButton("Skip step", on_click=lambda _: self.lesson_skip()),
                        ft.TextButton("Restart", on_click=lambda _: self.start_lesson()),
                        ft.TextButton("End", on_click=lambda _: self.stop_lesson()),
                    ],
                    spacing=0,
                    wrap=True,
                ),
            ]
        )
        return body

    def _mode_button(self, mode: TutorialMode, label: str) -> ft.Control:
        skin = self.skin
        chosen = self.tutorial_mode == mode
        return ft.Container(
            ft.Text(label, size=12, color=skin.page if chosen else skin.panel_text),
            bgcolor=skin.target if chosen else None,
            border=ft.Border.all(1, skin.target),
            border_radius=14,
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            on_click=lambda _: self.set_tutorial_mode(mode),
            ink=False,  # not focusable: Tab and Enter must not land on it
            disabled=self.session is not None and not chosen,
        )

    def _speed_button(self, speed: float) -> ft.Control:
        skin = self.skin
        chosen = self.speed == speed
        return ft.Container(
            ft.Text(f"{speed:g}×", size=12, color=skin.page if chosen else skin.panel_text),
            bgcolor=skin.target if chosen else None,
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=8, vertical=2),
            on_click=lambda _: self.set_speed(speed),
            ink=False,  # not focusable: Tab and Enter must not land on it
        )

    def set_speed(self, speed: float) -> None:
        self.speed = speed
        self._draw_panel()
        self._save_prefs()

    def set_tutorial_mode(self, mode: TutorialMode) -> None:
        if self.session is not None:
            return
        self.tutorial_mode = mode
        self.feedback = ""
        self._draw_panel()

    def _pick_lesson(self, event: ft.Event[ft.Dropdown]) -> None:
        value = event.control.value
        for index, lesson in enumerate(self.lessons):
            if lesson.id == value:
                self.lesson_index = index
        self.feedback = ""
        self._draw_panel()

    @property
    def lessons(self) -> tuple[Lesson, ...]:
        """The chosen calculator's lessons, in its own keys."""
        return lessons_for(self.layout)

    @property
    def lesson(self) -> Lesson:
        lessons = self.lessons
        return lessons[min(self.lesson_index, len(lessons) - 1)]

    def start_lesson(self) -> None:
        """Put the student's calculation aside, set the calculator up and begin."""
        self.stop_demo()
        lesson = self.lesson
        if self.saved_before_lesson is None:
            self.saved_before_lesson = self.state.to_dict()
        lesson.prepare(self.state, test=self.tutorial_mode == "test")
        self.session = TutorialSession(lesson, mode=self.tutorial_mode)
        self.session._screens = expected_screens(lesson, self.shown_layout)
        self.pending = []
        self.pressed_faces = []
        self.feedback = ""
        self.refresh()
        if self.tutorial_mode == "show":
            self.page.run_task(self._play)

    def stop_lesson(self) -> None:
        self.stop_demo()
        self.session = None
        self.feedback = ""
        self.pending = []
        if self.saved_before_lesson is not None:
            with contextlib.suppress(DocumentFileError):
                self.state.from_dict(self.saved_before_lesson)
            self.saved_before_lesson = None
        self._show_layout(self.layout, switch_display=False)
        self.refresh()

    def _show_layout(self, layout: Layout, *, switch_display: bool = True) -> None:
        """Draw this layout's keypad and give the calculator its modes (and display)."""
        changed = layout is not self.shown_layout
        self.shown_layout = layout
        self.state.use_layout(
            layout.modes,
            linear=layout.linear,
            dialect=layout.dialect,
            switch_display=switch_display,
        )
        if changed:
            self.key_controls = {}
            self.fit()

    def _lesson_done(self) -> None:
        session = self.session
        if session is None:
            return
        if self.tutorial_mode == "guide":
            self.completed.add(session.lesson.key)
            self._save_prefs()
        self.feedback, self.feedback_ok = "Well done: every step is complete.", True

    def lesson_back(self) -> None:
        session = self.session
        if session is None:
            return
        self.stop_demo()
        session.back()
        self._replay_session()

    def lesson_skip(self) -> None:
        """Press the rest of this step's keys for the student."""
        session = self.session
        if session is None or session.is_complete:
            return
        step_index = session.step_index
        while not session.is_complete and session.step_index == step_index:
            key = session.target_key
            assert key is not None
            session.press(key)
            self.state.press(key)
        self.pending = []
        self.feedback = ""
        self.refresh()

    def _replay_session(self) -> None:
        session = self.session
        if session is None:
            return
        session.lesson.prepare(self.state)
        for key in session.keys_done():
            self.state.press(key)
        self.pending = []
        self.feedback = ""
        self.refresh()

    def stop_demo(self) -> None:
        self.demo_run += 1

    def _plan(self) -> list[layouts.Step]:
        session = self.session
        if session is None or session.is_complete:
            return []
        return layouts.plan(self.shown_layout, session.remaining_keys()) or []

    def _target_key(self) -> str | None:
        """The drawn key to press next (the one that glows), on the shown layout."""
        if self.session is None or self.tutorial_mode == "test":
            return None
        steps = self._plan()
        if not steps:
            return None
        presses = steps[0].presses
        if self.pending and len(presses) > 1:
            return presses[1].id  # SHIFT or ALPHA is already waiting
        return presses[0].id

    def _target_face(self) -> str:
        target = self._target_key()
        return self._layout_key(target).face if target else ""

    async def _play(self) -> None:
        """Show me: press the lesson's keys one by one on the shown keypad, each glowing first."""
        run = self.demo_run
        session = self.session
        while session is not None and not session.is_complete and run == self.demo_run:
            self.refresh()
            pause = DEMO_STEP + (DEMO_NEW_STEP if session.key_index == 0 else 0)
            await asyncio.sleep(pause / self.speed)
            if run != self.demo_run or self.session is not session:
                return
            target = self._target_key()
            if target is None:
                return
            self.on_layout_key(self._layout_key(target), from_demo=True)
        if session is not None and session.is_complete and run == self.demo_run:
            self.feedback, self.feedback_ok = "That is the whole lesson. Try Guide me next.", True
            self._draw_panel()

    def check_test(self) -> None:
        session = self.session
        if session is None:
            return
        challenge = session.lesson.challenge
        if challenge.check(self.state):
            self.completed.add(session.lesson.key)
            self._save_prefs()
            self.feedback, self.feedback_ok = "Correct. Well done.", True
        else:
            self.feedback = (
                f"Not yet. Check your keys and try again (the answer is {challenge.answer})."
            )
            self.feedback_ok = False
        self._draw_panel()

    # ------------------------------------------------------------------------------------------
    # storage, files and links (FR-FX-SHR-001 to -006)
    # ------------------------------------------------------------------------------------------

    def _schedule_save(self) -> None:
        if self.session is not None or self.save_pending:
            return  # a lesson never overwrites the student's own work
        self.save_pending = True

        async def save() -> None:
            await asyncio.sleep(SAVE_DELAY)
            self.save_pending = False
            if self.session is None:
                self.shell.write(AUTOSAVE_KEY, self.state.dumps(self.doc_name, compact=True))

        self.page.run_task(save)

    async def _load_state(self) -> None:
        route = self.shell.route or ""
        fragment = route.lstrip("/")
        if fragment.startswith("doc="):
            try:
                if self.state.open_fragment(fragment):
                    return
            except DocumentFileError as error:
                self.shell.notice("Share link", f"The link could not be opened: {error}.")
        saved = await self.shell.read(AUTOSAVE_KEY)
        if saved:
            try:
                self.doc_name = self.state.loads(saved)
            except DocumentFileError:
                self.state = ScientificState()

    async def _load_prefs(self) -> None:
        text = await self.shell.read(PREFS_KEY)
        if not text:
            return
        try:
            prefs = json.loads(text)
        except json.JSONDecodeError:
            return
        if not isinstance(prefs, dict):
            return
        if prefs.get("theme") in SKINS:
            self.skin_name = prefs["theme"]
        if prefs.get("layout") in LAYOUTS_BY_ID:
            self.layout = self.shown_layout = LAYOUTS_BY_ID[prefs["layout"]]
        done = prefs.get("completed")
        if isinstance(done, list):
            self.completed = {item for item in done if isinstance(item, str)}
        if isinstance(prefs.get("panel"), bool):
            self.panel_open = prefs["panel"]
        if prefs.get("speed") in SPEEDS:
            self.speed = prefs["speed"]

    def _save_prefs(self) -> None:
        self.shell.write(
            PREFS_KEY,
            json.dumps(
                {
                    "theme": self.skin_name,
                    "layout": self.layout.id,
                    "completed": sorted(self.completed),
                    "panel": self.panel_open,
                    "speed": self.speed,
                }
            ),
        )

    async def open_file(self, _: ft.Event[ft.MenuItemButton]) -> None:
        try:
            text = await self.shell.pick_file(("json",), "Open a calculation")
        except UnicodeDecodeError:
            self.shell.notice("Open", "That file is not a CASSim document.")
            return
        if text is None:
            return
        self.stop_lesson()
        trial = ScientificState()
        try:
            name = trial.loads(text)
        except DocumentFileError as error:
            self.shell.notice("Open", f"The file could not be opened: {error}.")
            return
        self.state.from_dict(trial.to_dict())
        self.doc_name = name
        self.refresh()
        self._schedule_save()

    async def save_file(self, _: object = None) -> None:
        await self.shell.save_file(
            f"{self.doc_name}.cassim.json", self.state.dumps(self.doc_name), "Save calculation"
        )

    def save_file_as(self) -> None:
        field = ft.TextField(label="Name", value=self.doc_name, autofocus=True)

        async def save(_: object) -> None:
            name = str(field.value or "").strip() or "Untitled"
            self.doc_name = name
            self.page.pop_dialog()
            await self.save_file()
            self._schedule_save()

        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Save as"),
                content=field,
                actions=[
                    ft.TextButton("Save", on_click=save),
                    ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog()),
                ],
            )
        )

    def open_share_link(self) -> None:
        try:
            url = self.shell.link(self.state.share_fragment(self.doc_name))
        except ValueError:
            self.shell.notice(
                "Share link",
                "This calculation is too big for a link. Use Doc ▸ Save and share the file.",
            )
            return

        def copy(_: object) -> None:
            self.shell.copy(url)
            self.page.pop_dialog()

        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Share link"),
                content=ft.Column(
                    [
                        ft.Text(
                            "Anyone who opens this link gets this calculator: its settings, "
                            "memories, STAT data and table. It stays in the link and is never "
                            "sent to a server.",
                            size=13,
                        ),
                        ft.TextField(value=url, read_only=True, dense=True, multiline=True),
                    ],
                    tight=True,
                    width=420,
                ),
                actions=[
                    ft.TextButton("Copy link", on_click=copy),
                    ft.TextButton("Close", on_click=lambda _: self.page.pop_dialog()),
                ],
            )
        )

    def load_example(self, index: int) -> None:
        self.stop_lesson()
        reason = examples.missing(index, self.layout)
        if reason:
            self.shell.notice("Examples", reason)
            return
        load_example(self.state, index)
        self.refresh()
        self._schedule_save()

    def confirm_reset(self) -> None:
        async def reset() -> None:
            self.stop_lesson()
            self.state.reset()
            self.doc_name = "Untitled"
            self.refresh()
            self._schedule_save()

        self.shell.confirm(
            "Reset all",
            "Clear every setting, memory, STAT data and the table? This cannot be undone.",
            "Reset",
            reset,
        )

    # ------------------------------------------------------------------------------------------
    # dialogs
    # ------------------------------------------------------------------------------------------

    def open_settings(self) -> None:
        """The SETUP choices as a form (FR-FX-CFG-001 to -005)."""
        setup = self.state.setup
        io = "line" if setup.input == "line" else ("math" if setup.output == "math" else "mathline")
        angle = ft.RadioGroup(
            ft.Row(
                [
                    ft.Radio(value=v, label=label)
                    for v, label in (("DEG", "Deg"), ("RAD", "Rad"), ("GRA", "Gra"))
                ]
            ),
            value=setup.angle,
        )
        display = ft.RadioGroup(
            ft.Column(
                [
                    ft.Radio(value="math", label="MthIO, MathO (natural input and answers)"),
                    ft.Radio(
                        value="mathline", label="MthIO, LineO (natural input, decimal answers)"
                    ),
                    ft.Radio(value="line", label="LineIO (all on one line)"),
                ],
                spacing=0,
            ),
            value=io,
        )
        number = ft.Dropdown(
            value=f"{setup.disp} {setup.digits}",
            options=[ft.DropdownOption(key=f"Norm {n}", text=f"Norm {n}") for n in (1, 2)]
            + [
                ft.DropdownOption(key=f"Fix {n}", text=f"Fix {n} (decimal places)")
                for n in range(10)
            ]
            + [
                ft.DropdownOption(key=f"Sci {n}", text=f"Sci {n} (significant figures)")
                for n in range(10)
            ],
            width=260,
            dense=True,
        )
        fraction = ft.RadioGroup(
            ft.Row(
                [
                    ft.Radio(value="d/c", label="d/c (improper)"),
                    ft.Radio(value="ab/c", label="a b/c (mixed)"),
                ]
            ),
            value=setup.fraction,
        )
        frequency = ft.Switch(label="STAT frequency column", value=setup.frequency)

        def apply(_: object) -> None:
            new = dataclasses.replace(setup)
            new.angle = "RAD" if angle.value == "RAD" else "GRA" if angle.value == "GRA" else "DEG"
            choice = display.value or "math"
            new.input = "line" if choice == "line" else "math"
            new.output = "math" if choice == "math" else "line"
            disp, digits = (number.value or "Norm 1").split()
            new.disp = "Fix" if disp == "Fix" else "Sci" if disp == "Sci" else "Norm"
            new.digits = int(digits)
            new.fraction = "ab/c" if fraction.value == "ab/c" else "d/c"
            self.state.set_frequency(on=bool(frequency.value))
            new.frequency = self.state.setup.frequency
            self.state.setup = new
            self.page.pop_dialog()
            self.refresh()
            self._schedule_save()

        def heading(text: str) -> ft.Text:
            return ft.Text(text, weight=ft.FontWeight.BOLD, size=13)

        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Calculator settings"),
                content=ft.Column(
                    [
                        heading("Angle unit"),
                        angle,
                        heading("Input and output"),
                        display,
                        heading("Number format"),
                        number,
                        heading("Fraction answers"),
                        fraction,
                        frequency,
                        ft.Text("These are the SETUP menu's choices (SHIFT then MODE).", size=12),
                    ],
                    tight=True,
                    spacing=6,
                    scroll=ft.ScrollMode.AUTO,
                    width=420,
                ),
                actions=[
                    ft.TextButton("Apply", on_click=apply),
                    ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog()),
                ],
            )
        )

    def open_appearance(self) -> None:
        """Appearance: the calculator whose keys to show (FR-FX-UI-005) and the colour theme."""
        calculator = ft.Dropdown(
            label="Calculator",
            value=self.layout.id,
            options=[ft.DropdownOption(key=layout.id, text=layout.title) for layout in LAYOUTS],
            width=320,
            dense=True,
        )
        choice = ft.RadioGroup(
            ft.Column(
                [ft.Radio(value=name, label=label) for name, label in SKIN_NAMES.items()],
                tight=True,
            ),
            value=self.skin_name,
        )

        def apply(_: object) -> None:
            self.page.pop_dialog()
            self.set_layout(calculator.value or layouts.DEFAULT.id, save=False)
            self.apply_skin(choice.value or "Dark")

        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Appearance"),
                content=ft.Column(
                    [
                        calculator,
                        ft.Text(
                            "The keys are named and arranged like that calculator's, so you can "
                            "find yours. CASSim Scientific works the same behind them; see Help "
                            "for what "
                            "each model does differently.",
                            size=12,
                        ),
                        ft.Text("Theme", weight=ft.FontWeight.BOLD, size=13),
                        choice,
                    ],
                    tight=True,
                    spacing=10,
                    width=360,
                ),
                actions=[
                    ft.TextButton("Apply", on_click=apply),
                    ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog()),
                ],
            )
        )

    def set_layout(self, layout_id: str, *, save: bool = True) -> None:
        """Show another calculator's keys. A lesson in progress ends first."""
        layout = LAYOUTS_BY_ID.get(layout_id, layouts.DEFAULT)
        if self.session is not None:
            self.stop_lesson()
        lesson_id = self.lesson.id
        self.layout = layout
        self.lesson_index = next(
            (i for i, lesson in enumerate(self.lessons) if lesson.id == lesson_id), 0
        )
        self.pending = []
        self._show_layout(layout)
        self.refresh()
        self._schedule_save()
        if save:
            self._save_prefs()

    def open_shortcuts(self) -> None:
        rows = [
            ft.Row(
                [
                    ft.Container(ft.Text(keys, weight=ft.FontWeight.BOLD, size=13), width=170),
                    ft.Text(what, size=13, expand=True),
                ],
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
            for keys, what in k.SHORTCUT_HELP
        ]
        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Keyboard shortcuts"),
                content=ft.Column(
                    [
                        *rows,
                        ft.Text(
                            "Hover over a key to see its own shortcut. The keypad works with a "
                            "mouse or touch as well.",
                            size=12,
                        ),
                    ],
                    tight=True,
                    spacing=4,
                    scroll=ft.ScrollMode.AUTO,
                    width=460,
                ),
                actions=[ft.TextButton("Close", on_click=lambda _: self.page.pop_dialog())],
            )
        )


def mount(shell: Shell) -> ScientificApp:
    return ScientificApp(shell)
