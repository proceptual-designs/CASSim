"""Analyze Graph on the Graphs page (FR-GRAPH-003), without Flet.

An item asks `graph?` when it needs one graph and the page has several (graphs2 D14), then
`lower bound?` and `upper bound?` with a dotted vertical line at the pointer (dy/dx asks
`position?`). A bound is set by a tap, by Enter at the pointer (Left and Right move it) or by a
typed number and Enter (R5-D33). The result stays on the page as an object that keeps only its
graphs' names and its bounds, so it is worked out again from the function each time the page is
drawn: a marked point moves when the function is redefined, and an integral's shading and value
follow it (R5-D32, R5-D33). The tool stays on for another go until Esc.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from cassim.device.menu import MenuItem
from cassim.devices.nspire.pages import graph_tools
from cassim.devices.nspire.pages.graph_tools import Tool, coordinate_text, plotted, to_graph
from cassim.graph.analysis import (
    bounded_area,
    derivative,
    find_inflection,
    find_intersection,
    find_maximum,
    find_minimum,
    find_zero,
    integral,
)
from cassim.graph.scene import Align, Box, Dots, Fill, Label, Segments, Shape, Stroke
from cassim.graph.zoom import parse_window_value

if TYPE_CHECKING:
    from cassim.device.keys import Binding
    from cassim.devices.nspire.pages.graphs import Graphs
    from cassim.graph.sampling import Viewport

type Function = Callable[[float], float]

# Menu > 6 Analyze Graph (graphs4 D1): argument, label, graphs used, bounds asked
ITEMS: tuple[tuple[str, str, int, int], ...] = (
    ("zero", "Zero", 1, 2),
    ("minimum", "Minimum", 1, 2),
    ("maximum", "Maximum", 1, 2),
    ("intersection", "Intersection", 2, 2),
    ("inflection", "Inflection", 1, 2),
    ("dydx", "dy/dx", 1, 1),
    ("integral", "Integral", 1, 2),
    ("bounded", "Bounded Area", 2, 2),
)
_SPEC = {name: (label, graphs, bounds) for name, label, graphs, bounds in ITEMS}
_POINTER_STEPS = 160  # 2 handheld px a press, as the zoom pointer (R6-A6)
_SHADE_POINTS = 80
_ZERO_RESIDUAL = 1e-9
_MIN_FILL_POINTS = 2
_EDGE = 1e-6  # a turning point this close to a bound (as a share of the span) is the bound
_TINY = 1e-8  # a found coordinate this small is shown as 0, as the device does
_TYPED = frozenset("0123456789.-−")


@dataclass(frozen=True)
class AnalysisObject:
    """A kept result: which item, on which graphs (by name), between which bounds."""

    kind: str
    names: tuple[str, ...]
    bounds: tuple[float, ...]

    def dump(self) -> dict[str, Any]:
        return {"kind": self.kind, "names": list(self.names), "bounds": list(self.bounds)}

    @classmethod
    def load(cls, data: object) -> AnalysisObject | None:
        if not isinstance(data, dict):
            return None
        kind, names, bounds = data.get("kind"), data.get("names"), data.get("bounds")
        if kind not in _SPEC or not isinstance(names, list) or not isinstance(bounds, list):
            return None
        _, graphs, count = _SPEC[kind]
        if len(names) != graphs or not all(isinstance(name, str) for name in names):
            return None
        if len(bounds) != count or not all(
            isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value)
            for value in bounds
        ):
            return None
        return cls(kind, tuple(names), tuple(float(value) for value in bounds))


@dataclass(frozen=True)
class Result:
    point: tuple[float, float] | None = None  # a marked point
    value: float | None = None  # an integral, an area or a slope


def menu() -> MenuItem:
    items = tuple(
        MenuItem(label, "graphs", f"analyze:{name}", key=str(number))
        for number, (name, label, _, _) in enumerate(ITEMS, start=1)
    )
    return MenuItem(
        "Analyze Graph",
        key="6",
        items=(*items, MenuItem("Analyze Conics", key="9", enabled=False)),
    )


def _function(graphs: Graphs, name: str) -> Function | None:
    entry = next((item for item in graphs.functions if item.name == name), None)
    if entry is None or entry.compiled is None:
        return None
    return entry.compiled


def _zero(function: Function, lower: float, upper: float) -> tuple[float, float]:
    try:
        return find_zero(function, lower, upper), 0.0
    except (ArithmeticError, ValueError) as error:
        # a zero that touches the axis (x^2 at 0) has no sign change: look for |f| = 0
        x, y = find_minimum(lambda t: abs(function(t)), lower, upper)
        if y > _ZERO_RESIDUAL:
            raise ValueError(str(error)) from error
        return x, 0.0


def _at_bound(
    point: tuple[float, float], function: Function, lower: float, upper: float
) -> tuple[float, float]:
    """A minimum or maximum reached at a bound is that bound's point: Minimum on x² from 0.943
    to 3 is `(0.943, 0.89)` (emulator run 6, R6-A8)."""
    edge = (upper - lower) * _EDGE
    for bound in (lower, upper):
        if abs(point[0] - bound) <= edge:
            return bound, function(bound)
    return point


def result(graphs: Graphs, item: AnalysisObject) -> Result | None:
    """The object's result from the functions as they are now, or None if there is none."""
    functions = [_function(graphs, name) for name in item.names]
    if any(function is None for function in functions):
        return None
    first = functions[0]
    assert first is not None
    second = functions[-1]
    assert second is not None
    lower, upper = min(item.bounds), max(item.bounds)
    points: dict[str, Callable[[], tuple[float, float]]] = {
        "zero": lambda: _zero(first, lower, upper),
        "minimum": lambda: _at_bound(find_minimum(first, lower, upper), first, lower, upper),
        "maximum": lambda: _at_bound(find_maximum(first, lower, upper), first, lower, upper),
        "inflection": lambda: find_inflection(first, lower, upper),
        "intersection": lambda: find_intersection(first, second, lower, upper),
    }
    values: dict[str, Callable[[], float]] = {
        "integral": lambda: integral(first, lower, upper),
        "bounded": lambda: bounded_area(first, second, lower, upper),
    }
    try:
        if item.kind in points:
            return Result(points[item.kind]())
        if item.kind in values:
            return Result(value=values[item.kind]())
        return Result((lower, first(lower)), derivative(first, lower))  # dy/dx
    except ArithmeticError, ValueError, TypeError:
        return None


