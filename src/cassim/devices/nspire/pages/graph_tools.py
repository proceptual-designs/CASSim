"""The Graphs page's Window / Zoom and Trace tools (FR-GRAPH-002), without Flet.

Zoom - Box, In and Out and the two traces are *tools*: once chosen they take the arrows, Enter,
taps and Esc until Esc leaves them, as on the device (graphs2 D8, graphs4 D8 and D11, graphs5
R5-D11). Box asks `1st corner?` then `2nd corner?` and starts again; In and Out ask `Center?`.
A trace shows `f2: (4.71, -2)` at the lower right in the graph's colour (Float 3 digits, as the
Graphs settings' Display Digits), steps with Left and Right, pans the window at either edge,
moves between graphs with Up and Down, and goes to a typed x on Enter.

Choices made without a capture are marked in the code: the arrow step of the zoom pointer, Up
going to the previous graph (G-D11d: Up from f1 went to f3; an earlier note said f2) and the
automatic trace step, 1% of the window width (0.2 on the Standard window; Simon's choice, decision
0034 item 7, where the device stepped about 0.26 to 0.3, D27 and R5-D11).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from cassim.device.keys import Binding
from cassim.device.menu import MenuItem
from cassim.device.wizard import Field, Wizard
from cassim.graph.sampling import Viewport, Window
from cassim.graph.scene import Align, Box, Dots, Label, Segments, Shape, Stroke
from cassim.graph.zoom import (
    DECIMAL,
    QUADRANT_1,
    STANDARD,
    TRIG,
    parse_window_value,
    window_text,
    zoom_about,
    zoom_box,
    zoom_data,
    zoom_fit,
    zoom_square,
)

if TYPE_CHECKING:
    from cassim.devices.nspire.pages.graphs import FunctionEntry, Graphs


class Tool(StrEnum):
    ZOOM_BOX = "box"
    ZOOM_IN = "in"
    ZOOM_OUT = "out"
    TRACE = "trace"
    TRACE_ALL = "trace_all"
    ANALYZE = "analyze"  # Analyze Graph; its keys and marks are in `graph_analyze`
    # Actions (emulator run 7, R7-B8, R7-B10); their work is in `graph_actions`
    ATTRIBUTES = "attributes"
    TEXT = "text"
    COORDINATES = "coordinates"
    CALCULATE = "calculate"


ZOOM_TOOLS = (Tool.ZOOM_BOX, Tool.ZOOM_IN, Tool.ZOOM_OUT)
ACTION_TOOLS = {
    Tool.ATTRIBUTES: "Attributes: click a graph",
    Tool.TEXT: "Text: click where it goes",
    Tool.COORDINATES: "Coordinates and Equations: click a point or a graph",
    Tool.CALCULATE: "Calculate: click an expression",
}
TRACE_TOOLS = (Tool.TRACE, Tool.TRACE_ALL)
# Window / Zoom items that set the window at once, by their menu argument
_PRESETS = {"standard": STANDARD, "quadrant1": QUADRANT_1, "trig": TRIG, "decimal": DECIMAL}
_POINTER_STEPS = 160  # an arrow moves the zoom pointer 1/160 of the plot, 2 handheld px (R6-A6)
_TRACE_STEP = 0.01  # automatic trace step: 1% of the width (decision 0034, item 7)
_TRACE_MARGIN = 0.1  # a traced point off the top or bottom is brought 10% inside (R5-D11)
_TYPED = frozenset("0123456789.-−")
_FLOAT_DIGITS = 3  # the Graphs settings' Display Digits, Float 3 (graphs2 D1)
_WINDOW_NAMES = ("xmin", "xmax", "ymin", "ymax")


@dataclass
class ToolState:
    """What the page's current tool is doing. None of it is saved with the document."""

    tool: Tool | None = None
    pointer: tuple[float, float] | None = None  # the zoom pointer, in screen pixels
    corner: tuple[float, float] | None = None  # Zoom - Box's first corner, in graph units
    trace_index: int = 0  # which function the trace is on
    trace_x: float | None = None  # the traced x; a new trace starts where the last one left
    trace_step: float | None = None  # None is Automatic
    typed: str = ""  # an x being typed during a trace
    user_window: Window | None = None  # Zoom - User returns here
    analysis: str = ""  # the Analyze Graph item being used (`zero`, `integral`...)
    picked: list[str] = field(default_factory=list)  # its graphs, by name
    bounds: list[float] = field(default_factory=list)  # its bounds so far
    message: str = ""  # why the last analysis found nothing
    # A dialog an Actions tool wants opened: ("attributes", name) or ("text", "x,y")
    request: tuple[str, str] | None = None


