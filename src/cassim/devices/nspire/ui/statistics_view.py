"""The Data & Statistics page controls and scene renderer."""

from __future__ import annotations

import math
from collections.abc import Callable

import flet as ft
import flet.canvas as cv

from cassim.app.context_menu import context_menu_region
from cassim.app.scene_canvas import layer_shapes, scene_colours
from cassim.app.theme import Theme
from cassim.device.keys import Action
from cassim.devices.nspire.pages.statistics import Statistics
from cassim.graph.scene import Box, Dots, Fill, Label, Layer, Polyline
from cassim.stats.plots import PlottedPoint, PlotType

AXIS_LABEL_HEIGHT = 20
AXIS_HIT_MARGIN = 28
AXIS_VERTICAL_MARGIN = 8
POINT_HIT_RADIUS = 12
DRAG_MARKER_SIZE = 14
DRAG_MARKER_RADIUS = 7
WHEEL_ZOOM_STEP = 600  # scroll pixels for a zoom by a factor of e, as on a Graphs page


def statistics_colours(theme: Theme) -> dict[str, str]:
    return scene_colours(theme)


class StatisticsView:
    def __init__(
        self,
        theme: Theme,
        on_action: Callable[[Action, str], None],
        scale: Callable[[], float],
    ) -> None:
        self.theme = theme
        self.colours = statistics_colours(theme)
        self.on_action = on_action
        self.scale = scale
        self.statistics: Statistics | None = None
        self._layers: dict[str, tuple[Layer, cv.Canvas]] = {}
        self._width = 320.0
        self._height = 200.0
        self._chart_height = 180.0
        self._selected_point: int | None = None
        self._drag_index: int | None = None
        self._drag_value: tuple[float, float] | None = None
        self._pinch_scale: float | None = None  # while two fingers zoom, the last scale
        self.x_button = ft.TextButton(
            content=ft.Text("Click to add variable", size=11, no_wrap=True),
            style=ft.ButtonStyle(padding=0),
            on_click=lambda _: self._menu("statistics_x"),
        )
        self.y_button = ft.TextButton(
            content=ft.Text("Click to add variable", size=11, no_wrap=True),
            style=ft.ButtonStyle(padding=0),
            on_click=lambda _: self._menu("statistics_y"),
        )
        self._x_axis_gesture = ft.GestureDetector(
            content=self.x_button,
            on_secondary_tap_down=lambda _: self._axis_context("x"),
            on_long_press_start=lambda _: self._axis_context("x"),
            mouse_cursor=ft.MouseCursor.CONTEXT_MENU,
        )
        self._y_axis_gesture = ft.GestureDetector(
            content=self.y_button,
            on_secondary_tap_down=lambda _: self._axis_context("y"),
            on_long_press_start=lambda _: self._axis_context("y"),
            mouse_cursor=ft.MouseCursor.CONTEXT_MENU,
        )
        self.message = ft.Text("", size=11, color=theme.error)
        self.canvas = ft.Stack([], expand=True)
        self._context_region = context_menu_region()
        self._drag_marker = ft.Container(
            width=DRAG_MARKER_SIZE,
            height=DRAG_MARKER_SIZE,
            border=ft.Border.all(2, theme.accent),
            border_radius=7,
            bgcolor=ft.Colors.TRANSPARENT,
            visible=False,
        )
        self._plot_gestures = ft.GestureDetector(
            content=self.canvas,
            on_tap_down=self._tap,
            on_long_press_start=self._context,
            on_secondary_tap_down=self._context,
            # One pointer drags a point; two pinch to zoom (Flutter allows pan or scale, not both)
            on_scale_start=self._scale_start,
            on_scale_update=self._scale_update,
            on_scale_end=self._scale_end,
            on_scroll=self._scroll,
            drag_interval=16,
            exclude_from_semantics=True,
            expand=True,
        )
        self.plot_stack = ft.Stack(
            [
                self._plot_gestures,
                self._x_axis_gesture,
                self._y_axis_gesture,
                self._drag_marker,
            ],
            expand=True,
        )
        self.control = ft.Column(
            [
                self.plot_stack,
                ft.Container(self.message, padding=ft.Padding.symmetric(horizontal=6, vertical=2)),
            ],
            spacing=0,
            expand=True,
        )

    def refresh(self, statistics: Statistics, width: float, height: float) -> None:
        self.statistics = statistics
        scale = self.scale()
        self._width, self._height = max(width, 120), max(height, 100)
        self._chart_height = max(self._height - 18 * scale, 64 * scale)
        scene = statistics.scene(self._width, self._chart_height, axis_labels=False)
        controls: list[ft.Control] = []
        for layer in scene.layers:
            kept = self._layers.get(layer.name)
            if kept is None or kept[0] != layer:
                kept = (
                    layer,
                    cv.Canvas(
                        layer_shapes(layer, self.colours),
                        width=self._width,
                        height=self._chart_height,
                    ),
                )
                self._layers[layer.name] = kept
            controls.append(kept[1])

        self.x_button.content = ft.Text(
            statistics.x_name or "Click to add variable",
            size=11,
            no_wrap=True,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self._x_axis_gesture.width = min(200, self._width - 16)
        self._x_axis_gesture.height = AXIS_LABEL_HEIGHT
        self._x_axis_gesture.left = (self._width - self._x_axis_gesture.width) / 2
        self._x_axis_gesture.top = max(self._chart_height - AXIS_LABEL_HEIGHT, 0)
        self.x_button.width = self._x_axis_gesture.width
        self.x_button.height = AXIS_LABEL_HEIGHT

        label_length = min(max(self._chart_height - 24, 80), 180)
        self.y_button.content = ft.Text(
            statistics.y_name or "Click to add variable",
            size=11,
            no_wrap=True,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self._y_axis_gesture.width = label_length
        self._y_axis_gesture.height = AXIS_LABEL_HEIGHT
        self._y_axis_gesture.left = -(label_length - AXIS_LABEL_HEIGHT) / 2
        self._y_axis_gesture.top = (self._chart_height - AXIS_LABEL_HEIGHT) / 2
        self._y_axis_gesture.rotate = ft.Rotate(angle=-math.pi / 2)
        self.y_button.width = label_length
        self.y_button.height = AXIS_LABEL_HEIGHT

        self._context_region.visible = True
        self._context_region.left = 0
        self._context_region.top = 0
        self._context_region.width = self._width
        self._context_region.height = self._chart_height
        controls.append(self._context_region)

        selected = next(
            (
                point
                for point in statistics.plotted_points(self._width, self._chart_height)
                if point.index == self._selected_point
            ),
            None,
        )
        self._drag_marker.visible = selected is not None
        if selected is not None:
            self._drag_marker.left = selected.screen_x - DRAG_MARKER_RADIUS
            self._drag_marker.top = selected.screen_y - DRAG_MARKER_RADIUS
        self.canvas.controls = controls
        self.message.value = statistics.message

    def click_at(self, x: float, y: float) -> bool:
        """Route axis labels and data points; the device pointer uses the same hit testing."""
        target = self._axis_target(x, y)
        if target == "x":
            self._menu("statistics_x")
        elif target == "y":
            self._menu("statistics_y")
        else:
            point = self._point_at(x, y)
            if point is not None:
                self._select_point(point.index, point.x, point.y)
                self.on_action("statistics_point", str(point.index))
            elif self._visual_point_at(x, y):
                if self.statistics is not None:
                    self.statistics.message = "Selected data point"
                self.on_action("statistics_point", "")
            elif self.statistics is not None:  # a click on nothing clears the selection
                self.statistics.select(None)
                self._selected_point = None
        return True

    def _menu(self, name: str) -> None:
        self.on_action("open_menu", name)

    def _axis_context(self, axis: str) -> None:
        self.on_action("context_menu", f"statistics_context_{axis}")

    def _axis_target(self, x: float, y: float) -> str:
        if x <= AXIS_HIT_MARGIN and AXIS_VERTICAL_MARGIN <= y <= (
            self._chart_height - AXIS_VERTICAL_MARGIN
        ):
            return "y"
        if y >= self._chart_height - AXIS_LABEL_HEIGHT and abs(x - self._width / 2) <= min(
            110, self._width / 2
        ):
            return "x"
        return ""

    def _point_at(self, x: float, y: float) -> PlottedPoint | None:
        if self.statistics is None:
            return None
        points = self.statistics.plotted_points(self._width, self._chart_height)
        if not points:
            return None
        point = min(
            points,
            key=lambda point: math.hypot(point.screen_x - x, point.screen_y - y),
        )
        return (
            point
            if math.hypot(point.screen_x - x, point.screen_y - y) <= POINT_HIT_RADIUS * self.scale()
            else None
        )

    def _select_point(self, index: int, x: float, y: float) -> None:
        self._selected_point = index
        if self.statistics is not None:
            self.statistics.select(index)
            self.statistics.message = (
                f"{x:g}"
                if not self.statistics.y_name and self.statistics.plot_type is PlotType.DOT
                else f"({x:g}, {y:g})"
            )

    def _visual_point_at(self, x: float, y: float) -> bool:
        if self.statistics is None:
            return False
        scene = self.statistics.scene(self._width, self._chart_height, axis_labels=False)
        return any(
            math.hypot(point_x - x, point_y - y) <= POINT_HIT_RADIUS * self.scale()
            for layer in scene.layers
            for shape in layer.shapes
            if isinstance(shape, Dots)
            for point_x, point_y in shape.points
        )

    def _tap(self, event: ft.TapEvent) -> None:
        position = event.local_position
        if position is not None:
            self.click_at(position.x, position.y)

    def _context(self, event: ft.TapEvent | ft.LongPressStartEvent) -> None:
        position = event.local_position
        target = self._axis_target(position.x, position.y) if position is not None else ""
        if not target and position is not None and self._visual_point_at(position.x, position.y):
            target = "point"
        if not target and position is not None:
            target = self._mark_at(position.x, position.y)
        self.on_action("context_menu", f"statistics_context_{target or 'plot'}")

    def _mark_at(self, x: float, y: float) -> str:
        """The mark under a right-click: a regression line or its label, a box plot or a
        histogram bar (stats4, R5-G2); "" for none."""
        statistics = self.statistics
        if statistics is None:
            return ""
        scene = statistics.scene(self._width, self._chart_height, axis_labels=False)
        reach = POINT_HIT_RADIUS * self.scale()
        shapes = [shape for layer in scene.layers for shape in layer.shapes]
        if statistics.regression:
            for shape in shapes:
                if (
                    isinstance(shape, Polyline)
                    and shape.stroke.colour == "curve2"
                    and any(math.hypot(px - x, py - y) <= reach for px, py in shape.points)
                ):
                    return "regression"
                if (
                    isinstance(shape, Label)
                    and shape.colour == "curve2"
                    and shape.x <= x <= shape.x + len(shape.text) * shape.size * 0.6
                    and shape.y <= y <= shape.y + shape.size * 1.4
                ):
                    return "regression"
        data = scene.layer("data")
        marks = (
            [shape for shape in data.shapes if isinstance(shape, Fill | Box | Polyline)]
            if data
            else []
        )
        corners = [point for shape in marks for point in _corners(shape)]
        if statistics.plot_type is PlotType.HISTOGRAM:
            for shape in marks:
                if isinstance(shape, Fill) and _inside(x, y, _corners(shape), 0):
                    return "histogram"
        elif statistics.plot_type is PlotType.BOX and corners and _inside(x, y, corners, reach):
            return "box"
        return ""

    def _scroll(self, event: ft.ScrollEvent) -> None:
        """The mouse wheel or a two-finger scroll zooms about the pointer (Simon's note 4)."""
        delta = max(-WHEEL_ZOOM_STEP, min(WHEEL_ZOOM_STEP, event.scroll_delta.y))
        position = event.local_position
        if delta and position is not None:
            self._zoom(math.exp(delta / WHEEL_ZOOM_STEP), position.x, position.y)

    def _zoom(self, factor: float, x: float, y: float) -> None:
        values = (self._width, self._chart_height, factor, x, y)
        self.on_action("statistics", "zoom:" + ",".join(format(v, ".17g") for v in values))

    def _scale_start(self, event: ft.ScaleStartEvent) -> None:
        if event.pointer_count > 1:
            self._pinch_scale = 1.0
            return
        self._pinch_scale = None
        self._pan_start(event.local_focal_point.x, event.local_focal_point.y)

    def _scale_update(self, event: ft.ScaleUpdateEvent) -> None:
        if event.pointer_count > 1 or self._pinch_scale is not None:
            if self._pinch_scale is None:  # a second finger came down during a drag
                self._pinch_scale = 1.0
                self._drag_index = None
            if math.isfinite(event.scale) and event.scale > 0:
                factor = self._pinch_scale / event.scale
                self._pinch_scale = event.scale
                self._zoom(factor, event.local_focal_point.x, event.local_focal_point.y)
            return
        self._pan_update(event.local_focal_point.x, event.local_focal_point.y)

    def _scale_end(self, _: ft.ScaleEndEvent) -> None:
        self._pinch_scale = None
        self._pan_end()

    def _pan_start(self, x: float, y: float) -> None:
        point = self._point_at(x, y)
        self._drag_index = point.index if point is not None else None
        self._drag_value = None
        if point is not None:
            self._select_point(point.index, point.x, point.y)
            self._drag_marker.left = point.screen_x - DRAG_MARKER_RADIUS
            self._drag_marker.top = point.screen_y - DRAG_MARKER_RADIUS
            self._drag_marker.visible = True

    def _pan_update(self, x: float, y: float) -> None:
        if self._drag_index is None or self.statistics is None:
            return
        value = self.statistics.drag_value_at(self._width, self._chart_height, x, y)
        if value is None:
            return
        self._drag_value = value
        self._drag_marker.left = x - DRAG_MARKER_RADIUS
        self._drag_marker.top = y - DRAG_MARKER_RADIUS
        self._drag_marker.update()

    def _pan_end(self) -> None:
        if (
            self._drag_index is not None
            and self._drag_value is not None
            and self.statistics is not None
        ):
            expression = self.statistics.drag_expression(self._drag_index, *self._drag_value)
            if expression is not None:
                self.on_action("statistics_eval", expression)
        self._drag_index = None
        self._drag_value = None
        self._drag_marker.visible = self._selected_point is not None


def _corners(shape: Fill | Box | Polyline) -> list[tuple[float, float]]:
    if isinstance(shape, Box):
        return [(shape.x, shape.y), (shape.x + shape.width, shape.y + shape.height)]
    return list(shape.points)


def _inside(x: float, y: float, points: list[tuple[float, float]], margin: float) -> bool:
    xs, ys = [px for px, _ in points], [py for _, py in points]
    return (
        bool(points)
        and min(xs) - margin <= x <= max(xs) + margin
        and min(ys) - margin <= y <= max(ys) + margin
    )
