"""The Data & Statistics page controls and scene renderer."""

from __future__ import annotations

from collections.abc import Callable

import flet as ft
import flet.canvas as cv

from cassim.app.context_menu import context_menu_region
from cassim.app.scene_canvas import COLOURS, layer_shapes
from cassim.app.theme import Theme
from cassim.device.keys import Action
from cassim.devices.nspire.pages.statistics import Statistics
from cassim.graph.scene import Layer

TOOLBAR = 30


def statistics_colours(theme: Theme) -> dict[str, str]:
    return {
        **COLOURS,
        "ink": theme.screen_text,
        "axis": theme.sheet_axis,
        "grid": theme.sheet_grid,
    }


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
        self._toolbar_height = TOOLBAR
        self.x_button = ft.TextButton(
            content="X: Click to add variable", on_click=lambda _: self._menu("statistics_x")
        )
        self.y_button = ft.TextButton(
            content="Y: Click to add variable", on_click=lambda _: self._menu("statistics_y")
        )
        self.plot_button = ft.TextButton(
            content="Plot Type", on_click=lambda _: self._menu("statistics_plot")
        )
        self.menu_button = ft.TextButton("Menu", on_click=lambda _: self._menu("menu"))
        self.message = ft.Text("", size=11, color=theme.error)
        self.canvas = ft.Stack([], expand=True)
        self._context_region = context_menu_region()
        self._plot_gestures = ft.GestureDetector(
            content=self.canvas,
            on_long_press_start=self._context,
            on_secondary_tap_down=self._context,
            expand=True,
        )
        self.control = ft.Column(
            [
                ft.Row(
                    [self.x_button, self.y_button, self.plot_button, self.menu_button],
                    spacing=0,
                    wrap=True,
                ),
                self._plot_gestures,
                ft.Container(self.message, padding=ft.Padding.symmetric(horizontal=6, vertical=2)),
            ],
            spacing=0,
            expand=True,
        )

    def refresh(self, statistics: Statistics, width: float, height: float) -> None:
        self.statistics = statistics
        scale = self.scale()
        self._width, self._height = max(width, 120), max(height, 100)
        self._toolbar_height = TOOLBAR * scale
        chart_height = max(self._height - self._toolbar_height - 18 * scale, 64 * scale)
        scene = statistics.scene(self._width, chart_height)
        controls: list[ft.Control] = []
        for layer in scene.layers:
            kept = self._layers.get(layer.name)
            if kept is None or kept[0] != layer:
                kept = (
                    layer,
                    cv.Canvas(
                        layer_shapes(layer, self.colours),
                        width=self._width,
                        height=chart_height,
                    ),
                )
                self._layers[layer.name] = kept
            controls.append(kept[1])
        self.canvas.controls = controls
        self._context_region.visible = True
        self._context_region.left = 0
        self._context_region.top = 0
        self._context_region.width = self._width
        self._context_region.height = chart_height
        self.canvas.controls.append(self._context_region)
        self.x_button.content = f"X: {statistics.x_name or 'Click to add variable'}"
        self.y_button.content = f"Y: {statistics.y_name or 'Click to add variable'}"
        self.plot_button.content = statistics.plot_type.value
        self.message.value = statistics.message

    def click_at(self, x: float, y: float) -> bool:
        """Route toolbar clicks; plot interactions are not enabled yet."""
        if y >= self._toolbar_height:
            return True
        width = self._width
        if x < width * 0.26:
            self._menu("statistics_x")
        elif x < width * 0.52:
            self._menu("statistics_y")
        elif x < width * 0.78:
            self._menu("statistics_plot")
        else:
            self._menu("menu")
        return True

    def _menu(self, name: str) -> None:
        self.on_action("open_menu", name)

    def _context(self, _: ft.TapEvent | ft.LongPressStartEvent) -> None:
        self.on_action("context_menu", "")