def start(graphs: Graphs, kind: str) -> None:
    if kind not in _SPEC:
        msg = f"unknown Analyze Graph item {kind!r}"
        raise ValueError(msg)
    indices = plotted(graphs)
    needed = _SPEC[kind][1]
    if len(indices) < needed:
        return  # nothing to analyse
    graph_tools.leave(graphs)
    state = graphs.tools
    state.tool = Tool.ANALYZE
    state.analysis = kind
    names = [graphs.functions[index].name for index in indices]
    if len(names) == needed:
        state.picked = names  # one graph (or two for Intersection): no `graph?` prompt
    width, height = graphs.viewport_size
    state.pointer = state.pointer or (width / 2, height / 2)
    state.trace_index = indices[0]


def prompt(graphs: Graphs) -> str:
    state = graphs.tools
    if state.tool is not Tool.ANALYZE:
        return ""
    if state.message:
        return ""  # the dialog shows it
    _, needed, bounds = _SPEC[state.analysis]
    if len(state.picked) < needed:
        return f"graph? {graphs.functions[state.trace_index].name}"
    text = "position?" if bounds == 1 else "upper bound?" if state.bounds else "lower bound?"
    return f"{text} {state.typed}" if state.typed else text


def _choose_graph(graphs: Graphs, name: str) -> None:
    state = graphs.tools
    if name not in state.picked:
        state.picked.append(name)


def _set_bound(graphs: Graphs, x: float) -> None:
    state = graphs.tools
    _, _, count = _SPEC[state.analysis]
    state.bounds.append(x)
    if len(state.bounds) < count:
        return
    item = AnalysisObject(state.analysis, tuple(state.picked), tuple(state.bounds))
    state.bounds = []
    if len(plotted(graphs)) > _SPEC[state.analysis][1]:
        state.picked = []
    if result(graphs, item) is None:
        label = _SPEC[item.kind][0].lower()
        noun = "zero" if item.kind == "zero" else label
        state.message = f"No {noun} found within the specified bounds"
        return
    graphs.objects.append(item)