def coordinate_text(value: float | None) -> str:
    """A traced coordinate in Float 3: three significant digits from 1 up, three decimal places
    below 1 (`4.71`, `0.027`, `-4.35`, `169`)."""
    if value is None or not math.isfinite(value):
        return "undef"
    if value == 0:
        return "0"
    text = _float_3(Decimal(repr(abs(value))))
    return f"-{text}" if value < 0 else text


def _float_3(value: Decimal) -> str:
    """Float 3 as the Calculator shows it (`core.format`), without the trailing point. Written
    here because `core.format` loads SymPy, which the UI worker must not (decision 0027)."""

    def trimmed(number: Decimal) -> str:
        text = format(number, "f")
        return text.rstrip("0").rstrip(".") if "." in text else text

    smallest = Decimal(1).scaleb(-_FLOAT_DIGITS)
    if smallest <= value < 1:
        return trimmed(value.quantize(smallest, ROUND_HALF_UP))
    step = Decimal(1).scaleb(value.adjusted() - _FLOAT_DIGITS + 1)
    rounded = value.quantize(step, ROUND_HALF_UP)
    exponent = rounded.adjusted()
    if 0 <= exponent < _FLOAT_DIGITS:
        return trimmed(rounded)
    mantissa = trimmed(rounded.scaleb(-exponent))
    return f"{mantissa if '.' in mantissa else mantissa + '.'}ᴇ{exponent}"


def _value(entry: FunctionEntry, x: float) -> float | None:
    if entry.compiled is None:
        return None
    try:
        value = entry.compiled(x)
    except ArithmeticError, TypeError, ValueError:
        return None
    return value if math.isfinite(value) else None


def plotted(graphs: Graphs) -> list[int]:
    """The functions a trace can visit: shown and plotted."""
    return [
        index
        for index, entry in enumerate(graphs.functions)
        if entry.visible and entry.compiled is not None
    ]


def set_window(graphs: Graphs, window: Window, *, user: bool = False) -> None:
    """Change the window; Window Settings, Box, In and Out also set the window Zoom - User
    returns to (graphs2 D8: User went back to the window after Zoom - In)."""
    graphs.window = window
    if user:
        graphs.tools.user_window = window


def zoom(graphs: Graphs, kind: str) -> None:
    """A Window / Zoom item by its menu argument."""
    state = graphs.tools
    if kind in _PRESETS:
        set_window(graphs, _PRESETS[kind])
    elif kind == "user":
        if state.user_window is not None:
            graphs.window = state.user_window
    elif kind == "fit":
        functions = [graphs.functions[index].compiled for index in plotted(graphs)]
        width = max(round(graphs.viewport_size[0]), 1)
        graphs.window = zoom_fit(graphs.window, [f for f in functions if f is not None], width)
    elif kind == "square":
        graphs.window = zoom_square(graphs.window, *graphs.viewport_size)
    elif kind == "data":
        graphs.window = zoom_data(graphs.window, [])  # no data plots on a Graphs page yet (4d)
    else:
        start(graphs, Tool(kind))


def start(graphs: Graphs, tool: Tool) -> None:
    state = graphs.tools
    state.typed = ""
    state.corner = None
    state.message = ""
    if tool in TRACE_TOOLS:
        indices = plotted(graphs)
        if not indices:
            state.tool = None
            return
        if state.tool not in TRACE_TOOLS:
            state.trace_index = (
                graphs.active_index if graphs.active_index in indices else indices[0]
            )
        if state.trace_index not in indices:
            state.trace_index = indices[0]
        window = graphs.window
        if state.trace_x is None:
            state.trace_x = (
                0.0 if window.x_min <= 0 <= window.x_max else (window.x_min + window.x_max) / 2
            )
        state.tool = tool
        _trace_to(graphs, state.trace_x)
        return
    width, height = graphs.viewport_size
    state.pointer = state.pointer or (width / 2, height / 2)
    state.tool = tool


