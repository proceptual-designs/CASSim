"""The Nspire handheld keypad."""

from __future__ import annotations

from collections.abc import Callable
from typing import cast

import flet as ft
import flet.canvas as cv

from cassim.app.theme import DARK, Theme
from cassim.device.keys import Key
from cassim.devices.nspire.ui.layout import KEY_GAP, KEY_H, key_span
from cassim.devices.nspire.ui.state import AppState
from cassim.devices.nspire.ui.views import label_text

STICK_KEY = "click"
ACCENT_KEY = "accent"
type Stick = Callable[[str, float, float], None]


def context_menu_icon(scale: float, colour: str) -> cv.Canvas:
    """A menu and pointer, drawn locally so the legend also works offline."""
    paint = ft.Paint(color=colour, stroke_width=scale, style=ft.PaintingStyle.STROKE)
    lines: list[cv.Shape] = [
        cv.Line(scale, y * scale, 8 * scale, y * scale, paint=paint) for y in (1, 4, 7)
    ]
    pointer: list[cv.Path.PathElement] = [
        cv.Path.MoveTo(9 * scale, 2 * scale),
        cv.Path.LineTo(9 * scale, 9 * scale),
        cv.Path.LineTo(11 * scale, 7 * scale),
        cv.Path.LineTo(13 * scale, 10 * scale),
        cv.Path.LineTo(14 * scale, 9 * scale),
        cv.Path.LineTo(12 * scale, 6 * scale),
        cv.Path.LineTo(15 * scale, 6 * scale),
        cv.Path.Close(),
    ]
    lines.append(cv.Path(pointer, paint=ft.Paint(color=colour, style=ft.PaintingStyle.FILL)))
    return cv.Canvas(lines, width=16 * scale, height=10 * scale)


