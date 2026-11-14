# Emulator check 6, run 4: part P (the touchpad pointer)

Observations only. Emulator: TI-Nspire CX CAS Premium Teacher Software 6.0.3.374, CX II-T CAS handheld view, Keypad + SideScreen at 250%. Document: new Handheld-size document, Radian, Automatic, Real, Float 8 (set through Document Settings; the new document had inherited Degree and I changed it to Radian). Page 1.1 Calculator with `1+1`, `x^2`, `solve(x^2=4,x)` (results 2, x², x=−2 or x=2); page 1.2 Lists & Spreadsheet with 1, 2, 3 in column A; page 1.3 Graphs with f1(x)=x².
Method: the computer mouse on the touchpad picture (press, drag, move without a button, click the centre) and the computer mouse on the handheld screen. A screen-only mouse cursor (an ordinary arrow) is drawn by the operating system and appears in screenshots one step late, so it is not the emulator's pointer; the rows below separate the two.

## Summary (first pass; the second pass at the end supersedes the lines it contradicts)
- Moving or dragging the mouse on the touchpad picture (with or without a button) did **not** move any pointer on the handheld screen. The picture of the pad only changes colour (blue) while the mouse is over or dragging on it.
- A pointer **is** drawn on the screen on the Graphs page after the centre key of the touchpad is clicked: an open-hand glyph, at the last place the computer mouse had been over the screen (not the screen centre). The arrow keys then move it in small steps. It did not hide on its own in the ~9 s I watched (no hide timer seen), so the "hides about a second after it stops" idea is **not** what this emulator does.
- On the Calculator and the Lists & Spreadsheet pages the arrow keys act as usual (select a history line, move a cell), whether or not the pointer was shown.
- With the computer mouse on the screen (these rows are "mouse on screen"): clicks place a cursor or select, hover over a graph curve highlights it and shows a label, and dragging on the Graphs page pans the window.

## P1: does a pointer appear from the touchpad?
Settings: as above. Keys: mouse: move onto the touchpad centre then right and down in small steps; press and drag; press, move in steps while held, screenshot while held, release.
Observed: the pad picture turned blue during the drag and hold. No pointer or cursor was drawn on the handheld screen on 1.1. Moving the mouse onto the touchpad produced no screen change. (Descriptions "pointer first shows" and "shape" are under P3 below, from the Graphs page.)
Screenshot: pages-shots-6/P1a-touchpad-drag-pad-highlight.png, P1b-touchpad-held-move.png, P1c-mouse-over-screen-no-pointer.png, P1d-mouse-over-touchpad-os-cursor-lag.png
Differs from CASSim or from this file's expectation? yes: the emulator's touchpad picture does not act as a pointer joystick by dragging; CASSim's joystick idea is its own design.

Then clicked the centre key of the touchpad (mouse click on the centre of the pad), on 1.3:
Observed: an open-hand pointer appeared on the graph screen near the bottom, next to the y-axis. That place is where the computer mouse had last been over the screen (about the lower right of the screen), not the screen centre. Shape in words: a hand with the fingers open, like a grab hand.
Screenshot: pages-shots-6/P1e-touchpad-centre-click-hand.png
Differs? not known.

Pressing the touchpad's up arrow region twice: a hint appeared beside the pointer: the word "text" and a small rounded badge with "tab" in it.
Screenshot: pages-shots-6/P1f-touchpad-up-click-text-hint.png

## P2: how long before it hides; does a key press hide it
Keys: computer keyboard Right once, then waited and photographed at 0, 1, 2, 4 and 9 seconds.
Observed: the hand pointer and the label "axes" (the pointer was over the y-axis) stayed on the screen at every time up to ~9 s after the last move. No hide timer seen. The key press `5` on 1.3 left the screen unchanged (no digit shown, pointer unchanged); a later sequence is under P3.
Screenshot: pages-shots-6/P7a-right-x3-moves-pointer.png, P2a-pointer-axes-label.png, P2b-pointer-after-9s.png
Differs? yes: no auto-hide in this emulator; CASSim's ~1 s hide is a design choice, not copied.

