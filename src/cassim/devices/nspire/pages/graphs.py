"""Function Graphs page data and scenes (FR-GRAPH-003, FR-GRAPH-004, FR-GRAPH-006)."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from cassim.core.compat.math_source import compile_math_source
from cassim.core.values import Expr
from cassim.device.clipboard import Clipboard
from cassim.device.engine import RemoteSession, graph_compile_op
from cassim.device.keys import Binding
from cassim.devices.nspire.pages.calculator import Calculator
from cassim.doc.document import PageType
from cassim.graph.sampling import (
    CompiledFunction,
    Viewport,
    Window,
    sample_function,
    tick_values,
)
from cassim.graph.scene import Align, Label, Layer, Scene, Segments, Stroke

if TYPE_CHECKING:
    from collections.abc import Generator

    from cassim.core.session import Session
    from cassim.doc.document import Page, Problem
    from cassim.graph.scene import Shape

_FUNCTION_RE = re.compile(r"f([1-9]\d?)$")
_MAX_FUNCTION_NUMBER = 99
_COLOURS = ("curve1", "curve2", "curve3", "curve4")
_WINDOW_FIELDS = 4


@dataclass
class FunctionEntry:
    name: str
    editing: Calculator = field(repr=False)
    expression: str = ""
    visible: bool = True
    source: str | None = field(default=None, repr=False)
    compiled: CompiledFunction | None = field(default=None, repr=False)
    error: str = ""


class Graphs:
    """A Graphs page's function definitions and view settings."""

    def __init__(
        self,
        session: Session | RemoteSession,
        reserved: tuple[str, ...] = (),
        clipboard: Clipboard | None = None,
    ) -> None:
        self.session = session
        self.clipboard = clipboard if clipboard is not None else Clipboard()
        self.window = Window()
        self._reserved_names = set(reserved)
        first = self._next_function_name(reserved)
        self.functions = [self._entry(first)] if int(first[1:]) <= _MAX_FUNCTION_NUMBER else []
        self.active_index = 0
        self._next_name = int(first[1:]) + 1
        self._viewport_width = 1.0
        self._viewport_height = 1.0

    def _entry(self, name: str) -> FunctionEntry:
        return FunctionEntry(name, Calculator(self.session, self.clipboard))

    def _next_function_name(self, reserved: tuple[str, ...]) -> str:
        numbers = [
            int(match[1])
            for name in (
                *(variable.name for variable in self.session.variables()),
                *reserved,
            )
            if (match := _FUNCTION_RE.fullmatch(name)) is not None
        ]
        return f"f{max(numbers, default=0) + 1}"

    def add_function(self) -> FunctionEntry:
        if self._next_name > _MAX_FUNCTION_NUMBER:
            msg = "all graph function slots are in use"
            raise ValueError(msg)
        name = f"f{self._next_name}"
        while self.session.is_defined(name) or name in self._reserved_names:
            self._next_name += 1
            if self._next_name > _MAX_FUNCTION_NUMBER:
                msg = "all graph function slots are in use"
                raise ValueError(msg)
            name = f"f{self._next_name}"
        entry = self._entry(name)
        self._next_name += 1
        self.functions.append(entry)
        return entry

    def reserve_function_name(self, name: str) -> None:
        self._reserved_names.add(name)

    def edit(self, binding: Binding) -> None:
        if self.functions:
            self.functions[self.active_index].editing.perform(binding)

    def submit_editor(self, index: int) -> None:
        if not 0 <= index < len(self.functions):
            msg = f"no graph function at index {index}"
            raise IndexError(msg)
        self.active_index = index
        editor = self.functions[index].editing.editor
        editor.complete_brackets()
        self.submit(index, editor.linear())

    def submit(self, index: int, expression: str) -> None:
        if not 0 <= index < len(self.functions):
            msg = f"no graph function at index {index}"
            raise IndexError(msg)
        entry = self.functions[index]
        expression = expression.strip()
        editor = entry.editing.editor
        if editor.linear() != expression:
            editor.clear()
            editor.insert_linear(expression)
            entry.editing.forget_undo()
        if not expression:
            entry.error = "Enter an expression for the function."
            return
        entry.expression = expression
        entry.error = ""
        entry.compiled = None
        entry.source = None
        if isinstance(self.session, RemoteSession):
            self.session.outbox.append(graph_compile_op(entry.name, expression))
            entry.error = "Plotting…"
        else:
            self._compile_local(self.session, entry)
        next_name = f"f{self._next_name}"
        if (
            index == len(self.functions) - 1
            and self._next_name <= _MAX_FUNCTION_NUMBER
            and not self.session.is_defined(next_name)
            and next_name not in self._reserved_names
        ):
            self.add_function()

    def _compile_local(self, session: Session, entry: FunctionEntry) -> None:
        from cassim.core.compat.sympy_adapter import compile_math  # noqa: PLC0415 (lazy SymPy import)

        definition = session.eval(f"{entry.name}(x):={entry.expression}")
        if definition.error is not None:
            entry.error = definition.error
            return
        parameter = "_cassim_graph_parameter"
        while session.is_defined(parameter):
            parameter += "_"
        expanded = session.preview(f"{entry.name}({parameter})")
        variable = session.preview(parameter)
        if expanded.error is not None or not isinstance(expanded.value, Expr):
            entry.error = expanded.error or "Graph function must be real-valued."
            return
        if variable.error is not None or not isinstance(variable.value, Expr):
            entry.error = "Could not create graph parameter."
            return
        try:
            source, _ = compile_math(expanded.value.raw, variable.value.raw)
            entry.source = source
            entry.compiled = CompiledFunction(source, compile_math_source(source))
        except ValueError as error:
            entry.error = str(error)

    def update(self) -> None:
        if not isinstance(self.session, RemoteSession):
            return
        for entry in self.functions:
            replies = self.session.graph_inbox.pop(entry.name, [])
            if not replies:
                continue
            reply = replies[-1]
            entry.source = reply["source"]
            entry.error = reply["error"] or ""
            entry.compiled = (
                None
                if entry.source is None
                else CompiledFunction(entry.source, compile_math_source(entry.source))
            )

    def set_window(self, window: Window) -> None:
        self.window = window

    def toggle(self, name: str) -> None:
        entry = next((item for item in self.functions if item.name == name), None)
        if entry is None:
            msg = f"no graph function named {name!r}"
            raise ValueError(msg)
        entry.visible = not entry.visible

    def zoom(self, factor: float) -> None:
        self.gesture(0, 0, factor, self._viewport_width / 2, self._viewport_height / 2)

    def gesture(self, dx: float, dy: float, factor: float, x: float, y: float) -> None:
        """Pan in screen pixels and zoom around a screen-space focal point."""
        values = (dx, dy, factor, x, y)
        if not all(math.isfinite(value) for value in values) or factor <= 0:
            msg = "graph gesture values must be finite and zoom must be positive"
            raise ValueError(msg)
        width, height = self._viewport_width, self._viewport_height
        window = self.window
        x_shift = dx * (window.x_max - window.x_min) / width
        y_shift = dy * (window.y_max - window.y_min) / height
        window = Window(
            window.x_min - x_shift,
            window.x_max - x_shift,
            window.y_min + y_shift,
            window.y_max + y_shift,
        )
        if factor != 1:
            x_anchor = window.x_min + x * (window.x_max - window.x_min) / width
            y_anchor = window.y_max - y * (window.y_max - window.y_min) / height
            x_span = (window.x_max - window.x_min) * factor
            y_span = (window.y_max - window.y_min) * factor
            x_min = x_anchor - x * x_span / width
            y_max = y_anchor + y * y_span / height
            window = Window(x_min, x_min + x_span, y_max - y_span, y_max)
        self.window = window

    def scene(self, width: float, height: float) -> Scene:
        viewport = Viewport(self.window, max(width, 120), max(height, 100))
        self._viewport_width, self._viewport_height = viewport.width, viewport.height
        scene = Scene(
            viewport.width,
            viewport.height,
            (
                Layer("grid", tuple(_axis_shapes(viewport))),
                Layer(
                    "curves",
                    tuple(
                        curve
                        for index, entry in enumerate(self.functions)
                        if entry.visible and entry.compiled is not None
                        for curve in sample_function(
                            entry.compiled,
                            viewport,
                            stroke=Stroke(_COLOURS[index % len(_COLOURS)], 2),
                        )
                    ),
                ),
            ),
        )
        return scene


