"""Function graph entry controls and scene rendering."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

import flet as ft

from cassim.app.scene_canvas import COLOURS, canvas
from cassim.app.theme import Theme
from cassim.device.editor import format_target
from cassim.device.keys import Action
from cassim.devices.nspire.pages.graphs import Graphs
from cassim.devices.nspire.ui.entry import EntryLine, row_height

_TOOLBAR_HEIGHT = 40
_FUNCTION_HEIGHT = 56
_ERROR_HEIGHT = 16
_CONTROL_SPACING = 2
_WHEEL_ZOOM_STEP = 600


class GraphsView:
    def __init__(
        self,
        theme: Theme,
        on_action: Callable[[Action, str], None],
        scale: Callable[[], float],
        math_size: Callable[[], float] | None = None,
        extend_click: Callable[[], bool] | None = None,
    ) -> None:
        self.theme = theme
        self.on_action = on_action
        self.scale = scale
        self.math_size = math_size if math_size is not None else lambda: 20 * self.scale()
        self.extend_click = extend_click if extend_click is not None else lambda: False
        self._width = 320.0
        self._height = 200.0
        self._plot_height = 100.0
        self._gesture_scale = 1.0
        self.functions = ft.Column(spacing=2)
        self.plot = ft.Container(expand=True, clip_behavior=ft.ClipBehavior.HARD_EDGE)
        self.toolbar = ft.Row(
            [
                ft.TextButton("Zoom +", on_click=lambda _: self._act("graphs_zoom", "0.5")),
                ft.TextButton("Zoom −", on_click=lambda _: self._act("graphs_zoom", "2")),
                ft.TextButton("Standard", on_click=lambda _: self._act("graphs_standard", "")),
            ],
            spacing=2,
            height=_TOOLBAR_HEIGHT,
        )
        self._plot_gestures = ft.GestureDetector(
            content=self.plot,
            on_scale_start=self._scale_start,
            on_scale_update=self._scale_update,
            on_scroll=self._scroll,
            drag_interval=16,
            expand=True,
        )
        self.control = ft.Column(
            [self.toolbar, self.functions, self._plot_gestures],
            spacing=2,
            expand=True,
        )

    def refresh(self, graphs: Graphs, width: float, height: float) -> None:
        self._width, self._height = max(width, 120), max(height, 100)
        scale = self.scale()
        self.toolbar.height = _TOOLBAR_HEIGHT * scale
        self.control.spacing = _CONTROL_SPACING * scale
        controls: list[ft.Control] = []
        function_heights: list[float] = []
        for index, entry in enumerate(graphs.functions):
            function_height = max(
                _FUNCTION_HEIGHT * scale,
                row_height(entry.editing.editor.root) * self.math_size() + 8 * scale,
            )
            function_heights.append(function_height)
            field = EntryLine(
                self.theme,
                self.math_size(),
                lambda path, pos, item=index: self._place(item, path, pos, self.extend_click()),
                graphs.session.is_defined,
                lambda path, pos, item=index: self._place(item, path, pos, True),
            ).build(entry.editing.editor, active=index == graphs.active_index)
            field_area = ft.GestureDetector(
                ft.Container(
                    ft.Row([field], scroll=ft.ScrollMode.AUTO),
                    height=function_height,
                    alignment=ft.Alignment.CENTER_LEFT,
                    bgcolor="#01ffffff",
                ),
                expand=True,
                on_tap=lambda _, item=index, editor=entry.editing.editor: self._place(
                    item, [], len(editor.root), self.extend_click()
                ),
                on_long_press_start=lambda _, item=index, editor=entry.editing.editor: self._place(
                    item, [], len(editor.root), True
                ),
            )
            controls.append(
                ft.Row(
                    [
                        ft.Text(f"{entry.name}(x) =", size=13 * scale),
                        field_area,
                        ft.TextButton(
                            "Plot",
                            on_click=lambda _, item=index: self._act("graphs_submit", str(item)),
                        ),
                        ft.TextButton(
                            "Hide" if entry.visible else "Show",
                            on_click=lambda _, name=entry.name: self._act("graphs_toggle", name),
                        ),
                    ],
                    spacing=2,
                    height=function_height,
                )
            )
            if entry.error:
                controls.append(
                    ft.Text(
                        entry.error,
                        size=11 * scale,
                        color=self.theme.error,
                        height=_ERROR_HEIGHT * scale,
                    )
                )
        self.functions.controls = controls
        self.functions.spacing = _CONTROL_SPACING * scale
        controls_height = (
            _TOOLBAR_HEIGHT + sum(bool(entry.error) * _ERROR_HEIGHT for entry in graphs.functions)
        ) * scale
        controls_height += sum(function_heights)
        controls_height += max(len(controls) - 1, 0) * _CONTROL_SPACING * scale
        controls_height += 2 * _CONTROL_SPACING * scale
        self._plot_height = max(self._height - controls_height, 100)
        colours = {
            **COLOURS,
            "ink": self.theme.screen_text,
            "axis": self.theme.sheet_axis,
            "grid": self.theme.sheet_grid,
        }
        self.plot.content = canvas(graphs.scene(self._width, self._plot_height), colours)

    def _place(self, index: int, path: Sequence[tuple[int, int]], pos: int, extend: bool) -> None:
        self._act("extend" if extend else "place", f"{index}:{format_target(path, pos)}")

    def _scale_start(self, _: ft.ScaleStartEvent) -> None:
        self._gesture_scale = 1.0

    def _scale_update(self, event: ft.ScaleUpdateEvent) -> None:
        if not math.isfinite(event.scale) or event.scale <= 0:
            return
        factor = self._gesture_scale / event.scale
        self._gesture_scale = event.scale
        delta = event.focal_point_delta
        self._gesture(
            delta.x, delta.y, factor, event.local_focal_point.x, event.local_focal_point.y
        )

    def _scroll(self, event: ft.ScrollEvent) -> None:
        delta = max(-_WHEEL_ZOOM_STEP, min(_WHEEL_ZOOM_STEP, event.scroll_delta.y))
        if delta == 0:
            return
        factor = math.exp(delta / _WHEEL_ZOOM_STEP)
        self._gesture(0, 0, factor, event.local_position.x, event.local_position.y)

    def _gesture(self, dx: float, dy: float, factor: float, x: float, y: float) -> None:
        if dx == 0 and dy == 0 and factor == 1:
            return
        values = (dx, dy, factor, x, y)
        argument = ",".join(format(value, ".17g") for value in values)
        self._act("graphs_gesture", argument)

    def _act(self, action: Action, argument: str) -> None:
        self.on_action(action, argument)
