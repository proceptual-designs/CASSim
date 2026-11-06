"""Zip src/cassim (pure Python, no tests) for the browser engine worker."""

import sys
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "src"
out = Path(sys.argv[1])
out.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted((root / "cassim").rglob("*.py")):
        z.write(f, f.relative_to(root).as_posix())
print(out, f"{out.stat().st_size / 1e3:.0f} kB")
