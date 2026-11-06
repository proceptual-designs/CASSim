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
from cassim.device.editor import Editor, Kind
from cassim.device.editor import Row as EditorRow

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


class Calculator:
    def __init__(self, session: Session | None = None, clipboard: Clipboard | None = None) -> None:
        self.session = session if session is not None else Session()
        self.clipboard = clipboard if clipboard is not None else Clipboard()
        self.editor = Editor()
        self.history: list[Entry] = []
        self.error: str | None = None  # a dialog waiting for a key press
        self.recall: tuple[int, Row] | None = None  # the history row Up has selected
        self._undo: list[Snapshot] = []
        self._redo: list[Snapshot] = []
        self._group: str | None = None  # the kind of edit in progress, for undo grouping

    # ---- actions ----------------------------------------------------------------------------

    def perform(self, binding: Binding) -> None:
        """Do what a key says. While a dialog is showing, any key only dismisses it."""
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
            template=self._template,
            power=self._power,
            backspace=lambda _: self._edit("other", self.editor.backspace),
            delete=lambda _: self._edit("other", self.editor.delete),
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

    def _template(self, kind: str) -> None:
        self._edit("other", lambda: self.editor.insert_template(Kind(kind)))

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
            self._edit("other", lambda: self.editor.insert_text(" ".join(text.split())))
        elif self.clipboard.nodes:
            self._edit("other", lambda: self.editor.paste(self.clipboard.nodes))

    def _snapshot(self) -> Snapshot:
        e = self.editor
        return copy.deepcopy(Snapshot(e.root, e.path, e.pos, e.selected, e.anchor))

    def _restore(self, snapshot: Snapshot) -> None:
        e = self.editor
        saved = copy.deepcopy(snapshot)
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

    def _enter(self, *, approximate: bool) -> None:
        if self.recall is not None:
            index, row = self.recall
            entry = self.history[index]
            self.recall = None
            self.editor.insert_text(entry.text if row == "entry" else entry.result.text)
            return
        text = self.editor.linear()
        if not text:
            return
        result = self.session.eval(text, approximate=approximate)
        if result.error is not None:
            self.error = result.error
            return
        self.history.append(
            Entry(
                text,
                self.editor.latex(cursor=False, is_function=self.session.is_function),
                result,
                approximate,
            )
        )
        self.editor.clear()
        self._undo.clear()
        self._redo.clear()
        self._group = None
