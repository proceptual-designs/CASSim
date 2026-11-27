"""Focused state tests for the standalone pseudocode Code view."""

import asyncio
import sys
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any, cast

import flet as ft
import pytest

from cassim.app.appearance import Appearance
from cassim.app.theme import DARK, HIGH_CONTRAST
from cassim.devices.pseudocode.ui.app import (
    BISECTION,
    CONDITION_COLUMN_WIDTH,
    D4_SAMPLE_SPACE,
    DICE_MAX_STATS,
    EDITOR_SIDE_PADDING,
    EDITOR_TOP,
    EXAMPLE,
    GCD_LCM,
    LEFT_RIEMANN,
    LINE_COLUMN_WIDTH,
    LINEAR,
    OUTPUT_COLUMN_WIDTH,
    POLYNOMIAL_NEWTON,
    PRIME_SIEVE,
    ROW_HEIGHT,
    VARIABLE_COLUMN_WIDTH,
    CodeApp,
    wrapped_rows,
)
from cassim.devices.pseudocode.ui.call_window import CallWindow
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

    def write(self, key: str, text: str) -> None:
        """Storage is not kept here (StoringShell keeps it)."""


def typed(app: CodeApp, text: str, selection_end: int | None) -> SimpleNamespace:
    """Send the fallback editor a change, with the selection Python last heard about, and
    return what the editor then holds (with no event loop the typing aid acts at once)."""
    selection = None if selection_end is None else SimpleNamespace(end=selection_end)
    control = SimpleNamespace(value=text, selection=selection, update=lambda: None)
    app.on_fallback_source(SimpleNamespace(control=control))  # ty: ignore[invalid-argument-type]
    return SimpleNamespace(value=app.current_source)


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

    app.cassim_action("home")

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


def call_window_app(width: float = 1100) -> CodeApp:
    shell = DummyShell()
    shell.page = SimpleNamespace(overlay=[], update=lambda: None, width=width, height=760)
    app = CodeApp(shell)  # ty: ignore[invalid-argument-type]
    app.trace_source = DOUBLING  # the program the run came from, as Run sets it
    app.result = run(DOUBLING, Settings())
    app.cursor = len(app.result.steps)
    return app


def highlighted(window: CallWindow) -> list[str]:
    """The code lines the window highlights (the line of the last trace row shown)."""
    found: list[str] = []

    def walk(control: object) -> None:
        if isinstance(control, ft.Container) and control.bgcolor == DARK.line_highlight:
            found.extend(texts(control))
        for name in ("content", "controls"):
            child = getattr(control, name, None)
            for item in child if isinstance(child, list) else [child]:
                if isinstance(item, ft.Control):
                    walk(item)

    walk(window.frame)
    return found


def test_a_call_row_opens_its_code_and_trace_in_a_window() -> None:
    """FR-TRC-013: the call's Calcs cell has an expand button; it opens a window with the
    function's code beside that call's trace, and a call inside it has its own button."""
    app = call_window_app()
    table, _, _ = app.update_vertical_trace()
    calls = app.call_rows(table)
    assert calls == {1: 1}  # the top-level row `f(1)`, after the `define` row

    app.show_call(calls[1])
    window = app.call_windows[-1]
    assert app.page.overlay == [window.host]
    shown = texts(window.frame)
    assert shown[0] == "f(1): n = 1"  # the title bar
    assert {"define f(n)", "  return f(m)", "end"} <= set(shown)  # the function's code
    assert {"4 / 4 steps", "Calcs / Output", "f(2)"} <= set(shown)  # its trace
    tooltips = _tooltips(window.frame)
    assert [tip for tip in tooltips if tip.startswith("Expand ")] == ["Expand f(2)"]
    assert {"Resize m column", "Move window", "Resize window", "Close"} <= set(tooltips)
    body = window.frame.content.controls[0].controls[1].content  # ty: ignore[unresolved-attribute]
    assert isinstance(body, ft.Row)  # code beside trace on a desktop

    window.close()
    assert app.page.overlay == []
    assert app.call_windows == []


