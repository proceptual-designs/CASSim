"""Function graph entry controls and scene rendering."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

import flet as ft

from cassim.app.context_menu import context_menu_region
from cassim.app.scene_canvas import COLOURS, canvas
from cassim.app.theme import Theme
from cassim.core.results import latex_for_markdown
from cassim.device.editor import format_target
from cassim.device.keys import Action
from cassim.devices.nspire.pages.graphs import Graphs
from cassim.devices.nspire.ui.entry import EntryLine, row_height
from cassim.graph.sampling import Window

_FUNCTION_HEIGHT = 52
_ERROR_HEIGHT = 16
_CONTROL_SPACING = 2
_WHEEL_ZOOM_STEP = 600
_LABEL_MARGIN = 6
_LABEL_SIZE = 14
_CURVE_COLOURS = ("curve1", "curve2", "curve3", "curve4", "curve5", "curve6")


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
        self.functions = ft.Column(spacing=0)
        self.plot = ft.Container(expand=True, clip_behavior=ft.ClipBehavior.HARD_EDGE)
        self._context_region = context_menu_region()
        self._plot_gestures = ft.GestureDetector(
            content=self.plot,
            on_scale_start=self._scale_start,
            on_scale_update=self._scale_update,
            on_scroll=self._scroll,
            on_secondary_tap_down=self._context,
            on_long_press_start=self._context,
            drag_interval=16,
            expand=True,
        )
        self.control = ft.Column(
            [self.functions, self._plot_gestures],
            spacing=0,
            expand=True,
        )

    def refresh(self, graphs: Graphs, width: float, height: float) -> None:
        self._width, self._height = max(width, 120), max(height, 100)
        scale = self.scale()
        controls: list[ft.Control] = []
        controls_height = 0.0
        if graphs.functions:
            index = graphs.active_index
            entry = graphs.functions[index]
            function_height = max(
                _FUNCTION_HEIGHT * scale,
                row_height(entry.editing.editor.root) * self.math_size() + 8 * scale,
            )
            field = EntryLine(
                self.theme,
                self.math_size(),
                lambda path, pos: self._place(index, path, pos, self.extend_click()),
                graphs.session.is_defined,
                lambda path, pos: self._place(index, path, pos, True),
            ).build(entry.editing.editor, active=True)
            field_area = ft.GestureDetector(
                ft.Container(
                    ft.Row([field], scroll=ft.ScrollMode.AUTO),
                    height=function_height,
                    alignment=ft.Alignment.CENTER_LEFT,
                    bgcolor="#01ffffff",
                ),
                expand=True,
                on_tap=lambda _, editor=entry.editing.editor: self._place(
                    index, [], len(editor.root), self.extend_click()
                ),
                on_long_press_start=lambda _, editor=entry.editing.editor: self._place(
                    index, [], len(editor.root), True
                ),
            )
            controls.append(
                ft.Container(
                    ft.Row(
                        [
                            ft.Checkbox(
                                value=entry.visible,
                                on_change=lambda _, name=entry.name: self._act(
                                    "graphs_toggle", name
                                ),
                                fill_color=self.theme.accent,
                                check_color=self.theme.screen_text,
                                visual_density=ft.VisualDensity.COMPACT,
                                semantics_label=f"Show {entry.name}",
                            ),
                            ft.Text(
                                f"{entry.name}(x) =",
                                size=13 * scale,
                                weight=ft.FontWeight.BOLD,
                                color=self.theme.screen_text,
                                no_wrap=True,
                            ),
                            field_area,
                            ft.TextButton(
                                content=ft.Semantics(
                                    content=ft.Icon(
                                        ft.Icons.LIST,
                                        color=self.theme.menu_accent,
                                        size=20 * scale,
                                    ),
                                    label="Graph function history",
                                ),
                                tooltip="Graph function history",
                                style=ft.ButtonStyle(padding=ft.Padding.all(2 * scale)),
                                on_click=lambda _: self._act("open_menu", "graphs_history"),
                            ),
                        ],
                        spacing=2 * scale,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        height=function_height,
                    ),
                    border=ft.Border(bottom=ft.BorderSide(2 * scale, self.theme.accent)),
                    padding=ft.Padding.symmetric(horizontal=4 * scale),
                )
            )
            controls_height += function_height
            if entry.error:
                controls.append(
                    ft.Text(
                        entry.error,
                        size=11 * scale,
                        color=self.theme.error,
                        height=_ERROR_HEIGHT * scale,
                    )
                )
                controls_height += _ERROR_HEIGHT * scale
        self.functions.controls = controls
        self.functions.spacing = _CONTROL_SPACING * scale
        self._plot_height = max(self._height - controls_height, 100)
        scene = graphs.scene(self._width, self._plot_height)
        colours = {
            **COLOURS,
            "ink": self.theme.screen_text,
            "axis": self.theme.sheet_axis,
            "grid": self.theme.sheet_grid,
        }
        drawing = canvas(scene, colours)
        labels = self._curve_labels(graphs)
        self._context_region.visible = True
        self._context_region.left = 0
        self._context_region.top = 0
        self._context_region.width = self._width
        self._context_region.height = self._plot_height
        self.plot.content = ft.Stack(
            [drawing, *labels, self._context_region],
            width=self._width,
            height=self._plot_height,
        )

    def _curve_labels(self, graphs: Graphs) -> list[ft.Control]:
        labels: list[ft.Control] = []
        for index, entry in enumerate(graphs.functions):
            if not entry.visible or entry.compiled is None or not entry.latex:
                continue
            point = self._label_point(entry.compiled, graphs.window)
            if point is None:
                continue
            x, y = point
            colour_name = _CURVE_COLOURS[index % len(_CURVE_COLOURS)]
            colour = COLOURS.get(colour_name, self.theme.screen_text)
            latex = rf"\mathrm{{{entry.name}}}(x)={entry.latex}"
            labels.append(
                ft.Container(
                    ft.Markdown(
                        f"${latex_for_markdown(latex)}$",
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                        fit_content=True,
                        latex_style=ft.TextStyle(
                            size=_LABEL_SIZE * self.scale(),
                            color=colour,
                        ),
                    ),
                    left=max(
                        _LABEL_MARGIN,
                        min(x + 5 * self.scale(), self._width - 50 * self.scale()),
                    ),
                    top=max(_LABEL_MARGIN, min(y - 22 * self.scale(), self._plot_height - 24)),
                )
            )
        return labels

    def _label_point(
        self, function: Callable[[float], float], window: Window
    ) -> tuple[float, float] | None:
        fractions = (0.7, 0.6, 0.8, 0.5, 0.9, 0.4)
        for fraction in fractions:
            x = window.x_min + fraction * (window.x_max - window.x_min)
            try:
                value = function(x)
            except ArithmeticError, TypeError, ValueError:
                continue
            if not math.isfinite(value):
                continue
            point = window.to_screen(x, value, self._width, self._plot_height)
            if 0 <= point[1] <= self._plot_height:
                return point
        return None

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

    def _context(self, _: ft.TapEvent | ft.LongPressStartEvent) -> None:
        self._act("context_menu", "")

    def _gesture(self, dx: float, dy: float, factor: float, x: float, y: float) -> None:
        if dx == 0 and dy == 0 and factor == 1:
            return
        values = (dx, dy, factor, x, y)
        argument = ",".join(format(value, ".17g") for value in values)
        self._act("graphs_gesture", argument)

    def _act(self, action: Action, argument: str) -> None:
        self.on_action(action, argument)
