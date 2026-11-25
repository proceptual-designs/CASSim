# Requirements traced here: FR-CALC-004
"""The entry line draws every template kind the model declares (decision 0035, stage 2)."""

from collections.abc import Iterator

import flet as ft
import pytest

from cassim.app.entry_line import DRAWN_KINDS, EntryLine
from cassim.app.theme import DARK
from cassim.device.editor import Editor
from cassim.device.templates import Kind


def test_every_declared_kind_has_a_drawing() -> None:
    assert set(Kind) == DRAWN_KINDS


@pytest.mark.parametrize("kind", list(Kind))
def test_every_kind_builds_controls(kind: Kind) -> None:
    editor = Editor()
    editor.insert_template(kind)
    EntryLine(DARK, 20, lambda _path, _pos: None).build(editor)


def _walk(control: ft.Control) -> Iterator[ft.Control]:
    yield control
    content = getattr(control, "content", None)
    if isinstance(content, ft.Control):
        yield from _walk(content)
    for child in getattr(control, "controls", None) or []:
        yield from _walk(child)


def test_the_constants_are_drawn_as_the_history_draws_them() -> None:
    """ⅇ is a bold upright e and ⅈ a bold italic i, as in the LaTeX (`\\mathbf{e}`,
    `\\boldsymbol{i}`), not the double-struck letters of a fallback font. The text keeps ⅇ and ⅈ."""
    editor = Editor()
    editor.insert_text("ⅇ+ⅈ")
    line = EntryLine(DARK, 20, lambda _path, _pos: None)
    texts = {str(c.value): c for c in _walk(line.build(editor)) if isinstance(c, ft.Text)}
    assert "ⅇ" not in texts
    assert "ⅈ" not in texts
    assert texts["e"].weight == ft.FontWeight.BOLD
    assert "KaTeX_Main" in str(texts["e"].font_family)  # upright
    assert texts["i"].weight == ft.FontWeight.BOLD
    assert "KaTeX_Math" in str(texts["i"].font_family)  # italic
    assert editor.linear() == "ⅇ+ⅈ"
