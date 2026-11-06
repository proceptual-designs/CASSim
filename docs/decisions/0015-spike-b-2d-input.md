# 0015. Spike B: two-dimensional (template) input

Date: 2026-11-06. Status: **ACCEPTED (owner, 2026-11-06): Option 2, our own template editor. Options 3 and 4 were researched but not built.** The model is now `src/cassim/device/editor.py` (tests in `tests/device/test_editor.py`).
Code: `spikes/spike6_web/src/editor.py` (model), `spikes/spike6_check.py` (desktop check against the engine), `spikes/run_web_spike6.py` (browser run), screenshots in `spikes/spike6_web/shots/`.
Owner direction: the editor must feel like the handheld (decision 0013 item 2 and the "familiar for demos and practice" aim), so a live preview beside a linear editor is out.

## Options

| | 2. Own template editor | 3. MathLive | 4. `math_keyboard` |
|---|---|---|---|
| What | Tree model (rows, fraction/power/root templates, cursor path) in Python; drawn as LaTeX with the cursor as a glyph. | Web component for 2D editing, outputs LaTeX. | Flutter field plus on-screen keyboard (simpleclub, BSD-3). |
| Needs Flutter/Dart | **No** | Yes (a Dart extension that hosts a DOM element) | Yes (a Dart extension) |
| Matches TI behaviour | Fully ours: `/` takes the preceding term, `^` and `√` open a slot, arrows move between slots, Backspace dissolves a template. | Close by default (fraction and exponent shortcuts); the rest is configuration. | Limited: its own key set, "customization options are currently limited" per its README. |
| Evidence | Built and run in Edge (below). | Docs only. | Pub.dev and README only. |
| Main risks | No mouse click-to-place cursor or drag selection (needs hit-testing); we write the editing rules ourselves. | Focus and key capture across the DOM/canvas boundary; iframe swallows pointer events (Flutter docs), so it must be a plain element, not an iframe; extra JS and fonts offline; converting its LaTeX to TI text. | Fraction/matrix/subscript support unclear; its own docs warn of odd physical-keyboard behaviour on mobile; the tree is not exposed, only TeX. |

## Findings for Option 2
1. **The cursor problem has a workaround.** `flutter_math` cannot draw a cursor, so the editor draws it as a glyph inside the LaTeX (`{\color{#4da3ff}\rule{0.06em}{1em}}`), the way `math_keyboard` does. Empty slots show `\square`. It renders in Flet's Markdown with no extra work (screenshots).
2. **The model feeds the existing engine unchanged.** `Editor.linear()` writes the TI text the parser already reads (`(1)/(3)+(1)/(4)`). `spike6_check.py` enters key sequences and evaluates them with the real `Session`: `1/3 → 1/4` gives `7/12`, `√2 → √8` gives `4`, `(1+2)/3` gives `1`.
3. **Speed.** About 2 to 3 ms per keystroke in Python, including the redraw call; occasional 12 to 14 ms.
4. **Flet's keyboard events are the weak point.** `page.on_keyboard_event` works in the web build, but `e.key` is the key, not the typed character: `Shift+6` arrives as `key='6', shift=True`, not `^`. A table for the US/AU layout would work for Chromebooks (the primary target), and the on-screen keypad sends characters directly, but other layouts and non-Latin input would not. A hidden text field or a Dart-side key handler would fix it.
5. **Not done in the prototype:** `^` (blocked by finding 4 under Playwright), `√` by key, matrices and lists as templates, selection, copy and paste, a blinking cursor (toggle the glyph on a timer), dropping the redundant brackets TI omits (`(1+2)/3` shows its numerator brackets), click-to-place, and Ctrl+Enter capture.

## Findings for Options 3 and 4 (research only)
- A Flet extension is a Python package that bundles Flutter code (`flet create --template extension`). The Dart side wraps a widget as a control, and Dart can send events to Python (`triggerEvent`). `flet build` applies extension settings.
- The docs do **not** say whether `flet build web` and `flet publish` handle extensions, so whether a custom control reaches the static web build is unconfirmed. `flet run` uses a prebuilt client that only has built-in controls.
- `flet-webview` lists Web as supported (wrapping `webview_flutter`), but its docs warn some events are not on web. A WebView is an iframe, so MathLive inside it would lose Flutter's pointer and focus coordination.
- MathLive loads as an ES module or UMD script, with fonts to copy and relocate (`MathfieldElement.fontsDirectory`), so it can be vendored for offline use. Its API supports setting `.value`, listening to input and reading LaTeX; custom keybindings and inline shortcuts exist but were not read.
- No Flutter SDK is installed here. `flet build` downloads its own, and the owner has offered to install one.

## Decision
Build **Option 2** for M2: it is pure Python and testable in `core`-style unit tests, it mirrors the handheld's template behaviour, and it already works end to end in the web build. Use Flutter only for a bounded check (below), not for the editor.

## Next
- Port the model into the product (`src/cassim/…`, not core, since it is UI state), with unit tests against the TI template behaviour; the handheld's behaviours should be captured on the simulator first (what `/`, `^`, `√`, Backspace and the arrows do, matrix entry, how brackets show).
- Flutter check, if the owner installs it: does `flet build web` with a trivial extension publish to a static folder that works offline from a Pages-style path, with the Pyodide setup from 0002? That decides whether any later Dart code (a typed-character key handler, MathLive, click-to-place) is possible at all.

## Handheld behaviours to confirm on the simulator
The editor's rules are from memory of the handheld. Check each in the Teacher Software and make the confirmed ones corpus or device cases:
1. `/` after `1`, `12.5`, `x`, `(a+b)`, `2^3` and `√2`: what becomes the numerator? (Built: the run of letters, digits and `.`, a bracketed group, a power, a root or a finished fraction.)
2. Does `(a+b)/2` keep the brackets in the numerator, or drop them? (Built: keeps them.)
3. Backspace in front of a fraction: does it enter it or delete it, and what does Backspace at the start of a slot do? (Built: enter; dissolve and keep the contents.)
4. Up and Down between numerator and denominator, and what Up/Down do on a normal line (history scroll?).
5. How `^` behaves after a bracket or function (`sin(x)^2`) and whether Right is needed to leave the exponent.
6. `√` key: the radicand slot, and the nth-root template.
7. Matrix and list entry: the template, Tab or arrow movement between cells.
8. Multiplication display (`·` or nothing) and how implicit products are shown.