def key(graphs: Graphs, binding: Binding) -> bool:
    """A key while an Analyze Graph item is on; False leaves it to the page."""
    state = graphs.tools
    if state.tool is not Tool.ANALYZE:
        return False
    action = binding.action
    if state.message:
        # The no-result dialog (R6-A8): Enter or Esc closes it; other keys wait for it.
        if action in ("enter", "escape"):
            state.message = ""
        return True
    picking = len(state.picked) < _SPEC[state.analysis][1]
    width, height = graphs.viewport_size
    x, y = state.pointer or (width / 2, height / 2)
    if action in ("left", "right"):
        step = width / _POINTER_STEPS
        state.pointer = (min(max(x + (step if action == "right" else -step), 0), width), y)
    elif action in ("up", "down") and picking:
        indices = plotted(graphs)
        position = indices.index(state.trace_index) if state.trace_index in indices else 0
        state.trace_index = indices[(position + (1 if action == "down" else -1)) % len(indices)]
    elif (action == "insert" and not picking) or action == "backspace":
        _type(state, binding)
    elif action == "enter":
        _enter(graphs, x)
    elif action == "escape":
        if state.typed:
            state.typed = ""
        else:
            graph_tools.leave(graphs)
    else:
        return action in ("insert_linear", "delete", "up", "down")
    return True


def _type(state: graph_tools.ToolState, binding: Binding) -> None:
    """A typed bound: digits, a point and a minus are added; Backspace takes one off."""
    if binding.action == "backspace":
        state.typed = state.typed[:-1]
    elif all(character in _TYPED for character in binding.arg):
        state.typed += binding.arg.replace("−", "-")


def _enter(graphs: Graphs, pointer_x: float) -> None:
    state = graphs.tools
    if len(state.picked) < _SPEC[state.analysis][1]:
        _choose_graph(graphs, graphs.functions[state.trace_index].name)
        return
    if state.typed:
        typed, state.typed = state.typed, ""
        try:
            value = parse_window_value(typed)
        except ValueError:
            return
        _set_bound(graphs, value)
        return
    _set_bound(graphs, to_graph(graphs, pointer_x, 0)[0])


def click(graphs: Graphs, x: float, y: float) -> None:
    """A tap: the graph nearest the tap when `graph?` is asked, else a bound at its x."""
    state = graphs.tools
    if state.message:  # a tap closes the no-result dialog and does nothing else
        state.message = ""
        return
    state.pointer = (x, y)
    state.typed = ""
    gx, gy = to_graph(graphs, x, y)
    if len(state.picked) < _SPEC[state.analysis][1]:
        best: tuple[float, str] | None = None
        for index in plotted(graphs):
            entry = graphs.functions[index]
            function = _function(graphs, entry.name)
            try:
                value = function(gx) if function is not None else math.nan
            except ArithmeticError, ValueError, TypeError:
                continue
            if math.isfinite(value) and entry.name not in state.picked:
                distance = abs(value - gy)
                if best is None or distance < best[0]:
                    best = (distance, entry.name)
        if best is not None:
            _choose_graph(graphs, best[1])
        return
    _set_bound(graphs, gx)


def perform(graphs: Graphs, argument: str) -> bool:
    """`analyze:<item>`, or a tap while an item is on. False: not Analyze Graph's."""
    verb, _, rest = argument.partition(":")
    if verb == "analyze":
        start(graphs, rest)
        return True
    if verb == "tap" and graphs.tools.tool is Tool.ANALYZE:
        x, y = (float(value) for value in rest.split(","))
        click(graphs, x, y)
        return True
    return False


def _point_label(point: tuple[float, float]) -> str:
    x, y = (0.0 if abs(value) < _TINY else value for value in point)
    return f"({coordinate_text(x)},{coordinate_text(y)})"


