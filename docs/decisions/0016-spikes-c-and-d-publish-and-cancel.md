# 0016. Spikes C and D: publishing under a project path, offline use, and cancel with restore

Date: 2026-11-06. Status: **GO for both, with the build steps and limits below.** Real GitHub Pages was not used (see "Not tested").
Code: `spikes/spike7_web/` (the shell: Flet app plus the real `cassim.core` in an engine worker), `spikes/run_web_spike7.py` (D), `spikes/run_web_spike8.py` (C), `spikes/make_cassim_zip.py`. Flet 1.0.5, Pyodide 314.0.7, headless Edge, Windows.

## Spike D: cancel and restore with the real engine

The engine worker (a Blob-spawned module worker, as in 0005) now loads SymPy and a zip of `src/cassim` (83 kB, served as a Flet asset) and runs a `Session`. The document model is the list of entries; a new engine rebuilds its Session by replaying them. A spare engine is kept booted.

| Measure | Result |
|---|---|
| Engine boot (Pyodide, SymPy, `cassim.core`), CDN build, headless | about 22 s each |
| Wasm memory per engine | 54 MB (109 MB with the spare) |
| `terminate()` on a busy engine | 0.7 to 1.8 ms |
| Cancel to a ready engine with the state rebuilt, spare already booted | 16 to 19 ms |
| Cancel again straight after the first (the replacement spare still booting) | **about 22 s** |
| State after cancel (`a:=5`, `f(x):=x^2+a`, then `f(3)`) | correct (14); the cancelled entry is not in the document |
| Replay of the document into a fresh Session | 10 entries 1.1 s (includes first-call SymPy warm-up), 50 entries 0.5 s, 200 entries 2.2 s, 500 entries 5.4 s (about 10 ms an entry for a mix of assignments, `solve` and `expand`) |
| Main thread after boot, through both cancels and all replays | 60 fps, longest frame gap 18 ms |

1. **Cancel meets the 1 s requirement** (NFR: cancel within 1 s): the busy engine is gone in under 2 ms and Flet's own loop never stalls. The main thread's only long stall (about 2.4 s) is the initial load.
2. **The second cancel is the weak spot.** A swap is instant only while a spare is booted, and booting takes about 22 s. Pressing Cancel twice within that window leaves the calculator unavailable until the new spare is ready. Mitigations to design in M2: show a "restarting" state rather than a frozen one; boot the spare from the cache with vendored packages (about 15 s in 0002); and consider making cancel cheaper by only replaying entries that changed state.
3. **Checkpointing** (0013 item 8): replay is linear at about 10 ms an entry and only happens after a cancel, so a checkpoint is not needed for ordinary documents (a problem of under 100 entries replays in about 1 s). Revisit if the replay time of a long document matters. The replay must skip nothing that sets state, including random seeds (`RandSeed` entries), so the document model should store the entries, not the results.
4. **The memory cost of a spare** is 54 MB of wasm. That is probably acceptable on a Chromebook; phones are not measured.
5. **Engine bug found on the way and fixed**: a result with about a thousand or more terms (for example `expand((x+y+z)^60)`) raised `RecursionError` out of `Session.eval`, because the printer recurses down a long left-leaning sum. It now comes back as the TI `Memory` error and the session carries on (`tests/unit/test_latex.py`).
6. Also seen, not fixed: `solve(x^7-3x^2+1=0,x)` returns `CRootOf(...)`, where TI shows numeric roots.

## Spike C: publishing under `/<repo>/` and using it offline

A static server that serves only below `/CASSim/` (as a Pages project site does), with `.mjs` and `.wasm` types set, stood in for Pages.

Build steps that work (all go in a `tools/` publish script for M2e):
1. `flet publish src/main.py --no-cdn --base-url CASSim`. Assets in `src/assets/` are copied into the **dist root** (not `dist/assets/`).
2. Patch `index.html`: `flet.pyodideUrl="pyodide/pyodide.mjs"` becomes `"./pyodide/pyodide.mjs"` (0002 finding 1).
3. Vendor Pyodide packages from `pyodide-lock.json` into `dist/pyodide/`: SymPy and its dependencies, plus `micropip`, `msgpack` and `six`, which Flet's worker needs. (0002 vendored only SymPy and SciPy and missed these two, which made the first load fail with two 404s.)
4. Vendor the two pure-Python PyPI wheels that Flet installs at start-up, `flet` and `repath`, into `dist/pyodide/` and **add them to `pyodide-lock.json`** (name, version, file, sha256, dependencies). micropip checks the lock first, so no request goes to PyPI. This closes the open item in 0002.
5. Replace `flutter_service_worker.js` with a precaching service worker (the next point).

Findings:
- **Flutter's own service worker no longer caches anything**: the one in the build only unregisters itself. The static build therefore has **no offline support unless CASSim ships its own service worker.** The spike's worker precaches a generated list of every file at install and then answers same-origin GETs cache-first. Registered at the site root (`/CASSim/`), it controlled the page, and the engine worker (a Blob worker) fetched the Pyodide files, the wheels and `cassim.zip` through it.
- **Offline reload works**: with the network switched off, a reload booted the app and the engine and returned correct results. The only failing request was an unused Rive wasm file from jsdelivr (harmless).
- **After the first load only one external request remains**: `cdn.jsdelivr.net/npm/@rive-app/flutter-native-wasm` (unused; it fails offline without effect).
- **Size**: the dist is about 82 MB with SymPy vendored (SciPy would add about 14 MB). The largest single file is 9.6 MB, far under GitHub Pages' 100 MB limit, and the total is far under its 1 GB limit. Unused CanvasKit variants could be trimmed.
- **Timing** (headless Edge, one engine plus its spare): engine ready after about 68 s on a first load and 61 s on an offline reload. This is two engine boots in sequence, so about half of it is the spare; the first calculator is usable about halfway.

## Not tested
- **Real GitHub Pages.** Pages for a private repository needs a paid GitHub plan, and publishing is outward-facing, so this was left for the owner. The simulation covers the sub-path, MIME types and the lack of headers; it does not cover Pages' own caching (`Cache-Control: max-age=600`), which is why the service worker should version its cache and fetch `index.html` network-first.
- **Update flow**: the spike's worker is cache-first forever. The product needs a versioned cache, a "new version available" prompt and a cleanup of old caches.
- Safari, iOS and a Chromebook (the primary targets): not run.
- The install prompt and the web manifest of the PWA, and the full precache size on a phone's data plan.
- Lazily imported SciPy offline.
