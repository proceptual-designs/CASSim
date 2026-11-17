"""Regions where the browser should leave right-click to a CASSim context menu."""

import flet as ft


def context_menu_region() -> ft.GestureDetector:
    """Mark a positioned region without taking gestures from its parent.

    The web page reads this cursor synchronously when the mouse is pressed; a worker round trip
    would arrive too late to cancel the browser's contextmenu event.
    """
    return ft.GestureDetector(
        content=ft.Container(bgcolor=ft.Colors.TRANSPARENT),
        mouse_cursor=ft.MouseCursor.CONTEXT_MENU,
        exclude_from_semantics=True,
        visible=False,
    )
