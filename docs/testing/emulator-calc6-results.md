# Emulator check 6, run 5 - Part 5 (Calculator / history) results

Observations only, from TI-Nspire CX CAS Premium Teacher Software 6.0.3.374, Handheld page size, Keypad + SideScreen, 250% zoom.
Settings: new document (Document8) Float 8, Radian, Normal, Real, Auto, CAS On, Vector Rectangular, Decimal, SI.
Screenshots: `pages-shots-6/R5-<row>-<name>.png`. Rows marked "zoom-only" were read from zoomed captures taken in a batch and have no cropped screenshot.
History used: E1 `2+3` -> 5; E2 `expand((x+2)·(x+2))` -> `x²+4·x+4`; E3 `solve(x·x=2,x)` -> `x=-√2 or x=√2`.

Document Settings seen: `R5-calc-docsettings-1.png`, `R5-calc-docsettings-2.png`.

## H1 m - Doc menu Edit
- Settings: as above.
- Keys: doc, 2.
- Observed: Edit ▶ lists 1 Undo (Ctrl+Z, enabled), 2 Redo (Ctrl+Y, greyed), 3 Cut (Ctrl+X, greyed), 4 Copy (Ctrl+C, greyed), 5 Paste (Ctrl+V), 6 Delete, 7 Color ▶ (greyed). Undo stayed enabled after the entry line was cleared on a new page. The Doc menu also lists 1 File ▶, 3 View, 4 Insert, 5 Page Layout, 6 Refresh Libraries, 7 Settings & Status, 8 Login…, 9 Press-to-Test ▶.
- Screenshot: `R5-H1m-doc-edit-undo.png`
- Differs from CASSim or from this file's expectation? Not compared in this run.

## H2 - selecting history items with the arrow keys
- a / l: Up from the empty entry line selects E3 result, then E3 input, E2 result, E2 input, E1 result, E1 input, then stops at the oldest (no wrap). The highlight covers the item only, not the whole row. (zoom-only)
- b: Down from E1 input goes to E1 result; Down past the newest returns to the entry line; more Down does nothing. (zoom-only)
- d: Left on a selected result puts a red caret at the start of the result (before `x`); Right moves it one step (past `x`, before the superscript 2). (zoom-only)
- f: Esc deselects and returns to the empty entry line. (zoom-only)
- g: with E3 input selected (Up twice), typing `q` changed nothing visible: E3 input stays selected, entry line empty, no `q` anywhere. Screenshot `R5-H2g-type-on-selection.png`.
- Key sweep from E3 input selected (zoom-only, one pass, not repeated): Home -> E1 input selected; End -> caret in entry line; ctrl+7 -> E1 input selected; ctrl+1 -> caret in entry line; ctrl+9 -> caret at the start of E1 input (editing); ctrl+3 -> caret in entry line. The same keys act as Home/End-like jumps; the exact mapping of ctrl+digits is read from zooms only and should be re-checked before it is relied on.
- shift+Up from the entry line: selects E3 input (highlight on the input only); a second shift+Up: no visible change (E3 input still the only highlight) (zoom-only).
- Tab on a selected input: caret appears at the start of the input text (editing mode). ctrl+a then: the whole input text highlighted with a caret at its end (zoom-only).
- Differs from CASSim or from this file's expectation? Not compared in this run.
- H2 c, e, h, i, j, k: not run yet (see end of file).

## H4 - bring-down (Return on a selected history line)
Setup for each: entry line empty or as stated, then Up to select (Up x6 = E1 input, x5 = E1 result, x1 = E3 result), then Return.
- a (E1 input `2+3`, Return): `2+3` appears in the entry line, not evaluated, caret after the `3`; history selection cleared. Screenshot `R5-H4a-bring-down-input.png`.
- b (E1 result `5`, Return): `5` in the entry line, caret after it. Screenshot `R5-H4b-bring-down-result.png`.
- c (entry line `7*` first, select E1 result, Return): the entry line shows `7· 5`, caret at the end, so inserted at the cursor, not replacing. Screenshot `R5-H4c-bring-down-after-7-times.png`.
- d (entry `abc`, caret between `a` and `bc`, bring down E1 result): `a5bc` with the caret after the `5` (inserted at the caret). Half-scale screenshot only, not cropped.
- e (entry `abc` with `bc` selected by shift+Left x2, bring down E1 result): the entry line became `a5`, so the bring-down replaced the selection. Half-scale screenshot only, not cropped.
- g (E3 result, Return): the entry line shows the result in 2D form, `x=-√2 or x=√2`, with the `or` as a word and square-root templates; a red caret sits at the end of the pasted item. Screenshot `R5-H4g-bring-down-e3-result.png`.
- Differs from CASSim or from this file's expectation? Not compared in this run.
- H4 f, h, i, j, k, l, m, n, o: not run (see end of file).

## H6 - empty Return repeats the last entry
- b: `3` Return; `ans+1` Return; empty Return; empty Return. History rows: `3` -> 3, `3+1` -> 4, `4+1` -> 5, `5+1` -> 6. The history shows `ans` replaced by its value, and each empty Return adds a new pair with the next result. Screenshot `R5-H6b-ans-plus-1-empty-return.png`.
- d: `2+3` Return, then an empty Return: a second `2+3` -> 5 pair is added (repeats an entry that has no `ans`). Screenshot `R5-H6d-no-ans-empty-return.png`.
- e: `randInt(1,6)` Return, then an empty Return: a second `randInt(1,6)` pair is added; both results happened to be 6, so a re-run is shown but a changed value is not shown. Screenshot `R5-H6e-randint-empty-return.png`.
- Differs from CASSim or from this file's expectation? Not compared in this run.
- H6 a, c, f, g, h, i: not run.

## H5 - Del, Backspace and clearing
Settings: as above. History at the start: E1-E3, `3`, `3+1`, `4+1`, `5+1`, `2+3`, `2+3`, `randInt(1,6)` x2.
- c: empty entry line, PC Delete key (twice) and PC Backspace (once): no change to the history or the entry line (the on-screen del key lights red for the first two). Clicking the on-screen `del` key on the empty entry line: no change. Screenshot `R5-H5c-empty-entry-backspace-no-change.png`. This is not the "deletes the previous output" behaviour described in the brief.
- a: select the last `randInt(1,6)` input (Up x2), PC Delete: no change (input still selected, both rows still there). Screenshot `R5-H5a-pc-delete-on-selected-input-no-change.png`.
- a: then PC Backspace: the selected pair (input and result) was removed as one pair; the highlight moved to the input of the previous pair (the first `randInt(1,6)`). Screenshot `R5-H5a-backspace-removes-pair.png`.
- a: then a click on the on-screen `del` key: that pair was removed as well; the highlight moved to the previous input (`2+3`). Screenshot `R5-H5a-onscreen-del-removes-pair.png`.
- Differs from CASSim or from this file's expectation? Not compared in this run.
- H5 b, d, e, f, g, h, i, j: not run (b, e, i not run: only an input was selected here; a result was not tried).

## H4 (continued) and H5 b/e side-observations
- o: select the last result (Up), Return (brings `5` down), Return again: a new pair `5` -> 5 was added, so the pasted text is evaluated as it stands. Screenshot `R5-H4o-bring-down-then-return-new-pair.png`.
- l: select that result (Up), ctrl+Return: no visible change (the result stays selected, the entry line stays empty, nothing brought down or approximated). Screenshot `R5-H4l-ctrl-return-on-selected-result.png`.
- m: not conclusive. After a result was selected I pressed ctrl+a, BackSpace, typed `+`, Up, Return. The `5` -> 5 pair that was selected had been removed (ctrl+a then BackSpace with a history item selected removed the pair, screenshot `R5-H5-ctrl-a-backspace-on-selected-result-removed-pair.png`), and the entry line then showed `5` with no `+`. The `+`-first bring-down was not isolated, so no result is recorded for it.
- H5 side-observation: with a history result selected, ctrl+a then BackSpace removed that pair (see the screenshot above). ctrl+a on its own with a selection was not photographed separately.
- Differs from CASSim or from this file's expectation? Not compared in this run.

