"""Control counts (ours vs EntryLine), layout timing and a hit/caret round-trip check."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8")
from app import entry_line_controls, make_editor  # noqa: E402
from layout import Layout  # noqa: E402
from painter import count_controls, paint  # noqa: E402

for i in range(3):
    e = make_editor(i)
    Layout(e.root, 20.0)
    t = time.perf_counter()
    for _ in range(50):
        lay = Layout(e.root, 20.0)
    ms = (time.perf_counter() - t) / 50 * 1000
    t = time.perf_counter()
    ctrls = paint(lay, "#000")
    pm = (time.perf_counter() - t) * 1000
    from cassim.devices.nspire.ui.entry import EntryLine
    from cassim.app.theme import DARK

    t = time.perf_counter()
    n_entry = count_controls(EntryLine(DARK, 20.0, lambda *_: None).build(e))
    em = (time.perf_counter() - t) * 1000
    bad = 0
    for path, r in lay.rows.items():
        mid = (r.top + r.bot) / 2
        for pos, g in enumerate(r.gaps):
            hp, hpos = lay.hit(g, mid)
            if len(hp) < len(path) or (hp == path and abs(lay.caret(hp, hpos)[0] - g) > 0.01):
                bad += 1
    print(f"expr {i+1}: layout {ms:.2f} ms, paint objects {pm:.2f} ms, ours {len(ctrls)} controls,"
          f" EntryLine {n_entry} controls (build {em:.1f} ms); hit mismatches {bad} of {sum(len(r.gaps) for r in lay.rows.values())} gaps")
