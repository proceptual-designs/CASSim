"""Focused state tests for the standalone pseudocode Code view."""

import asyncio
import sys
from collections.abc import Callable
from types import SimpleNamespace
from typing import cast

import flet as ft
import pytest

from cassim.devices.pseudocode.ui.app import (
    BISECTION,
    CONDITION_COLUMN_WIDTH,
    D4_SAMPLE_SPACE,
    DICE_MAX_STATS,
    EDITOR_SIDE_PADDING,
    EXAMPLE,
    GCD_LCM,
    LEFT_RIEMANN,
    LINE_COLUMN_WIDTH,
    LINEAR,
    OUTPUT_COLUMN_WIDTH,
    POLYNOMIAL_NEWTON,
    VARIABLE_COLUMN_WIDTH,
    CodeApp,
    wrapped_rows,
)
from cassim.runtime.pseudocode import TRANSLATION_MARKER, Settings, run, trace


def test_codemirror_is_only_mounted_with_a_page_document(monkeypatch) -> None:
    """The web UI runs in a worker: `js` exists there but has no `document` (start raised)."""
    monkeypatch.setitem(sys.modules, "js", SimpleNamespace())
    assert not CodeApp._has_browser_dom()
    monkeypatch.setitem(sys.modules, "js", SimpleNamespace(document=object()))
    assert CodeApp._has_browser_dom()


class DummyShell:
    def __init__(self) -> None:
        self.page = SimpleNamespace()
        self.update_label = "Check for Updates"
        self.changed = lambda: None
        self.home: Callable[[], None] | None = None
        self.notices: list[tuple[str, str]] = []

    def notice(self, title: str, message: str) -> None:
        self.notices.append((title, message))


def typed(app: CodeApp, text: str, selection_end: int | None) -> SimpleNamespace:
    """Send the fallback editor a change, with the selection Python last heard about."""
    selection = None if selection_end is None else SimpleNamespace(end=selection_end)
    control = SimpleNamespace(value=text, selection=selection, update=lambda: None)
    app.on_fallback_source(SimpleNamespace(control=control))  # ty: ignore[invalid-argument-type]
    return control


def test_typing_aid_finds_the_edit_without_a_current_selection() -> None:
    """FR-SYN-013: the selection reaches Python separately from the text, so it can be stale.
    After select-all and delete it still points into the old text; `<-` must still convert."""
    app = CodeApp(DummyShell())  # ty: ignore[invalid-argument-type]
    app.current_source = "x <"

    assert typed(app, "x <-", selection_end=0).value == "x ←"

    app.current_source = "a\nb"
    assert typed(app, "a <-\nb", selection_end=9).value == "a ←\nb"  # an edit mid-text


def test_typing_aid_is_a_setting_that_starts_on() -> None:
    """FR-SYN-013: no switch in the toolbar; Settings holds it, on by default."""
    app = CodeApp(DummyShell())  # ty: ignore[invalid-argument-type]

    assert app.typing_aid
    switches = [control for control in app.toolbar.controls if isinstance(control, ft.Switch)]
    assert switches == []


def test_typing_aid_converts_latex_words_but_not_in_strings_or_python() -> None:
    """FR-SYN-013: `\\theta ` became θ only in a mode the UI could not reach; now it works."""
    app = CodeApp(DummyShell())  # ty: ignore[invalid-argument-type]
    app.current_source = "x ← \\theta"
    assert typed(app, "x ← \\theta ", selection_end=None).value == "x ← θ "

    app.current_source = 'print "\\theta'
    assert typed(app, 'print "\\theta ', selection_end=None).value == 'print "\\theta '

    app.language = "python"
    app.current_source = "x <"
    assert typed(app, "x <-", selection_end=None).value == "x <-"


def test_typing_aid_off_in_settings_leaves_typing_alone() -> None:
    app = CodeApp(DummyShell())  # ty: ignore[invalid-argument-type]
    app.typing_aid = False
    app.current_source = "x <"

    assert typed(app, "x <-", selection_end=None).value == "x <-"


def test_bisection_example_starts_with_expression_function() -> None:
    assert BISECTION.startswith("define f(x)\n  return x*x - 2\nend\n")
    assert "precision ← 0.001" in BISECTION
    assert "while b-a > precision" in BISECTION
    assert run(BISECTION, Settings()).output == ["1.41504"]


def test_home_delegates_to_the_application_shell() -> None:
    shell = DummyShell()
    requested: list[bool] = []
    shell.home = lambda: requested.append(True)
    app = CodeApp(shell)  # ty: ignore[invalid-argument-type]

    app.home(SimpleNamespace())  # ty: ignore[invalid-argument-type]

    assert requested == [True]


