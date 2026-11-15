"""One Lists & Spreadsheet page, headless: cells, linked and formula columns, and recalculation.

The sheet runs in the engine beside the Problem's `Session` (decision 0031): its named columns
are the Problem's list variables, so a column named `xs` and the list `xs` are one thing. The
sheet keeps what was typed (cell text, formulas, names) and the values computed from it.

- A cell holds an entry as typed (`5`, `1/3`, `2^0.5`, `"text"`, `_`), a formula (`=a1+1`) or a
  value put there from a list. A column may have a column formula (`=a[]^2`) that fills it.
- Row 0 of a column stands for its column formula, so every formula is a node `(column, row)`.
- After any change the formulas that depend on it are evaluated again in dependency order, and
  each named column whose values changed is written to its variable. `sync` brings the sheet up
  to date after the Problem's variables have changed elsewhere (a Calculator entry).

Behaviour follows emulator check 6 (`docs/testing/emulator-sheet3-results.md`, part E, and
`emulator-sharing-results.md`, part G). What it did not show is marked in the code as a guess.
"""

import re
from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass, field, fields, is_dataclass, replace

from cassim.core import ast, errors
from cassim.core.catalog.statistics import RESULT_COMMANDS
from cassim.core.compat import sympy_adapter as cas
from cassim.core.errors import TIError
from cassim.core.evaluator import Evaluator
from cassim.core.format import to_text
from cassim.core.parser import parse
from cassim.core.scope import Function
from cassim.core.session import Session
from cassim.core.settings import variable_key
from cassim.core.values import Empty, Expr, ListValue, MatrixValue, Str, Value
from cassim.sheet import refs
from cassim.sheet.refs import COLUMNS, ROWS, Column, Found, Ref, Span, Variable

type Key = tuple[int, int]  # (column, row); row 0 is the column formula

# Stat Calculations: a column formula that is one of these commands fills the column with the
# values of `stat.results`; `: CopyVar stat.RegEqn,f1` after it saves the equation (slice 3c).
_RESULT_COMMANDS = frozenset(name.casefold() for name in RESULT_COMMANDS)
_SAVE = ": CopyVar stat.RegEqn,"
_SAVE_RE = re.compile(r"\s*:\s*CopyVar\s+stat\.RegEqn\s*,\s*(\w+)\s*$", re.IGNORECASE)

# A placeholder for each reference in a formula: a name nobody types, read as one name.
_PLACEHOLDER = "ϟ"
# Typed spellings an entry shows in TI's form (check 6, E5: `pi` shows as π, `sqrt` stays).
_SPELLING = {"pi": "π", "infinity": "∞", "@e": "ⅇ", "@i": "ⅈ"}
_SPELLING_RE = re.compile(r"(?<![\w@])(?:pi|infinity|@e|@i)(?!\w)")

# Dialog texts seen on the emulator (check 6).
SYNTAX_ERROR = "Syntax Error"
INVALID_INPUT = "Cannot accept change: Invalid input."
DURING_INSERTION = "Syntax error during insertion."
CIRCULAR = "Circular definition"
LINK_ERROR = "Link Error"
LINKED_TWICE = "Cannot link to same list/variable twice"
STAT_VARIABLE = "Variable Error. You cannot use the Stat variable in the Lists & Spreadsheet."


@dataclass(frozen=True, slots=True)
class Entry:
    """A cell typed without `=`, kept as typed. Formulas still use its value (check 6, E5)."""

    text: str


@dataclass(frozen=True, slots=True)
class Formula:
    """A cell or column formula, without its `=`."""

    text: str


@dataclass(frozen=True, slots=True)
class Constant:
    """A value put in a cell from a list, a sort or a paste: there is no text to read again."""

    value: Value


type Content = Entry | Formula | Constant


@dataclass(frozen=True, slots=True)
class Failed:
    """A cell that shows #ERR."""


type Computed = Value | Failed


@dataclass(frozen=True, slots=True)
class Shown:
    """A cell as drawn: its text, and whether it sits on the right (a number) or the left."""

    text: str
    right: bool = False


@dataclass(frozen=True, slots=True)
class Notice:
    """A dialog to show after a change that was kept, such as "Syntax Error in Cell: d8"."""

    title: str
    message: str


class SheetError(Exception):
    """A change the sheet refused. The cell or name cell stays in edit mode with its text."""

    def __init__(self, title: str, message: str) -> None:
        super().__init__(message)
        self.title = title
        self.message = message


DATA_LOSS = "Data Loss"
DATA_LOSS_MESSAGE = (
    "This operation may overwrite data in the current column(s). Do you wish to proceed?"
)


