"""Write `src/cassim/device/math_metrics.json` from the KaTeX fonts that ship with Flet.

    uv run python -m tools.math_metrics

The maths layout (`device/math_layout.py`, decision 0038) sets glyphs from these numbers, and
Flet draws them with the same fonts, so the two agree. Run this again when Flet is upgraded: a
test compares the file with the fonts installed.

For each font the file holds its line metrics (`hhea`: ascender, descender, line gap, in ems)
and, for each character, `[advance, height, depth, ink left, ink right]` in ems: the height and
depth of the glyph's outline above and below the baseline, and the left and right edges of its
ink. The layout takes the ink's overhang past the advance as TeX's italic correction.
"""

from __future__ import annotations

import json
import sys
from importlib.util import find_spec
from pathlib import Path
from typing import Any

from fontTools.ttLib import TTFont

OUT = Path(__file__).resolve().parents[1] / "src" / "cassim" / "device" / "math_metrics.json"
FONTS_IN_FLET = "web/assets/packages/flutter_math_fork/lib/katex_fonts/fonts"
NAMES = (
    "Main-Regular",
    "Main-Bold",
    "Main-Italic",
    "Math-Italic",
    "Math-BoldItalic",
    "AMS-Regular",
    "Size1-Regular",
    "Size2-Regular",
    "Size3-Regular",
    "Size4-Regular",
    "Typewriter-Regular",
)

type Glyph = list[float]


def fonts_folder() -> Path | None:
    """Where the installed Flet keeps the KaTeX fonts, or None without `flet_web`."""
    spec = find_spec("flet_web")
    if spec is None or spec.origin is None:
        return None
    folder = Path(spec.origin).parent / FONTS_IN_FLET
    return folder if folder.is_dir() else None


def _ems(value: float) -> float:
    return round(value, 5)


def font_metrics(path: Path) -> dict[str, object]:
    font: Any = TTFont(path)  # fontTools' tables are typed too loosely to check
    units = font["head"].unitsPerEm
    hhea = font["hhea"]
    outlines, advances = font["glyf"], font["hmtx"]
    glyphs: dict[str, Glyph] = {}
    for code, name in sorted(font.getBestCmap().items()):
        outline = outlines[name]
        if outline.numberOfContours == 0:
            height = depth = left = right = 0.0
        else:
            outline.recalcBounds(outlines)
            height, depth = max(0.0, outline.yMax / units), max(0.0, -outline.yMin / units)
            left, right = outline.xMin / units, outline.xMax / units
        advance = advances[name][0] / units
        glyphs[str(code)] = [_ems(advance), _ems(height), _ems(depth), _ems(left), _ems(right)]
    return {
        "hhea": [hhea.ascent / units, -hhea.descent / units, hhea.lineGap / units],
        "glyphs": glyphs,
    }


def metrics(folder: Path) -> dict[str, dict[str, object]]:
    return {name: font_metrics(folder / f"KaTeX_{name}.ttf") for name in NAMES}


def text(data: dict[str, dict[str, object]]) -> str:
    return json.dumps(data, separators=(",", ":")) + "\n"


def main() -> int:
    folder = fonts_folder()
    if folder is None:
        print("flet_web is not installed: uv sync --group web", file=sys.stderr)
        return 1
    OUT.write_text(text(metrics(folder)), encoding="utf-8", newline="\n")
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
