"""Host-side checks and timings for the layout (CPython; the browser runs it under Pyodide).

    uv run python spikes/math_render_a/check_layout.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "app" / "src"))

import mathlayout as ml  # noqa: E402
import treeio  # noqa: E402

cases = json.loads((HERE / "app" / "src" / "cases.json").read_text(encoding="utf-8"))
for n, case in enumerate(cases):
    row = treeio.load_row(case["tree"])
    styles = case["styles"]
    lookup = lambda p, s=styles: s.get(treeio.path_key(p), {})  # noqa: E731
    lay = ml.layout(row, lookup)
    reps = 50
    t0 = time.perf_counter()
    for _ in range(reps):
        ml.layout(row, lookup)
    ms = (time.perf_counter() - t0) / reps * 1000
    unmerged = len(ml.layout(row, lookup, merge=False).items)
    kinds = {}
    for it in lay.items:
        kinds[type(it).__name__] = kinds.get(type(it).__name__, 0) + 1
    # every stop's caret position, clicked, must give back that stop (or one at the same x/row)
    bad = 0
    stops = lay.stops()
    for path, pos in stops:
        x, top, bottom = lay.caret(path, pos)
        got = lay.hit(x, (top + bottom) / 2)
        if got != (path, pos):
            gx = lay.caret(*got)[0]
            if abs(gx - x) > 1e-6:
                bad += 1
                print("  click mismatch", path, pos, "->", got)
    print(
        f"case {n}: {ms:.2f} ms layout (CPython), size {lay.width:.2f} x {lay.height + lay.depth:.2f} em,"
        f" shapes {len(lay.items)} (unmerged {unmerged}) {kinds}, rows {len(lay.rows)},"
        f" stops {len(stops)}, click round-trip mismatches {bad}"
    )