class DataLossError(SheetError):
    """The action needs an OK first: "Data Loss" with OK and Cancel. Call again with
    `confirm=True` after OK."""

    def __init__(self) -> None:
        super().__init__(DATA_LOSS, DATA_LOSS_MESSAGE)


class ConflictError(SheetError):
    """A formula names something that is both a cell and a variable, such as `d1` (check run 2,
    E7). The caller asks "Cell or Variable?" for each name and enters the formula again with the
    answers in `choose`."""

    def __init__(self, formula: str, names: tuple[str, ...]) -> None:
        super().__init__("Conflict Detected", f"={formula}.")
        self.names = names


@dataclass(slots=True)
class ColumnInfo:
    name: str | None = None  # the linked list variable, folded
    shown_name: str | None = None  # as typed
    formula: str | None = None  # the column formula, without `=`
    failed: bool = False  # the column formula failed: every cell shows #ERR


@dataclass(frozen=True, slots=True)
class _Inputs:
    """What a formula reads."""

    cells: frozenset[Key] = frozenset()
    columns: frozenset[int] = frozenset()
    names: frozenset[str] = frozenset()


@dataclass(slots=True)
class _Outcome:
    changed: set[Key] = field(default_factory=set)
    notices: list[Notice] = field(default_factory=list)


