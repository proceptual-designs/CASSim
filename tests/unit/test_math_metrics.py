# Requirements traced here: FR-CALC-004
"""The font metrics the maths layout sets glyphs from are those of the fonts Flet draws with
(decision 0038): a Flet upgrade that changes a font fails here until the file is written again
(`uv run python -m tools.math_metrics`)."""

import json

import pytest
from tools import math_metrics


def test_the_metrics_file_matches_the_installed_fonts() -> None:
    folder = math_metrics.fonts_folder()
    if folder is None:
        pytest.skip("flet_web is not installed, so there are no fonts to read")
    written = json.loads(math_metrics.OUT.read_text(encoding="utf-8"))
    assert written == json.loads(math_metrics.text(math_metrics.metrics(folder)))


def test_every_font_the_layout_names_is_in_the_file() -> None:
    written = json.loads(math_metrics.OUT.read_text(encoding="utf-8"))
    assert set(written) == set(math_metrics.NAMES)
    for font in written.values():
        ascender, descender, gap = font["hhea"]
        assert 0.6 < ascender < 1.8
        assert 0.2 < descender < 1.3
        assert gap == pytest.approx(0.09)
        assert len(font["glyphs"]) > 10
