# 0018. Spike E: a custom Flutter extension in `flet build web`

Date: 2026-11-06. Status: **GO.** Dart code can ship in the static web build; the open question in 0015 is answered.
Code: `spikes/spike9_ext/` (the `FletPing` extension from `flet create --template extension`, plus `app/`), `spikes/run_web_spike9.py` (reuses the helpers from `run_web_spike8.py`). Flet 1.0.5, Flutter 3.44.8, Pyodide 314.0.7, headless Edge, Windows.

## Results

| Question | Result |
|---|---|
| Does `flet build web` accept a project that depends on an extension? | **Yes.** The extension is a path dependency in `[tool.flet.dev_packages]` (and `[tool.uv.sources]`). Flet adds it to the generated Flutter `pubspec.yaml` and registers it; no Dart tooling is run by hand. |
| Is a Flutter install needed? | **Not by us.** `flet build` finds no SDK and offers to install one; `--yes` accepts. It installed Flutter 3.44.8 into `~/flutter`. First build about 4 min (SDK download plus compile); a rebuild with the SDK present took 139 s. |
| Does the Dart control render in the static build? | **Yes.** A purple Dart-drawn box with the text from Python (screenshot `dist/spike9_shots/online_tapped.png`, not committed). |
| Does a Dart event reach Python? | **Yes.** `control.triggerEvent("ping", ...)` on tap fired `on_ping` in Python (`ping 1` printed and a `Text` added). This is the path a typed-character key handler, click-to-place or a MathLive host would use. |
| Works under a Pages-style sub-path (`/CASSim/`, files served only below it)? | **Yes**, built with `--base-url CASSim --no-cdn`. No 404s. |
| Works offline? | **Yes**, with spike 8's steps (vendored Pyodide packages and flet wheels, precaching service worker): reload with the network off, control renders and the tap still reaches Python. No external hosts requested. 93 files precached; dist 67.7 MB (main.dart.js 7.7 MB). |

## Differences from 0002/0016 (`flet publish`)

- `flet build web --no-cdn --base-url CASSim` already writes `pyodideUrl: "/CASSim/pyodide/pyodide.mjs"`, so the `./pyodide/` patch from `flet publish` is not needed (the script's patch step is a no-op).
- Flutter's own service worker was not registered (`getRegistrations()` empty after first load); spike 8's precaching worker replaces it and I registered it by hand. Registering it from the app shell is part of the existing M2e build step.
- `flet build` crashes on a cp1252 Windows console (rich writing `●`). Run it with `PYTHONUTF8=1 PYTHONIOENCODING=utf-8`.
- `flet build web` needs the SDK, so CI needs Flutter (the CLI installs it) or a cached one; `flet publish` did not.

## Decision

- Dart code is possible. The 2D editor stays pure Python for M2 (0015); a Dart extension is now a **supported fallback**, for example for typed-character capture, click-to-place or a MathLive host, when Python alone cannot do it.
- If the app later ships an extension, switch the web publish step from `flet publish` to `flet build web` and keep the spike 8 post-processing (vendoring, precache worker).

## Not tested

- Real GitHub Pages, Chrome, Safari and Chromebooks (as in 0016); build time and Flutter cache in CI.
- A control that hosts a DOM element (MathLive): the key and focus problems in 0015 are untouched by this spike.
- Extension behaviour of `flet run` (it uses a prebuilt client and will not show the control).