## H7 - entry line brackets and symbols
Settings: as above (Document8, Radian, Float 8).
- e: typing `sin(` shows `sin(` with a closing bracket already drawn after the caret (auto-close, both brackets as large glyphs, caret between them). Screenshot `R5-H7e-sin-open-bracket-autoclose.png`.
- d: typing `sin(2*(3+4` then Return: no error; the history shows `sin(2· (3+4))` -> `sin(14)` (brackets were already closed by the auto-close). Screenshot `R5-H7d-unclosed-brackets-return.png`.
- f: each typed then Return: `pi` -> input `π`, result `π`; `sqrt(2)` -> input drawn with a square-root template, result `√2`; `exp(1)` -> input drawn as `ⅇ` with a superscript 1, result `ⅇ`; `a<=b` -> input `a≤b`, result `a≤b`. `infinity`, `a>=b`, `a/=b` not typed. Screenshot `R5-H7f-pi-sqrt-exp-le-display.png`.
- i: `2 3` (space between digits) Return: input shown `2· 3`, result 6 (implied multiplication).
- k: `a:=2:a^2` Return: one pair; the input is shown `a:=2:a²` and the result is 4 (the last statement's value).
- h: `1/3` Return: input and result both shown as a stacked fraction 1 over 3.
- j: `x:=5` Return: one pair, input `x:=5`, result 5. This stored x=5 in Document8 for the rest of the session. Bring-down of an assignment not tried.
- Screenshot for i, k, h, j: `R5-H7-space-multistatement-fraction-assign.png`.
- Differs from CASSim or from this file's expectation? Not compared in this run.
- H7 a, b, c, g, l: not run.

## H3 - the mouse (Handheld view, Document8)
- a / c: a single click on a history input (`x:=5`, click between `:` and `=`) put a thin caret at the click point inside the input; no highlight on the item or the row; the entry line showed the empty dashed box. Screenshot `R5-H3a-click-on-input-caret.png`.
- a: a single click on a result (`5`) put the caret at the start of the result (before the `5`). A second click on it: same, nothing brought down. Screenshot `R5-H3a-click-on-result-caret.png`.
- b: a double-click inside `a:=2:a²` selected the `:=` token only (highlight on `:=`, a red caret mark after it). Screenshot `R5-H3b-double-click-selects-token.png`. Triple-click not tried.
- d: a drag from the left of `a:=2:a²` across to just before the superscript selected `a:=2:a` (highlight on those characters, caret after the `a`, before the `²`). Screenshot `R5-H3d-drag-select-in-history-input.png`.
- j: a right-click on a history input also selected the clicked part (`x:=` highlighted) and opened a menu: 1 Show Warning Info… (greyed), 2 Clear History (highlighted), 3 Copy, 4 Delete. Screenshot `R5-H3j-right-click-history-menu.png`.
- j: a right-click on the entry line opened: 1 Clear History (highlighted), 2 Cut (greyed), 3 Copy (greyed), 4 Paste, 5 Delete (greyed), 6 Select Variable ▶, 7 Symbols…, 8 Math Templates…. Screenshot `R5-H3j-right-click-entry-line-menu.png`. None of the menu items was chosen.
- Differs from CASSim or from this file's expectation? Not compared in this run.
- H3 e, f, g, h, i, k: not run.

## E1 - Algebra, Solve System of Equations (simulator-todo)
- Settings: Document8, Radian, Float 8, Real. `x:=5` had been stored earlier in this document.
- Keys: menu, 3 Algebra, 7 Solve System of Equations ▶, then 1 or 2.
- Observed (menus): menu 3 Algebra lists 1 Solve, 2 Factor, 3 Expand, 4 Zeros, 5 Complete the Square, 6 Numerical Solve, 7 Solve System of Equations ▶, 8 Polynomial Tools ▶, 9 Fraction Tools ▶, A Convert Expression ▶, and a down arrow (more items below, not scrolled). Item 7's submenu has 1 Solve System of Equations… and 2 Solve System of Linear Equations…. Screenshot `R5-E1-algebra-7-solve-system-submenu.png`.
- Observed (7 > 1): dialog "Solve a System of Equations": Number of equations 2 (spinner), Variables `x,y`, hint "Enter variable names separated by commas", OK and Cancel. Screenshot `R5-E1-solve-system-equations-dialog.png`. Cancelled, not run.
- Observed (7 > 2): dialog "Solve a System of Linear Equations" with the same fields. Screenshot `R5-E1-solve-system-linear-dialog.png`. OK gave a template `linSolve({ [ ] ; [ ] },{x,y})` with two empty boxes in a brace, the caret in the first box. Screenshot `R5-E1-linsolve-template-empty.png`. Typing `x+y=3`, Down, `x-y=1`, Return gave the history entry `linSolve({x+y=3, x−y=1},{x,y})` with result `{2,1}`. Screenshot `R5-E1-linsolve-result.png`. While being typed the `x` in the template showed bold (x held the value 5), and the result was still `{2,1}`.
- Differs from CASSim or from this file's expectation? Not compared in this run. The "Solve System of Equations…" (item 1) dialog was not run to a result.

## E2 and E3 (menu part) - Probability > Distributions (simulator-todo)
- Settings: Document8, Radian, Float 8.
- Keys: menu, 5 Probability, 5 Distributions ▶.
- Observed (menu): 5 Probability lists 1 Factorial (!), 2 Permutations, 3 Combinations, 4 Random ▶, 5 Distributions ▶. Distributions lists 1 Normal Pdf…, 2 Normal Cdf…, 3 Inverse Normal…, 4 t Pdf…, 5 t Cdf…, 6 Inverse t…, 7 χ² Pdf…, 8 χ² Cdf…, 9 Inverse χ²…, A Binomial Pdf…, B Binomial Cdf…, C Inverse Binomial…, D Inverse Binomial N…, E F Pdf…, F F Cdf…, G Inverse F…, H Geometric Pdf…, I Geometric Cdf…, J Poisson Pdf…, K Poisson Cdf… (list scrolls; K is the last). Screenshots `R5-E2-distributions-menu-1-to-A.png`, `R5-E2-distributions-menu-B-to-K.png`. This is the menu for E3 (t, χ², F listed); the t, χ² and F dialogs were not opened or run.
- E2 C Inverse Binomial…: dialog titled "Num Successes" with Cumulative Prob, Num Trials n, Prob Success p, a Matrix Form checkbox, OK, Cancel. Screenshots `R5-E2-inverse-binomial-dialog-empty.png`, `R5-E2-inverse-binomial-dialog-filled.png`. With 0.5, 10, 0.3 (Tab between fields) and OK by a mouse click (Return in the last field did not close the dialog; it selected the field text): history entry `invBinom(0.5,10,0.3)` with result 3. Screenshot `R5-E2-invbinom-result.png`.
- E2 D Inverse Binomial N…: dialog titled "Num Trials" with Cumulative Prob, Prob Success p, Successes x, Matrix Form checkbox. Screenshot `R5-E2-inverse-binomial-n-dialog-empty.png`. With 0.9, 0.3, 3: history entry `invBinomN(0.9,0.3,3)` with result 7. Screenshot `R5-E2-invbinomn-result.png`.
- Differs from CASSim or from this file's expectation? Not compared in this run.

## E3 - t, χ² and F dialogs (opened only)
- Keys: menu, 5, 5, then 4 (t Pdf…), 7 (χ² Pdf…), E (F Pdf…); Escape closed each dialog without running it.
- t Pdf: fields X Value, Deg of Freedom df; OK, Cancel.
- χ² Pdf: fields X Value, Deg of Freedom df; OK, Cancel.
- F Pdf: fields X Value, Numerator df, Denominator df; OK, Cancel.
- Evidence: 0.6-scale screenshots only (not cropped, not committed); no values entered and no results produced. The Cdf and Inverse dialogs for t, χ² and F were not opened.
- Differs from CASSim or from this file's expectation? Not compared in this run.

## E4 - d/dx template with empty boxes, run by Return
- Keys: menu, 4 Calculus, 1 Derivative, then Return with both boxes empty.
- Observed (menu): 4 Calculus lists 1 Derivative, 2 Derivative at a Point…, 3 Integral, 4 Limit, 5 Sum, 6 Product, 7 Function Minimum, 8 Function Maximum, 9 Tangent Line, A Normal Line, and a down arrow (more below, not scrolled). Screenshot `R5-E4-calculus-menu.png`.
- Observed: 1 Derivative pasted a template `d/d□(□)` with two empty dashed boxes (one under the `d`, one inside the bracket). Screenshot `R5-E4-derivative-template-empty-boxes.png`.
- Observed: Return with both boxes empty gave an Error dialog "Syntax" with an OK button. Screenshot `R5-E4-return-on-empty-template-syntax-error.png`. After OK the template stayed in the entry line, no history pair added. Screenshot `R5-E4-after-error-ok-template-stays.png`.
- Differs from CASSim or from this file's expectation? Not compared in this run.

## E5 - `getNum(` and `getDenom(` in the Catalog
- Keys: the keypad Catalog key (book icon), tab 1 (A-Z list), then letter key `g` and Down to step.
- Observed: both are listed in the Catalog's tab 1 between `Get` and `getKey(`: `getDenom(` with the hint line `getDenom(Expr)`, then `getKey(`, `getLangInfo()`, `getLockInfo(`, `getMode(`, then `getNum(` with the hint line `getNum(Expr)`. Screenshots `R5-E5-catalog-getnum.png`, `R5-E5-catalog-getdenom.png`. They were not pasted or run.
- Also seen: typing several letters (`getN`) did not narrow to a prefix; only the last letter counted (the list jumped to the first `n` entry, `nand`; `getD` jumped to `dbd(`). A single `g` jumped to the first `g` entry, `gcd(`. Screenshot `R5-E5-catalog-g-key-jumps-to-gcd.png`. The Catalog reopened remembering tab 1 and its last position.
- Differs from CASSim or from this file's expectation? Not compared in this run.

## F4 - keypad ctrl then the `·` key
- Settings: Document8, Radian, Float 8, Auto.
- Keys: typed `1/3`, clicked the on-screen ctrl key, then the on-screen `·` key (the legend printed above it reads "capture"), then Return.
- Observed: the entry line stayed `1/3` (no decimal point inserted, no approximate); the `·` key lit red. Screenshot `R5-F4-keypad-ctrl-dot-no-change.png`. Return then gave `1/3` shown as an exact stacked fraction, result 1 over 3. Screenshot `R5-F4-return-after-ctrl-dot-exact-fraction.png`. No capture dialog or other window appeared. Two separate mouse clicks were used for ctrl and `·`; a held-ctrl chord from the PC keyboard was not tried for this key.
- Differs from CASSim or from this file's expectation? Not compared in this run.

## Hand-back (Part 5, partial)

### Run on the emulator
- H1 m; H2 a, b, d, f, g, l (zoom-only except g); H2 key sweep and shift+Up and Tab / ctrl+a (zoom-only, one pass).
- H4 a, b, c, d, e, g, l, o.
- E4, E5, F4 (mouse clicks only).
- E2 (both run), E3 menu listing and the t Pdf, χ² Pdf, F Pdf dialogs opened (not run).
- E1 (linear system run, nonlinear dialog opened and cancelled).
- H3 a, b (double-click only), c, d, j.
- H7 d, e, f, h, i, j (not the bring-down), k (f partly: `infinity`, `>=`, `/=` not typed).
- H5 a (input selected only), c.
- H6 b, d, e.

### Not run (no results recorded; nothing is claimed for them)
- H1 i, H1 k.
- H2 c, e, h, i, j, k as written in the brief (only the one-pass zoom sweep above was done; it is not a full answer).
- H3 e, f, g, h, i, k and H3 b triple-click, H4 f, h, i, j, k, m, n, H5 b, d-j, H6 a, c, f-i, H7 a, b, c, g, l, H8, H9.
- Editor plan rows T3 f, T7, T8 c, T9, T10 c.
- Part B items 4-7 leftovers, hidden A3 / A11.
- simulator-todo.md E3 (dialogs opened but no values run; the other six t, χ², F dialogs not opened), E7, F1, F2, F3, F5.
- Reason: not reached in this run.

### Also seen, not covered by a row
- On the emulator the PC Delete key did nothing on a selected history input or on the empty entry line, while PC Backspace and the on-screen `del` key removed a selected pair (H5 a).
- After a click on the on-screen keypad, keyboard focus sat on the keypad panel (blue frame round the toolbox); the arrow keys still reached the Calculator page.
- Both `randInt(1,6)` results were 6, so H6 e does not show a changed value.
- Document9 (a blank new document, "Press menu") appeared on the emulator while I was away from the screen; I did not open it on purpose. It is to be closed without saving.

## E7 (simulator-todo): Doc > Insert menu, Program Editor and Add Python submenus

Settings: Document8, Radian, Automatic, Real, Float 8 (inherited as set for this run).
Keys: click doc key, 4 (Insert). Down pressed 12 times (the menu took a few seconds to scroll), then clicked the ▼ scroll arrow at the foot of the list. Down, Left, Down, Right inside the submenus; Escape to close.
Observed:
- Insert submenu, first page: 1 Problem, 2 Page (Ctrl+I), separator, 3 Calculator, 4 Graphs, 5 Geometry, 6 Lists & Spreadsheet, 7 Data & Statistics, 8 Notes, 9 Vernier DataQuest™, A Widget, then a ▼ scroll arrow.
- After scrolling: B Program Editor ▶, C Add Python ▶ (list ends there in this view; a ▲ arrow at the top).
- B Program Editor ▶ opens to the left: 1 New…, 2 Open…, 3 Import…, 4 View….
- C Add Python ▶ opens to the left: 1 New…, 2 Open… (greyed out), 3 Shell.
- Key presses sent while the menu was still opening landed late (the highlight caught up a few seconds after).
Screenshot: pages-shots-6/R5-E7-doc-insert-program-editor-submenu.png, R5-E7-doc-insert-add-python-submenu.png (the first-page view is full-screen only, not cropped).
Differs from CASSim or from this file's expectation? Not compared in this run.

## F1 (simulator-todo): ctrl+K on the keypad (only this combination run)

Settings: Document8, Radian, Automatic, Real, Float 8; empty entry line on page 1.1.
Keys: click status bar, click ctrl (90,437), click K (228,690); waited 6 s in total.
Observed: no dialog, menu or change on the entry line or history; the K key showed highlighted on the keypad image and ctrl stayed shown red. Two screenshots 3 s apart looked the same.
Screenshot: pages-shots-6/R5-F1-keypad-ctrl-K-no-visible-change.png
Not run from the F1 row: ctrl+N, O, S, W, R, G, T, M, E, F, H, B, 4, 6, Tab (several would open file dialogs or close the document; not risked in this run).
Differs from CASSim or from this file's expectation? Not compared in this run.

## F3 (simulator-todo): Delete on a fraction template

Settings: Document8, Radian, Automatic, Real, Float 8.
Keys: click status bar; click the templates key (354,480); Return on the highlighted fraction icon (first in the palette); type 7, Down, type 8, Right (cursor now after the template, red cursor lines either side); click the on-screen del key once; screenshot 3 s later. The same sequence was run twice with the same result.
Observed: before: stacked 7 over 8. After one del: entry line empty, whole template gone. No intermediate state (template selected/highlighted) was seen; screenshots were taken about 3 s after each step. A second Delete on an already selected template was therefore not observed.
Screenshot: pages-shots-6/R5-F3-fraction-template-before-delete.png, R5-F3-after-one-delete-template-gone.png
Differs from CASSim or from this file's expectation? Not compared in this run.

## Hand-back addendum (Part 5, later than the lists above; this addendum overrides them where they differ)

Run on the emulator since the lists above: E7 (Doc > Insert menu: Problem to Widget, Program Editor ▶ four items, Add Python ▶ three items), F1 ctrl+K only, F3 (single Delete removed the whole fraction template; the "second Delete on a selected template" step was not observed).
Not run: E7 Functions & Programs > Mode submenus; F1 ctrl+N, O, S, W, R, G, T, M, E, F, H, B, 4, 6, Tab; F2; F5; H8; H9; the other not-run rows named in the lists above.
Also seen: the emulator redraws slowly after menu key presses (menu items and highlight caught up 2 to 5 s later); Escape needed up to three presses to close the Insert submenu.

## H9 (history layout), partial: rows a, b (partly), c, d (partly), e (partly), g

Settings: new Document10 (Handheld page size), Document Settings checked on screen: Float 8, Radian, Exponential Normal, Real, Auto, CAS On. Calculator page 1.1, fresh history. Screen at 250% zoom, so distances below are screen pixels at that zoom, estimated by eye from the screenshot, not handheld pixels.
Keys: click status bar; typed in chunks of up to 9 characters; Return after each entry; 3 to 4 s wait before each screenshot.
Entries in order: `2+3`; `1/3`; `[1,2;3,4]`; `1234567+2345678+3456789`; `1234567+2345678+3456789+4567891+5678912+67891` (the 5-chunk long entry, 45 characters).
Observed:
- a: `2+3` and `5` share one row; the result sits at the right edge, the input at the left.
- c: `1/3` and the matrix are taller rows (about 135 and 122 px against about 80 px for `2+3`); input at the left and result at the right edge of the same row.
- b: the 23-character input with a 7-digit result (7037034) stays on one row. The 45-character input is NOT wrapped: it is cut off at the right with a small right-pointing triangle after the visible text (the visible text ended at `...4567891+567`), and the result (17351728) moved to its own line, right-aligned, under it. The exact break between the two lengths was not found (only these two lengths tried).
- d: only the long-input case seen (cut off with ▸, not wrapped); a wrapped long result was not tried.
- e: rows alternate a light grey and white background (row 1 grey, row 2 white, row 3 grey, row 4 white, row 5 grey); no separate rule lines were seen between rows; thickness/colour values not measured.
- g: the view first scrolled on the fifth entry (the 45-character one): the top of the `1/3` row was cut off and a scroll bar appeared; the entry line then sat about 40 px above the bottom edge of the display area (estimated). Entries before that fitted without scrolling (rows about 80, 135, 122, 75 px).
Not run: f (selection highlight), h (warning triangle), i (Float/Fix change), b threshold search, d wrapped result.
Screenshot: pages-shots-6/R5-H9ac-short-fraction-matrix-rows.png, R5-H9b-23-char-input-one-row.png, R5-H9bdg-45-char-input-truncated-view-scrolled.png
Differs from CASSim or from this file's expectation? Not compared in this run.

### H9 f (selection highlight)
Settings: Document10 as above, 45-character entry last in the history. Keys: click status bar, Up, wait 4 s.
Observed: the last RESULT (17351728) is highlighted in a mid-blue rectangle that covers only the result text with a small margin (about 8 px each side, estimated), not the whole row; the input text is not highlighted; the entry line shows an empty dashed box. The row keeps its light-grey shading.
Screenshot: pages-shots-6/R5-H9f-selection-highlight-result-only.png
Differs from CASSim or from this file's expectation? Not compared in this run.
Update to the H9 list above: f now run. Still not run: h, i, b threshold search, d wrapped result.

## Hand-back addendum 2 (Part 5; overrides the lists above where they differ)

Run on the emulator since addendum 1: H9 a, c, f in full; H9 b, d, e, g in part (see the H9 section; threshold not found, wrapped result not tried, line colours and thickness not measured).
Not run: H9 h, i; H8 (a to f); and every row named as not run in the lists above, except where addendum 1 and this one say otherwise.
State: new blank Document10 opened by the emulator when it was brought back from the wrong desktop; it holds the H9 entries. Open and unsaved: R5-test, Document4 to Document10.

## H8 a (keypad ctrl+1 and ctrl+7, no selected line only)

Settings: Document10 (Radian, Automatic, Real, Float 8), five history entries, view scrolled to the bottom, empty entry line.
Keys: click status bar; click ctrl (90,437) then the 1 key (158,564), wait 4 s, screenshot; click ctrl then the 7 key (158,480), wait 4 s, screenshot. Keypad clicks, not PC keys.
Observed:
- ctrl+1: the view stayed as it was, with the empty entry line visible at the bottom and no selection. It was already at the bottom, so whether ctrl+1 jumps to the last line is not settled (the question in the brief, "with 20 entries", was not tried).
- ctrl+7: the view scrolled to the top and the first history INPUT (`2+3`) was highlighted in blue (the input text only, not the result); the entry line was no longer visible. Escape then cleared the selection.
Not run: both keys with a selected line; ctrl+1 with 20 entries.
Screenshot: pages-shots-6/R5-H8a-keypad-ctrl-1-no-selection.png, R5-H8a-keypad-ctrl-7-selects-first-input.png
Differs from CASSim or from this file's expectation? Not compared in this run.

## H8 b (shift+Esc, keypad)

Settings: Document10 (Radian, Automatic, Real, Float 8), empty entry line at the bottom of the history.
Keys: click status bar; type 9 in the entry line; click ctrl (90,437) then Z (266,750); screenshot 4 s later (0.6 scale, not committed); click shift (158,437) then esc (90,295); screenshot 4 s later (full size).
Observed: after ctrl+Z the 9 was gone (empty entry line) and the toolbar undo/redo arrows were both active; after shift then esc the 9 was back in the entry line. So shift+Esc behaved as redo of the undone typing here. The 9 was then cleared with the del key.
Screenshot: pages-shots-6/R5-H8b-keypad-shift-esc-restores-undone-9.png (the after-undo view was half-scale only)
Differs from CASSim or from this file's expectation? Not compared in this run.

Update (addendum 3): H8 a (no-selection case) and H8 b are now run; H8 c (ctrl+K done in F1, ctrl+. in F4; ctrl+H and ctrl+J not run), d, e, f not run.

## H8 c (keypad ctrl+H, ctrl+J; ctrl+I seen by mistake)

Settings: Document10 (Radian, Automatic, Real, Float 8), page 1.1, empty entry line. Keypad clicks: status bar, ctrl (90,437), then the letter key; waits 4 to 5 s.
Observed:
- ctrl+H on page 1.1: no visible change (H key lit on the keypad image only).
- ctrl+J on page 1.1: no change to the page, but a "Screen Capture taken. View it." notice appeared at the bottom right of the window, outside the handheld crop. Seen after each of the two ctrl+J presses (the first on the Add menu described next, the second on page 1.1); not seen after ctrl+H.
- ctrl+I (clicked by mistake instead of H, I key is next to it): added a page (1.2) and opened its Add menu (1 Add Calculator, 2 Add Graphs, 3 Add Geometry, 4 Add Lists & Spreadsheet, 5 Add Data & Statistics, 6 Add Notes, 7 Add Vernier DataQuest™, 8 Add Widget, 9 Add Program Editor ▶, A Add Python ▶). The PC Escape key did not close it; clicking the on-screen esc key did, leaving a blank page 1.2 reading "Press menu". The stray page 1.2 is still in Document10.
- ctrl+. was run in F4, ctrl+K in F1.
Screenshot: pages-shots-6/R5-H8c-keypad-ctrl-H-no-visible-change.png, R5-H8c-keypad-ctrl-I-adds-page-menu.png, R5-H8c-keypad-ctrl-J-on-add-menu.png, R5-H8c-keypad-ctrl-J-screen-capture-toast.png (cropped, the notice is outside it) and R5-H8c-keypad-ctrl-J-screen-capture-toast-full.jpg (full window, shows the notice).
Differs from CASSim or from this file's expectation? Not compared in this run.
Update to addendum 3: H8 c is now run except that the ctrl+J notice was not checked further (what it saved, where).

## H9 i (Float/Fix change and earlier history entries)

Settings: Document12 (a new blank document the emulator opened), Document Settings checked first: Float 8, Radian, Normal, Real, Auto, CAS On. Then Display Digits changed to Fix 4 (the drop-down is a long list, Float 0 to Float 12 then Fix 0 to Fix 12; scrolling it with the mouse wheel changed the selected value, and I clicked Fix 4 from the visible part; Fix 2 was not chosen).
Keys: Add Calculator (menu key, 1); type `1/3.`, Return; doc, 7, 2; click the Display Digits arrow; scroll; click Fix 4; click OK; type `1/3.`, Return; waits of 3 to 5 s.
Observed: the first entry's result stayed 0.33333333 after the change; the second entry (same input) gave 0.3333. The input is shown as 1 over 3. with a decimal point in the denominator (typed `1/3.`). Earlier history entries did not change with the setting.
Document12 is left set to Fix 4.
Screenshot: pages-shots-6/R5-H9i-float8-entry-kept-after-fix4.png
Differs from CASSim or from this file's expectation? Not compared in this run. (The brief says the device is expected not to change earlier entries: matches that expectation.)
Update: H9 i now run. H9 h still not run.

## H9 h (warning triangle next to a history line)

Settings: Document12 (Radian, Automatic, Real, Display Digits now Fix 4 from H9 i).
Keys: click status bar; typed `(x^2`, Right (to leave the exponent), `-1)/(x-1)`, Return; waited 5 s; screenshot; click the triangle; screenshot; click OK with the mouse.
Observed: the input `(x^2-1)/(x-1)` shows a yellow warning triangle at the left edge of its row, vertically level with the middle of the stacked fraction; the result is x+1 at the right. Clicking the triangle opened a Warning dialog (title "Warning") with the text "Domain of the result might be larger than the domain of the input." (TI text, do not reuse) and an OK button; OK closed it and left the row unchanged.
A first attempt typed without Right after the `^` put everything after it in the exponent (shown as x with an exponent `(2-1)/(x-1)`, result 1/x^(x-1) style), no triangle; that mis-typed pair is still in the history above the real one and is not a result for this row.
Screenshot: pages-shots-6/R5-H9h-warning-triangle-left-of-input.png, R5-H9h-warning-dialog-text.png
Differs from CASSim or from this file's expectation? Not compared in this run.
Update: H9 h now run. H9 remaining: b threshold search, d wrapped result, e rule thickness/colours.

## H9 d (long result), second part

Settings: Document12 (Radian, Automatic, Real, Fix 4). Keys: typed `seq(n,n,1` and `,25)`, Return, waited 5 s.
Observed: input `seq(n,n,1,25)` on the first line at the left; the result `{1,2,3,...` on a second line starting at the LEFT edge (not right-aligned as short results are), not wrapped, cut off at the right edge after `...,17,1` with a small ▸ marker. The row is two lines tall.
Screenshot: pages-shots-6/R5-H9d-long-list-result-truncated-own-line.png
Differs from CASSim or from this file's expectation? Not compared in this run.
Update: H9 d is now run for both a long input and a long result (neither wraps; both are cut off with ▸).

## H3 f and i (mouse, part)

Settings: Document12 (Radian, Automatic, Real, Fix 4), history of about eight entries, entry line holding `123456789`.
f: click in the entry line text at x 650 (between 3 and 4): the cursor appeared between the 3 and the 4. Click at x 1200, well past the end of the text: the cursor went to the end of the text. Second line of a wrapped entry: not tried (entries do not wrap, see H9); template clicks (g) not tried.
i: mouse wheel up by 5 notches over the history (pointer at the middle of the screen): the view went to the top and the FIRST history input (1/3.) was highlighted in blue as a whole (the stacked fraction box), no scroll bar drag used. Wheel down by 10 notches: the view returned to the bottom, no highlight, the entry line text `123456789` and its cursor unchanged. Whether the highlight came from the wheel itself or from the earlier click state was not separated. The scroll bar and a wheel scroll with a line selected were not tried.
Screenshot: pages-shots-6/R5-H3f-click-inside-entry-text.png, R5-H3f-click-past-end-of-entry.png, R5-H3i-wheel-up-5-top-first-input-highlighted.png
Differs from CASSim or from this file's expectation? Not compared in this run.
Update: H3 f (partly) and i (partly) run. Still not run: H3 e, g, h, k and triple-click.

## H3 e (shift+click, entry line only)

Settings: Document12 (Radian, Automatic, Real, Fix 4); entry line `123456789`.
Keys: click the entry line at x 650 (cursor between 3 and 4), then shift+click at x 735 (click with the shift modifier from the tool); waits 2 and 4 s.
Observed: the characters 4567 were selected (blue highlight from the cursor position to the click position, character by character); the cursor sat after the 7. Shift+click on a history line not tried.
Screenshot: pages-shots-6/R5-H3e-shift-click-selects-in-entry-line.png
Differs from CASSim or from this file's expectation? Not compared in this run.
Update: H3 e run for the entry line only. Not run: H3 e (history line), g, h, k, triple-click.

## H3 k (drag and drop), within the entry line only

Settings: Document12 (Radian, Automatic, Real, Fix 4); entry line `123456789` with 4567 selected (from H3 e).
Keys: drag from the selected text (x 690) to the right of the end of the text (x 1100); wait 4 s.
Observed: the selected 4567 moved to the end: the line read `123894567` with 4567 still selected. So drag and drop of selected text within the entry line moves it (not a copy). Dragging a part of a history line into the entry line was not tried.
Screenshot: pages-shots-6/R5-H3k-drag-selection-within-entry-line.png
Differs from CASSim or from this file's expectation? Not compared in this run.

## Hand-back addendum 4 (Part 5; latest list, overrides the earlier lists where they differ)

Run since addendum 2: H8 a (no selection), b, c; H9 d (long result), f, h, i; H3 e (entry line), f (entry line), i (wheel only), k (within the entry line).
Not run: H9 b threshold search, e line colours and thickness; H3 e (history line), f (wrapped line), g, h, i (scroll bar, selected-line wheel), k (from a history line), triple-click; H8 d, e, f; ctrl+1 with 20 entries; E7 Mode submenus; F1 other ctrl combinations; F2; F5; H1 i, k; H2 c, e, h-k in full; H4 f, h-k, m, n; H5 b, d-j; H6 a, c, f-i; H7 a-c, g, l; editor rows T3 f, T7, T8 c, T9, T10 c; brief items 4-7 leftovers; hidden A3, A11.
State: the emulator keeps moving to another virtual desktop and opens a new blank document each time it is brought back (Document11, Document12). Open and unsaved: R5-test, Document4 to Document12. Document12 is set to Fix 4 and holds the H9 h, i, d and H3 e, f, i, k entries.

## H8 e (keypad ctrl+B, ctrl+R, ctrl+G, ctrl+T on a Calculator page)

Settings: Document12 (Radian, Automatic, Real, Fix 4), page 1.1, entry line `123894567` with 4567 selected.
Keys: click status bar; for each letter click ctrl (90,437) then the letter key (B (152,660), R (228,720), G (344,660), T (305,720)); wait 4 s; half-scale screenshot after each.
Observed: no visible change after any of the four: no dialog, menu, new page or change to the entry line or history; only the pressed letter key lit on the keypad image.
Screenshot: none committed (half-scale screenshots only, which cannot be cropped to the handheld box). This is therefore a half-scale observation, not a full-size one.
Differs from CASSim or from this file's expectation? Not compared in this run.
Update: H8 e run (half-scale only). H8 d and f still not run.

## H5 b (Del or Backspace on a selected RESULT)

Settings: Document13 (a new blank document the emulator opened; Radian shown in the title bar, Document Settings not re-opened this time, earlier new documents had been Float 8 / Radian / Auto / Real). Calculator page 1.1.
Two runs:
1. Entries `2+3`, `4+1`; Up selected the last result (5, blue box); click the on-screen del key (366,437): the WHOLE history was gone (empty page, entry cursor at the top). I did not separate this from the keypad ctrl key having been left switched on by earlier clicks (ctrl+del is the clear key); so this run does not settle the plain-Del question.
2. Entries `2+3`, `4+1`, `6+1`; three Up presses selected the result (5) of the middle pair `4+1`; PC BackSpace key: only the middle pair (`4+1` and its result) was removed; `2+3` and `6+1` stayed; the selection moved to the INPUT of the first pair (`2+3`, blue) and the entry line showed the empty dashed box. A result can therefore not be deleted on its own: the whole pair goes.
Screenshot: pages-shots-6/R5-H5b-del-key-on-selected-result-history-empty.png (run 1), R5-H5b-result-selected-before-backspace.png and R5-H5b-after-backspace-pair-removed.png (run 2)
Differs from CASSim or from this file's expectation? Not compared in this run.
Document13 now holds `2+3` and `6+1` with the first input selected.

## H5 d (repeated Del or Backspace on an empty entry line)

Settings: Document13 as in H5 b; history `2+3` / 5 and `6+1` / 7, empty entry line, nothing selected (Escape pressed first).
Keys: click status bar; PC BackSpace three times (4 s and a screenshot after each); then the on-screen del key (366,437) clicked twice (a screenshot after each).
Observed: no change after any of the five presses; both pairs stayed and the entry line stayed empty. This matches H5 c above and does not reproduce the "deletes the previous output" behaviour described in the brief. The on-screen del key showed lit red throughout, including in screenshots where nothing had been pressed for several seconds.
H5 d "history empty" case not reached (the history was never emptied this way).
Screenshot: pages-shots-6/R5-H5d-empty-entry-backspace-x3-del-x2-no-change.png (last screenshot only)
Differs from CASSim or from this file's expectation? Not compared in this run.
Note on H5 b run 1: with the same on-screen del key, a selected result removed the whole history in that run; the cause was not separated, see above.

## H5 e (select two lines with shift+Up, then delete)

Settings: Document13 as in H5 b; history `2+3` / 5 and `6+1` / 7.
Keys: click status bar; Up (selected the last result 7); shift+Up; wait 4 s; screenshot; PC BackSpace; wait 4 s; screenshot.
Observed: after shift+Up only the result 7 was highlighted (no extended selection over a second line). BackSpace then removed only the `6+1` pair; `2+3` / 5 stayed and its input became the selected item. So no multi-line selection or multi-delete was seen this way.
Screenshot: pages-shots-6/R5-H5e-shift-up-no-extended-selection.png, R5-H5e-backspace-removes-only-one-pair.png
Differs from CASSim or from this file's expectation? Not compared in this run.
Document13 now holds only `2+3` / 5.

## H5 g (after deleting the last pair: `ans` and variables), partial

Settings: Document13 as in H5 b; history `2+3` / 5.
Keys: Escape; typed `a:=5` Return, `3+4` Return; Up (selected the result 7); PC BackSpace; screenshot; Escape; typed `ans` Return; typed `a` Return; screenshot. Then a click on the `a:=5` input and BackSpace (see below); typed `a+1` Return.
Observed:
- BackSpace on the selected result of `3+4` removed that whole pair; `a:=5` / 5 was the last pair left, and its input was highlighted.
- `ans` then gave 5 (shown in the history as input `5`, result 5): Ans was the result of the new last pair, the `a:=5` result, not 7.
- `a` gave 5. The deleted pair did not define a variable, so the question "do variables defined by the deleted entry survive" was NOT tested: the defining pair itself was not deleted.
- A click on the `a:=5` input did not select the item as a whole; it put a text cursor inside the line (between `a:` and `=5`), and BackSpace did not remove the pair (the line still read `a:=5`; a character at the cursor may have been deleted but the line looked unchanged in the half-scale screenshot). `a+1` afterwards gave 6, so `a` was still 5.
Screenshot: pages-shots-6/R5-H5g-ans-and-a-after-deleting-last-pair.png
Differs from CASSim or from this file's expectation? Not compared in this run.
Update: H5 g partly run (Ans after deleting the last pair only). H5 f, h, i, j not run.

## H5 h (clear key), keypad ctrl+del only

Settings: Document13 as above, history of five pairs.
Keys: click status bar; typed `77` in the entry line (not screenshotted); click ctrl (90,437) then del (366,437); wait 5 s; screenshot.
Observed: the entry line was empty afterwards and all five history pairs were still there. Because `77` was not captured before the clear, that the clear removed the typed text (rather than the typing never having landed) is inferred, not seen.
Not run: shift+del, the Computer software's Edit > Clear / Clear History menu items, and whether the clear key clears the history when the entry line is already empty.
Screenshot: pages-shots-6/R5-H5h-keypad-ctrl-del-entry-line-empty-history-kept.png
Differs from CASSim or from this file's expectation? Not compared in this run.
Update: H5 h partly run.

## Hand-back addendum 5 (Part 5; latest list, overrides the earlier lists where they differ)

Run since addendum 4: H5 b, d, e in full; H5 g and h in part; H8 e (half-scale only).
Not run: H5 f, i, j, h (shift+del, Edit > Clear, Clear History), g (deleting a defining pair); everything else named as not run in addendum 4 except what is listed above.
State: Document13 (new blank document from the last desktop switch) holds `2+3`, `a:=5`, `5`, `a`, `a+1` and a variable a=5. Open and unsaved: R5-test, Document4 to Document13.

## H6 g and H6 f

Settings: Document14 (another new blank document the emulator opened). Its results show four decimals (13.0000), so Document14 inherited Display Digits Fix 4 from Document12; it is NOT Float 8. Radian in the title bar; Real/Auto not re-opened. (Document13 used for H5 may have had the same inheritance; its results were whole numbers, so nothing there depended on it.)
Keys: click status bar; Add Calculator (1); typed `10`, Return; typed `+1`, Return; empty Return; then click ctrl (90,437) and enter (366,606) on the empty entry line; waits 3 to 5 s.
Observed:
- g: `10` gives 10. A line typed as `+1` is shown in the history as `10+1` (Ans replaced by its stored value) with result 11. An empty Return then added a new pair `11+1` = 12: the empty Return repeated the `+1` entry with the new answer.
- f: ctrl+Enter (keypad ctrl then enter) on the empty line added `12+1` with result 13.0000, a decimal (approximate) form shown in the Fix 4 format. The input was shown with the stored value 12.
Screenshot: pages-shots-6/R5-H6g-plus1-then-empty-return-repeats.png (before the ctrl+Enter), R5-H6f-keypad-ctrl-enter-on-empty-line-decimal.png
Differs from CASSim or from this file's expectation? Not compared in this run. (The brief's expectation for f, "Ans as a decimal", matches what was seen.)
Update: H6 f and g run. Not run: H6 a, c, h, i.