def test_a_call_window_stacks_code_over_trace_on_a_phone() -> None:
    app = call_window_app(width=390)
    app.show_call(1)
    window = app.call_windows[-1]
    body = window.frame.content.controls[0].controls[1].content  # ty: ignore[unresolved-attribute]
    assert isinstance(body, ft.Column)
    assert (window.left, window.width) == (8.0, 390 - 16)


def test_a_call_window_steps_through_the_call_and_follows_it_in_the_code() -> None:
    """FR-TRC-013: Step, First and Last move through the call's own rows, as in the pane, and
    the code highlights the line of the last row shown."""
    app = call_window_app()
    app.show_call(1)
    window = app.call_windows[-1]

    def press(label: str) -> list[str]:
        button = next(b for b in _buttons(window.frame) if b.content == label)
        assert button.on_click is not None
        cast("Callable[[object], object]", button.on_click)(None)  # the window's lambdas
        return texts(window.frame)

    assert highlighted(window) == ["6", "  return f(m)"]  # the call's last row
    assert "0 / 4 steps" in press("First")
    assert "m = 1×2 = 2" not in texts(window.frame)
    assert highlighted(window) == ["1", "define f(n)"]
    after_step = press("Step")
    assert "1 / 4 steps" in after_step
    assert "m = 1×2 = 2" in after_step
    assert "f(2)" not in after_step
    assert highlighted(window) == ["2", "  m ← n*2"]
    assert "4 / 4 steps" in press("Last")
    assert "f(2)" in texts(window.frame)


def test_a_call_window_moves_and_resizes_within_the_page() -> None:
    app = call_window_app()
    app.show_call(1)
    window = app.call_windows[-1]
    left, top, width, height = window.left, window.top, window.width, window.height

    def drag(handler: Callable[[ft.DragUpdateEvent], None], x: float, y: float) -> None:
        """A drag from (500, 300) by (x, y) in three updates, as the browser reports it: each
        update carries the pointer's position, not the step."""
        start = SimpleNamespace(global_position=SimpleNamespace(x=500, y=300))
        window.start_drag(start)  # ty: ignore[invalid-argument-type]
        for part in (1, 2, 3):
            at = SimpleNamespace(x=500 + x * part / 3, y=300 + y * part / 3)
            handler(SimpleNamespace(global_position=at))  # ty: ignore[invalid-argument-type]

    drag(window.move, -30, 21)
    assert (window.frame.left, window.frame.top) == (left - 30, top + 21)
    drag(window.resize, 51, 42)
    assert (window.frame.width, window.frame.height) == (width + 51, height + 42)
    drag(window.resize, -5000, -5000)
    assert (window.width, window.height) == (320, 240)  # no smaller than this
    drag(window.move, -5000, -5000)
    assert (window.left, window.top) == (0, 0)  # still on the page


def test_a_call_window_opened_from_another_is_offset() -> None:
    app = call_window_app()
    app.show_call(1)
    app.show_call(3)  # f(2), called inside f(1)
    first, second = app.call_windows
    assert (second.left, second.top) == (first.left + 24, first.top + 24)
    assert app.page.overlay == [first.host, second.host]


def _buttons(control: object) -> list[ft.Button]:
    found: list[ft.Button] = []
    if isinstance(control, ft.Button):
        found.append(control)
    for name in ("content", "controls"):
        child = getattr(control, name, None)
        for item in child if isinstance(child, list) else [child]:
            if isinstance(item, ft.Control):
                found.extend(_buttons(item))
    return found


