"""The pseudocode workspace's boxed panes (FR-RUN-008)."""

import flet as ft

from cassim.devices.pseudocode.ui.panes import BoxedPane, PaneOptions


def test_the_resize_grip_covers_only_its_corner() -> None:
    """A pane-sized layer above the content took every click meant for it: the Code editor
    could not be typed into and the Symbols checkboxes could not be toggled (2026-11-22)."""
    content = ft.Text("content")
    pane = BoxedPane("Code", content, PaneOptions(height=300))

    assert pane.body.controls == [pane.content_host, pane.grip]
    assert (pane.grip.right, pane.grip.bottom) == (0, 0)
    grip = pane.grip.content
    assert isinstance(grip, ft.Container)
    # a corner a finger can use (SDD-15 section 8.3), far smaller than the pane
    assert (grip.width, grip.height) == (48, 40)