## H6 i (`ans` used twice in one entry), part

Settings: Document14 (Fix 4 inherited, see H6 g), previous answer 13.0000 from H6 f.
Keys: typed `ans*ans`, Return; empty Return; waits 4 to 5 s.
Observed: the first line was shown in the history as `13.·13.` with result 169.0000 (both ans replaced by the stored value, which carried a decimal point because the previous answer was approximate); the empty Return added `169.·169.` = 28561.0000. So an entry using ans twice repeats with the new answer in both places. The `f(ans)` function-call case was not tried.
Screenshot: pages-shots-6/R5-H6i-ans-twice-repeats-with-new-answer.png
Differs from CASSim or from this file's expectation? Not compared in this run.
Update: H6 i partly run (ans twice only). H6 a, c, h not run.

## H6 a (Newton entry repeated by empty Return), numeric version only

Settings: Document14, Radian, Display Digits Fix 4 (inherited), so results show 4 decimals.
Keys: first attempt (junk, kept in the history): typed `1.5`, Return, then `ans-(ans`, Right, `^2-2)/(2*ans)` without typing `^` first, so the typed `^` captured the rest as an exponent; that pair showed `1.5-(1.5)^(2-2)/(2·1.5)` = 0.5000 and two empty Returns gave -0.5000 and -1.5000 (not Newton; recorded only because it is in the screenshot history). Second attempt: `1.5`, Return, typed `ans-(ans^`, `2`, Right, `-2)/(2*`, `ans)`, Return, then three empty Returns (waits 2 s).
Observed: the entry shows as `1.5-(1.5)²-2 over 2·1.5` = 1.4167; the first empty Return gave `1.4166666666667-(1.4166666666667)²-2 over 2·1.4166666666667` = 1.4142; the next showed `1.4142156862745 ...` = 1.4142; the next `1.4142135623747 ...` = 1.4142. So each empty Return repeats the entry with the stored answer, shown to 13 digits in the history while the result is shown at Fix 4. Four evaluations in total (entry plus three empty Returns) were run; the result stays at 1.4142 at Fix 4 from the second line on. The version with `f(x):=x^2-2` and `derivative` was not run.
Screenshot: pages-shots-6/R5-H6a-newton-empty-return-repeats.png (the last two lines; the top of the history was seen on screen but not cropped)
Differs from CASSim or from this file's expectation? Not compared in this run.
Update: H6 a partly run (numeric version). H6 c, h not run.

