# Browser and device matrix

Evidence for NFR-PORT-001: every release is tested on the primary targets (Chromebooks, Chrome, Safari on macOS, iOS and iPadOS); Edge and Firefox are smoke-tested. Update this table whenever a run is made. A blank means not run.

Last updated 2026-11-08.

## Matrix

| Target | Priority | Last run | What was run | Result |
|---|---|---|---|---|
| Chromium, headless, on Windows 11 (Playwright picks Edge, then Chrome, then bundled Chromium; `tests/e2e/conftest.py`) | Primary (engine) | 2026-11-08 | `pytest -m e2e`: site build, install, offline reload, fonts at three viewport sizes, exam-style flows typed into the site, status-bar clicks, Cancel | 20 passed. The offline font test failed at 390 x 844 and 844 x 390 (a Noto Sans file was not vendored); fixed the same day and re-run for that test only (3 passed). The full suite has not been re-run since the fix. |
| Chrome (desktop, headed) | Primary | not run | | |
| Chromebook (ChromeOS) | Primary | not run | | Needs a device. Check install as a PWA, offline, touch, the hardware keyboard and Handheld at a Chromebook's window size. |
| Safari on macOS | Primary | not run | | Needs a Mac. Service worker, canvas and `BroadcastChannel` behave differently. |
| Safari on iPhone | Primary | not run | | Needs a device. Check Add to Home Screen, offline after install, Handheld fit with the address bar, the on-screen keypad and file save. |
| Safari on iPad | Primary | not run | | Needs a device. Tablet mode is not built; Handheld or Computer applies. |
| Edge (desktop, headed) | Secondary | not run | | Headless Chromium above may be Edge; a headed smoke run has not been done. |
| Firefox | Secondary | not run | | |
| Android Chrome (phone) | Not a stated target | not run | | The install-on-a-phone item in PLAN.md M2 is Simon's. |

## Not covered by any run

- A real GitHub Pages deploy and offline behaviour there (PLAN.md M2 exit item 1). Only a local server under `/CASSim/` has been used (decision 0016).
- Non-US keyboard layouts: typed characters come from a US/AU table (decision 0024).
- Screen readers (`docs/accessibility.md`).
- Engine start time: decision 0016 measured about 68 s to a ready engine on a first load and 61 s on an offline reload in headless Edge (one engine plus its spare). The current site has not been re-timed. NFR-PERF-001 asks for it to be measured and reported.

## How to run

- Automated: `uv run pytest -m e2e` (builds the site, takes several minutes).
- By hand: `uv run python -m tools.publish`, then serve `build/web` so that it appears under `/CASSim/`, open it in the target, and walk through the checklist below.

## Manual checklist for a device run

1. Open the site. The loading screen shows progress, then the calculator.
2. Type `solve(x^2-2=0,x)`, press Enter, and check the answer. Then `1/3` with Ctrl+Enter (or the keypad's ctrl and enter) for a decimal.
3. Define `a:=5`, then enter `seq(k,k,1,99999999)` (far too big to finish) and press Esc after a few seconds. The app must stay usable and `a` must still be 5.
4. Install the app, close it, turn the network off, and reopen it.
5. Doc, File, Save to file; reload; Open file. Copy a share link and open it in a new tab.
6. Rotate the device (phones and tablets) and resize the window (computers).
7. Record the date, device, OS and browser versions, and any problem in the table above.