def _tooltips(control: object) -> list[str]:
    found: list[str] = []
    tooltip = getattr(control, "tooltip", None)
    if isinstance(control, (ft.IconButton, ft.GestureDetector)) and isinstance(tooltip, str):
        found.append(tooltip)
    for name in ("content", "controls"):
        child = getattr(control, name, None)
        for item in child if isinstance(child, list) else [child]:
            if isinstance(item, ft.Control):
                found.extend(_tooltips(item))
    return found


def test_newton_example_uses_short_names_and_sits_with_numerical_methods() -> None:
    assert "coefficient" not in POLYNOMIAL_NEWTON
    assert "for each coeff in coeffs" in POLYNOMIAL_NEWTON
    output = run(POLYNOMIAL_NEWTON, Settings()).output
    assert len(output) == 8  # one x for each step of Newton's method
    assert output[-1] == "2.09455"  # the root after 8 steps of Newton's method

    app = CodeApp(DummyShell())  # ty: ignore[invalid-argument-type]
    groups = {
        str(group.content): [
            str(item.content) for item in group.controls if isinstance(item, ft.MenuItemButton)
        ]
        for group in app.build_examples_menu().controls
        if isinstance(group, ft.SubmenuButton)
    }
    assert groups["Numerical methods"] == ["Left Riemann sum", "Polynomial + Newton"]
    assert groups["Number theory"] == ["GCD and LCM", "Prime sieve (1 to 100)"]


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


def test_prime_sieve_example_lists_the_primes_up_to_100() -> None:
    result = run(PRIME_SIEVE, Settings())

    assert result.error is None
    primes = [int(p) for p in result.output[0].strip("[]").split(", ")]
    assert primes == [p for p in range(2, 101) if all(p % d for d in range(2, p))]
    assert len(primes) == 25


class PausePage(SimpleNamespace):
    """A page whose scheduled tasks are kept, to run when the test says the typing paused."""

    def __init__(self) -> None:
        super().__init__(waiting=[])

    def run_task(self, handler: Callable[..., object], *args: object) -> None:
        self.waiting.append((handler, args))


def paused_app(monkeypatch: pytest.MonkeyPatch) -> tuple[CodeApp, PausePage]:
    async def no_wait(_seconds: float) -> None:
        return None

    monkeypatch.setattr("cassim.devices.pseudocode.ui.app.asyncio.sleep", no_wait)
    shell = DummyShell()
    page = PausePage()
    shell.page = page
    app = CodeApp(shell)  # ty: ignore[invalid-argument-type]
    app.fallback_editor.update = lambda: None  # ty: ignore[invalid-assignment]
    app.current_source = ""
    return app, page


def type_keys(app: CodeApp, text: str) -> None:
    for end in range(len(app.current_source) + 1, len(text) + 1):
        control = SimpleNamespace(value=text[:end], selection=None, update=lambda: None)
        app.on_fallback_source(SimpleNamespace(control=control))  # ty: ignore[invalid-argument-type]


def pause(page: PausePage) -> None:
    """Typing stopped: every scheduled check runs, oldest first, as their sleeps end."""
    waiting, page.waiting = page.waiting, []
    for handler, args in waiting:
        asyncio.run(cast("Callable[..., Any]", handler)(*args))