## H6 c and H6 h (Up then Return after an `Ans` entry)

Settings: Document14, Radian, Fix 4 (inherited). The brief's `3`, Return, `ans+1` start was not seen as such: the typed `3` pair did not appear in the history above the first `ans+1` (which used the earlier answer 1.4142135623731), so this run starts from the 1.414... answer of H6 a, not from 3. Not investigated.
Keys: typed `ans+1`, Return (2.4142), one empty Return (3.4142); then Up on the empty line; then Return.
Observed: after Up the last result (3.4142) was highlighted (seen at half scale only, not cropped). After Return the entry line held `3.4142135623731` (the full stored value of the selected result, 13 digits), nothing was evaluated, and no new history pair was added. So Up then Return on a selected result brings the value down to the entry line and does not repeat the last entry (unlike an empty Return with nothing selected, which repeated it in H6 a). The Up-then-Return case was run once; it covers both the H6 c and H6 h questions only for a selected result, not for a selected input line.
Screenshot: pages-shots-6/R5-H6ch-up-return-brings-down-result-not-repeat.png
Differs from CASSim or from this file's expectation? Not compared in this run.
Update: H6 c and h run (selected result only). H6 a Newton with f(x) and the lost `3` entry not run.

## H5 f and H5 i (ctrl+A then Delete on a selected history line; Delete then ctrl+Z)