def _axis_shapes(viewport: Viewport) -> list[Shape]:
    window, width, height = viewport.window, viewport.width, viewport.height
    origin_x, origin_y = window.to_screen(0, 0, width, height)
    segments: list[tuple[float, float]] = []
    labels: list[Shape] = []
    tick_size = 3.0
    if window.y_min <= 0 <= window.y_max:
        segments.extend(((0, origin_y), (width, origin_y)))
        segments.extend(((width - 5, origin_y - 4), (width, origin_y)))
        segments.extend(((width - 5, origin_y + 4), (width, origin_y)))
        ticks = tick_values(window.x_min, window.x_max)
        for value in ticks:
            x, _ = window.to_screen(value, 0, width, height)
            segments.extend(((x, origin_y - tick_size), (x, origin_y + tick_size)))
        label_y = min(max(origin_y + 4, 0), height - 12)
        minimum, maximum = _format_end_values(window.x_min, window.x_max)
        labels.extend(
            (
                Label(2, label_y, minimum, 10, "axis"),
                Label(width - 2, label_y, maximum, 10, "axis", Align.RIGHT),
                Label(width - 4, max(origin_y - 15, 0), "x", 11, "axis", Align.RIGHT),
            )
        )
        positive = (
            next((value for value in ticks if 0 < value < window.x_max), None)
            if window.x_min <= 0
            else None
        )
        if positive is not None:
            x, _ = window.to_screen(positive, 0, width, height)
            labels.append(Label(x + 3, label_y, _format_tick(positive), 10, "axis"))
    if window.x_min <= 0 <= window.x_max:
        segments.extend(((origin_x, 0), (origin_x, height)))
        segments.extend(((origin_x - 4, 5), (origin_x, 0)))
        segments.extend(((origin_x + 4, 5), (origin_x, 0)))
        ticks = tick_values(window.y_min, window.y_max)
        for value in ticks:
            _, y = window.to_screen(0, value, width, height)
            segments.extend(((origin_x - tick_size, y), (origin_x + tick_size, y)))
        label_x = max(origin_x - 6, 0)
        minimum, maximum = _format_end_values(window.y_min, window.y_max)
        labels.extend(
            (
                Label(label_x, 1, maximum, 10, "axis", Align.RIGHT),
                Label(label_x, height - 12, minimum, 10, "axis", Align.RIGHT),
                Label(min(origin_x + 5, width - 11), 1, "y", 11, "axis"),
            )
        )
        positive = (
            next((value for value in ticks if 0 < value < window.y_max), None)
            if window.y_min <= 0
            else None
        )
        if positive is not None:
            _, y = window.to_screen(0, positive, width, height)
            labels.append(
                Label(label_x, max(y - 12, 0), _format_tick(positive), 10, "axis", Align.RIGHT)
            )
    return [Segments(tuple(segments), Stroke("axis", 1.2)), *labels] if segments else []