def leave(graphs: Graphs) -> None:
    state = graphs.tools
    state.tool = None
    state.corner = None
    state.typed = ""
    state.analysis = ""
    state.picked = []
    state.bounds = []
    state.message = ""


def trace_step(graphs: Graphs) -> float:
    state = graphs.tools
    if state.trace_step is not None:
        return state.trace_step
    return (graphs.window.x_max - graphs.window.x_min) * _TRACE_STEP


def _trace_to(graphs: Graphs, x: float) -> None:
    """Move the trace to x, panning the window to keep the point in view (R5-D11: the window
    follows at either edge, and up or down when the point leaves the top or the bottom)."""
    state = graphs.tools
    state.trace_x = x
    window = graphs.window
    shift = x - window.x_max if x > window.x_max else x - window.x_min if x < window.x_min else 0
    if shift:
        window = Window(window.x_min + shift, window.x_max + shift, window.y_min, window.y_max)
    y = _value(graphs.functions[state.trace_index], x)
    if y is not None:
        height = window.y_max - window.y_min
        margin = height * _TRACE_MARGIN
        if y > window.y_max:
            window = Window(window.x_min, window.x_max, y + margin - height, y + margin)
        elif y < window.y_min:
            window = Window(window.x_min, window.x_max, y - margin, y - margin + height)
    graphs.window = window


def _switch_graph(graphs: Graphs, step: int) -> None:
    state = graphs.tools
    indices = plotted(graphs)
    if not indices:
        leave(graphs)
        return
    position = indices.index(state.trace_index) if state.trace_index in indices else 0
    state.trace_index = indices[(position + step) % len(indices)]
    if state.trace_x is not None:
        _trace_to(graphs, state.trace_x)


def key(graphs: Graphs, binding: Binding) -> bool:
    """A key while a tool is on. False leaves it to the page (the entry line, menus)."""
    state = graphs.tools
    if state.tool is None or state.tool is Tool.ANALYZE:
        return False
    if state.tool in TRACE_TOOLS:
        return _trace_key(graphs, binding)
    return _zoom_key(graphs, binding)


def _trace_key(graphs: Graphs, binding: Binding) -> bool:
    state = graphs.tools
    action = binding.action
    if plotted(graphs) == []:
        leave(graphs)
        return False
    if action in ("left", "right"):
        state.typed = ""
        step = trace_step(graphs)
        _trace_to(graphs, (state.trace_x or 0.0) + (step if action == "right" else -step))
    elif action in ("up", "down"):
        # Up goes to the previous graph, wrapping (G-D11d: Up from f1 went to f3)
        _switch_graph(graphs, -1 if action == "up" else 1)
    elif action == "escape":
        if state.typed:
            state.typed = ""
        else:
            leave(graphs)
    else:
        return _typed_key(graphs, binding)
    return True


def _typed_key(graphs: Graphs, binding: Binding) -> bool:
    """Typing an x during a trace, then Enter to go there (graphs4 D11)."""
    state = graphs.tools
    action = binding.action
    if action == "insert":
        if all(character in _TYPED for character in binding.arg):
            state.typed += binding.arg.replace("−", "-")
    elif action == "backspace":
        state.typed = state.typed[:-1]
    elif action == "enter":
        typed, state.typed = state.typed, ""
        try:
            x = parse_window_value(typed) if typed else None
        except ValueError:
            x = None
        if x is not None:
            _trace_to(graphs, x)
        elif not typed:
            # Enter with nothing typed leaves a point with its coordinates (R6-A3)
            graphs.keep_trace_point()
    else:
        return action in ("insert_linear", "delete")
    return True


def _zoom_key(graphs: Graphs, binding: Binding) -> bool:
    state = graphs.tools
    width, height = graphs.viewport_size
    x, y = state.pointer or (width / 2, height / 2)
    step = width / _POINTER_STEPS
    moves = {"left": (-step, 0), "right": (step, 0), "up": (0, -step), "down": (0, step)}
    if binding.action in moves:
        dx, dy = moves[binding.action]
        state.pointer = (min(max(x + dx, 0), width), min(max(y + dy, 0), height))
    elif binding.action == "enter":
        click(graphs, x, y)
    elif binding.action == "escape":
        leave(graphs)
    else:
        return False
    return True