Settings: Document14, Radian, Fix 4 (inherited). Entry line emptied first (ctrl+a, BackSpace).
Keys: Up three times (the result 2.4142 of `1.4142135623731+1` was selected), ctrl+a, PC Delete, then ctrl+z. Waits 1 to 2 s.
Observed (f): ctrl+a changed nothing visible (the result 2.4142 stayed selected; the keypad A key was lit). PC Delete then removed the whole pair `1.4142135623731+1` = 2.4142 from the history and the input of the next pair (`2.4142135623731+1`) became selected. (This differs from the earlier note in this file that PC Delete does nothing: that was on an empty entry line.) The keypad del key was lit during the Delete.
Observed (i): ctrl+z restored the deleted pair in its old place; the restored input `1.4142135623731+1` was shown selected, the next pair intact. Run once.
Screenshots: pages-shots-6/R5-H5f-ctrl-A-result-stays-selected.png, R5-H5f-pc-delete-removed-pair-next-input-selected.png, R5-H5i-ctrl-Z-restores-deleted-pair.png
Differs from CASSim or from this file's expectation? Not compared in this run.
Update: H5 f and i run (one selection each).

## H5 j (delete from the middle of a longer history)

Settings: Document14, Radian, Fix 4 (inherited); history of about 11 pairs (H6 entries), entry line empty.
Keys: Up six times (the input `1.4166666666667 - ...` of the second Newton pair was selected, seen at half scale), PC Delete, wait 2 s.
Observed: the whole pair (that input and its 1.4142) was removed. The next input (`1.4142156862745 - ...`) became selected and sat at the top of the visible history, with the later pairs below it and the entry line out of view; so the view did not jump to the bottom but the selected item moved to the top edge. Run once on a history that was only a little longer than the screen, so the long-history question is only partly answered.
Screenshot: pages-shots-6/R5-H5j-delete-middle-pair-view.png
Differs from CASSim or from this file's expectation? Not compared in this run.
Update: H5 j run (once).