def test_typing_aid_waits_for_a_pause_then_converts_what_was_typed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-SYN-013: converting sent the whole text back from Python, overwriting keys typed in
    the meantime; now nothing is sent until typing pauses, then everything typed converts."""
    app, page = paused_app(monkeypatch)

    type_keys(app, "y <- @pi")
    assert app.current_source == "y <- @pi"  # nothing sent back while typing
    assert len(page.waiting) == len("y <- @pi")
    pause(page)  # only the last check acts; the others see that typing went on

    assert app.current_source == "y ← π"
    assert app.fallback_editor.value == "y ← π"
    assert app.typing_undo == ("y ← π", "y <- @pi")  # Ctrl+Z restores the typed text


def test_typing_aid_leaves_a_paste_and_strings_alone(monkeypatch: pytest.MonkeyPatch) -> None:
    app, page = paused_app(monkeypatch)
    pasted = "x <- 1\nprint x"
    control = SimpleNamespace(value=pasted, selection=None, update=lambda: None)
    app.on_fallback_source(SimpleNamespace(control=control))  # ty: ignore[invalid-argument-type]
    pause(page)
    assert app.current_source == pasted

    type_keys(app, pasted + '\nprint "<-"')
    pause(page)
    assert app.current_source.endswith('print "<-"')


def test_a_typed_name_starting_with_e_is_not_an_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    app, page = paused_app(monkeypatch)
    type_keys(app, "print @exp + @e")
    pause(page)
    assert app.current_source == "print @exp + ⅇ"


def test_typing_aid_puts_the_caret_back_after_what_was_typed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-SYN-013: after the conversion the caret is where the typing left it, not at the end
    of the text (setting the text would put it there)."""
    app, page = paused_app(monkeypatch)
    app.current_source = "a\nprint b"
    for text in ("a \nprint b", "a <\nprint b", "a <-\nprint b"):  # typed after the `a`
        control = SimpleNamespace(value=text, selection=None, update=lambda: None)
        app.on_fallback_source(SimpleNamespace(control=control))  # ty: ignore[invalid-argument-type]
    pause(page)

    assert app.current_source == "a ←\nprint b"
    selection = app.fallback_editor.selection
    assert selection is not None
    assert (selection.base_offset, selection.extent_offset) == (3, 3)  # just after the ←


def test_a_call_window_is_modal_and_rearranges_as_it_is_resized() -> None:
    """FR-TRC-013: a dimmed layer over the page takes its clicks while the window is open, and
    the code and trace sit side by side or stack as the window's width allows."""
    app = call_window_app()
    app.show_call(1)
    window = app.call_windows[-1]
    barrier, frame = window.host.controls
    assert frame is window.frame
    assert isinstance(barrier, ft.Container)
    assert (barrier.left, barrier.top, barrier.right, barrier.bottom) == (0, 0, 0, 0)
    assert barrier.bgcolor is not None
    assert isinstance(window.body.content, ft.Row)  # 960 px wide: side by side

    def resize_to(width: float) -> None:
        start = SimpleNamespace(global_position=SimpleNamespace(x=0, y=0))
        window.start_drag(start)  # ty: ignore[invalid-argument-type]
        to = SimpleNamespace(x=width - window.width, y=0)
        window.resize(SimpleNamespace(global_position=to))  # ty: ignore[invalid-argument-type]

    resize_to(500)
    assert isinstance(window.body.content, ft.Column)  # narrow: code above trace
    resize_to(800)
    assert isinstance(window.body.content, ft.Row)


def test_a_call_window_divider_resizes_its_columns() -> None:
    """FR-TRC-013: the line between code and trace is a resize grip, as in the main view."""
    app = call_window_app()
    app.show_call(1)
    window = app.call_windows[-1]
    assert "Resize columns" in [
        control.tooltip
        for control in window.body.content.controls  # ty: ignore[unresolved-attribute]
        if isinstance(control, ft.GestureDetector)
        for control in [control.content]
    ]
    width = window.width - 16 - 12  # less the body's padding and the divider
    start = window.first.width
    assert start is not None
    assert start == pytest.approx(0.42 * width)

    def drag(dx: float) -> None:
        window.resize_columns(SimpleNamespace(global_delta=SimpleNamespace(x=dx, y=0)))  # ty: ignore[invalid-argument-type]

    drag(100)
    assert window.first.width == pytest.approx(start + 100)
    drag(10_000)
    assert window.split == 0.8  # no further than this
    resize = SimpleNamespace(global_position=SimpleNamespace(x=0, y=0))
    window.start_drag(resize)  # ty: ignore[invalid-argument-type]
    window.resize(SimpleNamespace(global_position=SimpleNamespace(x=-100, y=0)))  # ty: ignore[invalid-argument-type]
    assert window.first.width == pytest.approx(0.8 * (window.width - 28))  # keeps its share