def to_graph(graphs: Graphs, x: float, y: float) -> tuple[float, float]:
    """A screen point of the plot in graph units."""
    window = graphs.window
    width, height = graphs.viewport_size
    return (
        window.x_min + x * (window.x_max - window.x_min) / width,
        window.y_max - y * (window.y_max - window.y_min) / height,
    )


def click(graphs: Graphs, x: float, y: float) -> None:
    """A tap or Enter at screen point (x, y) while a tool is on."""
    state = graphs.tools
    state.pointer = (x, y)
    point = to_graph(graphs, x, y)
    if state.tool is Tool.ZOOM_BOX:
        if state.corner is None:
            state.corner = point
            return
        corner, state.corner = state.corner, None
        try:
            set_window(graphs, zoom_box(corner, point), user=True)
        except ValueError:
            return  # a box with no width or height does nothing; the tool asks again
        width, height = graphs.viewport_size
        state.pointer = (width / 2, height / 2)
    elif state.tool in (Tool.ZOOM_IN, Tool.ZOOM_OUT):
        factor = 0.5 if state.tool is Tool.ZOOM_IN else 2.0
        set_window(graphs, zoom_about(graphs.window, *point, factor), user=True)
        width, height = graphs.viewport_size
        state.pointer = (width / 2, height / 2)
    elif state.tool in TRACE_TOOLS:
        state.typed = ""
        _trace_to(graphs, point[0])
    else:
        _action_click(graphs, x, y, point)


def _action_click(graphs: Graphs, x: float, y: float, point: tuple[float, float]) -> None:
    """A tap with an Actions tool on: Attributes takes the curve under it, Text a place for
    text, Coordinates and Equations a point or a curve to label, Calculate a text to work out
    (emulator run 7, R7-B8, R7-B10)."""
    from cassim.devices.nspire.pages import graph_actions  # noqa: PLC0415

    state = graphs.tools
    if state.tool is Tool.ATTRIBUTES:
        index = graph_actions.curve_at(graphs, x, y)
        if index is not None:
            state.request = ("attributes", graphs.functions[index].name)
    elif state.tool is Tool.TEXT:
        state.request = ("text", f"{point[0]!r},{point[1]!r}")
    elif state.tool is Tool.COORDINATES:
        text = graph_actions.coordinates_text(graphs, x, y)
        if text is not None:
            graphs.texts.append(graph_actions.TextObject(point[0], point[1], text))
    elif state.tool is Tool.CALCULATE:
        index = graph_actions.text_at(graphs, x, y)
        value = graph_actions.calculate(graphs, index) if index is not None else None
        if index is not None and value is not None:
            item = graphs.texts[index]
            width = graphs.window.x_max - graphs.window.x_min
            graphs.texts.append(
                graph_actions.TextObject(item.x + width * 0.06 * len(item.text), item.y, value)
            )


def prompt(graphs: Graphs) -> str:
    state = graphs.tools
    if state.tool is Tool.ZOOM_BOX:
        return "2nd corner?" if state.corner is not None else "1st corner?"
    if state.tool in (Tool.ZOOM_IN, Tool.ZOOM_OUT):
        return "Center?"
    return ""


def readout(graphs: Graphs) -> str:
    """The trace's coordinate label: `f2: (4.71, -2)`, or the x being typed."""
    state = graphs.tools
    if state.tool not in TRACE_TOOLS or state.trace_x is None:
        return ""
    entry = graphs.functions[state.trace_index]
    if state.typed:
        return f"{entry.name}: x = {state.typed}"
    x = state.trace_x
    return f"{entry.name}: ({coordinate_text(x)}, {coordinate_text(_value(entry, x))})"


