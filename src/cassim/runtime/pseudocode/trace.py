"""Trace tables built from a recorded run (docs/pseudocode/trace-tables.md).

Both layouts are views of the same `Step` list: building one never re-runs the program, and each
takes a `cursor` (number of steps shown) so the table fills in as the student steps forwards.
"""

from dataclasses import dataclass, field, replace

from cassim.runtime.pseudocode import arith
from cassim.runtime.pseudocode.settings import Settings
from cassim.runtime.pseudocode.steps import RunResult, Step
from cassim.runtime.pseudocode.tree import (
    Define,
    For,
    ForEach,
    If,
    Program,
    RepeatTimes,
    RepeatUntil,
    Stmt,
    While,
)

TICK, CROSS = "✔", "❌"


@dataclass(frozen=True, slots=True)
class VerticalRow:
    step: int
    line: int
    cells: dict[str, str]  # variable -> value, only where it changed
    calc: str
    conditions: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class VerticalTable:
    variables: list[str]
    conditions: list[str] = field(default_factory=list)
    rows: list[VerticalRow] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class VerticalSelection:
    """Columns requested in a vertical trace view."""

    variables: tuple[str, ...] = ()
    conditions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class HorizontalRow:
    line: int
    code: str
    cells: list[str]  # one per column


@dataclass(slots=True)
class HorizontalTable:
    columns: list[str]
    rows: list[HorizontalRow] = field(default_factory=list)


def _show(value: object, settings: Settings) -> str:
    return arith.format_value(value, settings, minus=arith.MINUS)


def calc_text(step: Step) -> str:
    """The Calcs / Output cell of a step."""
    if step.cond is not None:
        return f"{step.cond[0]} is {'true' if step.cond[1] else 'false'}"
    if step.output is not None:
        return step.output
    return step.calc


def _shown(result: RunResult, cursor: int | None) -> list[Step]:
    end = len(result.steps) if cursor is None else cursor
    return [s for s in result.steps[:end] if s.kind != "halt"]


def vertical(
    result: RunResult, settings: Settings, *, cursor: int | None = None, max_depth: int = 0
) -> VerticalTable:
    """One row per executed line; a variable cell is filled only on the row where it changes.

    `max_depth` 0 shows top-level lines only (a function call is one row); a larger value also
    shows the lines run inside functions.
    """
    return _vertical_table([s for s in _shown(result, cursor) if s.depth <= max_depth], settings)


def call_steps(result: RunResult, call: int, *, cursor: int | None = None) -> list[Step]:
    """The lines run directly inside the call recorded as step `call`, up to `cursor`.

    Lines of calls made from inside it are left out; each of those has its own `call` step."""
    shown = _shown(result, cursor)
    if not 0 <= call < len(shown) or shown[call].kind != "call":
        return []
    depth = shown[call].depth
    inside: list[Step] = []
    for s in shown[call + 1 :]:
        if s.depth <= depth:
            break
        if s.depth == depth + 1:
            inside.append(s)
    return inside


def call_table(
    result: RunResult, settings: Settings, call: int, *, cursor: int | None = None
) -> VerticalTable:
    """The vertical trace of one function call, as `vertical` draws the top level.

    A call made from inside it is one row whose parameters are left out: they belong to that
    call's own table, not to this call's variables."""
    steps = [
        replace(s, changes=()) if s.kind == "call" else s
        for s in call_steps(result, call, cursor=cursor)
    ]
    return _vertical_table(steps, settings)


def call_parameters(result: RunResult, call: int, settings: Settings) -> str:
    """`n = 1, k = 2`: the values the call recorded as step `call` started with."""
    if not 0 <= call < len(result.steps) or result.steps[call].kind != "call":
        return ""
    return ", ".join(f"{c.name} = {_show(c.new, settings)}" for c in result.steps[call].changes)


def _vertical_table(steps: list[Step], settings: Settings) -> VerticalTable:
    table = VerticalTable([])
    for s in steps:
        for c in s.changes:
            if c.name not in table.variables:
                table.variables.append(c.name)
        if s.cond is not None and s.cond[0] not in table.conditions:
            table.conditions.append(s.cond[0])
    for s in steps:
        cells = {c.name: _show(c.new, settings) for c in s.changes}
        conditions = {s.cond[0]: "true" if s.cond[1] else "false"} if s.cond is not None else {}
        table.rows.append(VerticalRow(s.index, s.line, cells, calc_text(s), conditions))
    return table


