# Requirements traced here: FR-CALC-004
"""The entry line draws every template kind the model declares (decision 0035, stage 2)."""

import pytest

from cassim.app.theme import DARK
from cassim.device.editor import Editor
from cassim.device.templates import Kind
from cassim.devices.nspire.ui.entry import DRAWN_KINDS, EntryLine


def test_every_declared_kind_has_a_drawing() -> None:
    assert set(Kind) == DRAWN_KINDS


@pytest.mark.parametrize("kind", list(Kind))
def test_every_kind_builds_controls(kind: Kind) -> None:
    editor = Editor()
    editor.insert_template(kind)
    EntryLine(DARK, 20, lambda _path, _pos: None).build(editor)