def _format_end_values(minimum: float, maximum: float) -> tuple[str, str]:
    for precision in range(3, 18):
        labels = (f"{minimum:.{precision}g}", f"{maximum:.{precision}g}")
        if labels[0] != labels[1]:
            return labels
    return (repr(minimum), repr(maximum))


def _format_tick(value: float) -> str:
    return f"{value:.3g}" if math.isfinite(value) else ""


def new_graphs(problem: Problem) -> Graphs:
    reserved = tuple(
        entry.name
        for page in problem.pages
        if (graphs := graphs_of(page)) is not None
        for entry in graphs.functions
        if entry.expression
    )
    return Graphs(problem.session, reserved, problem.clipboard)


def dump_graphs(graphs: Graphs) -> dict[str, Any]:
    from cassim.devices.nspire.pages import dump_nodes  # noqa: PLC0415

    return {
        "window": [
            graphs.window.x_min,
            graphs.window.x_max,
            graphs.window.y_min,
            graphs.window.y_max,
        ],
        "functions": [
            {
                "name": item.name,
                "expression": item.expression,
                "visible": item.visible,
                "nodes": dump_nodes(item.editing.editor.root),
            }
            for item in graphs.functions
            if item.expression or not item.editing.editor.is_empty
        ],
    }


def load_graphs(
    page_type: PageType, problem: Problem, data: dict[str, Any]
) -> Generator[Any, None, Graphs]:
    from cassim.devices.nspire.pages import load_nodes  # noqa: PLC0415

    graphs = new_graphs(problem)
    window = data.get("window")
    if (
        isinstance(window, list)
        and len(window) == _WINDOW_FIELDS
        and all(isinstance(value, int | float) and not isinstance(value, bool) for value in window)
    ):
        bounds = tuple(float(value) for value in window)
        if (
            all(math.isfinite(value) for value in bounds)
            and bounds[0] < bounds[1]
            and bounds[2] < bounds[3]
        ):
            graphs.window = Window(*bounds)
    entries = data.get("functions")
    if isinstance(entries, list):
        for saved in entries:
            if not isinstance(saved, dict):
                continue
            name, expression = saved.get("name"), saved.get("expression")
            if not isinstance(name, str) or not _FUNCTION_RE.fullmatch(name):
                continue
            if not isinstance(expression, str):
                continue
            while len(graphs.functions) <= int(name[1:]) - 1:
                graphs.add_function()
            entry = next((item for item in graphs.functions if item.name == name), None)
            if entry is None:
                continue
            graphs.reserve_function_name(name)
            entry.visible = saved.get("visible") is not False
            if expression.strip():
                graphs.submit(graphs.functions.index(entry), expression)
            nodes = saved.get("nodes")
            if isinstance(nodes, str | list):
                editor = entry.editing.editor
                editor.clear()
                editor.root = load_nodes(nodes)
                editor.pos = len(editor.root)
                entry.editing.forget_undo()
    yield from ()
    return graphs


def graphs_of(page: Page | None) -> Graphs | None:
    return page.model if page is not None and isinstance(page.model, Graphs) else None
