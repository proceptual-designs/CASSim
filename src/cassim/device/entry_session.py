"""One entry line being edited: the 2D editor with its undo, clipboard and keys (FR-CALC-004).

The Calculator's entry line, a Graphs function entry and a Lists & Spreadsheet cell each own one,
so they type, select, paste and undo alike. What differs between pages comes in as `EntryRules`:
`ans_prefix` (an operator typed first gets `Ans` in front: the Calculator only), `cells_paste`
(the sheet's paste rule) and `undo`. An owner that keeps more than the entry line in its undo
steps (the Calculator's history) attaches it to each step with `keep` and `restore`, and adds
steps of its own with `remember`.

It has no Flet and no key names: a `Binding` from a keymap says what to do, `perform` does it.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import TYPE_CHECKING

from cassim.device.clipboard import Clipboard
from cassim.device.editor import MARK, Editor, Kind, Template, parse_target

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from cassim.device.editor import Row
    from cassim.device.keys import Action, Binding

# Characters that continue a run of typing: undo takes a run of them back in one step
OPERAND_CHARS = frozenset("0123456789.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_πⅇⅈ")

# Editor methods, named as their actions, that move the cursor or the selection
MOVES: tuple[Action, ...] = (
    "left", "right", "up", "down", "tab", "shift_tab", "home", "end", "select_left",
    "select_right", "select_all", "select_word_left", "select_word_right", "select_to_start",
    "select_to_end", "word_left", "word_right",
)  # fmt: skip


@dataclass
class Snapshot[Extra]:
    """The entry line at one moment, for undo and redo, with what the owner keeps beside it."""

    root: Row
    path: list[tuple[int, int]]
    pos: int
    selected: bool
    anchor: int | None
    extra: Extra | None = None


@dataclass(frozen=True)
class EntryRules:
    """What differs between pages' entry lines."""

    ans_prefix: bool = False  # an operator typed first gets `Ans` in front (the Calculator)
    # A sheet cell's paste: text is typed as it is, not with its spaces run together, and
    # copied cells, which have text but no nodes, paste as their text
    cells_paste: bool = False
    undo: bool = True  # keep undo steps (a sheet cell has no undo of its own)


def _nothing() -> None:
    pass