class Sheet:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._contents: dict[Key, Content] = {}
        self._values: dict[Key, Computed] = {}
        self._columns = [ColumnInfo() for _ in range(COLUMNS)]
        self._inputs: dict[Key, _Inputs] = {}  # each formula's inputs, row 0 for a column's
        # Who reads what, so a change reaches its readers without a search of every formula.
        self._cell_readers: dict[Key, set[Key]] = {}
        self._readers_within: dict[int, set[Key]] = {}  # read some cell of the column
        self._column_readers: dict[int, set[Key]] = {}  # read the column whole, `a[]`
        self._name_readers: dict[str, set[Key]] = {}
        self._seen = session.scope.revision  # the Problem's revision this sheet is up to date at
        self.revision = 0  # raised by every change to what is drawn
        self._locks: tuple[set[str], set[str]] = (set(), set())  # (lists, read-only) it holds

    # ----- reading -------------------------------------------------------------------------

    def column(self, column: int) -> ColumnInfo:
        return self._columns[column]

    def content(self, column: int, row: int) -> Content | None:
        return self._contents.get((column, row))

    def value(self, column: int, row: int) -> Computed | None:
        """A cell's value; None when it is blank."""
        if self._columns[column].failed:
            return Failed()
        return self._values.get((column, row))

    def text(self, column: int, row: int) -> str:
        """What the entry line shows for a cell: the typed text or `=formula`."""
        content = self._contents.get((column, row))
        if isinstance(content, Entry):
            return content.text
        if isinstance(content, Formula):
            return f"={content.text}"
        if isinstance(content, Constant):
            # A value put there rather than typed reads as a formula of itself: `=7`,
            # `="Title"` (check 5 E8, E11; run 2 G3; run 4 S1)
            return "=" + to_text(content.value, self._session.settings)
        value = self._values.get((column, row))
        return "" if value is None or isinstance(value, Failed) else self._show(value).text

    def saved(self, key: Key) -> tuple[str, str]:
        """A cell's content as a file keeps it: ("entry" or "formula", text). A value from a list
        is written at 14 digits (exact values stay exact), so it reads back as the same value."""
        content = self._contents.get(key)
        if isinstance(content, Formula):
            return "formula", content.text
        if isinstance(content, Constant):
            full = replace(self._session.settings, digits="float14")
            return "entry", to_text(content.value, full)
        return "entry", content.text if isinstance(content, Entry) else ""

    def shown(self, column: int, row: int) -> Shown:
        """A cell as drawn (check 6, E5, E20, E21)."""
        value = self.value(column, row)
        if value is None:
            # A gap inside a linked list is an empty element (check run 2, E12; G).
            linked = self._columns[column].name is not None
            return Shown("_" if linked and row < self.last_row(column) else "")
        if isinstance(value, Failed):
            return Shown("#ERR")
        content = self._contents.get((column, row))
        shown_as_typed = isinstance(content, Entry) and not isinstance(value, Str)
        if shown_as_typed and not _plain_number(content.text):
            return Shown(_canonical(content.text))  # `2^0.5`, `π`: as typed, on the left
        return self._show(value)

    def last_row(self, column: int) -> int:
        """The last filled row of a column, 0 if it is empty."""
        rows = [row for (c, row) in self._values if c == column and row > 0]
        rows += [row for (c, row) in self._contents if c == column and row > 0]
        return max(rows, default=0)

    def column_values(self, column: int) -> ListValue:
        """A column as a list: rows 1 to its last filled row, a blank or #ERR cell as `_`."""
        items: list[Value] = []
        for row in range(1, self.last_row(column) + 1):
            value = self.value(column, row)
            items.append(Empty() if value is None or isinstance(value, Failed) else value)
        return ListValue(tuple(items))

    def variable(self, name: str) -> Value | Function | None:
        """A variable of the sheet's Problem, such as `stat.results`."""
        return self._session.scope.get(self._key(name))

    def find(self, name: str) -> int | None:
        """The column linked to the variable `name`, if any."""
        key = self._key(name)
        for index, info in enumerate(self._columns):
            if info.name == key:
                return index
        return None

    # ----- changing ------------------------------------------------------------------------

    def set_cell(
        self,
        column: int,
        row: int,
        text: str,
        *,
        choose: dict[str, str] | None = None,
        confirm: bool = False,
    ) -> list[Notice]:
        """Type `text` into a cell and press Enter. Raises SheetError when the handheld keeps
        the cell in edit mode; returns the dialogs to show when it keeps the change. A name
        nothing defines stays as a name (check 5, E20: `=zzq` shows `zzq`)."""
        key = (column, row)
        if not 1 <= row <= ROWS or not 0 <= column < COLUMNS:
            raise SheetError(SYNTAX_ERROR, INVALID_INPUT)
        self._take_over({column}, confirm=confirm)
        text = text.strip()
        if not text:
            return self._replace({key: None})
        if text.startswith("="):
            formula = self._checked_formula(key, text[1:], choose or {})
            return self._replace({key: Formula(formula)})
        try:
            parse(text)
        except TIError as error:
            raise SheetError(SYNTAX_ERROR, DURING_INSERTION) from error
        return self._replace({key: Entry(text)})

    def set_column_formula(
        self, column: int, text: str, *, choose: dict[str, str] | None = None
    ) -> list[Notice]:
        """Enter a column formula in the formula row, or clear it with "". Clearing keeps the
        values as they are (check run 2, E20: the #ERR cells stayed)."""
        info = self._columns[column]
        key = (column, 0)
        text = text.strip().removeprefix("=")
        if not text:
            info.formula = None
            info.failed = False
            self._unlink(key)
            kept = {
                (c, r): Constant(v)
                for (c, r), v in self._values.items()
                if c == column and not isinstance(v, Failed)
            }
            self._contents.update(kept)
            self.revision += 1
            self._relock()
            return []
        formula = self._checked_formula(key, text, choose or {})
        old = [(c, r) for (c, r) in self._contents if c == column]
        for cell in old:
            del self._contents[cell]
            self._unlink(cell)
        info.formula = formula
        self._link(key, self._read_inputs(formula))
        outcome = _Outcome(changed=set(old))
        self._recalculate({key}, outcome)
        self._relock()
        return outcome.notices

    def set_name(self, column: int, text: str) -> list[Notice]:
        """Name a column, which links it to the list variable of that name (check 6, E7):
        an existing list replaces the column's data, a new name takes the column's data, and a
        name already linked on this sheet is refused. "" unlinks the column."""
        info = self._columns[column]
        text = text.strip()
        if not text:
            info.name = info.shown_name = None
            self.revision += 1
            self._relock()
            return []
        if text.casefold().startswith("stat."):
            raise SheetError(LINK_ERROR, STAT_VARIABLE)  # check run 2, G20
        try:
            node = parse(text).statements
            if len(node) != 1 or not isinstance(node[0], ast.Name):
                raise TIError(0, INVALID_INPUT)
            name = self._evaluator().name_for_store(text)
        except TIError as error:
            raise SheetError(SYNTAX_ERROR, INVALID_INPUT) from error
        if any(other.name == name for other in self._columns if other is not info):
            raise SheetError(LINK_ERROR, LINKED_TWICE)
        stored = self._session.scope.get(name)
        if stored is not None and not isinstance(stored, ListValue):
            raise SheetError(SYNTAX_ERROR, INVALID_INPUT)  # run 4, S14: k:=5, then a column named k
        info.name, info.shown_name = name, text
        outcome = _Outcome()
        if isinstance(stored, ListValue) and info.formula is None:
            self._fill_from_list(column, stored, outcome)
            self._recalculate(set(), outcome)
        else:
            self._recalculate(set(), outcome)
            self._write(column)
        self.revision += 1
        self._relock()
        return outcome.notices

    def recalculate(self) -> list[Notice]:
        """Ctrl+R, and a change of Document Settings: every formula again (check 6, E23)."""
        outcome = _Outcome()
        for key, content in self._contents.items():
            if isinstance(content, Entry):  # `1/3` becomes 0.333… in Approximate mode
                self._store_value(key, self._content_value(content), outcome)
        self._recalculate(set(self._inputs), outcome)
        return outcome.notices

    @property
    def locks(self) -> tuple[set[str], set[str]]:
        """The names this sheet holds: (linked lists, formula columns' variables)."""
        return self._locks

    def contents(self) -> dict[Key, Content]:
        """Every cell's content, for an action that moves cells (`sheet.actions`) or a save."""
        return dict(self._contents)

    def put(self, contents: dict[Key, Content | None], *, confirm: bool = False) -> list[Notice]:
        """Set several cells at once, as Fill and Paste do, then recalculate. None clears."""
        self._take_over({column for column, _ in contents}, confirm=confirm)
        return self._replace(contents)

    def _take_over(self, columns: set[int], *, confirm: bool) -> None:
        """Typing into a column that has a column formula asks first (Data Loss); OK drops the
        formula and the values it made, so only what is typed is left (check 5, E8; run 4, S6
        and S16)."""
        taken = sorted(c for c in columns if self._columns[c].formula is not None)
        if not taken:
            return
        if not confirm:
            raise DataLossError
        for column in taken:
            info = self._columns[column]
            info.formula = None
            info.failed = False
            self._unlink((column, 0))
            for key in [k for k in self._values if k[0] == column and k[1] > 0]:
                del self._values[key]
        outcome = _Outcome(changed={(c, 1) for c in taken})
        self._recalculate(set(), outcome)
        self._relock()

    def restore(self, contents: dict[Key, Content], columns: list[ColumnInfo]) -> list[Notice]:
        """Replace the whole sheet, as after an insert, delete or sort, or when a document is
        opened, and compute it all again. Named columns are written to their lists."""
        old = set(self._contents) | set(self._values)
        for key in list(self._inputs):
            self._unlink(key)
        self._contents = dict(contents)
        self._values = {}
        self._columns = [ColumnInfo(info.name, info.shown_name, info.formula) for info in columns]
        outcome = _Outcome(changed=old | set(contents))
        for key, content in self._contents.items():
            if isinstance(content, Formula):
                self._link(key, self._read_inputs(content.text))
            else:
                self._store_value(key, self._content_value(content), outcome)
        for column, info in enumerate(self._columns):
            if info.formula is not None:
                self._link((column, 0), self._read_inputs(info.formula))
            elif info.name is not None:
                self._write(column)  # first, so formulas that use the list by name find it
        self._recalculate(set(self._inputs), outcome)
        for column, info in enumerate(self._columns):
            if info.name is not None:
                self._write(column)
        self.revision += 1
        self._relock()
        return outcome.notices

    def sync(self) -> list[Notice]:
        """Catch up with variables changed outside the sheet since it last looked: a linked
        column takes its list's new values, a deleted list unlinks its column (which keeps its
        values), and formulas that use a changed name are evaluated again (check run 2, G)."""
        scope = self._session.scope
        changed = scope.changed_since(self._seen)
        if not changed:
            return []
        outcome = _Outcome()
        for index, info in enumerate(self._columns):
            if info.name is None or info.name not in changed:
                continue
            stored = scope.get(info.name)
            if stored is None:
                info.name = info.shown_name = None
                self._keep_as_constants(index)
            elif (
                isinstance(stored, ListValue)
                and info.formula is None
                and stored != self.column_values(index)  # not the sheet's own write
            ):
                self._fill_from_list(index, stored, outcome)
        nodes = {key for name in changed for key in self._name_readers.get(name, ())}
        self._recalculate(nodes, outcome)
        self._seen = scope.revision
        self._relock()
        return outcome.notices

    # ----- formulas --------------------------------------------------------------------------

    def _key(self, name: str) -> str:
        return variable_key(self._session.settings, name)

    def _evaluator(self) -> Evaluator:
        return Evaluator(self._session.settings, None, self._session.scope)

    def check_formula(self, column: int, text: str, choose: dict[str, str]) -> str:
        """A column formula as it would be kept, or the SheetError it would raise (Conflict
        Detected first), without changing the sheet: Stat Calculations asks this before Data
        Loss (run 4, S7)."""
        return self._checked_formula((column, 0), text.strip().removeprefix("="), choose)

    def _checked_formula(self, key: Key, text: str, choose: dict[str, str]) -> str:
        """The formula to keep, with `'` before names chosen as variables; raises SheetError
        for a formula the handheld refuses while it is being typed."""
        text, save = _split_save(text)
        found = refs.scan(text)
        if any(not item.reference.valid for item in found):
            raise SheetError(SYNTAX_ERROR, DURING_INSERTION)
        conflicts = tuple(
            item.reference.name
            for item in found
            if isinstance(item.reference, Ref)
            and self._session.scope.get(self._key(item.reference.name)) is not None
            and item.reference.name not in choose
        )
        conflicts += tuple(
            name for name in self._column_names_in(text, found) if name not in choose
        )
        if conflicts:
            raise ConflictError(text, conflicts)
        for name, picked in choose.items():
            column = self.find(name)
            if column is not None and not refs.address(name):
                # A column's name: `u[]`, the column itself, or `'u`, the list (run 4, S11)
                spelled = f"{refs.column_letter(column)}[]" if picked == "cell" else f"'{name}"
                text = refs.renamed(text, name, spelled)
        found = refs.scan(text)
        text = refs.rewrite(
            text,
            found,
            lambda item: (
                f"'{item.reference.name}"
                if isinstance(item.reference, Ref) and choose.get(item.reference.name) == "variable"
                else text[item.start : item.end]
            ),
        )
        try:
            self._parsed(text, refs.scan(text))
        except TIError as error:
            raise SheetError(SYNTAX_ERROR, DURING_INSERTION) from error
        inputs = self._read_inputs(text)
        if self._reaches(key, inputs):
            raise SheetError(SYNTAX_ERROR, CIRCULAR)
        return text + (f"{_SAVE}{save}" if save else "")

    def _column_names_in(self, text: str, found: list[Found]) -> list[str]:
        """The names in a formula that are this sheet's linked columns: the handheld asks
        "Column or Variable?" for each (run 4, S11)."""
        try:
            node = self._parsed(text, found)
        except TIError:
            return []
        linked = {info.name: info.shown_name for info in self._columns if info.name is not None}
        seen: list[str] = []
        for name in _names(node):
            key = self._key(name)
            if name.startswith(_PLACEHOLDER) or key not in linked or name in seen:
                continue
            if any(isinstance(i.reference, Variable) and i.reference.name == name for i in found):
                continue  # written `'name` already: the variable
            seen.append(name)
        return seen

    def _parsed(self, text: str, found: list[Found]) -> ast.Expr | ast.Command:
        rewritten = refs.rewrite(
            text,
            found,
            lambda item: (
                item.reference.name
                if isinstance(item.reference, Variable)
                else f"{_PLACEHOLDER}{found.index(item)}"
            ),
        )
        return _one_expression(rewritten)

    def _read_inputs(self, text: str) -> _Inputs:
        text, save = _split_save(text)
        found = refs.scan(text)
        cells: set[Key] = set()
        columns: set[int] = set()
        for item in found:
            reference = item.reference
            if isinstance(reference, Ref):
                cells.add(reference.key())
            elif isinstance(reference, Span):
                cells.update(reference.cells())
            elif isinstance(reference, Column):
                columns.add(reference.column)
        names = {
            self._key(name)
            for name in _names(self._parsed(text, found))
            if not name.startswith(_PLACEHOLDER)
        }
        del save  # the function a regression is saved to is written, not read
        return _Inputs(frozenset(cells), frozenset(columns), frozenset(names))

    def _evaluate(self, key: Key) -> Computed:
        """A formula's value; a failure is Failed, and a list in a single cell is too."""
        text = self._columns[key[0]].formula if key[1] == 0 else None
        if text is None:
            content = self._contents.get(key)
            assert isinstance(content, Formula)
            text = content.text
        try:
            return self._compute(text, skip_failed=False)
        except TIError, RecursionError:
            return Failed()

    def _compute(self, text: str, *, skip_failed: bool) -> Computed:
        """A formula's value; a TIError goes to the caller. A reference to a #ERR cell makes
        the formula #ERR, unless `skip_failed` (to find the error message of a column)."""
        text, save = _split_save(text)
        found = refs.scan(text)
        bindings: dict[str, Value] = {}
        for index, item in enumerate(found):
            reference = item.reference
            if isinstance(reference, Variable):
                continue
            value = self._reference_value(reference)
            if isinstance(value, Failed):
                if skip_failed:
                    continue
                return value
            bindings[self._key(f"{_PLACEHOLDER}{index}")] = value
        evaluator = self._evaluator()
        node = self._parsed(text, found)
        with evaluator.bound(bindings):
            if isinstance(node, ast.Command):
                return self._statistics(evaluator, node, save)
            return evaluator.evaluated(node)

    def _statistics(self, evaluator: Evaluator, node: ast.Command, save: str | None) -> Value:
        """A Stat Calculations column: run the command and take the values of `stat.results`
        (the labels are written beside it once, by `actions.stat_calc`). The `stat.` variables
        and a saved regression equation follow the data, since this runs again when they
        change (run 4, S1 to S3)."""
        evaluator.line(ast.Line((node,)))
        scope = self._session.scope
        results = scope.get("stat.results")
        if not isinstance(results, MatrixValue):
            raise TIError(errors.DOMAIN)
        if save:
            equation = scope.get("stat.regeqn")
            if isinstance(equation, Function):
                scope.define(self._key(save), equation)
        return ListValue(tuple(row[1] for row in results.rows))

    def _reference_value(self, reference: Ref | Span | Column) -> Computed:
        if isinstance(reference, Ref):
            value = self.value(*reference.key())
            return Empty() if value is None else value
        if isinstance(reference, Column):
            return self.column_values(reference.column)
        items: list[Value] = []
        for cell in reference.cells():
            value = self.value(*cell)
            if isinstance(value, Failed):
                return value
            items.append(Empty() if value is None else value)
        return ListValue(tuple(items))

    # ----- the dependency graph ----------------------------------------------------------------

    def _feeds(self, producer: Key, inputs: _Inputs) -> bool:
        """Whether the formula at `producer` writes something `inputs` reads."""
        column, row = producer
        if row == 0:  # a column formula writes the whole column
            return column in inputs.columns or any(c == column for c, _ in inputs.cells)
        if producer in inputs.cells or column in inputs.columns:
            return True
        name = self._columns[column].name
        return name is not None and name in inputs.names

    def _link(self, key: Key, inputs: _Inputs) -> None:
        """Record a formula's inputs, and it as a reader of each of them."""
        self._unlink(key)
        self._inputs[key] = inputs
        for cell in inputs.cells:
            self._cell_readers.setdefault(cell, set()).add(key)
            self._readers_within.setdefault(cell[0], set()).add(key)
        for column in inputs.columns:
            self._column_readers.setdefault(column, set()).add(key)
        for name in inputs.names:
            self._name_readers.setdefault(name, set()).add(key)

    def _unlink(self, key: Key) -> None:
        inputs = self._inputs.pop(key, None)
        if inputs is None:
            return
        for cell in inputs.cells:
            self._cell_readers[cell].discard(key)
            self._readers_within[cell[0]].discard(key)
        for column in inputs.columns:
            self._column_readers[column].discard(key)
        for name in inputs.names:
            self._name_readers[name].discard(key)

    def _readers(self, key: Key) -> set[Key]:
        """The formulas that read what changes when `key` does: a cell, or with row 0 a whole
        column; also those that read the column whole or by its list's name."""
        column, row = key
        found = set(self._column_readers.get(column, ()))
        found |= (
            self._readers_within.get(column, set())
            if row == 0
            else self._cell_readers.get(key, set())
        )
        name = self._columns[column].name
        if name is not None:
            found |= self._name_readers.get(name, set())
        return found

    def _reaches(self, start: Key, inputs: _Inputs) -> bool:
        """Whether a formula at `start` with these inputs would read its own result: whether
        `start`, or a formula downstream of it, writes something the inputs read."""
        downstream = self._dependents({start}) - {start}
        return self._feeds(start, inputs) or any(self._feeds(key, inputs) for key in downstream)

    def _dependents(self, changed: set[Key]) -> set[Key]:
        """The formulas that read any of the changed cells, directly or through others."""
        dirty: set[Key] = set()
        queue = deque(changed)
        while queue:
            for key in self._readers(queue.popleft()):
                if key not in dirty:
                    dirty.add(key)
                    queue.append(key)
        return dirty

    def _order(self, nodes: set[Key]) -> list[Key]:
        """The formulas in an order where each comes after those it reads (Kahn's method, so a
        2,500-row chain from Fill needs no deep recursion). A cycle is left out."""
        readers = {key: (self._readers(key) & nodes) - {key} for key in nodes}
        waiting = dict.fromkeys(nodes, 0)
        for found in readers.values():
            for reader in found:
                waiting[reader] += 1
        ready = deque(sorted(key for key, count in waiting.items() if count == 0))
        order: list[Key] = []
        while ready:
            key = ready.popleft()
            order.append(key)
            for reader in readers[key]:
                waiting[reader] -= 1
                if waiting[reader] == 0:
                    ready.append(reader)
        return order

    def _recalculate(self, nodes: set[Key], outcome: _Outcome) -> None:
        """Evaluate `nodes` and everything that reads them or the changed cells, then write
        each named column that changed to its variable."""
        dirty = self._dependents(outcome.changed | nodes) | nodes
        dirty &= set(self._inputs)
        order = self._order(dirty)
        # A named column's list is written as soon as its cells change, so the formulas that
        # read it by name (`=mean(xs)`, `OneVar 'd1`) see the new values, not the old.
        self._write_named({c for c, _ in outcome.changed})
        for key in order:
            if key[1] == 0:
                self._fill_column(key[0], outcome)
            else:
                self._store_value(key, self._evaluate(key), outcome)
            self._write_named({key[0]})
        for key in dirty - set(order):
            self._store_value(key, Failed(), outcome)  # a cycle through a variable: #ERR
        for column in sorted({c for c, _ in outcome.changed}):
            if self._columns[column].name is not None:
                self._write(column)
        if outcome.changed:
            self.revision += 1

    def _write_named(self, columns: set[int]) -> None:
        for column in sorted(columns):
            if self._columns[column].name is not None:
                self._write(column)

    def _store_value(self, key: Key, value: Computed, outcome: _Outcome) -> None:
        if isinstance(value, ListValue | MatrixValue) and key[1] > 0:
            value = Failed()  # a list does not fit a cell (check 6, E23)
        if isinstance(value, Failed) and isinstance(self._contents.get(key), Formula):
            outcome.notices.append(Notice(f"Syntax Error in Cell: {_name(key)}", "Syntax"))
        if self._values.get(key) != value:
            self._values[key] = value
            outcome.changed.add(key)

    def _fill_column(self, column: int, outcome: _Outcome) -> None:
        """Evaluate a column formula into its cells (check 6, E14; check run 2, E20)."""
        info = self._columns[column]
        old = {key for key in self._values if key[0] == column and key[1] > 0}
        value = self._evaluate((column, 0))
        message = None
        if isinstance(value, Failed):
            message = self._column_error((column, 0))
        elif not isinstance(value, ListValue):
            # One value fills the whole column (run 4, S15: `=5` showed 5 as far down as was
            # looked, row 18; the whole column is a guess beyond that).
            value = ListValue((value,) * ROWS)
        elif len(value.items) > ROWS:
            message = "Syntax"  # guess: more rows than the sheet has
        if message is not None:
            info.failed = True
            title = f"Syntax Error in Column: {refs.column_letter(column)}"
            outcome.notices.append(Notice(title, message))
            outcome.changed.update(old)
            return
        assert isinstance(value, ListValue)
        info.failed = False
        for row, item in enumerate(value.items, start=1):
            self._store_value((column, row), item, outcome)
        for key in old:
            if key[1] > len(value.items):
                del self._values[key]
                outcome.changed.add(key)

    def _column_error(self, key: Key) -> str:
        """The message of the error a column formula gives, for its dialog."""
        info = self._columns[key[0]]
        assert info.formula is not None
        try:
            self._compute(info.formula, skip_failed=True)
        except TIError as error:
            return error.message
        return "Syntax"

    def _replace(self, contents: dict[Key, Content | None]) -> list[Notice]:
        """Put new contents in cells, then recalculate what depends on them."""
        outcome = _Outcome()
        for key, content in contents.items():
            self._unlink(key)
            if content is None:
                self._contents.pop(key, None)
                if self._values.pop(key, None) is not None:
                    outcome.changed.add(key)
                continue
            self._contents[key] = content
            if isinstance(content, Formula):
                self._link(key, self._read_inputs(content.text))
            else:
                self._store_value(key, self._content_value(content), outcome)
                outcome.changed.add(key)
        formulas = {key for key, content in contents.items() if isinstance(content, Formula)}
        self._recalculate(formulas, outcome)
        return outcome.notices

    def _content_value(self, content: Entry | Constant) -> Computed:
        if isinstance(content, Constant):
            return content.value
        evaluator = self._evaluator()
        try:
            node = _one_expression(content.text)
            if isinstance(node, ast.Command):
                return Failed()  # a statistics command is a column formula, not an entry
            return evaluator.evaluated(node)
        except TIError:
            return Failed()

    # ----- linked lists ------------------------------------------------------------------------

    def _write(self, column: int) -> None:
        """Store a named column's values in its variable."""
        name = self._columns[column].name
        assert name is not None
        scope = self._session.scope
        values = self.column_values(column)
        if not values.items:
            values = ListValue((Empty(),))  # an empty linked column is {_} (check run 2, G20)
        if scope.get(name) != values:
            scope.define(name, values)
        if self._seen == scope.revision - 1:
            self._seen = scope.revision  # the sheet's own write is not news to it

    def _relock(self) -> None:
        """Tell the Problem which names this sheet holds: a linked list must stay a list, and a
        formula column's variable takes no store (check run 2, G4, G9, G14)."""
        scope = self._session.scope
        scope.lists -= self._locks[0]
        scope.read_only -= self._locks[1]
        named = [info for info in self._columns if info.name is not None]
        lists = {info.name for info in named if info.formula is None and info.name}
        read_only = {info.name for info in named if info.formula is not None and info.name}
        scope.lists |= lists
        scope.read_only |= read_only
        self._locks = (lists, read_only)

    def _fill_from_list(self, column: int, items: ListValue, outcome: _Outcome) -> None:
        """Replace a linked column's cells with a list's elements."""
        old = [key for key in self._contents if key[0] == column]
        old += [key for key in self._values if key[0] == column and key[1] > 0]
        for key in old:
            self._contents.pop(key, None)
            self._values.pop(key, None)
            self._unlink(key)
            outcome.changed.add(key)
        for row, item in enumerate(items.items, start=1):
            if isinstance(item, Empty):
                continue
            self._contents[(column, row)] = Constant(item)
            self._values[(column, row)] = item
            outcome.changed.add((column, row))

    def _keep_as_constants(self, column: int) -> None:
        for key, value in list(self._values.items()):
            if key[0] == column and not isinstance(value, Failed):
                self._contents[key] = Constant(value)
                self._unlink(key)
        self.revision += 1

    # ----- display ---------------------------------------------------------------------------

    def _show(self, value: Value) -> Shown:
        if isinstance(value, Str):
            return Shown(value.value)
        if isinstance(value, Expr) and cas.is_undefined(value.raw):
            return Shown("#UNDEF")
        text = to_text(value, self._session.settings)
        return Shown(text, right=isinstance(value, Expr) and cas.to_fraction(value.raw) is not None)