def shapes(graphs: Graphs, viewport: Viewport, colour: Callable[[str], str]) -> tuple[Shape, ...]:
    """The tool's marks: the zoom pointer and its prompt, the box being drawn, the trace points
    and the readout."""
    state = graphs.tools
    if state.tool is None:
        return ()
    if state.tool in ACTION_TOOLS:
        # the device shows the tool's icon at the top left until Esc (R7-B10); CASSim, its name
        return (Label(8, 4, ACTION_TOOLS[state.tool], 12),)
    window, width, height = viewport.window, viewport.width, viewport.height
    found: list[Shape] = []
    if state.tool in ZOOM_TOOLS:
        x, y = state.pointer or (width / 2, height / 2)
        size = 6.0
        found.append(
            Segments(((x - size, y), (x + size, y), (x, y - size), (x, y + size)), Stroke("ink"))
        )
        if state.corner is not None:
            cx, cy = window.to_screen(*state.corner, width, height)
            found.append(
                Box(min(x, cx), min(y, cy), abs(x - cx), abs(y - cy), Stroke("ink", 1, dashed=True))
            )
        found.append(Label(min(x + 8, width - 70), min(y + 8, height - 16), prompt(graphs), 11))
        return tuple(found)
    if state.tool not in TRACE_TOOLS or state.trace_x is None:
        return ()
    x_screen = window.to_screen(state.trace_x, 0, width, height)[0]
    indices = plotted(graphs) if state.tool is Tool.TRACE_ALL else [state.trace_index]
    if state.tool is Tool.TRACE_ALL:
        found.append(Segments(((x_screen, 0), (x_screen, height)), Stroke("ink", 2)))
    for index in indices:
        entry = graphs.functions[index]
        value = _value(entry, state.trace_x)
        if value is not None:
            point = window.to_screen(state.trace_x, value, width, height)
            found.append(Dots((point,), colour(entry.name), 9))
    current = graphs.functions[state.trace_index]
    found.append(
        Label(width - 4, height - 18, readout(graphs), 13, colour(current.name), Align.RIGHT)
    )
    return tuple(found)


def window_wizard(graphs: Graphs) -> Wizard:
    """Window Settings (D7): XMin, XMax, XScale, YMin, YMax, YScale, the values in full digits."""
    window = graphs.window
    auto = (("Auto", "Auto"),)
    fields = (
        Field("xmin", "XMin", window_text(window.x_min)),
        Field("xmax", "XMax", window_text(window.x_max)),
        Field("xscale", "XScale", "Auto", choices=auto),
        Field("ymin", "YMin", window_text(window.y_min)),
        Field("ymax", "YMax", window_text(window.y_max)),
        Field("yscale", "YScale", "Auto", choices=auto),
    )
    return Wizard(
        "Window Settings",
        fields,
        steps=lambda values: [Binding("graphs", f"window:{_window_argument(values)}")],
        check=_window_problems,
    )


def _window_values(values: Mapping[str, str]) -> list[float]:
    return [parse_window_value(values.get(name, "")) for name in _WINDOW_NAMES]


def _window_argument(values: Mapping[str, str]) -> str:
    return ",".join(repr(value) for value in _window_values(values))


def _window_problems(values: Mapping[str, str]) -> list[str]:
    problems = []
    for name, label in zip(_WINDOW_NAMES, ("XMin", "XMax", "YMin", "YMax"), strict=True):
        try:
            parse_window_value(values.get(name, ""))
        except ValueError:
            problems.append(f"{label}: enter a number")
    if problems:
        return problems
    x_min, x_max, y_min, y_max = _window_values(values)
    if x_min >= x_max:
        problems.append("XMin must be less than XMax")
    if y_min >= y_max:
        problems.append("YMin must be less than YMax")
    return problems


def apply_window(graphs: Graphs, argument: str) -> None:
    bounds = [float(value) for value in argument.split(",")]
    if len(bounds) != len(_WINDOW_NAMES):
        msg = "a window needs four values"
        raise ValueError(msg)
    set_window(graphs, Window(*bounds), user=True)


def trace_step_wizard(graphs: Graphs) -> Wizard:
    """Trace Step… (R5-D11): Automatic, or Enter Value… with the value."""
    step = graphs.tools.trace_step
    fields = (
        Field(
            "mode",
            "Trace Step",
            "auto" if step is None else "value",
            choices=(("auto", "Automatic"), ("value", "Enter Value…")),
        ),
        Field("value", "Value", "" if step is None else window_text(step)),
    )
    return Wizard(
        "Trace Step",
        fields,
        steps=lambda values: [
            Binding(
                "graphs",
                "trace_step:auto"
                if values["mode"] == "auto"
                else f"trace_step:{parse_window_value(values['value'])!r}",
            )
        ],
        check=_trace_step_problems,
    )


