"""The warning triangle (FR-CALC-007): shared by every page that can give a value with a caution.

A small yellow triangle beside the item; hovering shows the message, and a click or tap opens a
dialog titled Warning with the message and OK, as the handheld does (decision 0026,
`docs/testing/emulator-domain-results.md`). The glyph is a Material icon, not device artwork.
"""

from __future__ import annotations

from collections.abc import Sequence

import flet as ft

from cassim.app.theme import DARK

COLOUR = DARK.warning  # the device's yellow, drawn on the screen in every theme


def warning_dialog(messages: Sequence[str]) -> ft.AlertDialog:
    def close(e: ft.Event[ft.TextButton]) -> None:
        e.control.page.pop_dialog()

    return ft.AlertDialog(
        title=ft.Text("Warning"),
        content=ft.Text("\n".join(messages)),
        actions=[ft.TextButton("OK", on_click=close)],
    )


def warning_mark(messages: Sequence[str], size: float = 16) -> ft.Control:
    """The triangle for `messages`, or an empty control when there are none."""
    if not messages:
        return ft.Container(width=0)
    text = "\n".join(messages)

    def show(e: ft.Event[ft.GestureDetector]) -> None:
        e.control.page.show_dialog(warning_dialog(messages))

    icon = ft.Icon(
        ft.Icons.WARNING_ROUNDED,
        color=COLOUR,
        size=size,
        tooltip=text,
        semantics_label="Warning: " + text,
    )
    return ft.GestureDetector(icon, on_tap=show, mouse_cursor=ft.MouseCursor.CLICK)
