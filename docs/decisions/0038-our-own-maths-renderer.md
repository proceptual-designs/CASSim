# 0038: Our own maths renderer: layout in Python, painted on a canvas

Status: built 2026-11-26 at Simon's request, after two spikes; checked in headless Chromium on a desktop only. Replaces the control-drawn entry line of 0019 and the LaTeX cursor of 0036, and is option A of 0035 taken further. A custom Flutter widget (0035 option C) is still expected to replace the painting later.

## Why
Two renderers drew the same maths, and neither could do the whole job.
1. **LaTeX (flutter_math, the history).** One control a row and good typesetting, but the canvas gives Python no layout: a click cannot be turned into a place, and widths had to be estimated. A cursor or a selection has to be put into the LaTeX, where it takes part in the layout. 0036 made that nearly neutral, but brackets, radicals and fractions still changed size as the cursor passed, and the renderer has no `\smash` to stop it.
2. **Flet controls (the entry line, 0019).** Exact clicks, but about ten controls a character: a large result brought down with Enter made each arrow key very slow and Flet's `scroll_to` timed out. Its fractions, roots and spacing were its own, so a row changed shape between the history and the entry.

Simon chose one renderer of our own (2026-11-25) and asked for more than one way of building it to be tried first.

## The spikes
Both laid the maths out in Python from the KaTeX fonts' own metrics and differed in the drawing.
- **A: one canvas.** 44 shapes for a `cSolve` result that took 737 controls in the old entry line. Layout 1.0 to 1.6 ms on the desktop and 2.7 ms in Pyodide; first draw 6.7 ms in Pyodide; a cursor move 0.6 ms, since only the cursor's layer is sent.
- **B: positioned `Text` controls.** 55 controls for the same result; layout about 1 ms (desktop Python only; not timed in the browser); first draw 9 to 35 ms. It scaled glyphs for tall brackets and radicals, and found that a text style needs `letter_spacing=0` said outright.

A was closer to the LaTeX, covered more template kinds and was faster where it mattered, so the build follows A (Simon, 2026-11-26). The spike code stays on its branches and is not in the build.

## What is built
- **`device/math_layout.py`: the layout, with no Flet.** `layout(row)` gives a `Layout`: a flat list of glyph runs, rules and outlines, and for each row of the tree its place, its nodes' boxes and its gaps (the cursor's stops). The rules are TeX's as KaTeX applies them in text style: atom classes and the spaces between them (a `+` with nothing to work on is a sign), fraction shifts and clearances, script shifts, the radical's clearance, `\left \right` sizing, arrays, and big operators with limits at the side. Units are ems, so one layout serves any size. All nineteen template kinds are set (a test checks the list against `Kind`).
- **`device/math_metrics.json`: the fonts' numbers.** Advance, height, depth and ink edges of every glyph in the eleven KaTeX fonts Flet ships, and each font's line metrics. `tools/math_metrics.py` writes it from the installed fonts and a test compares the two, so a Flet upgrade that changes a font is caught.
- **`app/math_canvas.py`: the painter.** `MathLine` paints an editor: the selection on a canvas under the maths, the maths on its own canvas, the cursor on one above, and one gesture detector over all three. `draw(row)` paints a row with no cursor. Consecutive characters in one font are one text shape, so a plain line is a single shape however long.
- **The cursor and the selection are not in the maths.** They are arithmetic on the layout (`Layout.caret`, `selection`, `cell`) drawn on their own layers. The maths is set from the tree alone, so moving the cursor cannot change a glyph's size or place (tests check both the layout and the painted shapes). The cursor is as tall as a line of its row's text whatever is beside it.
- **Clicks are exact at any depth.** `Layout.hit` gives the innermost row under a point and its nearest gap. A slot's click area is wider than its text where that helps: the whole width above a fraction's bar is the numerator's, and a matrix cell has its padding. This gives back the exact click that 0036 gave up in a picked row.
- **One renderer everywhere there is a tree.** The Calculator's entry line, a picked history row, the history rows themselves, a Graphs function entry and a spreadsheet cell's edit bar are all drawn this way, so a row looks the same in the history, when picked and when brought down. `Line.row` carries a history row's tree. A row with no tree (a message such as `Done`, an error, a result SymPy draws) is still LaTeX.
- **Widths are measured, not estimated, where the drawing is ours.** One line or two for an entry and its result (0036) uses the layout's real width, and a long line follows its cursor from the cursor's real position. Estimates remain only for the LaTeX rows.
- **`app/entry_line.py` is gone**, with its tests; its click, long-press, selection, drag and every-kind tests are carried over to the canvas line.

## Choices made on the way
- **TeX's rules, not flutter_math's.** Side by side at large size the two agree on spacing, operators, matrices and plain brackets. flutter_math differs from TeX in small text: it always draws a root sign at full size, and sizes a large bracket to the small text it is in. Matching that pixel for pixel would mean copying quirks, so the layout follows TeX, and the history moved to the same renderer so there is nothing left to disagree with.
- **Real glyphs for radicals and brackets.** The root sign and tall brackets are the fonts' own glyphs (ordinary, then four large sizes), and beyond the largest a bracket is built from the fonts' end pieces with a rule between. Only a root taller than three ems falls back to a drawn outline.
- **Characters no KaTeX font has.** ⅇ and ⅈ are a bold upright e and a bold italic i (as the LaTeX drew them); `≠` is `=` with TeX's stroke through it; ᴇ is an upright E; `°`, `'`, ᵀ, ʳ and ᵍ are set as superscripts. Anything else falls back to the app's font with a guessed width. The stored text is unchanged.

## Measured (desktop, headless Chromium, the dev server)
- The `cSolve(x^3+3x-2=0,x)` result lays out in 2 to 6 ms in desktop Python (50 items, 27 rows).
- Ten arrow presses through that result as a picked row took 0.59 s, of which 0.5 s was the test script's own pauses. This is a rough figure: per-key build and send times are still to be read from `#/debug/keytime`.

## Left open
- Nothing here has been checked on a Chromebook, in Safari, or on the desktop app, and nothing against the emulator. The fonts are Flet's own, so the desktop app should match the browser, but it has not been looked at.
- Every key still redraws the whole screen, so the maths canvas is rebuilt and sent each time. Sending only the cursor's layer on a cursor move (as spike A did) needs the line's controls kept between redraws.
- The first click on an unpicked history row still places the cursor from estimated widths (`recall_at`); it could use `Layout.hit` now.
- A drag only moves a selection; dragging to select is not built.
- Result rows SymPy draws, messages and errors are still LaTeX or plain text.
- The Pseudocode and Scientific devices do not use the canvas line yet; `MathStyle` is where a device would set its own look.