def test_help_opens_the_pseudocode_page_of_the_wiki() -> None:
    shell = DummyShell()
    asked: list[tuple[str, str]] = []
    shell.menu_action = lambda action, page="": asked.append((action, page)) or True  # ty: ignore[unresolved-attribute]
    app = CodeApp(shell)  # ty: ignore[invalid-argument-type]

    app.cassim_action("help")  # CASSim > Help (wiki)…, which the shell opens for every app

    assert asked == [("help", "Pseudocode.html")]


def test_step_in_the_main_table_steps_over_a_call_and_highlights_the_line() -> None:
    """Step runs a call's own lines in one step (they are seen in its window), and the band
    behind the editor follows the line of the last row, as the call window does."""
    app = call_window_app()
    app.fallback_editor.value = DOUBLING
    app.to_start(None)
    assert app.status.value == "0 / 4 steps"  # define, the call f(1), y ← its value, print y
    assert app.line_band.visible is False

    app.step_forward(None)
    assert (app.status.value, app.highlighted_line) == ("1 / 4 steps", 1)  # define f(n)
    assert app.line_band.top == EDITOR_TOP

    app.step_forward(None)  # over f(1): its lines have all run
    assert (app.status.value, app.highlighted_line) == ("2 / 4 steps", 8)
    assert app.line_band.top == EDITOR_TOP + 7 * ROW_HEIGHT
    assert [
        row.line for row in trace.call_table(app.result, Settings(), 1, cursor=app.cursor).rows
    ] == [2, 3, 6, 6]

    app.step_back(None)
    assert (app.status.value, app.highlighted_line) == ("1 / 4 steps", 1)
    app.to_end(None)
    assert app.status.value == "4 / 4 steps"


def test_a_condition_inside_a_function_is_not_a_main_table_column() -> None:
    """`m > 4` runs inside f: like f's variables, it belongs to the call's window."""
    app = call_window_app()
    assert app.condition_labels() == ()
    _, columns, _ = app.update_vertical_trace()
    assert not [key for key, _, _ in columns if key.startswith("condition:")]


class StoringShell(DummyShell):
    """A shell with storage, a file picker and dialogs, for Open, Save, Import and Export."""

    def __init__(self) -> None:
        super().__init__()
        self.stored: dict[str, str] = {}
        self.downloads: list[tuple[str, str]] = []
        self.picked: str | None = None
        self.dialogs: list[Any] = []
        self.tasks: list[Any] = []
        self.page = SimpleNamespace(
            width=1000,
            show_dialog=self.dialogs.append,
            pop_dialog=lambda: self.dialogs.pop() if self.dialogs else None,
            run_task=lambda handler, *args: self.tasks.append(handler(*args)),
        )

    async def read(self, key: str) -> str | None:
        return self.stored.get(key)

    def write(self, key: str, text: str) -> None:
        self.stored[key] = text

    def remove(self, key: str) -> None:
        self.stored.pop(key, None)

    def confirm(self, title: str, message: str, action: str, accept) -> None:
        asyncio.run(accept())

    async def save_file(self, name: str, text: str, title: str = "") -> None:
        self.downloads.append((name, text))

    async def pick_file(self, extensions: tuple[str, ...], title: str = "") -> str | None:
        return self.picked

    def run_tasks(self) -> None:
        tasks, self.tasks = self.tasks, []
        for task in tasks:
            asyncio.run(task)


