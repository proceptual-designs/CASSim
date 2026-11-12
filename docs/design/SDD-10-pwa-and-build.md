# SDD-10. Build, offline site and deploy

Status: describes `tools/publish.py` and the CI workflow at 2026-11-08. Requirements: FR-PWA-001 to FR-PWA-004, NFR-PERF-001 to NFR-PERF-005, NFR-REL-001, NFR-PORT-001, NFR-LEG-003, NFR-MAINT-005. Decisions: 0002, 0016, 0018, 0027. The static site is the only supported build; native builds are a future Would (PLAN.md section 13).

## Goal

A folder of static files that any free host can serve at the root (the default, as on Cloudflare Pages) or under a sub-path (`--base-url CASSim`), that installs as a PWA, and that works with the network off after the first visit, with no request to any other host (no CDN, no Google fonts, no PyPI).

## Pipeline

`python -m tools.publish [--dist DIR] [--base-url CASSim] [--cdn]` (default output `build/web`) runs `build()`:

| Step | What it does | Why |
|---|---|---|
| `stage` | Copies the `cassim` package (without `assets`) and a generated `main.py` into a temp folder (`%TEMP%/cassim_web_app`), with `src/assets` holding the symbols font and a generated `pyproject.toml` that names only `flet`. | `flet publish` reads a self-contained app folder. The staged `main.py` imports `cassim.app.main.main` and starts it; it never imports SymPy (0027). |
| `flet publish src/main.py --distpath DIST [--base-url B] [--no-cdn]` | Flet's static web build: Flutter app, CanvasKit, Pyodide core, Python worker. | The base build (decision 0002). |
| `patch_index` | Adds the manifest and meta tags, the loading screen, the update bar and the install and fullscreen bridge to `index.html`. | FR-PWA-001, FR-PWA-003. |
| `vendor_pyodide` | Copies the packages Pyodide still loads at run time (`RUNTIME_PACKAGES`: msgpack, pyyaml) into `pyodide/`. | `flet publish --no-cdn` self-hosts Pyodide core but not its packages (0002). |
| `write_app_archive` | Replaces Flet's `app.tar.gz` with one holding `main.py`, `cassim` and, under `__pypackages__`, Flet, repath and six, compiled to bytecode. | No micropip and no compiling at start-up (0027). |
| `vendor_fallback_fonts` | Copies `tools/fallback_fonts/` into `assets/fonts/`. | Flutter fetches Noto fallback fonts for glyphs Roboto lacks; they are committed so the build needs no Google request. |
| `write_engine_zip` | Zips `cassim` without the UI, plus SymPy and mpmath, compiled to bytecode, as `cassim.zip`. | The engine worker boots its own Pyodide and unpacks it, with no `loadPackage` (SDD-02, 0027). |
| `write_icons`, `write_manifest` | Draws the icons (Pillow, CASSim's own artwork) and writes `manifest.webmanifest`. | FR-PWA-001. |
| `add_offline_cache` | Writes `version.json`, `precache.json` (every file) and replaces Flutter's self-unregistering `flutter_service_worker.js`. | FR-PWA-002. |

Wheels are downloaded once into `%TEMP%/cassim_wheels`. Bytecode is written only when the build's Python has Pyodide's minor version (otherwise source ships and the browser compiles it). The build prints the file count and size; `python -m tools.loadtime [--build]` times start-up (0027). With `--cdn` the vendoring steps are skipped (Pyodide and CanvasKit then come from CDNs).

## Service worker

The version string is `<pyproject version>+<content hash>`, so any change to any file changes the cache name.

- **install:** fetch `precache.json` with no cache and `cache.addAll` the whole list (about 100 files, about 83 MB).
- **activate:** delete every other cache and claim clients.
- **fetch:** same-origin GETs only. Navigations are network-first (so a new version is noticed even though hosts cache for minutes) and fall back to the cached `index.html` offline. Everything else is cache-first, filling the cache on a miss.
- **update:** the page registers the worker, and when a new one is `installed` while another controls the page, the update bar appears. Reload posts `skipWaiting` and the page reloads on `controllerchange`.

Because the Python app runs in a Web Worker with no DOM, install and fullscreen requests go over a `BroadcastChannel("cassim")` to the page (`app/web.py` `Bridge`, `BODY_TAGS`).

## Offline rule and its test

`tests/e2e/test_pwa.py` builds the real site with `tools.publish`, serves it from a sub-path with Playwright, and checks: the page installs, a reload with the network off works, and no view at 1280 x 720, 390 x 844 or 844 x 390 requests a file that 404s (the font test). If it names a new font, download it from `https://fonts.gstatic.com/s/<path>` into `tools/fallback_fonts/` with the same path.

## Hosting requirements

One build of the whole app exists today. Single-device bundles (`--bundle`, one archive per device, per-device precaching) are planned in PLAN.md section 15 and FR-PROF-008; this document is updated when they are built.

- Any static host that serves `.mjs` as `text/javascript` and `.wasm` correctly. No special headers are needed (COOP and COEP are deliberately not used, SDD-02).
- Built with the default `--base-url ''` the site is served at the root; with `--base-url CASSim` it must be served under `/CASSim/`.
- Cloudflare Pages (PLAN.md section 14): the headless smoke test loaded, evaluated, precached 95 files and reloaded offline (2026-11-13).

## CI

`.github/workflows/ci.yml` runs on pushes to `main` and pull requests: `uv sync --locked --group web`, `ruff format --check`, `ruff check`, `ty check`, `pytest -m "not e2e" --cov=cassim`, and the traceability check. The e2e tests (which build the site) are run locally. `.github/workflows/deploy.yml` deploys to Cloudflare Pages: `main` to the testing site and the help pages, a GitHub release to the stable site (PLAN.md section 14).

## Measured (decisions 0002, 0016 and 0027)

| | Result |
|---|---|
| Cold start, CDN build | about 35 s |
| Cold start, vendored | about 15 s |
| Download | CDN 22 MB dist plus about 33 MB fetched; vendored 73 MB plus 21.7 MB packages (spike) |
| Current site | 94 precached files, 90 MB (2026-11-12) |
| Start-up, current site (0027, desktop Chromium) | first screen 4.9 s cold, 2.6 s warm; engine ready 6.7 s cold, 4.3 s warm |

No fixed budgets exist (SRS); NFR-PERF-001 and NFR-PERF-005 ask only that they are measured and reported.

## Known gaps and risks

- Safari, iOS and Chromebook have not run the site; service-worker and canvas behaviour differ there.
- The build downloads Pyodide packages and two PyPI wheels at build time; a download failure fails the build. They are cached in `%TEMP%`, not in the repo.
- `RUNTIME_PACKAGES` and `ENGINE_PACKAGES` must match what Flet and the engine import; a missing one fails only at run time in the browser (the e2e tests catch it).
- Pyodide upgrade procedure (NFR-MAINT-005) is not written down: bump the version, rebuild, run the e2e suite.
- If the app ships a Dart extension, switch from `flet publish` to `flet build web` and keep the post-processing (0018).
- The disclaimer, privacy text and third-party notices are in the app's About dialog; the notices have not been checked against the shipped files (NFR-LEG-003).
