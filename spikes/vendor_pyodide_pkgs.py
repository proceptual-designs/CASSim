"""Vendor Pyodide packages (and deps from pyodide-lock.json) into a --no-cdn flet build."""

import json
import sys
import urllib.request
from pathlib import Path

dist = Path(sys.argv[1])
want = sys.argv[2:]
pyo = dist / "pyodide"
lock = json.loads((pyo / "pyodide-lock.json").read_text())
base = (
    "https://cdn.jsdelivr.net/pyodide/v"
    + json.loads((pyo / "package.json").read_text())["version"]
    + "/full/"
)
pk = lock["packages"]
seen: list[str] = []


def add(n: str) -> None:
    n = n.lower()
    if n in seen:
        return
    seen.append(n)
    for d in pk[n]["depends"]:
        add(d)


for w in want:
    add(w)
total = 0
for n in seen:
    f = pk[n]["file_name"]
    dest = pyo / f
    if not dest.exists():
        data = urllib.request.urlopen(base + f).read()
        dest.write_bytes(data)
        total += len(data)
    print(f"{n:12s} {f} {dest.stat().st_size / 1e6:.1f} MB")
print("downloaded", round(total / 1e6, 1), "MB; base", base)
