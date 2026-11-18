"""Focused state tests for the standalone pseudocode Code view."""

from types import SimpleNamespace
from typing import cast

import flet as ft

from cassim.devices.pseudocode.ui.app import BISECTION, CodeApp
from cassim.runtime.pseudocode import trace


class DummyShell:
    def __init__(self) -> None:
        self.page = SimpleNamespace()
        self.update_label = "Check for Updates"
        self.changed = lambda: None


def test_bisection_example_starts_with_expression_function() -> None:
    assert BISECTION.startswith("define f(x)\n  return x*x - 2\nend\n")
    assert "while (b-a)/2 > 0.2" in BISECTION


def test_set_source_clears_the_previous_trace() -> None:
    app = CodeApp(DummyShell())  # ty: ignore[invalid-argument-type]
    app.cursor = 12
    app.selection = trace.VerticalSelection(("x",), ())

    app.set_source("x ← 1\nprint x")

    assert app.result is None
    assert app.cursor == 0
    assert app.current_source == "x ← 1\nprint x"
    assert app.trace.controls


def test_line_numbers_and_language_toggle_update_codemirror() -> None:
    app = CodeApp(DummyShell())  # ty: ignore[invalid-argument-type]

    class CM:
        def __init__(self) -> None:
            self.options: dict[str, object] = {}
            self.refreshed = False

        def setOption(self, name: str, value: object) -> None:
            self.options[name] = value

        def refresh(self) -> None:
            self.refreshed = True

    cm = CM()
    app.cm = cm

    app.toggle_line_numbers(SimpleNamespace(control=SimpleNamespace(value=False)))  # ty: ignore[invalid-argument-type]
    assert app.line_numbers_visible is False
    assert cm.options["lineNumbers"] is False

    event = cast(
        ft.Event[ft.SegmentedButton],
        SimpleNamespace(control=SimpleNamespace(selected=["python"], update=lambda: None)),
    )
    app.toggle_language(event)
    assert app.language == "python"
    assert cm.options["mode"] == "python"


def test_console_toggle_keeps_editor_and_console_layout_state() -> None:
    app = CodeApp(DummyShell())  # ty: ignore[invalid-argument-type]

    app.toggle_console(SimpleNamespace(control=SimpleNamespace(value=False)))  # ty: ignore[invalid-argument-type]
    assert app.console_visible is False
    assert app.console_box.visible is False

    app.toggle_console(SimpleNamespace(control=SimpleNamespace(value=True)))  # ty: ignore[invalid-argument-type]
    assert app.console_visible is True
    assert app.console_box.visible is True
