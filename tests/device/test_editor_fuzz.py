"""Random edits and clicks never break the editor (FR-CALC-004): the cursor stays on a real row,
the line can always be turned into text and LaTeX, and the model stays consistent. A second test
checks that the canvas line draws whatever state the fuzz reaches, with its cursor."""

import copy
from typing import Any

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from cassim.app.math_canvas import MathLine
from cassim.app.theme import DARK
from cassim.device.editor import Editor, Kind, Row, Template
from cassim.device.templates import GRIDS

_CHARS = st.sampled_from(list('0123456789abxye+-*/^()., π√"{}[]=;'))
_SHAPE = st.tuples(st.integers(1, 3), st.integers(1, 3))
_PATH = st.lists(st.tuples(st.integers(0, 4), st.integers(0, 9)), max_size=4)
_TEXTS = st.sampled_from(["x^2+1", "√(3)*2", "a^-b^c", "{1,2}", "[1,2;3,4]", "", "^", "√", '"a^b'])
_MOVES = [
    "left",
    "right",
    "up",
    "down",
    "tab",
    "shift_tab",
    "home",
    "end",
    "backspace",
    "delete",
    "select_left",
    "select_right",
    "select_all",
    "select_word_left",
    "select_word_right",
    "select_to_start",
    "select_to_end",
    "word_left",
    "word_right",
    "cycle_accent",
    "complete_brackets",
    "copy",
    "cut",
    "paste",
]

_TYPING = st.one_of(
    st.tuples(st.just("char"), _CHARS),
    st.tuples(st.just("template"), st.tuples(st.sampled_from(list(Kind)), _SHAPE)),
)
_OPS = st.one_of(
    _TYPING,
    st.tuples(st.just("move"), st.sampled_from(_MOVES)),
    st.tuples(st.just("cells"), st.tuples(st.sampled_from(["row", "col"]), st.integers(-1, 1))),
    st.tuples(st.just("linear"), _TEXTS),
    st.tuples(st.just("token"), st.tuples(_PATH, st.integers(-2, 12))),
    st.tuples(st.just("drop"), st.tuples(_PATH, st.integers(-2, 12))),
    st.tuples(st.just("click"), st.tuples(_PATH, st.integers(-2, 12), st.booleans())),
)


def valid(editor: Editor) -> None:
    row = editor.root
    for index, slot in editor.path:
        node = row[index]
        assert isinstance(node, Template)
        row = node.slots[slot]
    assert 0 <= editor.pos <= len(row)
    if editor.anchor is not None:
        assert 0 <= editor.anchor <= len(row)
        assert editor.anchor != editor.pos
    if editor.selected:
        assert editor.pos >= 1
        assert isinstance(row[editor.pos - 1], Template)
    check_grids(editor.root)
    editor.linear()
    editor.latex()
    editor.latex(cursor=False)
    editor.selection()
    editor.missing_closers()
    assert copy.deepcopy(editor.root) == editor.root


def check_grids(row: Row) -> None:
    for node in row:
        if isinstance(node, Template):
            if node.kind in GRIDS:
                assert node.cols >= 1
                assert node.slots
                assert len(node.slots) % node.cols == 0
            for slot in node.slots:
                check_grids(slot)


def apply(editor: Editor, name: str, arg: Any, clipboard: Row) -> Row:
    """Do one operation; return the clipboard (the last copied or cut nodes)."""
    if name == "char":
        editor.insert(str(arg))
    elif name == "template":
        kind, shape = arg
        editor.insert_template(kind, shape)
    elif name == "move":
        if arg == "copy":
            return editor.selection()
        if arg == "cut":
            return editor.cut()
        if arg == "paste":
            editor.paste(clipboard)
        else:
            getattr(editor, str(arg))()
    elif name == "cells":
        axis, step = arg
        editor.select_cells(axis, step)
    elif name == "linear":
        editor.insert_linear(str(arg))
    elif name == "token":
        path, pos = arg
        editor.select_token(path, pos)
    elif name == "drop":
        path, pos = arg
        editor.move_selection(path, pos)
    else:
        path, pos, extend = arg
        editor.place(path, pos, extend=extend)
    return clipboard


@settings(max_examples=250, deadline=None)
@given(st.lists(_OPS, max_size=40))
def test_random_edits_and_clicks_keep_the_cursor_valid(ops: list[tuple[str, object]]) -> None:
    editor = Editor()
    clipboard: Row = []
    for name, arg in ops:
        clipboard = apply(editor, name, arg, clipboard)
        valid(editor)


@settings(max_examples=40, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(st.lists(_OPS, max_size=30))
def test_the_entry_line_draws_any_fuzzed_state(ops: list[tuple[str, object]]) -> None:
    editor = Editor()
    clipboard: Row = []
    for name, arg in ops:
        clipboard = apply(editor, name, arg, clipboard)
    line = MathLine(DARK, 20, lambda _path, _pos: None)
    line.build(editor)
    path, pos = line.place_at(*line.point_at(editor.path, editor.pos))
    assert tuple(path) in line.layout.rows  # a click where the cursor is finds a real place
    assert 0 <= pos <= len(line.layout.rows[tuple(path)].gaps)


@settings(max_examples=150, deadline=None)
@given(st.lists(_TYPING, max_size=30))
def test_a_restored_snapshot_gives_the_same_text(ops: list[tuple[str, object]]) -> None:
    editor = Editor()
    clipboard: Row = []
    for name, arg in ops:
        clipboard = apply(editor, name, arg, clipboard)
    restored = Editor()
    restored.root = copy.deepcopy(editor.root)
    restored.path = list(editor.path)
    restored.pos = editor.pos
    restored.selected = editor.selected
    restored.anchor = editor.anchor
    assert restored.linear() == editor.linear()
    assert restored.latex() == editor.latex()


def test_a_drop_target_outside_the_row_is_clamped() -> None:
    """Found by the fuzz: `move_selection` took `pos` unchecked and left the cursor off the row."""
    for pos in (-1, 5):
        editor = Editor("0")
        editor.select_left()
        editor.move_selection([], pos)
        valid(editor)
        assert editor.linear() == "0"