## P3: joystick or laptop touchpad; speed; edges
Keys: computer keyboard Right (the arrow keys), 3, then 1, then 10, then 60 presses.
Observed: each Right press moves the pointer a small step to the right (about 5 screen pixels, a few percent of the screen width). After 10 more presses the glyph was an ordinary arrow rather than the hand at the same height. After 60 more presses the pointer was not visible on the screen (it either ran off the right edge or hid; the screen showed no pointer). Up ×20 and the key `5` changed nothing visible. I could not tell fast from slow drags because the touchpad picture does not move the pointer.
Screenshot: pages-shots-6/P3a-right-x10-arrow.png, P3b-right-x60-offscreen.png
Differs? not known: edge behaviour (clamp or leave the screen) not settled; a hold-still joystick could not be tested.

## P4: what a click does
(mouse on screen; the real centre-click of the touchpad was used only on 1.3)
- Click on a history entry (`x²`, input): a text cursor is placed inside the entry text at the click point (after the x²). The entry line shows a dashed empty box. The entry is not selected as a whole.
- Click on a history result (`x=−2 or x=2`): a text cursor is placed inside the result text (between − and 2).
- Click in the entry line: a text cursor in the entry line.
- Open Menu, click a row (3 Algebra): the submenu opens to its right (list 3 Expand to B Trigonometry visible, arrows to scroll). Hover over a row highlights it. A click on 7 Matrix & Vector opened its submenu; a click on 2 Number opened its submenu. Escape closed only after clicking the status bar first (two Escape presses).
- Click a cell on 1.2 (A2): the cell gets a blue frame; the name box shows A2 and the formula bar shows 2.
- Click a column letter on 1.2 (A): the whole column A is framed in blue; the name box shows A.
- Click on empty space on 1.3: nothing visible happens.
Screenshot: pages-shots-6/P4a-click-history-entry.png, P4b-click-history-result.png, P4c-click-entry-line.png, P4d-menu-hover-row.png, P4e-menu-click-opens-submenu.png, P4f-sheet-cell-click.png, P4g-sheet-column-letter-click.png, P4h-graph-empty-click.png
Differs? not known; CASSim may click-to-place-cursor in history lines the same way.

## P5: hover shapes and pop-ups
(mouse on screen)
- Over the curve on 1.3: the curve draws thicker and a label "graph f1" appears beside the pointer.
- Over the x-axis on 1.3: no label for the axis from the computer mouse; a hint "text" with a "tab" badge appeared beside the pointer.
- Over a page tab on 1.1 the pointer drawn was a pointing hand (the glyph in the screenshots over the tab).
- Over a cell on 1.2: arrow (no pop-up).
Screenshot: pages-shots-6/P5a-hover-curve-graph-f1.png, P5b-hover-axis-text-tab.png
Differs? not known.

## P6: holding the click on 1.3
(computer mouse press and drag)
- From empty space: the graph window pans (x range from −10…10 to about −12.64…7.36, y range shifted); the curve itself unchanged.
- From the curve: the window pans the same way (the curve is not reshaped or moved; x range to about −14.34…5.66).
Screenshot: pages-shots-6/P6a-drag-empty-pans.png, P6b-drag-on-curve-pans.png
Differs? not known: a grab on a function curve here pans rather than editing it.

## P7: arrow keys with the pointer showing
- On 1.2 after clicking the touchpad centre, Down moved the selected cell from A1 to A2 as usual.
- On 1.1 after clicking the touchpad centre, Up selected the last result (`x=−2 or x=2`, whole result highlighted) as usual.
- On 1.3 the arrows moved the pointer (P3).
Screenshot: pages-shots-6/P7b-sheet-down-moves-cell.png, P7c-calc-up-selects-result.png
Differs? not known.

## Run, not run, also seen
Run: P1 (touchpad drag/hold and centre click), P2 (hide timing, long hold), P3 (arrow steps and edge, partly), P4 (all but the touchpad centre-click on each target), P5, P6, P7.
Not run: P3 fast vs slow drag comparison and the hold-still joystick test (the touchpad picture did not move a pointer); the centre-click of the touchpad on each P4 target; P5 hover over a page tab and a cell shape described only for the tab.
Also seen: a new document opened with the previous document's Degree setting; typing `solve(x^2=4,x)` without pressing Right after the exponent gives a Syntax error dialog.

## Second pass (finishing part P; supersedes the first pass where they differ)
Settings: same document. Computer keyboard arrows and mouse; the touchpad picture's centre key was clicked with the mouse.
Correction: the glyph seen on the Graphs page is the emulator's own pointer, not a lagging computer cursor. Evidence: it stays where it is for at least 2 s while the computer mouse is elsewhere (on the keypad), and the arrow keys move it.

