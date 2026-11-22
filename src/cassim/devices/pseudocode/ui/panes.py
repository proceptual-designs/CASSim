"""Reusable panes for the pseudocode teaching workspace."""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from dataclasses import dataclass, field

import flet as ft

TITLE_HEIGHT = 42


def _safe_update(control: ft.Control) -> None:
    with contextlib.suppress(RuntimeError):
        control.update()


@dataclass(frozen=True, slots=True)
class PaneOptions:
    """Sizing, state and callbacks for a boxed pane."""

    height: float
    minimum: float = 140
    maximum: float = 720
    collapsed: bool = False
    on_change: Callable[[], None] | None = None
    title_controls: list[ft.Control] = field(default_factory=list)


class BoxedPane:
    """A collapsible, vertically resizable pane with a persistent title row."""

    def __init__(
        self,
        title: str,
        content: ft.Control,
        options: PaneOptions,
    ) -> None:
        self.title = title
        self.height = options.height
        self.minimum = options.minimum
        self.maximum = options.maximum
        self.collapsed = options.collapsed
        self.on_change = options.on_change
        self.content = content
        self.content_host = ft.Container(content, expand=True, padding=4)
        self.grip = ft.GestureDetector(
            ft.Container(
                ft.Icon(ft.Icons.DRAG_HANDLE, size=15),
                width=36,
                height=24,
                alignment=ft.Alignment.BOTTOM_RIGHT,
                tooltip=f"Resize {title}",
            ),
            mouse_cursor=ft.MouseCursor.RESIZE_UP_DOWN,
            on_vertical_drag_update=self._resize,
            # Pinned to the corner: a pane-sized overlay took every click meant for the
            # content, so the editor and the checkboxes could not be used.
            right=0,
            bottom=0,
        )
        self.toggle = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT if self.collapsed else ft.Icons.EXPAND_MORE,
            tooltip=f"{'Expand' if self.collapsed else 'Collapse'} {title}",
            on_click=self.toggle_collapsed,
            icon_size=18,
            width=36,
            height=36,
        )
        title_controls: list[ft.Control] = []
        if options.title_controls:
            title_controls.append(
                ft.Container(
                    ft.Row(options.title_controls, tight=True, spacing=4),
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                )
            )
        title_row = ft.Row(
            [
                ft.Text(title, weight=ft.FontWeight.BOLD),
                *title_controls,
                *([] if options.title_controls else [ft.Container(expand=True)]),
                self.toggle,
            ],
            spacing=4,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.body = ft.Stack([self.content_host, self.grip], expand=True)
        self.container = ft.Container(
            ft.Column(
                [
                    ft.Container(
                        title_row,
                        height=TITLE_HEIGHT,
                        padding=ft.Padding.symmetric(horizontal=8),
                    ),
                    self.body,
                ],
                spacing=0,
                expand=True,
                # Full width, so the grip sits in the pane's corner, not at the content's edge.
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            border=ft.Border.all(1),
            border_radius=4,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )
        self._draw()

    def _draw(self) -> None:
        self.container.height = TITLE_HEIGHT if self.collapsed else self.height
        self.body.visible = not self.collapsed
        self.toggle.icon = ft.Icons.CHEVRON_RIGHT if self.collapsed else ft.Icons.EXPAND_MORE
        self.toggle.tooltip = f"{'Expand' if self.collapsed else 'Collapse'} {self.title}"

    def toggle_collapsed(self, _: ft.Event[ft.IconButton] | None = None) -> None:
        self.collapsed = not self.collapsed
        self._draw()
        _safe_update(self.container)
        if self.on_change is not None:
            self.on_change()

    def set_collapsed(self, value: bool) -> None:
        if self.collapsed == value:
            return
        self.collapsed = value
        self._draw()

    def _resize(self, event: ft.DragUpdateEvent) -> None:
        if event.global_delta is None or self.collapsed:
            return
        self.height = min(self.maximum, max(self.minimum, self.height + event.global_delta.y))
        self.container.height = self.height
        _safe_update(self.container)
        if self.on_change is not None:
            self.on_change()
