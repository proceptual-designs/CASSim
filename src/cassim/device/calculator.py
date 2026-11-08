"""The Calculator page model (FR-CALC-004, FR-DEV-001): an entry line, a history and a session.

It has no Flet and no key names: a `Binding` from a keymap says what to do, `perform` does it.
Behaviour follows the emulator runs in `docs/testing/` (decision 0017).
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from cassim.core.session import Result, Session
from cassim.device.clipboard import Clipboard
from cassim.device.editor import MARK, Editor, Kind, Node, parse_target
from cassim.device.editor import Row as EditorRow
from cassim.device.engine import RemoteSession

if TYPE_CHECKING:
    from collections.abc import Callable

    from cassim.device.keys import Binding

type Row = Literal["entry", "result"]

_OPERAND_CHARS = frozenset("0123456789.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_πⅇⅈ")


@dataclass
class Snapshot:
    """The entry line at one moment, for undo and redo."""

    root: EditorRow
    path: list[tuple[int, int]]
    pos: int
    selected: bool
    anchor: int | None


@dataclass(frozen=True)
class Entry:
    """One finished line of the history."""

    text: str  # as the parser read it
    latex: str  # as drawn: templates stacked
    result: Result
    approximate: bool = False
    nodes: tuple[Node, ...] = ()  # the entry's templates and characters, for recall


@dataclass(frozen=True)
class Pending:
    """An entry waiting for the engine."""

    text: str
    approximate: bool


class Calculator:
    def __init__(
        self, session: Session | RemoteSession | None = None, clipboard: Clipboard | None = None
    ) -> None:
        self.session = session if session is not None else Session()
        self.clipboard = clipboard if clipboard is not None else Clipboard()
        self.editor = Editor()
        self.history: list[Entry] = []
        self.error: str | None = None  # a dialog waiting for a key press
        self.recall: tuple[int, Row] | None = None  # the history row Up has selected
        self._undo: list[Snapshot] = []
        self._redo: list[Snapshot] = []
        self._group: str | None = None  # the kind of edit in progress, for undo grouping
        # With a deferred session (the maths runs in another worker) Enter only queues the entry;
        # the app evaluates it and calls `finish` (or `abort` after a Cancel).
        self.pending: Pending | None = None

    # ---- actions ----------------------------------------------------------------------------

    def perform(self, binding: Binding) -> None:
        """Do what a key says. While a dialog is showing, any key only dismisses it."""
        if self.pending is not None:
            return  # busy: the app's Runner owns the keyboard until the result arrives
        if self.error is not None:
            self.error = None
            return
        action = self._actions().get(binding.action)
        if action is None:
            msg = f"unknown action {binding.action!r}"
            raise ValueError(msg)
        action(binding.arg)

    def _actions(self) -> dict[str, Callable[[str], None]]:
        move = {
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
        actions: dict[str, Callable[[str], None]] = {
            name: self._mover(method) for name, method in move.items()
        }
        actions.update(
            insert=self._insert,
            insert_linear=lambda text: self._edit(
                "other", lambda: self.editor.insert_linear(text, MARK)
            ),
            template=self._template,
            power=self._power,
            backspace=lambda _: self._edit("other", self.editor.backspace),
            delete=lambda _: self._edit("other", self.editor.delete),
            clear=lambda _: self._edit("other", self.editor.clear),
            copy=lambda _: self._copy(),
            cut=lambda _: self._cut(),
            paste=self._paste,
            up=lambda _: self._vertical(up=True),
            down=lambda _: self._vertical(up=False),
            enter=lambda _: self._enter(approximate=False),
            approximate=lambda _: self._enter(approximate=True),
            undo=lambda _: self._step(self._undo, self._redo),
            redo=lambda _: self._step(self._redo, self._undo),
            escape=lambda _: self._mover(lambda: None)(""),
            recall_at=self._recall_at,
            select_cells=self._select_cells,
            place=lambda arg: self._place(arg, extend=False),
            extend=lambda arg: self._place(arg, extend=True),
        )
        return actions

    def _mover(self, method: Callable[[], None]) -> Callable[[str], None]:
        def move(_: str) -> None:
            self.recall = None
            self._group = None
            method()

        return move

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
        nodes = self.editor.selection()
        if nodes:
            self.clipboard.nodes = nodes

    def _cut(self) -> None:
        if self.editor.selection():
            self._edit("other", lambda: setattr(self.clipboard, "nodes", self.editor.cut()))

    def _paste(self, text: str) -> None:
        """Paste the clipboard's nodes, or `text` from the system clipboard if it differs."""
        if text and text != self.clipboard.text:
            self._edit("other", lambda: self.editor.insert_linear(" ".join(text.split())))
        elif self.clipboard.nodes:
            self._edit("other", lambda: self.editor.paste(self.clipboard.nodes))

    def _snapshot(self) -> Snapshot:
        e = self.editor
        return copy.deepcopy(Snapshot(e.root, e.path, e.pos, e.selected, e.anchor))

    def _restore(self, snapshot: Snapshot) -> None:
        e = self.editor
        saved = copy.deepcopy(snapshot)
        e.cell_sel = None
        e.root, e.path, e.pos, e.selected, e.anchor = (
            saved.root,
            saved.path,
            saved.pos,
            saved.selected,
            saved.anchor,
        )

    def _step(self, source: list[Snapshot], target: list[Snapshot]) -> None:
        if source:
            target.append(self._snapshot())
            self._restore(source.pop())
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
        self.recall = rows[at] if at < len(rows) else None

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
        """A click on a history row (`INDEX:entry` or `INDEX:result`): the first click picks it,
        a second click on the same row brings it into the entry line."""
        index, _, row = spec.partition(":")
        picked = (int(index), "result" if row == "result" else "entry")
        if not 0 <= picked[0] < len(self.history):
            return
        if self.recall == picked:
            self._enter(approximate=False)
        else:
            self.recall = picked

    def _enter(self, *, approximate: bool) -> None:
        if self.recall is not None:
            index, row = self.recall
            entry = self.history[index]
            self.recall = None
            if row == "entry" and entry.nodes:  # keep fractions and powers as templates
                self.editor.paste(list(entry.nodes))
            else:
                self.editor.insert_text(entry.text if row == "entry" else entry.result.text)
            return
        text = self.editor.linear()
        if not text:
            return
        if getattr(self.session, "deferred", False):
            self.pending = Pending(text, approximate)
            return
        self.finish(self.session.eval(text, approximate=approximate), text, approximate)

    def finish(self, result: Result, text: str, approximate: bool) -> None:
        """Record an evaluated entry: history on success, an error dialog otherwise."""
        self.pending = None
        if result.error is not None:
            self.error = result.error
            return
        self.history.append(
            Entry(
                text,
                self.editor.latex(cursor=False, is_function=self.session.is_function),
                result,
                approximate,
                tuple(copy.deepcopy(self.editor.root)),
            )
        )
        self.editor.clear()
        self._undo.clear()
        self._redo.clear()
        self._group = None