def _name(key: Key) -> str:
    return f"{refs.column_letter(key[0])}{key[1]}"


def _canonical(text: str) -> str:
    """An entry as the handheld shows it: TI's own spelling of the constants, `pi` as `π`."""
    return _SPELLING_RE.sub(lambda match: _SPELLING.get(match.group(), match.group()), text)


def _plain_number(text: str) -> bool:
    """Whether an entry is a number or a fraction of numbers, which the cell shows as a value
    (right-aligned, `5.` in Approximate mode); anything else is shown as typed (check 6, E5)."""
    try:
        statements = parse(text).statements
    except TIError:
        return False
    if len(statements) != 1:
        return False
    node = statements[0]
    if isinstance(node, ast.Unary) and node.op == "-":
        node = node.operand
    if isinstance(node, ast.Binary) and node.op == "/":
        return isinstance(node.left, ast.Number) and isinstance(node.right, ast.Number)
    return isinstance(node, ast.Number)


def _one_expression(text: str) -> ast.Expr | ast.Command:
    """`text` as a single expression: a cell holds no store, definition or command, except a
    statistics command whose results fill a column (`OneVar d1,1`)."""
    statements = parse(text).statements
    node = statements[0] if len(statements) == 1 else None
    if isinstance(node, ast.Command) and node.name.casefold() in _RESULT_COMMANDS:
        return node
    if node is None or isinstance(node, ast.Assign | ast.Store | ast.Define | ast.Command):
        raise TIError(0, "Syntax")
    return node


def _split_save(text: str) -> tuple[str, str | None]:
    """A regression's column formula and the function its equation is saved to, from
    `LinRegMx xs,ys,1: CopyVar stat.RegEqn,f1` (the emulator writes the same shape)."""
    found = _SAVE_RE.search(text)
    if found is None:
        return text, None
    return text[: found.start()], found.group(1)


def _names(node: object) -> Iterator[str]:
    """Every name a formula uses, as a variable or as a function it calls."""
    if isinstance(node, ast.Name):
        yield node.text
        return
    if isinstance(node, ast.Call):
        yield node.func
    if is_dataclass(node) and not isinstance(node, type):
        for item in fields(node):
            yield from _names(getattr(node, item.name))
    elif isinstance(node, tuple):
        for item in node:
            yield from _names(item)