class EntrySession[Extra = None]:
    """An `Editor` with undo and redo, the shared clipboard and an action table."""

    def __init__(
        self,
        clipboard: Clipboard | None = None,
        rules: EntryRules | None = None,
        *,
        keep: Callable[[], Extra] | None = None,
        restore: Callable[[Extra], None] | None = None,
        on_key: Callable[[], None] | None = None,
    ) -> None:
        """`keep` gives what an undo step carries beside the entry line, `restore` puts it back;
        `on_key` runs before every edit or move in the entry line (the Calculator drops its
        picked history row)."""
        self.clipboard = clipboard if clipboard is not None else Clipboard()
        rules = rules if rules is not None else EntryRules()
        self.rules = rules
        self.ans_prefix = rules.ans_prefix
        self.cells_paste = rules.cells_paste
        self._keeps_undo = rules.undo
        self._keep = keep
        self._restore_extra = restore
        self._on_key = on_key
        self._editor = Editor(ans_prefix=rules.ans_prefix)
        self._undo: list[Snapshot[Extra]] = []
        self._redo: list[Snapshot[Extra]] = []
        self._group: str | None = None  # the kind of edit in progress, for undo grouping
        self._actions = self._action_table()

    @property
    def editor(self) -> Editor:
        return self._editor

    @editor.setter
    def editor(self, editor: Editor) -> None:
        editor.ans_prefix = self.ans_prefix
        self._editor = editor

    def reset(self) -> Editor:
        """A fresh, empty entry line with no undo: the new editor."""
        self.editor = Editor()
        self.forget_undo()
        return self._editor

    # ---- keys -------------------------------------------------------------------------------

    def perform(self, binding: Binding) -> bool:
        """Do what a key says to the entry line. False if this is not an entry-line action."""
        action = self._actions.get(binding.action)
        if action is None:
            return False
        action(binding.arg)
        return True

    def handles(self, action: str) -> bool:
        return action in self._actions

    def _action_table(self) -> dict[str, Callable[[str], object]]:
        actions: dict[str, Callable[[str], object]] = {name: self._move_key(name) for name in MOVES}
        actions.update(
            {
                "home_key": self._move_key("home"),
                "escape": lambda _: self._moved(_nothing),
                "select_cells": self.select_cells,
                "insert": self.insert,
                "insert_linear": self.insert_linear,
                "template": self.template,
                "power": self.power,
                "accent": lambda _: self.accent(),
                "backspace": self.backspace,
                "delete": lambda _: self.delete(),
                "clear": lambda _: self.clear(),
                "copy": lambda _: self.copy(),
                "cut": lambda _: self.cut(),
                "paste": self.paste,
                "undo": lambda _: self.step(undo=True),
                "redo": lambda _: self.step(undo=False),
                "place": lambda target: self.place(target, extend=False),
                "extend": lambda target: self.place(target, extend=True),
                "select_token": self.select_token,
                "drop": self.drop,
            }
        )
        return actions

    def _move_key(self, name: str) -> Callable[[str], None]:
        return lambda _: self.move(name)

    # ---- moving -----------------------------------------------------------------------------

    def _moved(self, method: Callable[[], None]) -> None:
        if self._on_key is not None:
            self._on_key()
        self._group = None
        method()

    def move(self, name: str) -> None:
        """An editor movement by its action name (`left`, `select_word_right`, `up`, ...)."""
        self._moved(getattr(self._editor, name))

    def select_cells(self, spec: str) -> None:
        """`row:-1`, `row:1`, `col:-1` or `col:1`: select (then grow) a matrix's rows or columns."""
        axis, _, step = spec.partition(":")
        self._moved(lambda: self._editor.select_cells(axis, int(step or 0)))

    def place(self, target: str, *, extend: bool) -> None:
        """A click in the entry line (`place`) or a shift+click (`extend`): see `Editor.place`."""
        self._at_target(target, lambda path, pos: self._editor.place(path, pos, extend=extend))

    def select_token(self, target: str) -> None:
        """A double-click selects the token there."""
        self._at_target(target, self._editor.select_token)

    def _at_target(
        self, target: str, act: Callable[[Sequence[tuple[int, int]], int], None]
    ) -> None:
        try:
            path, pos = parse_target(target)
        except ValueError:
            return
        self._moved(lambda: act(path, pos))

    def drop(self, target: str) -> None:
        """Selected text dragged to `target` moves there (H3 k); undoable."""
        try:
            path, pos = parse_target(target)
        except ValueError:
            return
        self.edit("other", lambda: self._editor.move_selection(path, pos))

    # ---- editing, with undo groups ----------------------------------------------------------

    def edit(self, kind: str, change: Callable[[], object]) -> None:
        """Run an edit. Undo steps back one group: a run of operands, or one operator; typing
        over a selection is a step of its own."""
        if self._on_key is not None:
            self._on_key()
        if self._editor.anchor is not None:
            kind = "other"
        if self._keeps_undo and (kind != self._group or kind != "operand"):
            self.remember()
        self._group = kind
        change()

    def insert(self, text: str) -> None:
        """Type `text` key by key."""
        kind = "operand" if all(char in OPERAND_CHARS for char in text) else "operator"
        self.edit(kind, lambda: self._editor.insert_text(text))

    def insert_linear(self, text: str) -> None:
        """Paste linear text; a `MARK` in it is where the cursor is left."""
        self.edit("other", lambda: self._editor.insert_linear(text, MARK))

    def template(self, spec: str) -> None:
        """A `Kind` name, with `:ROWS,COLS` for a matrix or `:ROWS` for a piecewise or system
        template (`fraction`, `matrix:2,3`, `system:2`); `list:3` is a list of three."""
        kind, _, shape = spec.partition(":")
        rows, _, cols = shape.partition(",")
        size = (int(rows), int(cols or 1)) if shape else (2, 2)
        if kind == Kind.LIST:
            size = (1, int(rows) if shape else 3)
        self.edit("other", lambda: self._editor.insert_template(Kind(kind), size))

    def power(self, exponent: str) -> None:
        """A key that opens an exponent already holding `exponent` (x squared)."""

        def change() -> None:
            self._editor.insert("^")
            self._editor.insert_text(exponent)

        self.edit("other", change)

    def accent(self) -> None:
        self.edit("operand", self._editor.cycle_accent)

    def backspace(self, arg: str = "") -> None:
        """Backspace, or the keypad's del (`whole`), which takes a template just before the
        cursor away in one press (run 5, F3) where Backspace highlights it first (0017)."""
        if not self._editor.is_empty:
            self.edit("other", self._whole if arg == "whole" else self._editor.backspace)

    def _whole(self) -> None:
        editor = self._editor
        row = editor.row()
        before = row[editor.pos - 1] if editor.pos and editor.anchor is None else None
        if isinstance(before, Template) and not editor.selected:
            editor.backspace()  # highlights it
        editor.backspace()

    def delete(self) -> None:
        if not self._editor.is_empty:
            self.edit("other", self._editor.delete)

    def clear(self) -> None:
        self.edit("other", self._editor.clear)

    # ---- clipboard --------------------------------------------------------------------------

    def copy(self) -> bool:
        """Copy the selection. False if nothing is selected."""
        nodes = self._editor.selection()
        if nodes:
            self.clipboard.nodes = nodes
        return bool(nodes)

    def cut(self) -> bool:
        """Cut the selection (undoable). False if nothing is selected."""
        if not self._editor.selection():
            return False
        self.edit("other", lambda: setattr(self.clipboard, "nodes", self._editor.cut()))
        return True

    def paste(self, text: str) -> None:
        """Paste the clipboard's nodes, or `text` from the system clipboard if it differs.

        With `cells_paste` (a sheet cell) text is typed as it is, not with its spaces run
        together, and copied cells, which have text but no nodes, paste as their text."""
        clipboard = self.clipboard
        if self.cells_paste:
            typed = text if text and (text != clipboard.text or not clipboard.nodes) else ""
            if not typed and not clipboard.nodes:
                typed = clipboard.text
        else:
            typed = " ".join(text.split()) if text and text != clipboard.text else ""
        if typed:
            self.edit("other", lambda: self._editor.insert_linear(typed))
        elif clipboard.nodes:
            self.edit("other", lambda: self._editor.paste(clipboard.nodes))

    # ---- undo -------------------------------------------------------------------------------

    def snapshot(self) -> Snapshot[Extra]:
        """The entry line now (a copy), with what `keep` gives."""
        e = self._editor
        root, path = copy.deepcopy((e.root, e.path))
        extra = self._keep() if self._keep is not None else None
        return Snapshot(root, path, e.pos, e.selected, e.anchor, extra)

    def remember(self, snapshot: Snapshot[Extra] | None = None) -> None:
        """Add an undo step: `snapshot`, or the entry line now. Redo is cleared."""
        self._undo.append(snapshot if snapshot is not None else self.snapshot())
        self._redo.clear()

    def end_group(self) -> None:
        """The next edit starts an undo step of its own."""
        self._group = None

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def forget_undo(self) -> None:
        """Drop the undo and redo history (after a document is loaded)."""
        self._undo.clear()
        self._redo.clear()
        self._group = None

    def step(self, *, undo: bool) -> bool:
        """Undo (or redo) one step. False if there was none."""
        source, target = (self._undo, self._redo) if undo else (self._redo, self._undo)
        stepped = bool(source)
        if source:
            target.append(self.snapshot())
            self._restore(source.pop())
        self._group = None
        return stepped

    def _restore(self, snapshot: Snapshot[Extra]) -> None:
        e = self._editor
        root, path = copy.deepcopy((snapshot.root, snapshot.path))
        e.cell_sel = None
        e.root, e.path, e.pos, e.selected, e.anchor = (
            root,
            path,
            snapshot.pos,
            snapshot.selected,
            snapshot.anchor,
        )
        if snapshot.extra is not None and self._restore_extra is not None:
            self._restore_extra(snapshot.extra)
