"""The Calculator page model (FR-CALC-004, FR-DEV-001): an entry line, a history and a session.

It has no Flet and no key names: a `Binding` from a keymap says what to do, `perform` does it.
Behaviour follows the emulator runs in `docs/testing/` (decision 0017).
"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from cassim.core.results import Result
from cassim.device.clipboard import Clipboard
from cassim.device.editor import (
    MARK,
    Editor,
    Kind,
    Node,
    Template,
    linear_text,
    modernised,
    parse_target,
    position_near,
    substitute_ans,
)
from cassim.device.editor import Row as EditorRow
from cassim.device.editor_ast import row_from_text
from cassim.device.engine import RemoteSession, local_session
from cassim.device.recall import full_selection

if TYPE_CHECKING:
    from collections.abc import Callable

    from cassim.core.session import Session
    from cassim.device.keys import Action, Binding
    from cassim.doc.document import Page

type Row = Literal["entry", "result"]

# Keys that move or select inside the picked history row while one is picked
_RECALL_MOVES = frozenset(
    {
        "left", "right", "tab", "shift_tab", "home", "end", "select_left", "select_right",
        "select_all", "select_word_left", "select_word_right", "select_to_start",
        "select_to_end", "word_left", "word_right",
    }
)  # fmt: skip

# `ans` as a word of its own, as the entry line spells it (`Ans`, typed `ans`)
_ANS_WORD = re.compile(r"(?<![\w.])ans(?![\w(])", re.IGNORECASE)

_OPERAND_CHARS = frozenset("0123456789.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_πⅇⅈ")


@dataclass
class Snapshot:
    """The entry line at one moment, for undo and redo."""

    root: EditorRow
    path: list[tuple[int, int]]
    pos: int
    selected: bool
    anchor: int | None
    history: tuple[Entry, ...] = ()  # undo goes back over evaluations and deletes too


@dataclass(frozen=True)
class Entry:
    """One finished line of the history."""

    text: str  # as the parser read it
    latex: str  # as drawn: templates stacked
    result: Result
    approximate: bool = False
    nodes: tuple[Node, ...] = ()  # the entry's templates and characters, for recall
    # The entry as typed, with `ans` still in it: what Enter on an empty line runs again, and what
    # a saved file keeps. `nodes` and `text` show the value `ans` had (emulator check 3, H1 g).
    source: tuple[Node, ...] = ()


@dataclass(frozen=True)
class Pending:
    """An entry waiting for the engine."""

    text: str
    approximate: bool


class Calculator:
    def __init__(
        self, session: Session | RemoteSession | None = None, clipboard: Clipboard | None = None
    ) -> None:
        self.session = session if session is not None else local_session()
        self.clipboard = clipboard if clipboard is not None else Clipboard()
        self.editor = Editor()
        self.history: list[Entry] = []
        self.error: str | None = None  # a dialog waiting for a key press
        self.error_title = "Error"  # the dialog's title ("Warning" for Show Warning Info)
        self.recall: tuple[int, Row] | None = None  # the history row Up has selected
        self._recalled = Editor()  # the picked row as an editor: a cursor and a selection in it
        # A picked result at full precision: what Enter and copy take (the row shows `text`)
        self._recalled_full: EditorRow | None = None
        self.recall_touched = False  # a key or click has moved inside the picked row
        self._undo: list[Snapshot] = []
        self._redo: list[Snapshot] = []
        self._group: str | None = None  # the kind of edit in progress, for undo grouping
        self._synced: Entry | None = None  # the entry the session's `Ans` was last set from
        # With a deferred session (the maths runs in another worker) Enter only queues the entry;
        # the app evaluates it and calls `finish` (or `abort` after a Cancel).
        self.pending: Pending | None = None

    # ---- actions ----------------------------------------------------------------------------

    def perform(self, binding: Binding) -> None:
        """Do what a key says. While a dialog is showing, any key only dismisses it."""
        if self.pending is not None:
            return  # busy: the app's Runner owns the keyboard until the result arrives
        if self.error is not None:
            self.error, self.error_title = None, "Error"
            return
        action = self._actions().get(binding.action)
        if action is None:
            msg = f"unknown action {binding.action!r}"
            raise ValueError(msg)
        action(binding.arg)

    def _actions(self) -> dict[Action, Callable[[str], None]]:
        move: dict[Action, Callable[[], None]] = {
            "left": self.editor.left,
            "right": self.editor.right,
            "tab": self.editor.tab,
            "shift_tab": self.editor.shift_tab,
            "home": self.editor.home,
            "end": self.editor.end,
            "select_left": self.editor.select_left,
            "select_right": self.editor.select_right,
            "select_all": self.editor.select_all,
            "select_word_left": self.editor.select_word_left,
            "select_word_right": self.editor.select_word_right,
            "select_to_start": self.editor.select_to_start,
            "select_to_end": self.editor.select_to_end,
            "word_left": self.editor.word_left,
            "word_right": self.editor.word_right,
        }
        actions: dict[Action, Callable[[str], None]] = {
            name: self._recall_move(name) for name in move
        }
        actions.update(
            {
                "insert": self._insert,
                "insert_linear": lambda text: self._edit(
                    "other", lambda: self.editor.insert_linear(text, MARK)
                ),
                "template": self._template,
                "power": self._power,
                "accent": lambda _: self._edit("operand", self.editor.cycle_accent),
                "backspace": lambda arg: self._delete(self._backspace(arg), forward=False),
                "delete": lambda _: self._delete(self.editor.delete, forward=True),
                "clear": lambda arg: (
                    self.clear_history()
                    if arg == "history"
                    else self._edit("other", self.editor.clear)
                ),
                "copy": lambda _: self._copy(),
                "cut": lambda _: self._cut(),
                "paste": self._paste,
                "up": lambda _: self._vertical(up=True),
                "down": lambda _: self._vertical(up=False),
                "enter": lambda _: self._enter(approximate=False),
                "approximate": lambda _: self._enter(approximate=True),
                "undo": lambda _: self._step(self._undo, self._redo),
                "redo": lambda _: self._step(self._redo, self._undo),
                "escape": lambda _: self._mover(lambda: None)(""),
                "home_key": lambda arg: (
                    self._first_line() if self.recall else self._recall_move("home")(arg)
                ),
                "first_line": lambda _: self._first_line(),
                "last_line": lambda _: self._mover(lambda: None)(""),  # ctrl+1: entry line
                "recall_at": self._recall_at,
                "select_cells": self._select_cells,
                "place": lambda arg: self._place(arg, extend=False),
                "extend": lambda arg: self._place(arg, extend=True),
                "recall_place": lambda arg: self._recall_place(arg, extend=False),
                "recall_extend": lambda arg: self._recall_place(arg, extend=True),
                "recall_token": self._recall_token,
                "select_token": lambda arg: self._at_target(arg, self.editor.select_token),
                "drop": self._drop,
            }
        )
        return actions

    def _mover(self, method: Callable[[], None]) -> Callable[[str], None]:
        def move(_: str) -> None:
            self.recall = None
            self._group = None
            method()

        return move

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def _first_line(self) -> None:
        """ctrl+7: pick the first history row (emulator runs S5 b, H2 c)."""
        if self.history:
            self._pick((0, "entry"))

    @property
    def recall_editor(self) -> Editor | None:
        """The picked history row as an editor, or None when no row is picked."""
        return self._recalled if self.recall is not None else None

    def _pick(self, picked: tuple[int, Row] | None) -> None:
        """Pick a history row (or none). The row opens as an editor with the cursor at its left
        (Simon, 2026-11-20), so the keys and clicks can move inside it and select part of it."""
        self.recall = picked
        self.recall_touched = False
        if picked is None:
            return
        entry = self.history[picked[0]]
        self._recalled = Editor()
        self._recalled_full = None
        if picked[1] == "entry" and entry.nodes:
            self._recalled.root = copy.deepcopy(list(entry.nodes))
        elif picked[1] == "entry":
            # Parsed, not typed key by key: a typed `^` or `√` would take in the rest of the line
            self._recalled.root = row_from_text(entry.text)
        else:
            # The row moves through the digits it shows; Enter and copy take the full value
            self._recalled.root = row_from_text(entry.result.text)
            if entry.result.full and entry.result.full != entry.result.text:
                self._recalled_full = row_from_text(entry.result.full)

    def _recall_nodes(self) -> EditorRow:
        """What the picked row gives Enter or copy: its selected part (all of it if nothing is
        selected), at full precision for a result."""
        picked = self._recalled
        if self._recalled_full is not None:
            return full_selection(picked, self._recalled_full)
        return picked.selection() or copy.deepcopy(picked.root)

    def _recall_move(self, name: str) -> Callable[[str], None]:
        """A movement key: inside the picked row while one is picked, else in the entry line."""
        entry_move = self._mover(getattr(self.editor, name))

        def move(arg: str) -> None:
            if self.recall is None or name not in _RECALL_MOVES:
                entry_move(arg)
            else:
                self.recall_touched = True
                getattr(self._recalled, name)()

        return move

    def _backspace(self, arg: str) -> Callable[[], None]:
        """Backspace, or the keypad's del (`whole`), which takes a template just before the
        cursor away in one press (run 5, F3) where Backspace highlights it first (0017)."""
        editor = self.editor

        def whole() -> None:
            row = editor.row()
            before = row[editor.pos - 1] if editor.pos and editor.anchor is None else None
            if isinstance(before, Template) and not editor.selected:
                editor.backspace()  # highlights it
            editor.backspace()

        return whole if arg == "whole" else editor.backspace

    def _at_target(self, target: str, act: Callable[[list[tuple[int, int]], int], None]) -> None:
        """Do `act` at a click's target in the entry line (a double-click selects a token)."""
        try:
            path, pos = parse_target(target)
        except ValueError:
            return
        self._mover(lambda: act(path, pos))("")

    def _drop(self, target: str) -> None:
        """Selected text dragged to `target` in the entry line moves there (H3 k); undoable."""
        try:
            path, pos = parse_target(target)
        except ValueError:
            return
        self._edit("other", lambda: self.editor.move_selection(path, pos))

    def _recall_token(self, target: str) -> None:
        """A double-click in the picked history row selects the token there (H3 b)."""
        if self.recall is None:
            return
        try:
            path, pos = parse_target(target)
        except ValueError:
            return
        self.recall_touched = True
        self._recalled.select_token(path, pos)

    def _recall_place(self, target: str, *, extend: bool) -> None:
        """A click in the picked row: put the cursor there, or extend the selection."""
        if self.recall is None:
            return
        try:
            path, pos = parse_target(target)
        except ValueError:
            return
        self.recall_touched = True
        self._recalled.place(path, pos, extend=extend)

    def clear_history(self) -> None:
        """Clear History (the context menus, Actions 5): every pair goes at once, with no
        question asked, and `Ans` with them; variables stay (run 5, H5 h). The device greys its
        Undo afterwards; CASSim keeps undo, which brings the history back."""
        if not self.history:
            return
        self._undo.append(self._snapshot())
        self._redo.clear()
        self.history.clear()
        self._pick(None)
        self._group = None
        self._sync_ans()

    def warning_info(self) -> str | None:
        """The picked line's warnings as one message (Show Warning Info…), or None."""
        if self.recall is None:
            return None
        warnings = self.history[self.recall[0]].result.warnings
        return "\n".join(warnings) if warnings else None

    def show_warning_info(self) -> None:
        """Show Warning Info…: the picked line's warnings in a dialog."""
        info = self.warning_info()
        if info is not None:
            self.error, self.error_title = info, "Warning"

    def _delete(self, remove_in_entry: Callable[[], None], *, forward: bool) -> None:
        """Del or Backspace: on a picked history row it deletes that entry and its result, and
        undo brings them back; on an empty entry line it does nothing (emulator check 3, H5 c);
        otherwise it edits the entry line.

        After a delete the input of the pair that takes its place is picked, as a text editor
        moves: Delete picks the next pair, Backspace (and the keypad's del) the previous one, and
        either takes the other side at an end of the history (run 5, H5 a, b, e, f, g, j)."""
        if self.recall is None:
            if not self.editor.is_empty:
                self._edit("other", remove_in_entry)
            return
        self._undo.append(self._snapshot())
        self._redo.clear()
        index = self.recall[0]
        del self.history[index]
        self._group = None
        self._sync_ans()
        if not self.history:
            self._pick(None)
            return
        after = index < len(self.history)  # a pair moved up into the deleted one's place
        before = index > 0
        self._pick((index if after and (forward or not before) else index - 1, "entry"))

    # ---- editing, with undo groups ----------------------------------------------------------

    def _insert(self, text: str) -> None:
        kind = "operand" if all(char in _OPERAND_CHARS for char in text) else "operator"
        self._edit(kind, lambda: self.editor.insert_text(text))

    def _template(self, spec: str) -> None:
        """A `Kind` name, with `:ROWS,COLS` for a matrix or `:ROWS` for a piecewise or system
        template (`fraction`, `matrix:2,3`, `system:2`)."""
        kind, _, shape = spec.partition(":")
        rows, _, cols = shape.partition(",")
        size = (int(rows), int(cols or 1)) if shape else (2, 2)
        if kind == Kind.LIST:  # `list:3` is three elements
            size = (1, int(rows) if shape else 3)
        self._edit("other", lambda: self.editor.insert_template(Kind(kind), size))

    def _power(self, exponent: str) -> None:
        """A key that opens an exponent already holding `exponent` (x squared)."""
        self._edit("other", lambda: self._insert_power(exponent))

    def _insert_power(self, exponent: str) -> None:
        self.editor.insert("^")
        self.editor.insert_text(exponent)

    def _edit(self, kind: str, change: Callable[[], None]) -> None:
        """Run an edit. Undo steps back one group: a run of operands, or one operator."""
        self.recall = None
        if self.editor.anchor is not None:
            kind = "other"  # typing over a selection is a step of its own
        if kind != self._group or kind != "operand":
            self._undo.append(self._snapshot())
            self._redo.clear()
        self._group = kind
        change()

    def _copy(self) -> None:
        """Copy the selection in the entry line or, with a history row picked, the selected part
        of that row (all of it if nothing in it is selected), at full precision for a result."""
        nodes = self._recall_nodes() if self.recall is not None else self.editor.selection()
        if nodes:
            self.clipboard.nodes = nodes

    def _cut(self) -> None:
        if self.recall is not None:  # history is not edited by cutting: it is a copy
            self._copy()
        elif self.editor.selection():
            self._edit("other", lambda: setattr(self.clipboard, "nodes", self.editor.cut()))

    def _paste(self, text: str) -> None:
        """Paste the clipboard's nodes, or `text` from the system clipboard if it differs."""
        if text and text != self.clipboard.text:
            self._edit("other", lambda: self.editor.insert_linear(" ".join(text.split())))
        elif self.clipboard.nodes:
            self._edit("other", lambda: self.editor.paste(self.clipboard.nodes))

    def _snapshot(self) -> Snapshot:
        e = self.editor
        saved = copy.deepcopy(Snapshot(e.root, e.path, e.pos, e.selected, e.anchor))
        saved.history = tuple(self.history)
        return saved

    def forget_undo(self) -> None:
        """Drop the undo and redo history (after a document is loaded)."""
        self._undo.clear()
        self._redo.clear()
        self._group = None

    def _ans_entry(self) -> Entry | None:
        """The last entry that gave `Ans` a value (not an error, and not a bare `Done`)."""
        for entry in reversed(self.history):
            if entry.result.error is None and entry.result.text not in ("", "Done"):
                return entry
        return None

    def _sync_ans(self) -> None:
        """`Ans` follows what is left in the history after an undo or a delete (H5 g)."""
        entry = self._ans_entry()
        if entry is not self._synced:
            self._synced = entry
            self.session.set_ans(None if entry is None else entry.result.full or entry.result.text)

    def _restore(self, snapshot: Snapshot) -> None:
        e = self.editor
        saved = copy.deepcopy(snapshot)
        saved.history = snapshot.history
        self.history[:] = saved.history
        self.recall = None
        e.cell_sel = None
        e.root, e.path, e.pos, e.selected, e.anchor = (
            saved.root,
            saved.path,
            saved.pos,
            saved.selected,
            saved.anchor,
        )

    @property
    def can_undo(self) -> bool:
        """There is typing, an evaluation or a delete to undo on this page."""
        return bool(self._undo)

    def _step(self, source: list[Snapshot], target: list[Snapshot]) -> None:
        if source:
            target.append(self._snapshot())
            self._restore(source.pop())
            self._sync_ans()
        self._group = None

    # ---- history ----------------------------------------------------------------------------

    def _vertical(self, *, up: bool) -> None:
        """Up and Down move between template rows; on an empty line they walk the history."""
        walking = self.recall is not None or (
            up and self.editor.is_empty and not self.editor.path and self.history
        )
        if not walking:
            self._group = None
            (self.editor.up if up else self.editor.down)()
            return
        rows: list[tuple[int, Row]] = [
            (i, kind) for i in range(len(self.history)) for kind in ("entry", "result")
        ]
        at = rows.index(self.recall) if self.recall in rows else len(rows)
        at = max(at - 1, 0) if up else at + 1
        self._pick(rows[at] if at < len(rows) else None)

    def _select_cells(self, spec: str) -> None:
        """`row:-1`, `row:1`, `col:-1` or `col:1`: select (then grow) a matrix's rows or columns."""
        axis, _, step = spec.partition(":")
        self._mover(lambda: self.editor.select_cells(axis, int(step or 0)))("")

    def _place(self, target: str, *, extend: bool) -> None:
        """A click in the entry line (`place`) or a shift+click (`extend`): see `Editor.place`."""
        try:
            path, pos = parse_target(target)
        except ValueError:
            return
        self._mover(lambda: self.editor.place(path, pos, extend=extend))("")

    def _recall_at(self, spec: str) -> None:
        """A click on a history row (`INDEX:entry` or `INDEX:result`, with `@EMS` when the click
        was on the maths, that many ems from its left) puts a cursor in it, near the click, not
        a highlight over the whole item (run 5, H3 a, c). The picked row is then drawn as an
        editor, so a mouse click inside it only moves its cursor (`recall_place`), as on the
        device; a second `recall_at` on it (the keypad's pointer, which cannot aim inside a
        row) brings it down (Simon, 2026-11-20)."""
        spec, _, ems = spec.partition("@")
        index, _, row = spec.partition(":")
        picked = (int(index), "result" if row == "result" else "entry")
        if not 0 <= picked[0] < len(self.history):
            return
        if self.recall == picked:
            self._enter(approximate=False)
            return
        self._pick(picked)
        self.recall_touched = True
        try:
            near = float(ems) if ems else None
        except ValueError:
            near = None
        if near is not None:  # the cursor shows where the click was
            self._recalled.pos = position_near(self._recalled.root, near)

    def _enter(self, *, approximate: bool) -> None:
        if self.recall is not None:
            # What is selected in the picked row comes down to the entry line, else the whole row;
            # fractions and powers stay templates, and a result's numbers come at full precision
            nodes = self._recall_nodes()
            self.recall = None
            self.editor.paste(nodes)
            return
        self.editor.complete_brackets()  # `sin(2*(3+4` is entered as `sin(2*(3+4))`
        text = self.editor.linear()
        if not text and self.history:
            # Enter on an empty line runs the last entry again, as typed, so an `ans` in it takes
            # the new value (Newton's method: `ans-f(ans)/f'(ans)`, Enter, Enter, ...) and a
            # random one gives a new number (emulator check 3, H6)
            last = self.history[-1]
            if last.source:
                self.editor.paste(list(last.source))
            elif last.nodes:
                self.editor.paste(list(last.nodes))
            else:
                self.editor.insert_text(last.text)
            text = self.editor.linear()
        if not text:
            return
        refused = self._refused()
        if refused is not None:  # a dialog, and the entry stays on the entry line to be mended
            self.error = refused
            return
        if getattr(self.session, "deferred", False):
            self.pending = Pending(text, approximate)
            return
        self.finish(self.session.eval(text, approximate=approximate), text, approximate)

    def _refused(self) -> str | None:
        """Why the entry line cannot be run at all, or None. These are caught before the engine
        and leave no history pair: a template with every box empty (run 5, E4: an empty d/dx
        gives a syntax error and stays), and `Ans` with no answer on the page (after Clear
        History, or first on a fresh page: run 5, H5 h; editor check T1 i)."""
        if _has_empty_template(self.editor.root):
            return "Syntax error: fill in the empty boxes"
        if self._ans_entry() is None and _ANS_WORD.search(self.editor.linear()):
            return "No previous answer: Ans is undefined"
        return None

    def finish(self, result: Result, text: str, approximate: bool) -> None:
        """Record an evaluated entry: history on success, an error dialog otherwise."""
        self.pending = None
        if result.error is not None:
            # a dialog, and the entry stays in the history with the message as a quoted string
            self.error = result.error
            result = Result(f'"{result.error}"', "", None, result.error)
        # undo goes back to the entry as typed, cursor at its end
        before = self._snapshot()
        before.path, before.pos, before.selected, before.anchor = [], len(before.root), False, None
        self._undo.append(before)
        self._redo.clear()
        # the entry is kept as written on paper: π, √ and ⅇ^ for pi, sqrt( and exp(, Catalog
        # names in the Catalog's case, and `ans` shown as the value it had. Names are bold only
        # on the entry line: the history draws a defined name italic again (check 4, A4).
        shown = Editor()
        shown.root = modernised(self.editor.root)
        previous = self._ans_entry()
        if previous is not None:
            shown.root = substitute_ans(shown.root, previous.result.full or previous.result.text)
        entry = Entry(
            linear_text(shown.root) if shown.root != self.editor.root else text,
            shown.latex(cursor=False),
            result,
            approximate,
            tuple(shown.root),
            tuple(copy.deepcopy(self.editor.root)),
        )
        self.history.append(entry)
        if result.error is None and result.text not in ("", "Done"):
            self._synced = entry
        self.editor.clear()
        self._group = None


def _has_empty_template(row: EditorRow) -> bool:
    """Whether some template in `row` has nothing in any of its boxes."""
    for node in row:
        if isinstance(node, Template):
            if node.slots and not any(node.slots):
                return True
            if any(_has_empty_template(slot) for slot in node.slots):
                return True
    return False


def calculator_of(page: Page) -> Calculator | None:
    """The Calculator on a page, or None when the page is another type or not built yet."""
    return page.model if isinstance(page.model, Calculator) else None


def calculator_on(page: Page) -> Calculator:
    """The Calculator on a page that is known to hold one."""
    calculator = calculator_of(page)
    if calculator is None:
        msg = f"a {page.kind} page has no Calculator"
        raise TypeError(msg)
    return calculator
