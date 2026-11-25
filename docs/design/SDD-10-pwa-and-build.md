# SDD-10. Build, offline site and deploy

Status: describes `tools/publish.py` and the CI workflow at 2026-11-16; the bundles and the CI and deploy triggers were brought up to date on 2026-11-25. Requirements: FR-PWA-001 to FR-PWA-004, NFR-PERF-001 to NFR-PERF-005, NFR-REL-001, NFR-PORT-001, NFR-LEG-003, NFR-MAINT-005. Decisions: 0002, 0016, 0018, 0027. The static site is the only supported build; native builds are a future Would (PLAN.md section 13).

## Goal

A folder of static files that any free host can serve at the root (the default, as on Cloudflare Pages) or under a sub-path (`--base-url CASSim`), that installs as a PWA, and that works with the network off after installation completes. Essential resources are vendored.

## Pipeline

`python -m tools.publish [--bundle all|tin|pseudo|sci] [--dist DIR] [--base-url CASSim] [--cdn]` (default output `build/web`) runs `build()`. A bundle is the shell and a list of devices (decision 0032 item 8): `all` holds every built device and Home, and each single-device bundle holds one device for its own site.

| Step | What it does | Why |
|---|---|---|
| `stage` | Copies the `cassim` package (without `assets`) and a generated `main.py` into a temp folder (`%TEMP%/cassim_web_app`), with `src/assets` holding the symbols font and a generated `pyproject.toml` that names only `flet`. | `flet publish` reads a self-contained app folder. The staged `main.py` imports `cassim.app.main.main` and starts it; it never imports SymPy (0027). |
| `flet publish src/main.py --distpath DIST [--base-url B] [--no-cdn]` | Flet's static web build: Flutter app, CanvasKit, Pyodide core, Python worker. | The base build (decision 0002). |
| `patch_index` | Adds the manifest and meta tags, loading screen and browser status, install and fullscreen bridge to `index.html`. | FR-PWA-001, FR-PWA-003. |
| `disable_unused_rive` | Disables the unused Rive initializer in Flet 1.0.5's JavaScript CanvasKit build, and fails the build if its expected version or generated code changes. | FR-PWA-002: no Rive CDN request. |
| `vendor_pyodide` | Copies the packages Pyodide still loads at run time (`RUNTIME_PACKAGES`: msgpack, pyyaml) into `pyodide/`. | `flet publish --no-cdn` self-hosts Pyodide core but not its packages (0002). |
| `write_app_archive` | Replaces Flet's `app.tar.gz` with one holding `main.py`, `cassim` and, under `__pypackages__`, Flet, repath and six, compiled to bytecode. | No micropip and no compiling at start-up (0027). |
| `vendor_fallback_fonts` | Copies `tools/fallback_fonts/` into `assets/fonts/`. | Flutter fetches Noto fallback fonts for glyphs Roboto lacks; they are committed so the build needs no Google request. |
| `write_engine_zip` | Zips `cassim` without the UI, plus SymPy and mpmath, compiled to bytecode, as `cassim.zip`. | The engine worker boots its own Pyodide and unpacks it, with no `loadPackage` (SDD-02, 0027). |
| `write_icons`, `write_manifest` | Draws the icons (Pillow, CASSim's own artwork, text set in a Noto Sans Bold subset kept in `tools/icon_font/` with its OFL licence) and writes `manifest.webmanifest`. | FR-PWA-001. |
| `add_offline_cache` | Writes `version.json`, `precache.json` and a service worker with the SHA-256 of each offline asset. | FR-PWA-002. |

Wheels are downloaded once into `%TEMP%/cassim_wheels`. Bytecode is written only when the build's Python has Pyodide's minor version (otherwise source ships and the browser compiles it). The build prints the file count and size; `python -m tools.loadtime [--build]` times start-up (0027). With `--cdn` the vendoring steps are skipped (Pyodide and CanvasKit then come from CDNs), and offline readiness is not offered.

## Service worker

The version string is `<pyproject version>+<content hash>`, covering site content and the service-worker template.

- **install:** fetch each asset without the HTTP cache and check it against the build's embedded SHA-256 manifest. An incomplete or mismatched installation is discarded.
- **activate:** after successful installation, delete older CASSim caches for the same service-worker scope and claim clients; failed updates leave the active cache intact. Legacy unscoped caches are left untouched because their scope cannot be identified safely.
- **fetch:** same-origin GETs only. Navigations use the cached `index.html` first, so an unavailable host or network filter cannot prevent the app from opening. If the host redirects `index.html` to the directory URL, the worker returns a new response without the redirect history: browsers otherwise reject that cached response for navigation. Other resources are cache-first, filling the cache on a miss.
- **update:** the page registers the worker and reports a waiting update through the bridge. The CASSim button shows a red dot and the menu offers Reload; it posts `skipWaiting` and the page reloads on `controllerchange`. Unsaved changes require confirmation.
- **readiness:** the page asks its controlling worker whether all verified assets remain present and reports the status to the CASSim menu. Retry fetches and verifies missing assets. The browser is asked for persistent storage where supported; it may decline, and users can still clear data.

Because the Python app runs in a Web Worker with no DOM, install and fullscreen requests go over a `BroadcastChannel("cassim")` to the page (`app/web.py` `Bridge`, `BODY_TAGS`). The page also reports the CSS safe-area insets, including after a resize. In the installed app on a phone-sized window, the CASSim menu toggles whether the layout uses the cutout area; the choice starts on and lasts for the session.

## Offline rule and its test

`tests/e2e/test_pwa.py` builds the real site with `tools.publish` and serves it from both the root
and a sub-path.
One Playwright test waits for every precache entry and service-worker control, closes the page,
then verifies CAS calculations after the host returns HTTP 503, returns a block page with HTTP 200,
and after the network is switched off. It explicitly forces a service-worker update check against
each failing host response. A second test verifies that updates are still offered and applied.
Additional tests cover corrupted and interrupted installs and updates, and repair of a missing
cache entry. A redirected-index test covers online and offline launches and cache repair at both
the root and a sub-path, including Cloudflare Pages' directory redirect. Chromium-family,
Firefox and Playwright WebKit also calculated with the host down
and HTTP caching disabled; Playwright WebKit additionally passed browser-offline navigation.
Playwright Firefox's browser-offline navigation failed with `NS_ERROR_OFFLINE` on both the
unchanged baseline and this build, so that scenario remains unverified. These tests exercise
browser contexts, not OS-installed windows; real Safari and Chromebook remain untested.
An offline Edge run recovered a saved document and settings, switched views and calculated.
Two instrumented offline cancellations terminated the worker within one second and restored
variables, but earlier experiments also observed cancellations exceeding one second; those
samples do not establish compliance with NFR-PERF-004.
The font test checks views at 1280 x 720, 390 x 844 and 844 x 390 for 404s. If it names a new
font, download it from `https://fonts.gstatic.com/s/<path>` into `tools/fallback_fonts/` with the
same path.

On reopening, navigations use the cached page without waiting for the site. The browser checks the
site's service-worker script for updates; the
`version.json` request is served from the cache when available. Other cached app resources are
loaded from the service worker, with a network request on a cache miss. Flutter also attempts to
initialize an unused Rive plugin; the build disables this in the supported Flet JavaScript build.
The first visit and precache require access to the site. Wait for “Offline: Ready” in the CASSim menu before
disconnecting.

## Hosting requirements

The `all` bundle and the single-device bundles `tin`, `pseudo` and `sci` are built and deployed (`--bundle`, FR-PROF-008, PLAN.md section 15). Loading each device's files only on first use inside the `all` bundle (FR-PROF-005) is still to do.

- Any static host that serves `.mjs` as `text/javascript` and `.wasm` correctly. No special headers are needed (COOP and COEP are deliberately not used, SDD-02).
- Built with the default `--base-url ''` the site is served at the root; with `--base-url CASSim` it must be served under `/CASSim/`.
- Cloudflare Pages (PLAN.md section 14): the headless smoke test loaded, evaluated, precached 95 files and reloaded offline (2026-11-13).

## CI

The gate is `uv run python -m tools.local_ci`, run locally before a branch merges into `main` (AGENTS.md, "Development workflow"): Ruff, Ty, pytest with coverage, the coverage floors, the traceability check and the browser tests. `.github/workflows/ci.yml` runs the same groups once per batch pull request, when it is marked ready for review, and on manual dispatch; it does not run on drafts or on pushes to `main`, and it skips the browser job for a batch that cannot affect the browser. `.github/workflows/deploy.yml` deploys to Cloudflare Pages: a push to `main` that changes the app goes to the testing site (`cassim-calc`), one that changes `docs/wiki` to the help pages, and a GitHub release to the stable site (`cassim-app`) and the single-device sites (`cassim-tin`, `cassim-pseudo`, `cassim-sci`) (PLAN.md sections 14 and 15).

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
- One root-hosted Edge run populated the cache but did not acquire a controller within 150 seconds
  while other builds and browser tests were running. An isolated retry succeeded; the cause of the
  timeout is unconfirmed.
- The Flet 1.0.5 Rive workaround patches generated JavaScript and must be reviewed on a Flet
  upgrade; the build deliberately fails if its expected version or code changes.
- The build downloads Pyodide packages and two PyPI wheels at build time; a download failure fails the build. They are cached in `%TEMP%`, not in the repo.
- `RUNTIME_PACKAGES` and `ENGINE_PACKAGES` must match what Flet and the engine import; a missing one fails only at run time in the browser (the e2e tests catch it).
- Pyodide upgrade procedure (NFR-MAINT-005) is not written down: bump the version, rebuild, run the e2e suite.
- If the app ships a Dart extension, switch from `flet publish` to `flet build web` and keep the post-processing (0018).
- The disclaimer, privacy text and third-party notices are in the app's About dialog; the notices have not been checked against the shipped files (NFR-LEG-003).
