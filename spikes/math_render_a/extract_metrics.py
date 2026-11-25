"""Dev-time: read the KaTeX fonts that ship with flet_web and write `app/src/metrics.json`.

Run from the repository root (fontTools is not a project dependency):

    uv run --with fonttools python spikes/math_render_a/extract_metrics.py

For each font the JSON holds the vertical metrics Flutter may use for the line box (hhea, OS/2
typo and win, unitsPerEm) and, per code point, `[advance, height, depth, xmin, xmax]` in ems:
height/depth from the glyph's bounding box (yMax, -yMin, clipped at 0) and its ink's left and
right edges. The layout takes max(0, xmax - advance) as TeX's italic correction (the TFM value is
not in the TTF).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[2]
FONTS = (
    ROOT
    / ".venv/Lib/site-packages/flet_web/web/assets/packages/flutter_math_fork/lib/katex_fonts/fonts"
)
NAMES = [
    "KaTeX_Main-Regular",
    "KaTeX_Main-Bold",
    "KaTeX_Main-Italic",
    "KaTeX_Math-Italic",
    "KaTeX_Math-BoldItalic",
    "KaTeX_AMS-Regular",
    "KaTeX_Size1-Regular",
    "KaTeX_Size2-Regular",
    "KaTeX_Size3-Regular",
    "KaTeX_Size4-Regular",
    "KaTeX_Typewriter-Regular",
]
OUT = Path(__file__).resolve().parent / "app" / "src" / "metrics.json"


def _r(v: float) -> float:
    return round(v, 5)


def font_metrics(path: Path) -> dict:
    font = TTFont(path)
    upm = font["head"].unitsPerEm
    hhea, os2 = font["hhea"], font["OS/2"]
    glyf = font["glyf"]
    hmtx = font["hmtx"]
    glyphs: dict[str, list[float]] = {}
    for cp, name in sorted(font.getBestCmap().items()):
        advance = hmtx[name][0] / upm
        g = glyf[name]
        if g.numberOfContours == 0:
            height = depth = xmin = xmax = 0.0
        else:
            g.recalcBounds(glyf)
            height = max(0.0, g.yMax / upm)
            depth = max(0.0, -g.yMin / upm)
            xmin, xmax = g.xMin / upm, g.xMax / upm
        glyphs[str(cp)] = [_r(advance), _r(height), _r(depth), _r(xmin), _r(xmax)]
    return {
        "upm": upm,
        "hhea": [hhea.ascent / upm, -hhea.descent / upm, hhea.lineGap / upm],
        "typo": [os2.sTypoAscender / upm, -os2.sTypoDescender / upm, os2.sTypoLineGap / upm],
        "win": [os2.usWinAscent / upm, os2.usWinDescent / upm],
        "kern": any(t in font for t in ("kern", "GPOS", "GSUB")),
        "glyphs": glyphs,
    }


def main() -> None:
    data = {name.removeprefix("KaTeX_"): font_metrics(FONTS / f"{name}.ttf") for name in NAMES}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8", newline="\n")
    kb = OUT.stat().st_size / 1024
    print(f"wrote {OUT} ({kb:.0f} KB); kerning or shaping tables: "
          f"{[n for n, f in data.items() if f['kern']] or 'none'}", file=sys.stderr)


if __name__ == "__main__":
    main()
