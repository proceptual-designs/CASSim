"""A modal window over the Pseudocode workspace: moved by its title bar, resized by its corner
grip, closed by its button. The call trace (FR-TRC-013) opens in one: its two parts sit side by
side when the window is wide enough and stack when it is narrow, rearranging as it resizes."""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from typing import TYPE_CHECKING

import flet as ft

from cassim.app.sizes import POINTER_TARGET, page_is_phone

if TYPE_CHECKING:
    from flet import Page

STACK_WIDTH = 640  # a window narrower than this stacks its two parts in one column
MIN_WIDTH, MIN_HEIGHT = 320, 240
DIVIDER_WIDTH = POINTER_TARGET  # a hit area a finger can use (SDD-15 section 8.3)
BODY_PADDING = 16  # the body's padding, left and right
TITLE_HEIGHT = 40


def _safe_update(control: ft.Control) -> None:
    with contextlib.suppress(RuntimeError):
        control.update()


def is_phone(page: Page) -> bool:
    """On a phone (`cassim.app.sizes`) the window fills the page."""
    return page_is_phone(page)


class CallWindow:
    """A modal window in the page overlay: a dimmed layer behind it keeps the page from being
    used until it closes. `first` and `second` are its two parts (the call's code and its
    trace). `offset` steps it down and right, so a window opened from another (a call inside
    a call) does not hide it exactly."""

    def __init__(  # noqa: PLR0913
        self,
        page: Page,
        title: str,
        first: ft.Container,
        second: ft.Control,
        *,
        offset: int = 0,
        on_close: Callable[[CallWindow], None] | None = None,
    ) -> None:
        self.page = page
        self.first, self.second = first, second
        self.split = 0.42  # the first part's share of the width, side by side
        self.on_close = on_close
        # Pointer x, y and window left, top, width, height when a move or resize began.
        self.drag_from = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        page_width = float(getattr(page, "width", 1000) or 1000)
        page_height = float(getattr(page, "height", 700) or 700)
        if is_phone(page):
            self.width, self.height = page_width - 16, page_height - 32
            self.left, self.top = 8.0, 16.0 + 12 * offset
        else:
            self.width = min(960.0, page_width - 48)
            self.height = min(580.0, page_height - 64)
            self.left = (page_width - self.width) / 2 + 24 * offset
            self.top = (page_height - self.height) / 2 + 24 * offset
        title_bar = ft.GestureDetector(
            ft.Container(
                ft.Row(
                    [
                        ft.Icon(ft.Icons.DRAG_INDICATOR, size=16),
                        ft.Text(title, weight=ft.FontWeight.BOLD, expand=True, no_wrap=True),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            icon_size=18,
                            tooltip="Close",
                            on_click=lambda _: self.close(),
                        ),
                    ],
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                height=TITLE_HEIGHT,
                padding=ft.Padding.only(left=10, right=2),
            ),
            mouse_cursor=ft.MouseCursor.MOVE,
            on_pan_start=self.start_drag,
            on_pan_update=self.move,
            tooltip="Move window",
        )
        grip = ft.GestureDetector(
            ft.Container(
                ft.Icon(ft.Icons.SOUTH_EAST, size=16),
                width=POINTER_TARGET,
                height=POINTER_TARGET,
                alignment=ft.Alignment.BOTTOM_RIGHT,
            ),
            mouse_cursor=ft.MouseCursor.RESIZE_DOWN_RIGHT,
            on_pan_start=self.start_drag,
            on_pan_update=self.resize,
            tooltip="Resize window",
            right=0,
            bottom=0,
        )
        self.stacked = self.width < STACK_WIDTH
        self.body = ft.Container(
            self._arrange(),
            expand=True,
            padding=ft.Padding.only(left=8, right=8, bottom=12),
        )
        self.frame = ft.Container(
            ft.Stack(
                [
                    ft.Column(
                        [title_bar, self.body],
                        spacing=0,
                        expand=True,
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    ),
                    grip,
                ],
                expand=True,
            ),
            left=self.left,
            top=self.top,
            width=self.width,
            height=self.height,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border=ft.Border.all(1, ft.Colors.OUTLINE),
            border_radius=10,
            shadow=ft.BoxShadow(blur_radius=18, color=ft.Colors.SHADOW),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )
        # Modal: the dimmed layer covers the page and takes its clicks until the window closes.
        barrier = ft.Container(
            bgcolor=ft.Colors.with_opacity(0.4, ft.Colors.SCRIM),
            left=0,
            top=0,
            right=0,
            bottom=0,
        )
        self.host = ft.Stack([barrier, self.frame], expand=True)

    def _content_width(self) -> float:
        return max(1.0, self.width - BODY_PADDING - DIVIDER_WIDTH)

    def _arrange(self) -> ft.Control:
        """The two parts side by side, with a divider that resizes them, or stacked when the
        window is narrow."""
        if self.stacked:
            self.first.width, self.first.expand = None, 2
            return ft.Column(
                [self.first, ft.Divider(height=8), self.second], spacing=0, expand=True
            )
        self.first.width, self.first.expand = self.split * self._content_width(), None
        divider = ft.GestureDetector(
            ft.Container(
                ft.Icon(ft.Icons.DRAG_INDICATOR, size=14),
                width=DIVIDER_WIDTH,
                expand=True,
                alignment=ft.Alignment.CENTER,
                tooltip="Resize columns",
            ),
            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
            on_horizontal_drag_update=self.resize_columns,
            drag_interval=25,
        )
        return ft.Row(
            [self.first, divider, self.second],
            spacing=0,
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    def resize_columns(self, event: ft.DragUpdateEvent) -> None:
        """Drag the divider: the first part's share of the width, kept between 20% and 80%."""
        if event.global_delta is None or self.stacked:
            return
        width = self._content_width()
        self.split = min(0.8, max(0.2, self.split + event.global_delta.x / width))
        self.first.width = self.split * width
        _safe_update(self.first)

    def open(self) -> CallWindow:
        self.page.overlay.append(self.host)
        _safe_update(self.page)
        return self

    def close(self) -> None:
        if self.host in self.page.overlay:
            self.page.overlay.remove(self.host)
            _safe_update(self.page)
        if self.on_close is not None:
            self.on_close(self)

    def _bounds(self) -> tuple[float, float]:
        return (
            float(getattr(self.page, "width", 1000) or 1000),
            float(getattr(self.page, "height", 700) or 700),
        )

    def start_drag(self, event: ft.DragStartEvent) -> None:
        """Note where a move or resize starts: the pointer and the window as they were."""
        self.drag_from = (
            event.global_position.x,
            event.global_position.y,
            self.left,
            self.top,
            self.width,
            self.height,
        )

    def _dragged(self, event: ft.DragUpdateEvent) -> tuple[float, float]:
        """How far the pointer has moved since the drag started (from positions: Flet's
        pan `global_delta` counts from the start of the drag, not from the last update)."""
        x, y = self.drag_from[:2]
        return event.global_position.x - x, event.global_position.y - y

    def move(self, event: ft.DragUpdateEvent) -> None:
        page_width, page_height = self._bounds()
        dx, dy = self._dragged(event)
        left, top = self.drag_from[2:4]
        self.left = min(max(0.0, left + dx), page_width - 80)
        self.top = min(max(0.0, top + dy), page_height - TITLE_HEIGHT)
        self.frame.left, self.frame.top = self.left, self.top
        _safe_update(self.frame)

    def resize(self, event: ft.DragUpdateEvent) -> None:
        page_width, page_height = self._bounds()
        dx, dy = self._dragged(event)
        width, height = self.drag_from[4:]
        self.width = min(max(MIN_WIDTH, width + dx), page_width - self.left)
        self.height = min(max(MIN_HEIGHT, height + dy), page_height - self.top)
        self.frame.width, self.frame.height = self.width, self.height
        stacked = self.width < STACK_WIDTH
        if stacked != self.stacked:  # crossed the line: rearrange the two parts
            self.stacked = stacked
            self.body.content = self._arrange()
        elif not stacked:  # the columns keep their shares of the new width
            self.first.width = self.split * self._content_width()
        _safe_update(self.frame)