### P1 (again): where does it first show, and its shape
Observed: it shows at the place the computer mouse last was over the handheld screen, and stays there when the mouse leaves. Shapes seen: an ordinary arrow over empty graph space; an open hand near the y-axis; a four-way cross-arrow (move) over the curve, with the curve drawn thick and the label "graph f1"; a pointing hand over a page tab; a text I-beam over history text and the entry line on 1.1.
Screenshot: pages-shots-6/P8a-pointer-after-centre-click-arrow.png, P8g-left-x30-pointer-over-curve.png, P8m-down-x10-pointing-hand-on-tab.png, P8o-centre-click-over-entry.png

### P2 (again): hiding and key presses
Observed: after the last arrow press the pointer stayed on screen with no change for at least 9 s (checked at 1, 2, 4 and 9 s) and again after 2 s in the second pass. Pressing `5` with the pointer showing on 1.3 changed nothing: the pointer stayed and no digit appeared.
Screenshot: pages-shots-6/P8d-key5-pointer-stays.png
Differs? yes: no auto-hide and no hide on a key press in the emulator.

### P3 (again): step size, hold, edges
Observed: Right ×8 moves it about 38 screen pixels (about 4.7 px per press, 1 press about 0.6 % of the screen width); Down ×8 moves it about the same distance. Holding Right for 1 s and for 3 s moved it right out of view (the pointer was not visible afterwards). Then Left ×30 brought it back over the curve (so it had been stopped at the right edge, glyph clipped there, not lost); Left ×90 more put it at the middle-left; Left ×190 and ×290 left it at the left edge, and Right ×10 moved it off the edge at once (so it stops at the left edge; it does not travel past it). Up ×100 moved it to the top, over the page-tab strip (it can leave the page area upward); Down ×10 then showed the pointing hand over tab 1.1. A fast hold covers more distance than the single presses (the key auto-repeats); the speed of a press does not matter because the mouse cannot drive the pad.
Screenshot: pages-shots-6/P8b-right-x8-pointer-moves.png, P8c-down-x8-pointer-moves.png, P8e-hold-right-1s-pointer-gone.png, P8f-hold-right-3s-pointer-gone.png, P8h-left-x90-arrow.png, P8i-left-x190-left-edge.png, P8j-left-x290-left-edge-clamped.png, P8k-right-x10-leaves-edge.png, P8l-up-x100-pointer-over-tab.png
Differs? not known: the pointer stops at the screen edges (clamped).

### P4 (touchpad centre-click, pointer over the target)
Observed:
- Pointer over the page tab 1.1 (on 1.3), centre key clicked: the page changes to 1.1 (the tab is picked).
- Pointer over a history entry on 1.1 (`1+1` row) then centre click: the pointer drew as a text I-beam at the entry; no caret was visible in `1+1` afterwards (the previous highlight on the last result stayed). Not settled what this click did.
- Pointer over the empty part of the entry-line row, centre click: a caret appeared at the start of the last result `x=−2 or x=2` (a caret, not a highlight). Not settled whether this is the click's effect.
- Not run: pointer over a menu row, a sheet cell, a column letter and the curve with a centre click (the pointer could only be placed by the real mouse, whose click already acts on the target).
Screenshot: pages-shots-6/P8n-centre-click-on-tab-switches-page.png, P8o-centre-click-over-entry.png, P8p-centre-click-over-entry-line.png
Differs? not known.

### P5 (again): hover
Observed: pointer over a page tab: a pointing hand; over the curve: move cross-arrow, thick curve and label "graph f1"; over the axis area: a hint "axes" (second pass) or "text" with a "tab" badge (first pass).

### P6 / P7: unchanged from the first pass. Arrow keys move the pointer on 1.3 only; on 1.1 and 1.2 they act as usual.

## Run, not run, also seen (replaces the lists above)
Run: P1 to P7, with the corrections in this section.
Not run: P4 centre-click on a menu row, a sheet cell, a column letter, the curve and empty graph space with the touchpad (only with the real mouse); P3 fast versus slow drags (the touchpad picture does not move the pointer).
Also seen: a new document opened with the previous document's Degree setting; typing `solve(x^2=4,x)` without pressing Right after the exponent gives a Syntax error dialog.
