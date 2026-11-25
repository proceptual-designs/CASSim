"""Dev-time extractor: KaTeX font metrics to metrics.json.

Run: uv run --with fonttools python spikes/math_render_b/extract_metrics.py
Per font: unitsPerEm, hhea/OS2 ascent+descent, and per glyph [advance, yMax, yMin] in em.
"""

import json
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[2]
FONTS = (
    ROOT / ".venv/Lib/site-packages/flet_web/web/assets/packages/flutter_math_fork"
    "/lib/katex_fonts/fonts"
)
NAMES = [
    "Main-Regular", "Main-Bold", "Main-Italic", "Main-BoldItalic", "Math-Italic",
    "Math-BoldItalic", "Size1-Regular", "Size2-Regular", "Size3-Regular", "Size4-Regular",
    "Typewriter-Regular", "AMS-Regular",
]  # fmt: skip

out: dict[str, dict] = {}
for name in NAMES:
    path = FONTS / f"KaTeX_{name}.ttf"
    if not path.exists():
        continue
    f = TTFont(path)
    upm = f["head"].unitsPerEm
    cmap = f.getBestCmap()
    hmtx = f["hmtx"]
    glyf = f["glyf"]
    glyphs = {}
    for cp, gname in cmap.items():
        if cp > 0x2FFF:
            continue
        adv = hmtx[gname][0] / upm
        g = glyf[gname]
        ymax = g.yMax / upm if g.numberOfContours else 0.0
        ymin = g.yMin / upm if g.numberOfContours else 0.0
        glyphs[chr(cp)] = [round(adv, 4), round(ymax, 4), round(ymin, 4)]
    os2 = f["OS/2"]
    hhea = f["hhea"]
    out[name] = {
        "upm": upm,
        "hhea": [hhea.ascent / upm, hhea.descent / upm, hhea.lineGap / upm],
        "typo": [os2.sTypoAscender / upm, os2.sTypoDescender / upm, os2.sTypoLineGap / upm],
        "win": [os2.usWinAscent / upm, os2.usWinDescent / upm],
        "has_kern": "kern" in f or "GPOS" in f,
        "has_gsub": "GSUB" in f,
        "glyphs": glyphs,
    }
    o = out[name]
    print(name, o["hhea"], o["typo"], o["win"], o["has_kern"], o["has_gsub"], len(glyphs))
(Path(__file__).parent / "metrics.json").write_text(
    json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
)
