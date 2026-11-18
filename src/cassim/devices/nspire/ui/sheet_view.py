"""The Lists & Spreadsheet page drawn with Flet (slice 3b): the grid, the bar and dialogs.

The grid is a `Scene` (`cassim.devices.nspire.sheet_scene`) on one canvas per layer. A refresh
rebuilds only the layers that changed, so a cursor move sends the cursor layer and no text
(spike A, decision 0031).

Touch first (decision 0031 item 7): a tap picks a cell (a row number picks the row, a column head
the name cell), a double tap edits, a long press or a right-click opens the context menu, a
one-finger drag scrolls and a mouse drag selects a block (run 2, E4), and the wheel scrolls.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import replace

import flet as ft
import flet.canvas as cv

from cassim.app.context_menu import context_menu_region
from cassim.app.scene_canvas import layer_shapes
from cassim.app.theme import Theme
from cassim.device.editor import Template, format_target
from cassim.device.keys import Action
from cassim.devices.nspire.pages.spreadsheet import Dialog, Spreadsheet
from cassim.devices.nspire.sheet_scene import ROW, cell_at, context_regions, fit, sheet_scene
from cassim.devices.nspire.ui.entry import EntryLine, row_height
from cassim.graph.scene import Layer

BAR = 22  # the bar under the grid, in the handheld's pixels


def sheet_colours(theme: Theme) -> dict[str, str]:
    """The scene's colour names for the screen the sheet sits on. The screen is light, so the
    scene's dark-theme defaults (light ink) would not show (fixed after slice 3b)."""
    return {
        "ink": theme.screen_text,
        "axis": theme.sheet_axis,
        "grid": theme.sheet_grid,
        "header": theme.sheet_header,
        "cursor": theme.accent,
        "selection": theme.selection,
        "edit": theme.sheet_edit,
    }