def _shade(graphs: Graphs, viewport: Viewport, item: AnalysisObject) -> list[tuple[float, float]]:
    window, width, height = viewport.window, viewport.width, viewport.height
    lower, upper = min(item.bounds), max(item.bounds)
    functions = [_function(graphs, name) for name in item.names]
    xs = [lower + (upper - lower) * index / _SHADE_POINTS for index in range(_SHADE_POINTS + 1)]

    def values(function: Function | None) -> list[tuple[float, float]]:
        found = []
        for x in xs:
            try:
                y = function(x) if function is not None else 0.0
            except ArithmeticError, ValueError, TypeError:
                continue
            if math.isfinite(y):
                found.append(window.to_screen(x, y, width, height))
        return found

    top = values(functions[0])
    bottom = values(functions[1]) if len(functions) > 1 else values(None)
    return [*top, *reversed(bottom)]


def object_shapes(graphs: Graphs, viewport: Viewport) -> tuple[Shape, ...]:
    """The kept results, worked out from the functions as they are now."""
    window, width, height = viewport.window, viewport.width, viewport.height
    found: list[Shape] = []
    for item in graphs.objects:
        outcome = result(graphs, item)
        if outcome is None:
            continue
        if outcome.point is not None:
            x, y = window.to_screen(*outcome.point, width, height)
            found.append(Dots(((x, y),), "ink", 7))
            text = _point_label(outcome.point)
            if outcome.value is not None:
                text = f"dy/dx={coordinate_text(outcome.value)}"
            found.append(Label(x + 4, y + 2, text, 13))
            continue
        outline = _shade(graphs, viewport, item)
        if len(outline) > _MIN_FILL_POINTS:
            found.append(Fill(tuple(outline), "axis", 0.45))
        ends = tuple(window.to_screen(bound, 0, width, height) for bound in sorted(item.bounds))
        if item.kind == "integral":
            found.append(Dots(ends, "ink", 6))
        middle = (item.bounds[0] + item.bounds[1]) / 2
        mx, my = window.to_screen(middle, 0, width, height)
        found.append(
            Label(
                mx,
                max(min(my - 18, height - 16), 0),
                coordinate_text(outcome.value),
                13,
                "ink",
                Align.CENTRE,
            )
        )
    return tuple(found)


_DIALOG_WIDTH = 220
_DIALOG_HEIGHT = 74


def _message_dialog(message: str, width: float, height: float) -> tuple[Shape, ...]:
    """A no-result dialog over the graph, closed by OK (Enter), Esc or a tap: the device shows
    "No zero found within the specified bounds" in an Error dialog (emulator run 6, R6-A8)."""
    box_width = min(_DIALOG_WIDTH, width - 8)
    left, top = (width - box_width) / 2, (height - _DIALOG_HEIGHT) / 2
    corners = (
        (left, top),
        (left + box_width, top),
        (left + box_width, top + _DIALOG_HEIGHT),
        (left, top + _DIALOG_HEIGHT),
    )
    return (
        Fill(corners, "paper", 1.0),
        Box(left, top, box_width, _DIALOG_HEIGHT, Stroke("ink", 1)),
        Label(left + 8, top + 6, "Error", 12),
        Label(left + 8, top + 24, message, 11, width=box_width - 16),
        Label(left + box_width - 8, top + _DIALOG_HEIGHT - 18, "OK", 12, align=Align.RIGHT),
    )


def tool_shapes(graphs: Graphs, viewport: Viewport) -> tuple[Shape, ...]:
    """The item's prompt at the lower left and the dotted line at the pointer."""
    state = graphs.tools
    if state.tool is not Tool.ANALYZE:
        return ()
    width, height = viewport.width, viewport.height
    if state.message:
        return _message_dialog(state.message, width, height)
    found: list[Shape] = [Label(4, height - 18, prompt(graphs), 12)]
    picking = len(state.picked) < _SPEC[state.analysis][1]
    if not picking and not state.message:
        x = (state.pointer or (width / 2, height / 2))[0]
        found.append(Segments(((x, 0), (x, height)), Stroke("ink", 1, dashed=True)))
    found.extend(
        Dots((viewport.window.to_screen(bound, 0, width, height),), "ink", 6)
        for bound in state.bounds
    )
    return tuple(found)