def test_single_device_code_view_does_not_offer_home() -> None:
    app = CodeApp(DummyShell())  # ty: ignore[invalid-argument-type]

    labels = [
        control.content
        for control in app.cassim_menu.controls
        if isinstance(control, ft.MenuItemButton)
    ]
    assert "Home" not in labels


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
            self.value = EXAMPLE

        def setOption(self, name: str, value: object) -> None:
            self.options[name] = value

        def refresh(self) -> None:
            self.refreshed = True

        def getValue(self) -> str:
            return self.value

        def setValue(self, value: str) -> None:
            self.value = value

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
    assert "for" in cm.value
    assert "terms" in cm.value


def test_loaded_example_uses_current_language_and_can_switch_back() -> None:
    app = CodeApp(DummyShell())  # ty: ignore[invalid-argument-type]
    python = cast(
        ft.Event[ft.SegmentedButton],
        SimpleNamespace(control=SimpleNamespace(selected=["python"], update=lambda: None)),
    )
    pseudocode = cast(
        ft.Event[ft.SegmentedButton],
        SimpleNamespace(control=SimpleNamespace(selected=["pseudocode"], update=lambda: None)),
    )

    app.toggle_language(python)
    app.load_example(EXAMPLE)

    assert app.language == "python"
    assert "terms = 10" in app.source()
    assert TRANSLATION_MARKER not in app.source()
    assert "←" not in app.source()

    app.toggle_language(pseudocode)

    assert app.language == "pseudocode"
    assert "terms ← 10" in app.source()
    assert run(app.source(), Settings()).output == ["89"]


def test_console_pane_starts_collapsed_and_keeps_editor_layout_state() -> None:
    app = CodeApp(DummyShell())  # ty: ignore[invalid-argument-type]
    assert app.console_pane.collapsed is True
    assert app.console_pane.body.visible is False

    app.console_pane.toggle_collapsed()
    assert app.console_pane.collapsed is False
    assert app.console_pane.body.visible is True

    app.console_pane.toggle_collapsed()
    assert app.console_pane.collapsed is True
    assert app.console_pane.body.visible is False


def test_new_examples_run_as_intended() -> None:
    assert run(EXAMPLE, Settings()).output == ["89"]
    result = run(LINEAR, Settings(seed=42))
    assert result.output == ["7"]


def test_classic_algorithm_examples_run() -> None:
    assert run(GCD_LCM, Settings()).output == ["6", "420"]
    assert run(DICE_MAX_STATS, Settings()).error is None
    sample_space = run(D4_SAMPLE_SPACE, Settings())
    assert sample_space.error is None
    assert sample_space.output[0].count("[") == 17
    assert run(LEFT_RIEMANN, Settings()).error is None
    assert run(POLYNOMIAL_NEWTON, Settings()).error is None


def test_run_discovers_constants_and_starts_at_the_first_trace_step() -> None:
    app = CodeApp(DummyShell())  # ty: ignore[invalid-argument-type]
    app.set_source(BISECTION)

    asyncio.run(app.run_code(SimpleNamespace()))  # ty: ignore[invalid-argument-type]

    assert app.result is not None
    assert app.cursor == 0
    assert app.constant_names() == ("precision",)
    assert "f" in app.function_names()
    assert "precision" not in app.selection.variables
    assert app.constant_value("precision") == "0.001"
    assert app.console_pane.collapsed is False


def test_constant_toggle_changes_the_table_without_rerunning() -> None:
    app = CodeApp(DummyShell())  # ty: ignore[invalid-argument-type]
    app.result = run(BISECTION, Settings(), trace=True)
    app.choices = trace.vertical_choices(app.result, Settings())
    app.selection = trace.VerticalSelection(
        tuple(app.choices.variables),
        app.condition_selection_values(),
    )
    original = app.result
    event = cast(
        ft.Event[ft.Checkbox],
        SimpleNamespace(control=SimpleNamespace(value=False)),
    )

    app.variable_toggle("precision")(event)

    assert app.result is original
    assert "precision" not in app.selection.variables


def test_boxed_pane_resize_is_clamped() -> None:
    app = CodeApp(DummyShell())  # ty: ignore[invalid-argument-type]
    pane = app.editor_pane
    event = SimpleNamespace(global_delta=SimpleNamespace(y=10_000))

    pane._resize(event)  # ty: ignore[invalid-argument-type]
    assert pane.height == pane.maximum

    event.global_delta.y = -20_000
    pane._resize(event)  # ty: ignore[invalid-argument-type]
    assert pane.height == pane.minimum