class SheetView:
    def __init__(
        self,
        theme: Theme,
        on_action: Callable[[Action, str], None],
        scale: Callable[[], float],
        click: Callable[[Sequence[tuple[int, int]], int], None] | None = None,
        hold: Callable[[Sequence[tuple[int, int]], int], None] | None = None,
    ) -> None:
        self.theme = theme
        self.colours = sheet_colours(theme)
        self.on_action = on_action
        self.scale = scale
        self.click = click or (lambda path, pos: on_action("place", format_target(path, pos)))
        self.hold = hold or (lambda path, pos: on_action("extend", format_target(path, pos)))
        self.shift: Callable[[], bool] = lambda: False
        self.sheet: Spreadsheet | None = None
        self._layers: dict[str, tuple[Layer, cv.Canvas]] = {}
        self._drag = 0.0  # pixels dragged and not yet turned into rows
        self._mouse = False  # the drag in progress is a mouse's: it selects
        self.grid = ft.Stack([], expand=True)
        self._context_regions = [context_menu_region(), context_menu_region()]
        detector = ft.GestureDetector(
            content=ft.Container(self.grid, expand=True),
            on_tap_down=self._tap,
            on_double_tap_down=self._double_tap,
            on_long_press_start=self._long_press,
            on_secondary_tap_down=self._secondary_tap,
            on_pan_start=self._pan_start,
            on_pan_update=self._pan,
            on_scroll=self._scroll,
            drag_interval=16,
            expand=True,
        )
        self.address = ft.Text("", color=theme.title_text, weight=ft.FontWeight.BOLD)
        self.entry = ft.Text("", color=theme.title_text, no_wrap=True, expand=True)
        self.entry_box = ft.Container(self.entry, expand=True, on_click=self._edit_bar)
        self.bar = ft.Container(
            ft.Row(
                [
                    self.address,
                    self.entry_box,
                ],
                spacing=8,
            ),
            bgcolor=theme.title_bar,
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
        )
        self.dialog = ft.Container(visible=False, alignment=ft.Alignment.CENTER, expand=True)
        self.control = ft.Column(
            [ft.Stack([detector, self.dialog], expand=True), self.bar], spacing=0, expand=True
        )

    # ---- drawing ---------------------------------------------------------------------------------

    def refresh(self, sheet: Spreadsheet, width: float, height: float) -> None:
        """Draw `sheet` in a body `width` by `height` (the bar included)."""
        self.sheet = sheet
        scale = self.scale()
        editor = sheet.editor
        bar_height = BAR * scale
        if editor and any(isinstance(node, Template) for node in editor.root):
            wanted = max(52, 16 + 16 * row_height(editor.root)) * scale
            bar_height = min(wanted, max(BAR * scale, height - ROW * scale))
        grid_height = max(height - bar_height, ROW * scale)
        rows, columns = fit(width, grid_height, sheet, scale)
        if (rows, columns) != (sheet.rows_shown, sheet.columns_shown):
            sheet.set_window(rows, columns)
            sheet.update()  # the window grew: ask for the cells now on show
        screen = sheet.screen()
        scene = sheet_scene(screen, scale, width, grid_height)
        canvases: list[ft.Control] = []
        for layer in scene.layers:
            kept = self._layers.get(layer.name)
            if kept is None or kept[0] != layer:
                shapes = layer_shapes(layer, self.colours)
                kept = (layer, cv.Canvas(shapes, width=width, height=grid_height))
                self._layers[layer.name] = kept
            canvases.append(kept[1])
        regions = context_regions(screen, scale, width, grid_height)
        for index, control in enumerate(self._context_regions):
            control.visible = index < len(regions)
            if control.visible:
                control.left, control.top, control.width, control.height = regions[index]
            canvases.append(control)
        self.grid.controls = canvases
        size = 12 * scale
        self.address.value, self.address.size = screen.address, size
        self.entry.value = screen.entry
        self.entry.size = size
        self.entry_box.content = (
            ft.Column(
                [
                    ft.Row(
                        [
                            EntryLine(
                                replace(self.theme, screen_text=self.theme.title_text),
                                size,
                                self.click,
                                sheet.session.is_defined,
                                self.hold,
                            ).build(editor)
                        ],
                        spacing=0,
                        scroll=ft.ScrollMode.AUTO,
                    )
                ],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
            )
            if editor is not None
            else self.entry
        )
        self.bar.height = bar_height
        self._show_dialog(screen.dialog, scale)

    def _show_dialog(self, dialog: Dialog | None, scale: float) -> None:
        self.dialog.visible = dialog is not None
        if dialog is None:
            return
        buttons: list[ft.Control] = [
            ft.TextButton("OK", on_click=lambda _: self.on_action("sheet_ok", ""))
        ]
        if dialog.cancel:
            buttons.append(
                ft.TextButton("Cancel", on_click=lambda _: self.on_action("sheet_cancel", ""))
            )
        self.dialog.content = ft.Container(
            ft.Column(
                [
                    ft.Text(dialog.title, size=14 * scale, weight=ft.FontWeight.BOLD),
                    ft.Text(dialog.message, size=13 * scale),
                    ft.Row(buttons, alignment=ft.MainAxisAlignment.END),
                ],
                spacing=6,
                tight=True,
            ),
            bgcolor=self.theme.error,
            padding=12,
            border_radius=6,
            width=280 * scale,
        )

    # ---- touch and mouse -------------------------------------------------------------------------

    def _edit_bar(self, _: object) -> None:
        self.on_action("sheet_bar", "")

    def _cell(self, x: float, y: float) -> tuple[int, int] | None:
        if self.sheet is None:
            return None
        return cell_at(x, y, self.sheet.screen(), self.scale())

    def _pick(self, position: ft.Offset | None, *, extend: bool = False) -> bool:
        """Put the cursor on the cell at `position`; a row number selects its row."""
        if position is None:
            return False
        cell = self._cell(position.x, position.y)
        if cell is None:
            return False
        column, row = cell
        if column < 0:
            self.on_action("sheet_tap", f"0,{row}")
            self.on_action("sheet", "select_row")
            return True
        self.on_action("sheet_tap", f"{column},{row}{',extend' if extend else ''}")
        return True

    def _tap(self, event: ft.TapEvent) -> None:
        self._pick(event.local_position, extend=self.shift())

    def click_at(self, x: float, y: float) -> bool:
        """A click by the keypad's pointer at (`x`, `y`) in the sheet's frame, as a tap there."""
        return self._pick(ft.Offset(x, y))

    def _double_tap(self, event: ft.TapEvent) -> None:
        if self.shift():
            self._pick(event.local_position, extend=True)
            return
        editing_formula = (
            self.sheet is not None
            and self.sheet.editing is not None
            and self.sheet.editing.startswith("=")
        )
        if self._pick(event.local_position) and not editing_formula:
            self.on_action("enter", "")

    def _long_press(self, event: ft.LongPressStartEvent) -> None:
        if self._pick(event.local_position):
            self.on_action("context_menu", "")

    def _secondary_tap(self, event: ft.TapEvent) -> None:
        if self._pick(event.local_position):
            self.on_action("context_menu", "")

    def _pan_start(self, event: ft.DragStartEvent) -> None:
        self._drag = 0.0
        self._mouse = event.kind == ft.PointerDeviceType.MOUSE
        if self._mouse:
            self._pick(event.local_position, extend=self.shift())

    def _pan(self, event: ft.DragUpdateEvent) -> None:
        if self._mouse:
            self._pick(event.local_position, extend=True)
            return
        delta = event.local_delta
        if delta is not None:
            self._scroll_by(-delta.y)

    def _scroll(self, event: ft.ScrollEvent) -> None:
        self._scroll_by(event.scroll_delta.y)

    def _scroll_by(self, pixels: float) -> None:
        """Scroll whole rows: the pixels add up until they make a row."""
        self._drag += pixels
        row = ROW * self.scale()
        rows = int(self._drag / row)
        if rows:
            self._drag -= rows * row
            self.on_action("sheet_drag", f"0,{rows}")
