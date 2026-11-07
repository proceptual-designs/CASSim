"""Random edits and clicks never break the editor (FR-CALC-004): the cursor stays on a real row,
the line can always be turned into text and LaTeX, and undo-free state stays consistent."""

from hypothesis import given, settings
from hypothesis import strategies as st

from cassim.device.editor import Editor, Kind, Template

_CHARS = st.sampled_from(list("0123456789abxy+-*/^()., π"))
_KINDS = st.sampled_from([Kind.FRACTION, Kind.POWER, Kind.ROOT, Kind.MATRIX])
_PATH = st.lists(st.tuples(st.integers(0, 4), st.integers(0, 9)), max_size=4)

_OPS = st.one_of(
    st.tuples(st.just("char"), _CHARS),
    st.tuples(st.just("template"), _KINDS),
    st.tuples(
        st.just("move"),
        st.sampled_from(
            [
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
            ]
        ),
    ),
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
    editor.linear()
    editor.latex()
    editor.selection()


@settings(max_examples=300, deadline=None)
@given(st.lists(_OPS, max_size=40))
def test_random_edits_and_clicks_keep_the_cursor_valid(ops: list[tuple[str, object]]) -> None:
    editor = Editor()
    for name, arg in ops:
        if name == "char":
            editor.insert(str(arg))
        elif name == "template":
            assert isinstance(arg, Kind)
            editor.insert_template(arg)
        elif name == "move":
            getattr(editor, str(arg))()
        else:
            assert isinstance(arg, tuple)
            path, pos, extend = arg
            editor.place(path, pos, extend=extend)
        valid(editor)