## H5 h (more ways to clear): application Edit menu, context-menu Clear History

Settings: Document14, Radian, Fix 4 (inherited).
Keys and observed:
- Application Edit menu (opened with the mouse, entry line empty, a history input selected): Undo Ctrl+Z, Redo Ctrl+Y (greyed), Cut Ctrl+X (greyed), Copy Ctrl+C, Paste Ctrl+V (greyed), Rename F2 (greyed), Delete Delete, Page Layout ▶, Color ▶. There is no Clear or Clear History item in this menu. The menu sits outside the handheld crop box, so the evidence is a full-window JPG. Menu closed with Escape, nothing chosen.
- Right-click on a history line, then item 2 Clear History (clicked): the whole history disappeared at once, with no confirmation dialog, and only the empty entry line was left (the Undo toolbar icon went grey in the next screenshot). A right-click here selected the clicked input (it was the `1.4142135623731+1` input) and showed the same four items as in H3 j (1 Show Warning Info… greyed, 2 Clear History, 3 Copy, 4 Delete).
- Then `ans`, Return: an Error dialog "Undefined Ans" (TI text, do not reuse; it says the previous calculation did not create Ans or none was entered), OK clicked with the mouse. So after Clear History there is no Ans.
- Not run: shift+Del; the entry-line Clear History item; whether variables survive Clear History (no variable was defined in this document); ctrl+Z after Clear History.
Screenshots: pages-shots-6/R5-H5h-context-menu-on-history-line.png, R5-H5h-context-menu-clear-history-result-empty.png, R5-H5h-ans-after-clear-history-undefined-error.png, R5-H5h-edit-menu-no-clear-full.jpg (full window)
Differs from CASSim or from this file's expectation? Not compared in this run.
Update: H5 h run in part (Edit menu and context-menu Clear History only).