def vertical_choices(
    result: RunResult, settings: Settings, *, max_depth: int = 0
) -> VerticalSelection:
    """The variable and condition columns available for one recorded run."""
    table = vertical(result, settings, max_depth=max_depth)
    return VerticalSelection(tuple(table.variables), tuple(table.conditions))


def selected_vertical(
    result: RunResult,
    settings: Settings,
    selection: VerticalSelection,
    *,
    cursor: int | None = None,
    max_depth: int = 0,
) -> VerticalTable:
    """A vertical table containing only selected variable and condition columns."""
    table = vertical(result, settings, cursor=cursor, max_depth=max_depth)
    variables = [name for name in table.variables if name in selection.variables]
    chosen_conditions = {
        key.partition(": ")[2] if ": " in key else key for key in selection.conditions
    }
    conditions = [name for name in table.conditions if name in chosen_conditions]
    rows = [
        VerticalRow(
            row.step,
            row.line,
            {name: value for name, value in row.cells.items() if name in selection.variables},
            row.calc,
            {name: value for name, value in row.conditions.items() if name in chosen_conditions},
        )
        for row in table.rows
    ]
    return VerticalTable(variables, conditions, rows)


def _lines(stmts: list[Stmt], in_loop: bool, out: set[tuple[int, bool]]) -> None:
    for s in stmts:
        out.add((s.line, in_loop))
        match s:
            case If():
                for _, body, line in s.branches:
                    out.add((line, in_loop))
                    _lines(body, in_loop, out)
                if s.orelse is not None:
                    out.add((s.else_line, in_loop))
                    _lines(s.orelse, in_loop, out)
            case While() | For() | ForEach() | RepeatTimes():
                _lines(s.body, True, out)
            case RepeatUntil():
                _lines(s.body, True, out)
                out.add((s.until_line, True))
            case Define():
                _lines(s.body, in_loop, out)
            case _:
                pass


def _source_lines(stmts: list[Stmt]) -> list[tuple[int, bool]]:
    found: set[tuple[int, bool]] = set()
    _lines(stmts, False, found)
    return sorted(found)


def _region(program: Program, loop_line: int) -> tuple[list[Stmt], str]:
    """The function that holds the loop (and its name), or the whole program if at top level."""
    for s in program.body:
        if isinstance(s, Define) and any(line == loop_line for line, _ in _source_lines(s.body)):
            return [s], s.name
    return [s for s in program.body if not isinstance(s, Define)], ""


def horizontal(
    result: RunResult, program: Program, settings: Settings, *, cursor: int | None = None
) -> HorizontalTable | None:
    """The desk-check layout, or None when the run has more than one loop or a nested loop.

    Columns are Init, then one per loop pass (the last holds the final failing test and anything
    after the loop). Rows are the source lines of the function holding the loop, or of the program.
    """
    if not result.horizontal_eligible:
        return None
    steps = _shown(result, cursor)
    looped = [s for s in result.steps if s.kind != "halt" and s.loop is not None]
    if not looped:
        return None
    assert looped[0].loop is not None
    region, function = _region(program, looped[0].loop[0])
    passes = max(s.loop[1] for s in looped if s.loop)
    columns = ["Init", *(f"Loop {n}" for n in range(1, passes + 1))]
    cells: dict[tuple[int, int], list[str]] = {}
    seen_loop = False
    for s in steps:
        if s.function != function:
            continue
        if s.loop is not None:
            column, seen_loop = s.loop[1], True
        else:
            column = passes if seen_loop else 0
        text = _cell(s, settings)
        line = (
            region[0].line if s.kind == "call" and function else s.line
        )  # the call fills `define`
        if text:
            cells.setdefault((line, column), []).append(text)
    executed = {line for line, _ in cells}
    table = HorizontalTable(columns)
    for line, in_loop in _source_lines(region):
        row = []
        for column in range(len(columns)):
            texts = cells.get((line, column))
            if texts:
                row.append("; ".join(texts))
            elif in_loop and column > 0 and line in executed:
                row.append("(skip)")
            else:
                row.append("")
        table.rows.append(HorizontalRow(line, program.lines[line - 1].strip(), row))
    return table


def _cell(step: Step, settings: Settings) -> str:
    if step.cond is not None:
        return f"{step.cond[0]} {TICK if step.cond[1] else CROSS}"
    if step.output is not None:
        return step.output
    changes = "; ".join(f"{c.name} ← {_show(c.new, settings)}" for c in step.changes)
    if step.kind == "call":
        return f"{step.calc}; {changes}" if changes else step.calc
    return changes or step.calc
