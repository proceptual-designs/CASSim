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
        shapes: list[Shape] = []
        grid: list[tuple[float, float]] = []
        for x in tick_values(self.window.x_min, self.window.x_max):
            px, _ = self.window.to_screen(x, 0, viewport.width, viewport.height)
            grid.extend(((px, 0), (px, viewport.height)))
            if x:
                _, y = self.window.to_screen(x, 0, viewport.width, viewport.height)
                shapes.append(Label(px + 3, y + 3, _format_tick(x), 10, "axis"))
        for y in tick_values(self.window.y_min, self.window.y_max):
            _, py = self.window.to_screen(0, y, viewport.width, viewport.height)
            grid.extend(((0, py), (viewport.width, py)))
            if y:
                x, _ = self.window.to_screen(0, y, viewport.width, viewport.height)
                shapes.append(Label(x + 4, py - 12, _format_tick(y), 10, "axis"))
        shapes.append(Segments(tuple(grid), Stroke("grid", 0.6)))
        x_axis = self.window.to_screen(0, 0, viewport.width, viewport.height)
        shapes.append(
            Segments(
                (
                    (0, x_axis[1]),
                    (viewport.width, x_axis[1]),
                    (x_axis[0], 0),
                    (x_axis[0], viewport.height),
                ),
                Stroke("axis", 1.2),
            )
        )
        shapes.extend(
            (
                Label(8, 6, "Functions", 12),
                Label(viewport.width - 6, viewport.height - 18, "x", 11, "axis", Align.RIGHT),
            )
        )
        scene = Scene(
            viewport.width,
            viewport.height,
            (
                Layer("grid", tuple(shapes)),
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


def _format_tick(value: float) -> str:
    return f"{value:g}" if math.isfinite(value) else ""


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