## H5 g, second part (deleting the defining pair)

Settings: Document14 after Clear History (see H5 h), Radian, Fix 4 (inherited).
Keys: typed `a:=5`, Return, `a+1`, Return (6); Up three times (the result 5 of `a:=5` was selected, seen at half scale); PC Delete; then typed `a`, Return.
Observed: Delete removed the whole `a:=5` pair; the input `a+1` became selected. Then `a` gave 5: the variable a survives after the entry that defined it was deleted from the history. (The empty-history `ans` case is in H5 h: Undefined Ans error.) A text cursor was not needed to select the pair; Up was used, as clicking a history line only places a text cursor.
Screenshots: pages-shots-6/R5-H5g-defining-pair-deleted-a-plus-1-left.png, R5-H5g-a-still-5-after-defining-pair-deleted.png
Differs from CASSim or from this file's expectation? Not compared in this run.
Update: H5 g fully run.

## H3 b (triple-click), H3 g (clicks on a fraction), H3 h (blank area)

Settings: Document14, Radian, Fix 4 (inherited).
H3 b: triple-click on the input `a+1` highlighted the whole input; a double-click on the same input highlighted only the `+` (the earlier double-click row is in this file's H3 section). Half-scale screenshots only (not croppable): R5-H3b-triple-click-selects-whole-input-half.jpg, R5-H3b-double-click-selects-plus-sign-half.jpg. Nothing was brought down.
H3 h: with the `a+1` pair selected, a single click on the blank area below the entry line dropped the selection and placed the text cursor in the entry line (half scale only): R5-H3h-click-blank-below-entry-cursor-in-entry-half.jpg. A click above the first line was not run.
H3 g: entry `12/34+5` built with the fraction template (templates key, first icon, Return; typed `12`, Down, `34`, Right, `+5`). A click on the numerator between the 1 and the 2 put the cursor there (typed X gave `1X2`); a click on the fraction bar put the cursor in the denominator between the 3 and the 4 (typed Y gave `3Y4`); a click on the denominator between the 3 and the 4 put the cursor there (typed Z gave `3Z4`). Each typed letter was removed with BackSpace before the next click. The first two are zoomed screenshots (R5-H3g-click-numerator-cursor-in-numerator-zoom.jpg, R5-H3g-click-fraction-bar-cursor-in-denominator-zoom.jpg), the third is cropped (R5-H3g-click-denominator-cursor-in-denominator.png).
Differs from CASSim or from this file's expectation? Not compared in this run.
Update: H3 b triple-click, H3 g and H3 h (below the entry only) run.

## H3 f, wrapped-line part (a long entry in the entry line)

Settings: Document14, Radian, Fix 4 (inherited).
Keys: typed a 54-character sum of digit groups in chunks of 9 (`1111111+2222222+3333333+4444444+5555555+6666666+7777777+`), then a click at about x=800 in the entry line, typed `X`, BackSpace.
Observed: the entry line did not wrap onto a second line. The text scrolled sideways with a ◂ at the left edge (and a ▸ at the right edge once the cursor moved left). The click put the cursor in the text near the click point (typed X appeared inside the `4444444` group). So the "second line of a wrapped entry" case does not arise in the handheld view at this width. The Computer view was not tried for this row.
Screenshot: pages-shots-6/R5-H3f-long-entry-no-wrap-click-places-cursor.png
Differs from CASSim or from this file's expectation? Not compared in this run.
Update: H3 f wrapped-line part run (no wrapping seen).

## H6 a, second part (Newton with f(x) and derivative)

Settings: Document14, Radian, Fix 4 (inherited).
Keys: typed `f(x):=x^`, `2`, Right, `-2`, Return (Done); `1.5`, Return (1.5000); then typed `ans-f(ans)/derivative(f(x),x)|x=ans` in chunks (typed `f` and `derivative` letters, no autocomplete drop-down was seen), Return, and two empty Returns (waits 3 s).
Observed: the entry ran and each empty Return repeated it with the new answer. The history showed `1.4166666666667-f(...)/d/dx(f(x)) |x=1...` and `1.4142156862745-f(1.4142156862745)/d/dx(f(x)) |x=1...` with results 1.4142 each; the entry is drawn with a stacked fraction and the end of the `|x=` condition is cut off with ▸. Only the last two lines were cropped. The first result of the entry (1.4167) was not cropped.
Screenshot: pages-shots-6/R5-H6a-newton-with-f-and-derivative-repeats.png
Differs from CASSim or from this file's expectation? Not compared in this run.
Update: H6 a fully run (numeric and f(x) versions). H3 h "above the first line" not run; the lost `3` start in H6 c not investigated.

## H5 h, shift+Del (PC keyboard)

Settings: Document14, Radian, Fix 4 (inherited); history of the H6 a entries, entry line empty.
Keys: PC shift+Delete once, wait 2 s.
Observed: nothing visible changed (history and entry line the same; the keypad shift key was not lit). This was the PC keyboard chord, not the on-screen shift key then del, so it does not answer the keypad shift+del case.
Screenshot: pages-shots-6/R5-H5h-pc-shift-Delete-empty-line-no-change.png
Differs from CASSim or from this file's expectation? Not compared in this run.

## Hand-back addendum 6 (H3 to H6 pass)

Run on the emulator in this pass (each with a screenshot): H6 a (numeric and f(x) versions), H6 c and h (selected result only), H6 i (ans twice); H5 f, g (defining pair), h (Edit menu, context-menu Clear History, PC shift+Del), i, j; H3 b (triple-click), f (long entry, no wrapping), g (fraction clicks), h (below the entry).
Not run (reason): H5 h keypad shift+del, entry-line Clear History item, ctrl+Z after Clear History (not tried); H3 h above the first line (no blank area seen); H3 f in the Computer view (not tried); H6 c selected-input case and a clean `3` start (the typed 3 pair did not show; not investigated); H6 e `randInt` (not run in this pass).
Also seen, not covered: Edit menu items Page Layout ▶ and Color ▶ (not opened); Undo toolbar icon went grey after Clear History; PC Delete on a selected pair behaves as a delete (earlier note about PC Delete applied to an empty entry line only).