def test_workspace_split_and_trace_columns_resize() -> None:
    app = CodeApp(DummyShell())  # ty: ignore[invalid-argument-type]
    app.left_host = ft.Container(ft.Text("left"), width=500)
    app.page.width = 1100
    event = SimpleNamespace(global_delta=SimpleNamespace(x=60, y=0))

    app.resize_columns(event)  # ty: ignore[invalid-argument-type]
    assert app.column_split > 0.5

    app.resize_trace_column("__output__", event)  # ty: ignore[invalid-argument-type]
    assert app.trace_widths["__output__"] > OUTPUT_COLUMN_WIDTH

    app.result = run(EXAMPLE, Settings())
    app.choices = trace.vertical_choices(app.result, Settings())
    app.selection = trace.VerticalSelection(tuple(app.choices.variables), ())
    app.build_variables()
    original = tuple(app.symbol_widths)
    app.resize_symbol_columns(0, event)  # ty: ignore[invalid-argument-type]
    assert tuple(app.symbol_widths) != original
    assert len(app.symbol_columns) == 3
    assert app.resize_trace_column("__line__", event) is None  # ty: ignore[invalid-argument-type]
    app.resize_trace_column("__code__", event)  # ty: ignore[invalid-argument-type]
    assert app.trace_widths["__code__"] > 0


def test_console_entry_does_not_repeat_program_output() -> None:
    app = CodeApp(DummyShell())  # ty: ignore[invalid-argument-type]
    app.set_source("x ← 4\nprint x")
    app.console.value = "4"
    event = cast(
        ft.Event[ft.TextField],
        SimpleNamespace(
            control=SimpleNamespace(value="x + 1", update=lambda: None),
        ),
    )

    app.submit_console(event)

    assert str(app.console.value).count("\n4\n") == 0
    assert str(app.console.value).endswith("> x + 1\n5")


def test_editor_gutter_shares_the_outer_scroller() -> None:
    app = CodeApp(DummyShell())  # ty: ignore[invalid-argument-type]

    app.set_source("\n".join(f"print {number}" for number in range(30)))

    assert app.fallback_editor.min_lines == 31
    assert app.fallback_editor.max_lines == 5000
    assert len(str(app.line_number_gutter.value).splitlines()) == 30


def test_trace_layout_cycles() -> None:
    app = CodeApp(DummyShell())  # ty: ignore[invalid-argument-type]

    app.cycle_trace_layout(SimpleNamespace())  # ty: ignore[invalid-argument-type]
    assert app.trace_mode == "horizontal"
    app.cycle_trace_layout(SimpleNamespace())  # ty: ignore[invalid-argument-type]
    assert app.trace_mode == "none"
    app.cycle_trace_layout(SimpleNamespace())
    assert app.trace_mode == "vertical"


def test_horizontal_trace_at_first_does_not_report_unavailable() -> None:
    shell = DummyShell()
    app = CodeApp(shell)  # ty: ignore[invalid-argument-type]
    app.result = run(EXAMPLE, Settings(), trace=True)
    app.choices = trace.vertical_choices(app.result, Settings())
    app.selection = trace.VerticalSelection(tuple(app.choices.variables), ())
    app.cursor = 0

    app.change_trace_layout("horizontal")

    assert app.trace_mode == "horizontal"
    assert shell.notices == []
    assert app.trace.controls


def test_fixed_trace_column_widths_are_precomputed() -> None:
    assert (LINE_COLUMN_WIDTH, VARIABLE_COLUMN_WIDTH) == (40, 76)
    assert (CONDITION_COLUMN_WIDTH, OUTPUT_COLUMN_WIDTH) == (130, 140)


def test_python_console_accepts_print_and_expressions() -> None:
    app = object.__new__(CodeApp)
    app.python_console_namespace = {"__name__": "cassim_console"}

    assert app.submit_python_console("50 * 'hi'") == "hi" * 50
    assert app.submit_python_console("print(50 * 'hi')") == "hi" * 50
    assert app.submit_python_console("x = 6") == ""
    assert app.submit_python_console("x + 1") == "7"


def test_pseudocode_console_accepts_print_and_bare_expressions() -> None:
    app = object.__new__(CodeApp)

    assert app.pseudocode_console_source("x ← 4", 'print 50*"hi"') == ('x ← 4\nprint 50*"hi"')
    assert app.pseudocode_console_source("x ← 4", "x + 1") == "x ← 4\nprint x + 1"


DOUBLING = """\
define f(n)
  m ← n*2
  if m > 4 then
    return m
  end if
  return f(m)
end
y ← f(1)
print y"""


def texts(control: object) -> list[str]:
    """Every Text value inside a control tree, in order."""
    found: list[str] = []
    if isinstance(control, ft.Text) and isinstance(control.value, str):
        found.append(control.value)
    for name in ("content", "controls", "title"):
        child = getattr(control, name, None)
        for item in child if isinstance(child, list) else [child]:
            if isinstance(item, ft.Control):
                found.extend(texts(item))
    return found


