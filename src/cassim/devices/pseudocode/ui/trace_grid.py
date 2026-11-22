"""The trace table grid: resizable columns, shared by the trace pane and the call dialogs."""

from __future__ import annotations

import contextlib
from collections.abc import Callable

import flet as ft

LINE_COLUMN_WIDTH = 40
VARIABLE_COLUMN_WIDTH = 76
CONDITION_COLUMN_WIDTH = 130
OUTPUT_COLUMN_WIDTH = 140
ROW_HEIGHT = 38

# (key, title, default width): `__line__` is the fixed Line column, `__output__` Calcs / Output.
Column = tuple[str, str, float]


def _safe_update(control: ft.Control) -> None:
    with contextlib.suppress(RuntimeError):
        control.update()


class TraceGrid:
    """Draws a trace table whose columns resize by dragging the grip in their header.

    `widths` is kept between draws, so a resized column stays resized when the table is
    redrawn. A row in `calls` (row number -> step) is a call to a function defined in the
    code: its Calcs / Output cell has a button that calls `open_call` with the step."""

    def __init__(
        self,
        open_call: Callable[[int], None],
        widths: dict[str, float] | None = None,
    ) -> None:
        self.open_call = open_call
        self.widths: dict[str, float] = (
            widths
            if widths is not None
            else {"__line__": LINE_COLUMN_WIDTH, "__output__": OUTPUT_COLUMN_WIDTH}
        )
        self.active_columns: list[str] = []
        self.resize_controls: dict[str, list[ft.Container]] = {}
        self.container: ft.Container | None = None

    def build(
        self,
        columns: list[Column],
        rows: list[list[str]],
        calls: dict[int, int] | None = None,
    ) -> ft.Control:
        for key, _, default in columns:
            self.widths.setdefault(key, default)
        self.active_columns = [key for key, _, _ in columns]
        self.resize_controls = {key: [] for key in self.active_columns}
        headers = [self._header(key, title) for key, title, _ in columns]
        for (key, _, _), control in zip(columns, headers, strict=True):
            self.resize_controls[key].append(control)
        body_rows: list[ft.Control] = []
        calls = calls or {}
        for number, row in enumerate(rows):
            cells = [
                self._call_cell(key, value, calls[number])
                if key == "__output__" and number in calls
                else self._cell(key, value)
                for (key, _, _), value in zip(columns, row, strict=True)
            ]
            for (key, _, _), control in zip(columns, cells, strict=True):
                self.resize_controls[key].append(control)
            body_rows.append(ft.Row(list(cells), spacing=0, tight=True, height=ROW_HEIGHT))
        body = ft.Column(body_rows, scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)
        self.container = ft.Container(
            ft.Column([ft.Row(list(headers), spacing=0, tight=True), body], spacing=0, expand=True),
            width=sum(self.widths[key] for key, _, _ in columns),
            expand=True,
        )
        return ft.Row([self.container], scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)

    def resize(self, key: str, event: ft.DragUpdateEvent) -> None:
        if key == "__line__" or event.global_delta is None:
            return
        current = self.widths.get(key, VARIABLE_COLUMN_WIDTH)
        self.widths[key] = min(420, max(48, current + event.global_delta.x))
        for control in self.resize_controls.get(key, []):
            control.width = self.widths[key]
            _safe_update(control)
        if self.container is not None:
            self.container.width = sum(self.widths[column] for column in self.active_columns)
            _safe_update(self.container)

    def _header(self, key: str, title: str) -> ft.Container:
        width = self.widths[key]
        if key == "__line__":
            return ft.Container(
                ft.Text(
                    title,
                    weight=ft.FontWeight.BOLD,
                    size=12,
                    no_wrap=True,
                    text_align=ft.TextAlign.CENTER,
                ),
                width=LINE_COLUMN_WIDTH,
                height=ROW_HEIGHT,
                padding=0,
                border=ft.Border.all(1),
                alignment=ft.Alignment.CENTER,
            )

        def resize(event: ft.DragUpdateEvent) -> None:
            self.resize(key, event)

        grip = ft.GestureDetector(
            ft.Icon(ft.Icons.DRAG_INDICATOR, size=12),
            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
            on_horizontal_drag_update=resize,
            drag_interval=25,
            tooltip=f"Resize {title} column",
        )
        return ft.Container(
            ft.Row(
                [ft.Text(title, weight=ft.FontWeight.BOLD, size=12, expand=True), grip],
                tight=True,
                spacing=2,
            ),
            width=width,
            height=ROW_HEIGHT,
            padding=ft.Padding.symmetric(horizontal=6),
            border=ft.Border.all(1),
            alignment=ft.Alignment.CENTER_LEFT,
        )

    def _cell(self, key: str, value: str) -> ft.Container:
        return ft.Container(
            ft.Text(value, size=12, selectable=True, no_wrap=key == "__line__"),
            width=self.widths.get(key, VARIABLE_COLUMN_WIDTH),
            height=ROW_HEIGHT,
            padding=ft.Padding.symmetric(horizontal=6, vertical=4),
            border=ft.Border.all(1),
            alignment=ft.Alignment.CENTER_LEFT,
        )

    def _call_cell(self, key: str, value: str, call: int) -> ft.Container:
        """The call and a button that opens the call's own trace (FR-TRC-013)."""
        return ft.Container(
            ft.Row(
                [
                    ft.Text(value, size=12, selectable=True, expand=True),
                    ft.IconButton(
                        icon=ft.Icons.OPEN_IN_NEW,
                        icon_size=14,
                        width=28,
                        height=28,
                        padding=0,
                        tooltip=f"Expand {value}",
                        on_click=lambda _: self.open_call(call),
                    ),
                ],
                spacing=2,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=self.widths.get(key, OUTPUT_COLUMN_WIDTH),
            height=ROW_HEIGHT,
            padding=ft.Padding.only(left=6, right=2),
            border=ft.Border.all(1),
            alignment=ft.Alignment.CENTER_LEFT,
        )
