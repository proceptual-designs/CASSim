# 0004. Spike 3: Flet canvas drawing speed

Date: 2026-11-01. Status: **GO, using a single `Points` shape in POLYGON mode per curve.**

Setup: `spikes/spike3_web` (Flet 1.0.5 static build, Pyodide worker), driven by `spikes/run_web_spike3.py` in headless Edge. A 2000-point curve (`sin x + 0.3 sin 7x`) is rebuilt and pushed with `canvas.update()` for 40 pan steps and 40 zoom steps per variant. "update" is the Python-side cost of `update()` plus one event-loop yield, so it covers diffing, serialising and sending the patch. The browser side is sampled with `requestAnimationFrame`.

| Variant | Build (median) | Update (median / max) | Steps per second |
|---|---|---|---|
| One `Points`, `PointMode.POLYGON` | 2 ms | 5.4 to 5.8 ms / 13 ms | **119 to 135** |
| One `Path` (MoveTo + 1999 LineTo) | 11 to 13 ms | 33 to 37 ms / 80 ms | 17 to 20 |
| 1999 `Line` shapes | 33 ms | 1200 to 1470 ms | under 1 |

Browser frame rate stayed at about 59 fps during the `Points` and `Path` runs (max rAF gap 67 ms), so the Flutter main thread was not blocked.

## Decision
- Draw each curve (or each continuous branch of it) as one `canvas.Points(..., point_mode=cv.PointMode.POLYGON)`. At 5 ms per update there is room for several curves per frame and for trace and axes overlays.
- Never emit one shape per segment. Per-shape cost is about 0.7 ms, so a few hundred shapes is already too slow.
- `Path` is acceptable only for filled regions (integrals, shading) where a polygon fill is needed. Check it separately before relying on it.
- Discontinuities and asymptotes: break the curve into several `Points` shapes (one per branch). The engine's scene output should already be branch-split.
- `PointMode` is `flet.canvas.PointMode`, not `flet.PointMode`.

## Not measured (carry into M2/M3)
- Real pointer-driven pan and pinch zoom: the `GestureDetector` to Python round trip adds latency that this scripted test does not include. Pan updates will probably want throttling (drop events while an update is in flight).
- Whether the new frame is painted before the next update. Python-side timing proves the patch was sent, and rAF proves the main thread stayed responsive, but neither proves per-frame paint time. `Canvas.capture()` could check this.
- Phone-class hardware. These numbers are from a desktop Edge; expect a few times slower on a mid-range phone.
- Python evaluation of the function itself. Here it is plain `math.sin`; the real path will evaluate compiled SymPy lambdas (NumPy-vectorised), which should be faster than the 2 ms build above.