def test_a_call_row_opens_its_own_trace_in_a_dialog() -> None:
    """FR-TRC-013: the call's Calcs cell has an expand button; the dialog shows that call's
    lines, and a call inside it has its own button."""
    shell = DummyShell()
    dialogs: list[ft.AlertDialog] = []
    shell.page = SimpleNamespace(show_dialog=dialogs.append, pop_dialog=lambda: None)
    app = CodeApp(shell)  # ty: ignore[invalid-argument-type]
    app.result = run(DOUBLING, Settings())
    app.cursor = len(app.result.steps)

    table, _, _ = app.update_vertical_trace()
    calls = app.call_rows(table)
    assert calls == {0: 0}  # the top-level row `f(1)`

    app.show_call(calls[0])
    dialog = dialogs[-1]
    assert texts(dialog.title) == ["f(1): n = 1"]
    shown = texts(dialog.content)
    assert shown[:3] == ["Line", "m", "Calcs / Output"]
    assert "f(2)" in shown
    buttons = [tooltip for tooltip in _tooltips(dialog.content) if tooltip.startswith("Expand ")]
    assert buttons == ["Expand f(2)"]


def _tooltips(control: object) -> list[str]:
    found: list[str] = []
    if isinstance(control, ft.IconButton) and isinstance(control.tooltip, str):
        found.append(control.tooltip)
    for name in ("content", "controls"):
        child = getattr(control, name, None)
        for item in child if isinstance(child, list) else [child]:
            if isinstance(item, ft.Control):
                found.extend(_tooltips(item))
    return found


def test_newton_example_uses_short_names_and_sits_with_numerical_methods() -> None:
    assert "coefficient" not in POLYNOMIAL_NEWTON
    assert "for each coeff in coeffs" in POLYNOMIAL_NEWTON
    assert run(POLYNOMIAL_NEWTON, Settings()).output == ["2.09455"]

    app = CodeApp(DummyShell())  # ty: ignore[invalid-argument-type]
    groups = {
        str(group.content): [
            str(item.content) for item in group.controls if isinstance(item, ft.MenuItemButton)
        ]
        for group in app.build_examples_menu().controls
        if isinstance(group, ft.SubmenuButton)
    }
    assert groups["Numerical methods"] == ["Left Riemann sum", "Polynomial + Newton"]
    assert groups["Number theory"] == ["GCD and LCM"]


@pytest.mark.parametrize(
    ("line", "columns", "rows"),
    [
        ("print x", 20, 1),
        ("print x", 0, 1),  # width not known yet: no wrapping
        ("aaaa bbbb cccc", 9, 2),  # "aaaa bbbb" fits; "cccc" wraps
        ("aaaa bbbb cccc", 4, 3),
        ("  x ← x - polynomial(coeffs, x)/derivative(coeffs, x)", 30, 2),
        ("abcdefghijkl", 5, 3),  # a word longer than a row is split
    ],
)
def test_wrapped_rows_follows_word_wrapping(line: str, columns: int, rows: int) -> None:
    assert wrapped_rows(line, columns) == rows


def test_wrapped_lines_get_no_number_of_their_own() -> None:
    """The gutter numbers source lines; rows a long line wraps onto stay blank."""
    source = "x ← 1\naaaa bbbb cccc\nprint x"

    assert CodeApp._line_numbers_for(source, 9) == "1\n2\n\n3"
    assert CodeApp._line_numbers_for(source) == "1\n2\n3"

    app = CodeApp(DummyShell())  # ty: ignore[invalid-argument-type]
    app.code_char_width, app.symbol_char_width = 8.65, 11.37  # as measured in Edge
    app.editor_width = EDITOR_SIDE_PADDING + 9 * 8.65 + 1  # room for 9 code characters
    app.set_source(source)
    assert app.line_number_gutter.value == "1\n2\n\n3"


def test_symbols_are_measured_wider_than_code_characters() -> None:
    """A line with arrows wraps sooner than its length in characters suggests."""
    app = CodeApp(DummyShell())  # ty: ignore[invalid-argument-type]
    app.code_char_width, app.symbol_char_width = 8.65, 11.37
    app.editor_width = EDITOR_SIDE_PADDING + 460  # the 1100 px layout in Edge
    line = "  x ← x - polynomial(coeffs, x)/derivative(coeffs, x)"  # 461.2 px

    assert wrapped_rows(line, app.text_width(), app.char_width) == 2
    assert wrapped_rows(line.replace("←", "="), app.text_width(), app.char_width) == 1


def test_a_row_can_also_end_after_a_slash() -> None:
    # "x ← f(x)/" ends the first row; "derivative(c)" fits whole on the second (3 rows if
    # the line could only break at spaces).
    assert wrapped_rows("x ← f(x)/derivative(c)", 14) == 2
    assert wrapped_rows("aaaa/bbbb", 6) == 2  # breaks after the slash, not inside a word
