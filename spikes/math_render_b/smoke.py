"""Layout-only smoke test and timing (no Flet)."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).parent))
from cassim.device.editor_ast import row_from_text  # noqa: E402
from layout import Layout  # noqa: E402

from samples import EXPRESSIONS  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
for text in EXPRESSIONS:
    row = row_from_text(text)
    t = time.perf_counter()
    for _ in range(20):
        lay = Layout(row, 20.0)
    ms = (time.perf_counter() - t) / 20 * 1000
    print(f"{ms:.1f} ms  items={len(lay.items)} rows={len(lay.rows)} size={lay.width:.0f}x{lay.height:.0f}")
    print("  runs:", [it[3] for it in lay.items if it[0] == "t"][:12])