def test_open_and_save_use_app_storage_and_files_are_import_and_export() -> None:
    """FR-EDT-002, FR-EDT-003, FR-DOC-010 (decision 0033): Save and Open keep programs by name
    in the app's storage with their language; only Import and Export touch a file."""
    shell = StoringShell()
    app = CodeApp(shell)  # ty: ignore[invalid-argument-type]
    labels = [str(getattr(item, "content", "")) for item in app.doc_menu.controls]
    assert labels[:5] == ["Open…", "Save", "Save as…", "Import file…", "Export file…"]
    app.saved.fresh()
    app.set_source("x ← 1\nprint x\n")
    assert app.saved.dirty()

    app.saved.save()  # never saved: asks for a name
    dialog = shell.dialogs[-1]
    dialog.content.controls[1].value = "First steps"
    dialog.actions[0].on_click(None)
    shell.run_tasks()
    assert not shell.downloads  # nothing was downloaded
    assert '"language": "pseudocode"' in shell.stored["doc:First steps"]
    assert shell.notices[-1][0] == "Saved"
    assert not app.saved.dirty()

    app.set_source("y ← 2\n")
    app.saved.open()  # the list of saved programs; the open one has changes, so it asks first
    shell.dialogs[-1].content.controls[0].on_click(None)
    shell.run_tasks()
    assert app.source() == "x ← 1\nprint x\n"
    assert app.saved.name == "First steps"

    asyncio.run(app.export_file())
    assert shell.downloads[-1] == ("First steps.pseudo.txt", "x ← 1\nprint x\n")

    shell.picked = "z ← 3\n"
    app.import_file()
    shell.run_tasks()
    assert app.source() == "z ← 3\n"
    assert app.saved.current.stored is None  # an imported file is saved nowhere here yet


class ThemedShell(DummyShell):
    """A shell with the shared theme (SDD-15 section 7.1)."""

    def __init__(self, appearance: Appearance) -> None:
        super().__init__()
        self.appearance = appearance
        self.saved_appearances: list[Appearance] = []
        self.dialogs: list[ft.AlertDialog] = []
        self.page = SimpleNamespace(
            update=lambda: None,
            show_dialog=self.dialogs.append,
            pop_dialog=self.dialogs.pop,
            width=1000,
            height=700,
        )

    def save_appearance(self, appearance: Appearance) -> None:
        self.appearance = appearance
        self.saved_appearances.append(appearance)


def test_the_toolbar_and_page_follow_the_shared_theme() -> None:
    """SDD-15 gaps 1 and 2: the toolbar was drawn in Dark's colours whatever the theme, and
    the theme chosen elsewhere was not used."""
    shell = ThemedShell(Appearance("High contrast", {"High contrast": {"key": "#101010"}}))
    app = CodeApp(shell)  # ty: ignore[invalid-argument-type]
    app.apply_theme()
    assert shell.page.bgcolor == HIGH_CONTRAST.background
    for button in app.styled_buttons():
        assert button.style is not None
        fills = button.style.bgcolor
        assert isinstance(fills, dict)
        assert fills[ft.ControlState.DEFAULT] == "#101010"
    assert app.line_band.bgcolor == HIGH_CONTRAST.line_highlight


def test_appearance_is_saved_for_every_app() -> None:
    """SDD-15 gap 1: Appearance… was applied but never saved, so a reload was Dark again."""
    shell = ThemedShell(Appearance())
    app = CodeApp(shell)  # ty: ignore[invalid-argument-type]
    app.cassim_action("appearance")
    (shown,) = shell.dialogs
    assert shown.title.value == "Appearance"  # ty: ignore[unresolved-attribute]
    choice = next(c for c in shown.content.controls if isinstance(c, ft.SegmentedButton))  # ty: ignore[unresolved-attribute]
    choice.selected = ["Light"]
    choice.on_change(None)
    assert shell.page.theme_mode == ft.ThemeMode.LIGHT  # previewed
    save = shown.actions[-1].controls[-1]  # ty: ignore[unresolved-attribute]
    save.on_click(None)
    assert [a.theme_name for a in shell.saved_appearances] == ["Light"]
    assert app.appearance.theme_name == "Light"
