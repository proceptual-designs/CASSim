"""Shift-arrow selection and Ctrl+A (FR-CALC-004; emulator runs S1 h, S5 d and e)."""

from cassim.device.editor import Editor, Kind, linear_text


def test_shift_left_extends_one_node_at_a_time() -> None:
    editor = Editor("abc")
    editor.select_left()
    editor.select_left()
    assert editor.span == (1, 3)
    editor.select_right()
    assert editor.span == (2, 3)
    editor.select_right()
    assert editor.anchor is None  # back where it started: nothing selected


def test_a_template_is_selected_as_one_unit() -> None:
    editor = Editor("1")
    editor.insert_template(Kind.FRACTION)
    editor.insert("2")
    editor.right()
    editor.select_left()
    assert editor.span == (0, 1)  # the whole fraction, not a slot of it


def test_typing_replaces_the_selection() -> None:
    editor = Editor("a+b")
    editor.select_all()
    editor.insert("9")
    assert editor.linear() == "9"


def test_backspace_and_delete_remove_the_selection() -> None:
    editor = Editor("abc")
    editor.select_left()
    editor.select_left()
    editor.backspace()
    assert editor.linear() == "a"
    editor = Editor("abc")
    editor.home()
    editor.select_right()
    editor.delete()
    assert editor.linear() == "bc"


def test_plain_arrows_collapse_the_selection_to_an_edge() -> None:
    editor = Editor("abcd")
    editor.left()
    editor.select_left()
    editor.select_left()  # selects `bc`, cursor at 1
    editor.left()
    assert (editor.anchor, editor.pos) == (None, 1)
    editor.select_right()
    editor.select_right()
    editor.right()
    assert (editor.anchor, editor.pos) == (None, 3)


def test_fraction_template_takes_the_selection_as_numerator() -> None:
    """S1 h: with text selected, ctrl+/ makes it the numerator."""
    editor = Editor("ab")
    editor.select_left()
    editor.select_left()
    editor.insert_template(Kind.FRACTION)
    editor.insert("3")
    assert editor.linear() == "((ab)/(3))"


def test_selection_is_drawn_and_the_cursor_stays_outside_it() -> None:
    editor = Editor("abc")
    editor.select_left()
    editor.select_left()
    tex = editor.latex()
    assert r"\fcolorbox" in tex
    assert tex.startswith("a")
    assert tex.count("rule") == 1
    assert "colorbox" not in editor.latex(cursor=False)


def test_select_all_on_an_empty_line_selects_nothing() -> None:
    editor = Editor()
    editor.select_all()
    assert editor.anchor is None


def test_a_backslash_is_drawn_not_left_as_broken_latex() -> None:
    """`x\\` used to emit a raw backslash, which the renderer showed as a faint parse error."""
    tex = Editor("x\\").latex(cursor=False)
    assert tex == r"x\backslash "


def test_word_selection_runs_over_a_word_then_the_spaces() -> None:
    editor = Editor("sin(x) + 12")
    editor.select_word_left()
    assert editor.span == (9, 11)  # `12`
    editor.select_word_left()
    assert editor.span == (7, 11)  # the `+ ` before it is one step
    editor.select_word_left()
    assert editor.span == (5, 11)  # over the spaces, then the `)`


def test_word_right_and_word_left_move_without_selecting() -> None:
    editor = Editor("ab + cd")
    editor.home()
    editor.word_right()
    assert editor.pos == 3
    editor.word_right()
    assert editor.pos == 5
    editor.word_left()
    assert editor.pos == 3
    assert editor.anchor is None


def test_a_template_is_one_word() -> None:
    editor = Editor("1")
    editor.insert_template(Kind.FRACTION)
    editor.insert("2")
    editor.right()
    editor.insert("x")
    editor.select_word_left()
    editor.select_word_left()
    assert editor.span == (0, 2)


def test_select_to_start_and_end() -> None:
    editor = Editor("abcd")
    editor.left()
    editor.left()
    editor.select_to_end()
    assert editor.span == (2, 4)
    editor = Editor("abcd")
    editor.left()
    editor.select_to_start()
    assert editor.span == (0, 3)


def test_copy_keeps_templates_and_cut_removes_them() -> None:
    editor = Editor("1")
    editor.insert_template(Kind.FRACTION)
    editor.insert("2")
    editor.right()
    editor.select_left()
    copied = editor.selection()
    assert linear_text(copied) == "((1)/(2))"
    editor.paste(copied)
    assert editor.linear() == "((1)/(2))"  # replaced the selection with a copy of itself
    editor.paste(copied)
    assert editor.linear() == "((1)/(2))((1)/(2))"
    assert editor.root[0] is not editor.root[1]  # copies, not the same template twice
    editor.select_left()
    assert linear_text(editor.cut()) == "((1)/(2))"
    assert editor.linear() == "((1)/(2))"
