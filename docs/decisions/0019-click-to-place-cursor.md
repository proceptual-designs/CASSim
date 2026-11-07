# 0019. Click to place the cursor in the entry line

Date: 2026-11-07. Status: **DONE, with limits listed below.** Code: `Editor.place` in `src/cassim/device/editor.py`, `src/cassim/app/entry.py`, the `place` and `extend` actions in `device/calculator.py`. Tests: `tests/device/test_click_place.py` (headless), `tests/app/test_entry_click.py` (every click region of the built controls), `tools/app_click_shots.py` (Playwright, headless Edge; screenshots `docs/testing/app-shots/2d-click-*.png`).

## Problem

The entry line was one `ft.Markdown` block (flutter_math). A Flutter canvas gives Python no layout, so a click had no position in the tree to map to.

## Options

| Option | Verdict |
|---|---|
| (a) Draw the entry from Flet controls, one hit region per character, empty slot and template | **Chosen.** Pure Python, no layout guessing, testable by calling each tap handler. |
| (b) Keep LaTeX and overlay hit boxes from guessed glyph metrics | Rejected: fractions, roots and matrices change size with their contents, so the guesses drift. |
| (c) A Dart extension that reports positions | Still possible (0018) but needs a Flutter build and flutter_math internals; kept as a fallback only. |

## How it works

- `Editor.place(path, pos, extend=False)` puts the cursor in the row reached by `path` (clicks arrive as text, `format_target` / `parse_target`: `INDEX.SLOT/INDEX.SLOT:POS`). A path that has stopped being valid is cut where it stops and `pos` is clamped, so a late click never raises. A plain click drops the selection.
- Shift+click (`extend=True`) uses the existing `anchor`/`span` model. In the same row it moves the free end. If the two ends are in different rows (one inside a fraction slot, matrix cell or exponent), the selection takes the whole templates that hold them in their nearest common row, so a selection never starts inside a slot and ends outside it. This matches the rule already used for shift-arrows (a template is one unit).
- `app/entry.py` builds the line. Every character is a `Stack` of its text and two invisible tap zones (before it, after it); a template has the same two zones behind its contents, plus the same zones laid over its own drawn parts (fraction bar, radical sign and bar, matrix brackets). A slot's own row takes the click first, so a click in a numerator lands in the numerator while a click on the bar lands beside the fraction. A click in a row past its last character puts the cursor at the row's end; a matrix cell's padding and a short numerator's side space count as part of the slot.
- Flutter hit-tests a plain `Container` only if it has a colour, so the zones use an alpha 1/255 fill (`HIT`).
- Flet's tap event carries no modifier keys, and the page-level key event never reports a bare Shift. `main.py` wraps the layout in `ft.KeyboardListener` (autofocus) and keeps `App.shift` from its key down and key up events; `on_key` also refreshes it from the physical-key event. Playwright's `keyboard.down("Shift")` followed by a click was seen to extend the selection.
- The history stays LaTeX. A page without a calculator model still shows LaTeX.

## Visual differences from the LaTeX entry

The entry no longer uses KaTeX fonts: letters are italic Roboto (defined function names stay bold), the fraction bar and radical overline are drawn rules, the radical is the text glyph `√` at 1.15 times the size (it does not stretch for a tall radicand), exponents are set at 70 per cent, and matrix cells are aligned by column. The cursor is a 2 px bar of the accent colour, so it takes 2 px of width (the LaTeX rule took 0.06 em); the selection fill is the same `#7fb2e8`. The old and new entries are in `docs/testing/app-shots/` (`2d-select-fraction.png`, `2d-matrix.png` against `2d-click-*.png`).

## Limits and not done

- The "template just highlighted by Backspace" state (`Editor.selected`) was never drawn by the LaTeX renderer and still is not.
- A click on the thin border between a radical bar and its radicand lands in the radicand (before its first character), not beside the root.
- Touch devices: a tap is a click, but there is no way to shift-extend by touch yet (a long-press or a drag handle would be needed).
- Up to about 50 characters the controls are quick; a very long entry creates several controls per character. Not measured on a Chromebook.
- If the Shift key is released while the window has no focus, `App.shift` can stay set until the next key event.

## Follow-ups (2026-11-07)

- **Look:** the entry now uses the fonts the history uses: `packages/flutter_math_fork/KaTeX_Math` for letters and `KaTeX_Main` for everything else, with TeX-style space around binary operators. (Plain family names such as `KaTeX_Math` do not resolve; the package-qualified names do.)
- **Shift on focus loss:** `App.shift` is cleared when the page's lifecycle state leaves `resume`, because a key-up is lost when the window loses focus. Checked in headless Edge by dispatching a `blur` event with Shift held: the next click no longer extends the selection.
- **Checks:** a Hypothesis test (`tests/device/test_editor_fuzz.py`, 3,000 random sequences run by hand, 300 in CI) mixes typing, templates, arrows, selection, delete and clicks and asserts the cursor always sits on a real row. Browser runs covered numerator, denominator, exponent and matrix-cell clicks, shift+click across slots and cells, delete after a selection, and the handheld view.