class Keypad:
    """The on-screen keys, laid out as on the handheld (FR-DEV-005). Each key shows its ctrl and
    shift labels small above it; the pending modifier lights up and its layer's labels move onto
    the keys."""

    def __init__(
        self,
        state: AppState,
        on_key: Callable[[str], None],
        theme: Theme = DARK,
        install: Callable[[], None] | None = None,
        on_stick: Stick | None = None,
    ) -> None:
        self.state = state
        self.on_key = on_key
        # The centre key as a joystick: told "start", "move" (with the travel in key widths),
        # "end" and "tap". Without it the key is a plain button.
        self.on_stick = on_stick
        self._down = (0.0, 0.0)  # where the finger pressed on the centre key
        self.install = install  # set while the browser offers to install; None otherwise
        self.theme = theme
        self.control = ft.Column(spacing=KEY_GAP, tight=True)
        self._look: tuple[object, ...] | None = None
        self.refresh()

    def refresh(self) -> None:
        state = self.state
        # Everything that changes how a key looks. Rebuilding ~40 controls costs far more on a
        # phone than the unchanged diff, so an unchanged keypad is left alone.
        look = (
            id(state.keypad),
            state.pending,
            state.pad_scale,
            self.install is not None,
            self.theme,
        )
        if look == self._look:
            return
        self._look = look
        gap = self.state.kpx(KEY_GAP)
        self.control.spacing = gap
        keypad = self.state.keypad
        rows: list[ft.Control] = []
        for number, row in enumerate(keypad):
            tallest = self.state.kpx(key_span(max(key.height for key in row), KEY_H))
            keys = [self._key(key, tallest) for key in row]
            # Install takes the empty cell at the top right of the keypad, so it needs no row
            if number == 0 and self.install is not None and not row[-1].name:
                keys[-1] = self._install_key(row[-1])
            rows.append(ft.Row(keys, spacing=gap, tight=True))
        self.control.controls = rows

    def _install_key(self, cell: Key) -> ft.Control:
        install = self.install
        assert install is not None
        return ft.Container(
            label_text("Install", size=self.state.kpx(12), color="#ffffff"),
            width=self.state.kpx(key_span(cell.width)),
            height=self.state.kpx(key_span(cell.height, KEY_H)),
            alignment=ft.Alignment.CENTER,
            bgcolor=self.theme.accent,
            border_radius=self.state.kpx(7),
            ink=True,
            tooltip="Install CASSim",
            on_click=lambda _: install(),
        )

    def _key(self, key: Key, row_height: float = 0.0) -> ft.Control:
        state, theme = self.state, self.theme
        width = state.kpx(key_span(key.width))
        height = state.kpx(key_span(key.height, KEY_H))
        if not key.name:
            return ft.Container(width=width, height=height)
        pending = state.pending
        layer = {"ctrl": key.ctrl, "shift": key.shift}.get(pending, "")
        fill, text = theme.key_colours(key.style)
        small = state.kpx(8 if key.width < 1 else 9)
        ctrl_label: ft.Control = label_text(
            key.ctrl, size=small, color=theme.key_label, no_wrap=True
        )
        if key.name == "menu":
            ctrl_label = context_menu_icon(state.kpx(0.9), theme.key_label)
        labels = ft.Row(
            [
                ctrl_label,
                label_text(key.shift, size=small, color=theme.shift_label, no_wrap=True),
            ],
            spacing=state.kpx(3),
            alignment=ft.MainAxisAlignment.CENTER,
            tight=True,
        )
        size = state.kpx(13 if key.height < 1 or key.width < 1 else 15)
        main: ft.Control = label_text(
            layer or key.label,
            size=size,
            color=text,
            weight=ft.FontWeight.W_600,
            no_wrap=True,
        )
        if key.name == ACCENT_KEY:
            # Material's flag icon for now (Simon, 2026-11-14). TODO: find a better mark for a
            # key that cycles a letter's accents (options tried: ệ with a loop, arrows, è é ê).
            main = ft.Icon(ft.Icons.FLAG, size=size * 1.1, color=text)
        elif key.name == "menu" and pending == "ctrl":
            main = context_menu_icon(state.kpx(1.3), text)
        body: list[ft.Control] = [labels, main] if key.ctrl or key.shift else [main]
        stick = key.name == STICK_KEY and self.on_stick is not None
        colour = theme.modifier_on if pending == key.name else fill
        outline = theme.shift_label if key.name == "shift" else theme.key_outline
        box = ft.Container(
            ft.Column(
                body,
                spacing=0,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            width=width,
            height=height,
            alignment=ft.Alignment.CENTER,
            bgcolor=colour,
            border=ft.Border.all(state.kpx(2), outline)
            if key.outline or key.name == "shift"
            else None,
            border_radius=key_corners(key, height / 2 if key.style == "pad" else state.kpx(7)),
            ink=not stick,
            tooltip=key_tip(key),
            on_click=None if stick else lambda _, name=key.name: self.on_key(name),
        )
        if key.join == "down":  # fill the gap down to the lower piece, so the two read as one
            seam = ft.Container(
                left=0, top=height - 1, width=width, height=state.kpx(KEY_GAP) + 2, bgcolor=colour
            )
            # sized to the piece, so the seam overflows into the gap without growing the row
            piece = ft.Stack(
                [box, seam], width=width, height=height, clip_behavior=ft.ClipBehavior.NONE
            )
            if row_height <= height:
                return piece
            # a piece shorter than its row (return's tab) sits at the row's foot, by the gap
            return ft.Container(
                piece, width=width, height=row_height, alignment=ft.Alignment.BOTTOM_CENTER
            )
        return self._stick(box, width) if stick else box

    def _stick(self, box: ft.Control, width: float) -> ft.Control:
        """The centre key: a tap is a tap, and a drag steers the pointer like a joystick, by how
        far the finger has gone from where it pressed (in key widths, so the feel does not
        change with the keypad's scale)."""
        on_stick = cast("Stick", self.on_stick)

        def down(event: ft.DragDownEvent) -> None:
            self._down = (event.local_position.x, event.local_position.y)

        def move(event: ft.DragUpdateEvent) -> None:
            x, y = self._down
            here = event.local_position
            on_stick("move", (here.x - x) / width, (here.y - y) / width)

        return ft.GestureDetector(
            box,
            on_tap=lambda _: on_stick("tap", 0.0, 0.0),
            on_pan_down=down,
            on_pan_start=lambda _: on_stick("start", 0.0, 0.0),
            on_pan_update=move,
            on_pan_end=lambda _: on_stick("end", 0.0, 0.0),
            on_pan_cancel=lambda _: on_stick("end", 0.0, 0.0),
            drag_interval=16,
        )


def key_corners(key: Key, radius: float) -> ft.BorderRadius:
    """Rounded corners, except where a key's two pieces meet (an L-shaped return key): the upper
    piece is square below, and the lower, wider piece square at its top right."""
    if key.join == "down":
        return ft.BorderRadius(radius, radius, 0, 0)
    if key.join == "up":
        return ft.BorderRadius(radius, 0, radius, radius)
    return ft.BorderRadius.all(radius)


def key_tip(key: Key) -> str | None:
    """What the other layers of a key do, for a mouse hover or a long press."""
    layers = (("ctrl", key.ctrl), ("shift", key.shift))
    return ", ".join(f"{layer}: {label}" for layer, label in layers if label) or None
