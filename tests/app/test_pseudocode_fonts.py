"""Bundled fonts for the pseudocode source editor."""

from pathlib import Path
from types import SimpleNamespace
from typing import cast

from PIL import ImageFont

from cassim.app.shell import Shell
from cassim.devices.pseudocode.ui.app import CODE_FONT, MATH_FONT, CodeApp

ROOT = Path(__file__).parents[2]
FONTS = ROOT / "src" / "cassim" / "app" / "assets" / "fonts"


def test_code_font_is_bundled_with_a_complete_symbol_fallback() -> None:
    mono = ImageFont.truetype(FONTS / "RobotoMono-Regular.ttf", 24)
    maths = ImageFont.truetype(FONTS / "NotoSansMath-Regular.ttf", 24)

    assert mono.getname()[0] == "Roboto Mono"
    for codepoint in (0x2190, 0x2147, 0x03C0, 0x2264, 0x2265, 0x2260):
        _left, top, _right, bottom = maths.getbbox(chr(codepoint))
        assert bottom > top


def test_editor_can_switch_between_monospace_and_formatted_linear_text() -> None:
    app = CodeApp(cast(Shell, SimpleNamespace(page=None)))
    assert app.editor_text_style().font_family == CODE_FONT
    assert MATH_FONT in (app.editor_text_style().font_family_fallback or [])

    app.code_style = "formatted"
    assert app.editor_text_style().font_family == "sans-serif"
    assert MATH_FONT in (app.editor_text_style().font_family_fallback or [])