def _trace_step_problems(values: Mapping[str, str]) -> list[str]:
    if values.get("mode") != "value":
        return []
    try:
        step = parse_window_value(values.get("value", ""))
    except ValueError:
        return ["Value: enter a number"]
    return [] if step > 0 else ["Value: the step must be more than 0"]


def set_trace_step(graphs: Graphs, argument: str) -> None:
    if argument == "auto":
        graphs.tools.trace_step = None
        return
    step = float(argument)
    if not math.isfinite(step) or step <= 0:
        msg = "a trace step must be a positive number"
        raise ValueError(msg)
    graphs.tools.trace_step = step


def _action_result(graphs: Graphs, verb: str, rest: str) -> None:
    """What an Actions dialog or a curve drag sends back: `attributes:f1:{json}`,
    `text:x,y:words`, `drag_curve:index,dx,dy` (screen pixels)."""
    import json  # noqa: PLC0415

    from cassim.devices.nspire.pages import graph_actions  # noqa: PLC0415

    if verb == "attributes":
        name, _, values = rest.partition(":")
        graph_actions.apply_attributes(graphs, name, json.loads(values))
    elif verb == "text":
        place, _, words = rest.partition(":")
        x, y = (float(value) for value in place.split(","))
        if words.strip():
            graphs.texts.append(graph_actions.TextObject(x, y, words))
    else:
        index, dx, dy = rest.split(",")
        graph_actions.drag_curve(graphs, int(index), float(dx), float(dy))


def perform(graphs: Graphs, argument: str) -> None:
    """A `graphs` action that is not a dialog: `zoom:fit`, `tool:trace`, `tap:x,y`,
    `window:a,b,c,d`, `trace_step:0.5` or `escape`."""
    verb, _, rest = argument.partition(":")
    if verb == "zoom":
        zoom(graphs, rest)
    elif verb == "tool":
        start(graphs, Tool(rest))
    elif verb == "tap":
        if graphs.tools.tool is not None:
            x, y = (float(value) for value in rest.split(","))
            click(graphs, x, y)
    elif verb == "window":
        apply_window(graphs, rest)
    elif verb == "trace_step":
        set_trace_step(graphs, rest)
    elif verb in ("attributes", "text", "drag_curve"):
        _action_result(graphs, verb, rest)
    elif verb == "escape":
        leave(graphs)
    else:
        msg = f"unknown graphs action {argument!r}"
        raise ValueError(msg)


def window_zoom_menu() -> MenuItem:
    """Menu > 4 Window / Zoom, numbered as on the device (graphs4 D1)."""
    items = (
        ("1", "Window Settings…", "dialog:window"),
        ("2", "Zoom – Box", "zoom:box"),
        ("3", "Zoom – In", "zoom:in"),
        ("4", "Zoom – Out", "zoom:out"),
        ("5", "Zoom – Standard", "zoom:standard"),
        ("6", "Zoom – Quadrant 1", "zoom:quadrant1"),
        ("7", "Zoom – User", "zoom:user"),
        ("8", "Zoom – Trig", "zoom:trig"),
        ("9", "Zoom – Data", "zoom:data"),
        ("A", "Zoom – Fit", "zoom:fit"),
        ("B", "Zoom – Square", "zoom:square"),
        ("C", "Zoom – Decimal", "zoom:decimal"),
    )
    return MenuItem(
        "Window / Zoom",
        key="4",
        items=tuple(MenuItem(label, "graphs", argument, key=k) for k, label, argument in items),
    )


def trace_menu() -> MenuItem:
    """Menu > 5 Trace (graphs4 D1); Path Plot and the geometry traces are not built."""
    return MenuItem(
        "Trace",
        key="5",
        items=(
            MenuItem("Graph Trace", "graphs", "tool:trace", key="1"),
            MenuItem("Trace All", "graphs", "tool:trace_all", key="2"),
            MenuItem("Trace Step…", "graphs", "dialog:trace_step", key="3"),
            MenuItem("Path Plot", key="4", enabled=False),
            MenuItem("Geometry Trace", key="5", enabled=False),
            MenuItem("Erase Geometry Trace", key="6", enabled=False),
        ),
    )
