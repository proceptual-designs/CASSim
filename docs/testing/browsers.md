# Browser and device matrix

Evidence for NFR-PORT-001: every release is tested on the primary targets (Chromebooks, Chrome, Safari on macOS, iOS and iPadOS); Edge and Firefox are smoke-tested. Update this table whenever a run is made. A blank means not run.

Last updated 2026-11-16.

## Matrix

| Target | Priority | Last run | What was run | Result |
|---|---|---|---|---|
| Chrome 157, headless, Windows | Primary (engine) | 2026-11-16 | Deployed stable and testing sites; Cloudflare-style redirect; legacy-to-fixed local upgrade | Both deployed sites had complete caches but failed offline navigation with `ERR_FAILED`. The local legacy build upgraded to the fixed worker, preserved local storage and calculated offline. Browser contexts, not OS-installed windows. |
| Chrome 157, Android 17, Pixel 6 | Primary | 2026-11-16 | Wireless DevTools inspection of the testing site and a fixed local build in a browser tab and a separately installed test app | The testing site's cached index carried a redirect. The fixed build cached the redirected index and calculated `2+3 = 5` offline in the tab. The separately installed test WebAPK was closed and relaunched via its Android launcher activity with its local server and tunnel stopped; it loaded from its 93-entry cache. A subsequent reload with DevTools network emulation offline also loaded in app mode and calculated `2+3 = 5`. The phone's Wi-Fi remained on for debugging. Neither the existing installation nor the stable deployment was updated. |
| Chromium-family, headless, Windows | Primary (engine) | 2026-11-16 | Built site: failed updates (HTTP 503 and a 200 block page), offline CAS calculations, and applying an update | 2 passed. Browser-context simulation; not an OS-installed app or school-network test. |
| Chromium, headless, on Windows 11 (Playwright picks Edge, then Chrome, then bundled Chromium; `tests/e2e/conftest.py`) | Primary (engine) | 2026-11-08 | `pytest -m e2e`: site build, install, offline reload, fonts at three viewport sizes, exam-style flows typed into the site, status-bar clicks, Cancel | 20 passed. The offline font test failed at 390 x 844 and 844 x 390 (a Noto Sans file was not vendored); fixed the same day and re-run for that test only (3 passed). The full suite has not been re-run since the fix. |
| Chrome (desktop, headed) | Primary | not run | | |
| Chromebook (ChromeOS) | Primary | not run | | Needs a device. Check install as a PWA, offline, touch, the hardware keyboard and Handheld at a Chromebook's window size. |
| Safari on macOS | Primary | not run | | Needs a Mac. Service worker, canvas and `BroadcastChannel` behave differently. |
| Safari on iPhone | Primary | not run | | Needs a device. Check Add to Home Screen, offline after install, Handheld fit with the address bar, the on-screen keypad and file save. |
| Safari on iPad | Primary | not run | | Needs a device. Tablet mode is not built; Handheld or Computer applies. |
| Edge (desktop, headed) | Secondary | not run | | Headless Chromium above may be Edge; a headed smoke run has not been done. |
| Firefox | Secondary | not run | | |
| Simon's phone (model, OS and browser not recorded) | Unknown | 2026-11-12 | The GitHub Pages site, installed as an app; save and load (by hand, Simon) | Works. Slow (PLAN.md section 12, A6). Offline use and the rest of the checklist below were not recorded. |
| Desktop browser, GitHub Pages site (browser not recorded) | | by 2026-11-12 | <https://simonjtyler.github.io/CASSim/> opened (by hand, Simon) | Loads. |

## Not covered by any run

- Offline behaviour of the Cloudflare Pages site on a real device. A headless Chromium run loaded <https://cassim-calc.pages.dev/>, evaluated, and reloaded and evaluated offline (2026-11-13).
- Safari, iOS, iPadOS and Chromebook: no devices are available (2026-11-12).
- Non-US keyboard layouts: typed characters come from a US/AU table (decision 0024).
- Screen readers (`docs/accessibility.md`).
- Engine start time: decision 0016 measured about 68 s to a ready engine on a first load and 61 s on an offline reload in headless Edge (one engine plus its spare). The current site has not been re-timed. NFR-PERF-001 asks for it to be measured and reported.

## How to run

- Automated: `uv run pytest -m e2e` (builds the site, takes several minutes).
- CI runs its selected browser tests alongside the Python checks; the required `check` job passes
  only if both jobs succeed.
- By hand: `uv run python -m tools.publish`, then serve `build/web` at the root of a local server (or build with `--base-url CASSim` and serve it under `/CASSim/`), open it in the target, and walk through the checklist below.

## Manual checklist for a device run

1. Open the site. The loading screen shows progress, then the calculator.
2. Type `solve(x^2-2=0,x)`, press Enter, and check the answer. Then `1/3` with Ctrl+Enter (or the keypad's ctrl and enter) for a decimal.
3. Define `a:=5`, then enter `seq(k,k,1,99999999)` (far too big to finish) and press Esc after a few seconds. The app must stay usable and `a` must still be 5.
4. Install the app after the offline cache finishes downloading, close it, turn the network off,
   reopen it and evaluate a calculation.
5. Doc, File, Save (give a name); reload (the name is still shown); Open Document. Export File…, then Import File…. Copy a share link and open it in a new tab.
6. Rotate the device (phones and tablets) and resize the window (computers).
7. Record the date, device, OS and browser versions, and any problem in the table above.
