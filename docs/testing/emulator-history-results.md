# Emulator check 3: results (history area, undo, bring-down, delete, Ans repeat)

Run: 2026-11-10, TI-Nspire CX CAS Premium Teacher Software, OS version as installed on Simon's computer. Handheld-page-size document (Document3), with a second Computer-page-size document (Document4) for the layout comparison.
Settings used: Document Settings opened first and confirmed as **Float 8, Radian, Exponential Normal, Real, Auto, CAS On** (they were already these; title bar says RAD). The Computer-size document was not re-opened in Document Settings; it showed RAD and Float-8-style results.
Method: computer keyboard via the automation tool, plus a few clicks on the on-screen keypad `del` key. Marker letter `q` used to find the cursor where it mattered. Screenshots are `docs/testing/history-shots/H<n>-<letter>-<step>.png`, cropped to the screen (the full-screenshot ones for H9 are cropped to the page area).

**Honest limits of this run**
- Only part of the suite was run (see "Not run" at the end). Priority tests H1, H4, H5, H6 were run in the main; H2, H9 partly; H7, H3, H8 mostly not.
- The on-screen keypad was used only for `del` (H5 c). The ctrl and shift layers of the keypad were **not** tested, so H1 k is not answered.
- Screenshots were taken *after* each key press and sometimes the first frame caught the screen mid-redraw; where a before/after pair is missing it is stated. Not every row has both a before and an after file.
- One batch of keys was swallowed by an error dialog (see "Also seen"); the tests affected were repeated.
- Several earlier documents (Document1, Document2) were opened by the launch attempts and are empty.

Entries E1, E2, E3 are as in the task (`2+3`, `expand((x+2)^2,x)`, `solve(x^2=2,x)`). Typed with `^2` then Right.

---

## H1. Undo and redo around an evaluation

### H1 a: E1, Return, ctrl+Z
Keys: computer keyboard: 2 + 3 [Ret] [ctrl+Z]
Before: Add Calculator page 1.1 with one pair `2+3` / `5` (one row, result at the right edge), empty entry line; H1-a-1.png
After: the pair disappears; `2+3` is back in the entry line with the cursor at its **end**; nothing in history; H1-a-2.png
Matches CASSim (built 5)? **no**: CASSim says ctrl+Z does not undo an evaluation; the emulator does.

### H1 b: after (a), ctrl+Z again
Keys: ctrl+Z x4
After each press: (1) `2+` (2) `2` (3) empty entry line (4) **the Add Calculator application is removed**, page shows "Press menu". So typing `2+3` is **three** undo steps (digit, operator, digit), then an empty entry line, and the fourth press undoes the creation of the calculator page itself (undo crosses page creation). Screenshots H1-b-1 to H1-b-4.
Matches CASSim? no (CASSim stops at the entry line; undo history here includes page creation).

### H1 c: redo
Keys: from the "Press menu" page (state after b), ctrl+Y x5. The redo chain is the exact mirror: (1) calculator page back, empty (2) `2` (3) `2+` (4) `2+3` (5) the evaluation: pair `2+3` / `5` is back and the entry line is empty. So at the stage "after (a)" (input `2+3` in the entry line) one ctrl+Y re-evaluates it and the result returns. Screenshots H1-c-1 to H1-c-5.
Matches CASSim? no (redo of an evaluation exists).

### H1 d: E1, E2, E3 then ctrl+Z x3
Before: three pairs; H1-d-1.png (also shows the layout: each pair on one row when short, banded shading).
After 1st ctrl+Z: E3's input returns to the entry line (E3 pair gone, E1 and E2 stay). After the 2nd and 3rd press the entry line loses `)` and then `x`: `solve(x²=2,x)` becomes `solve(x²=2,x` then `solve(x²=2,`. So the entries are not restored three at a time: the **first press undoes the last evaluation, later presses undo the typing of that entry** one token at a time (here a closing bracket and a letter are single steps, unlike the operator grouping in S7). H1-d-2 to H1-d-4.
Matches CASSim? no.

### H1 e: `5` then ctrl+Z, ctrl+Y
`5` typed; ctrl+Z gives an empty entry line; ctrl+Y gives `5` back. Two more ctrl+Z: empty, then page 1.3 loses its calculator ("Press menu"). H1-e-1 to H1-e-4.
Matches CASSim? partly (typing undo yes; but undo also goes past typing to page creation).

### H1 f: store then undo
Keys: `5→a` [Ret], `a` [Ret], ctrl+Z, ctrl+Z, then `a` [Ret]. Typed the arrow with `→`.
After the two ctrl+Z the second pair is gone and the entry line is empty; then `a` gives `5`. A further test went back one more step (undo the `5→a` evaluation: `5→a` returns to the entry line, shown with the `a` in bold), cleared the line and typed `a` [Ret]: the answer was still **5**.
So **undoing an evaluation does not undo a store**; the variable keeps its value. H1-f-1 to H1-f-4.
Matches CASSim? unsure (CASSim has no undo of evaluations to compare).

### H1 g: Ans after undo
Keys: `2+3` [Ret], `ans*2` [Ret], ctrl+Z, [Ret].
The history shows the second entry as `5·2` (not `ans·2`): **`ans` is replaced by its value in the history line**. ctrl+Z returned `5·2` (the literal value) to the entry line, not `ans*2`. Return evaluated it to `10`. A further empty [Ret] added a new pair `5·2` / `10`. H1-g-1 to H1-g-4.
Matches CASSim (built 6)? no: CASSim keeps `Ans` visible; the emulator shows the value.

### H1 h: delete a pair, then ctrl+Z
After deleting a pair with BackSpace (see H5), ctrl+Z restores the deleted pair (selection back on its input in the history); a second ctrl+Z undoes the evaluation of the line above and returns its input to the entry line. H1-h-1 to H1-h-3.
Matches CASSim? no.

### H1 i, l, m, k: **not run**
(i) undo across pages: only seen that undo can remove the creation of a page (b, e); leaving and returning not tested. (l) limit not tested. (m) Edit menu not looked at. (k) keypad ctrl/shift undo keys not tested.

### H1 j: undo after an error
An evaluation that gave the dialog "Error: Argument must be an expression." was undone with ctrl+Z (the entry returned to the entry line) and ctrl+Y re-ran it and **showed the error dialog again**. After OK the history keeps the entry with the result text `"Error: Argument must be an expression."` in quotes. H1-j-1, H1-j-2.
Matches CASSim? unsure.

---

## H2. Selecting history lines (keyboard) (partly run)

### H2 a: Up from an empty entry line on E1..E3
Keys: Up x1, x2, x3. Order: **E3 result, E3 input, E2 result** (result then entry for each pair, bottom up). The highlight is a light-blue box around **the item only** (the text), not the row; the pair layout does not change. H2-a-1 to H2-a-3.
Matches CASSim (built 1)? **confirmed.**

### H2 b: Down
Down moves back toward the entry line; one more Down from the last pair's result returns to the entry line (cursor shown in an empty entry line); Down on the entry line itself: nothing visible. Confirmed by zoom series (not saved).

### H2 c (some): ctrl+7, ctrl+1, Home, End with a line selected
ctrl+7 selects the first history row (`2+3`). ctrl+1 moves to the **entry line** (the last line), with a cursor in it: this is the "re-test ctrl+1" answer. Home selects the first row's input (`2+3`) (it does not go to the start of the selected line). End: no visible effect. ctrl+9 and ctrl+3 not tested.

### H2 d, e, i: Left/Right/shift+arrows inside a line
With the E2 result `x²+4·x+4` selected: Left puts the cursor at the **start** of the line (before `x`); Right then steps **one character at a time and enters the exponent** (after `x`, then inside the `²`, after it, then past it before `+`). shift+Right selects one character at a time: `+`, then `4`, then `·`, `x` ... So the unit is a character (with the exponent as its own level), not a term, and a partial selection `+4·x` is possible. Highlight shown in H4-f-1.png. Matches CASSim (built 2)? **confirmed** (cursor/selection inside a line).
Home with a *history line* selected jumped to the first row of the page, so Home/End are not "start/end of this line" there.

### H2 f: Esc
Esc deselects the line and returns to the entry line (empty, cursor visible). Confirmed.

### H2 g: type `q` with a line selected
Nothing visible happened: `q` did not appear in the entry line and the selection stayed. (Tab and shift+Tab: after the sequence the screen state was not clean enough to say; **not answered**.)

### H2 k: ctrl+A
With a history input selected, ctrl+A leaves that line selected (no multi-line selection); ctrl+A then BackSpace deleted that pair.

### H2 l: Up at the oldest line
Stops on the first entry; does not wrap.

### H2 j: **not run** (no wrapped-result scrolling test)

---

## H3. The mouse: **not run**
Only clicks on keypad keys and dialog OK were used. A click on a blank part of the keypad panel made the emulator window take focus again (a point for whoever repeats this).

---

## H4. Bring-down (Enter on a selected line)

### H4 a: select the input, Return
E1 pair. Up, Up selected the input `2+3`; Return: `2+3` is **inserted into the empty entry line, not evaluated**, cursor at the end (marker `q` landed after it); the history selection is cleared. H4-a-1 (result selected), H4-a-2 (input selected), H4-a-3 (after Return, with `q`).
Matches CASSim (built 2)? **confirmed.**

### H4 b: select the result `5`, Return
`5` is inserted into the entry line; cursor after it. H4-b-1.png.

### H4 c: entry `7*`, select result `5`, Return
Up on a **non-empty one-line entry** selects the last result. Return gives `7·5` with the cursor after the `5` (it is inserted **at the cursor**, not replacing). H4-c-1, H4-c-2.

### H4 d: cursor between `a` and `bc`
Bring down `5` gives `a5|bc`: **inserted at the cursor position**. H4-d-1.

### H4 e: entry has a selection
With `bc` selected (shift+Left x2) the bring-down **replaces** the selection: `a5q`. H4-e-1, H4-e-2.

### H4 f: part of a 2D result
From the E2 result `x²+4·x+4` a selection of `+4·x` (shift+Right x4 after leaving the exponent) was brought down: only the selection arrives: `+4·x`, as ordinary text in the entry line. Bringing the whole result down gives `x²+4·x+4` **with the exponent as a superscript** (2D form kept). H4-f-1, H4-f-2.

### H4 g: whole of E3's result
`x=−√2 or x=√2` arrives with the real √ templates and the word `or` as text. H4-g-1.

### H4 h: input with a fraction, power and root
`(x^2)/(sqrt(3)+1)` entered; after Return it is shown as a stacked fraction in the history (brackets dropped). Bring-down of the input returns the **2D fraction** (x² over √3 + 1). H4-h-1.

### H4 i: list and matrix
`{1,2,3}` and `[1,2;3,4]` brought down in the same 2D form (list in braces, matrix as a 2×2 matrix). H4-i-1, H4-i-2.

### H4 j: decimal and exact
`approx(π)` result `3.1415927` (Float 8 shown) was brought down as **`3.1415926535898`**: more digits than displayed (about 14, not the displayed 8). `√2/2` stays exact in 2D. H4-j-1, H4-j-2.

### H4 k, l, m, n, o: **not run**
(k ctrl+C vs bring-down, l ctrl+Enter on a selected line, m `+` first, n repeated bring-down, o Return after bring-down — the last is partly seen in H6 c: bringing `6` down and pressing Return evaluated it as a new pair `6` / `6`.)

---

## H5. Del, Backspace and clearing

### H5 a: Del on an input; Backspace on another
Select E2's input, Del (the Delete key): the **whole pair (entry and result)** is removed and the selection moves to the next pair's input. Backspace on a selected line did the same for that pair. H5-a-1 to H5-a-3.
Matches CASSim (built 3, first half)? **confirmed.**

### H5 b: Del on a result
Selecting the result `x=−√2 or x=√2` and pressing Del removed the whole pair; a result cannot be deleted on its own. H5-b-1, H5-b-2.

### H5 c: Del / Backspace / shift+Del on an EMPTY entry line
**Nothing happens** with the Delete key, Backspace, shift+Delete, and a click on the on-screen `del` key: the history is unchanged and the entry line stays empty. **This does not reproduce the behaviour Simon described** (delete the last output and put the last input back with the cursor at its end). The equivalent in this emulator is ctrl+Z (H1 a). H5-c-1 to H5-c-5.
Matches CASSim (built 3, second half)? **differs.**

### H5 d, f, j: **not run**
### H5 e: multi-select
shift+Up with a result selected did **not** extend the selection (still one item). Multi-delete not possible this way. H5-e-1.

### H5 g: Ans after deleting pairs
After deleting the last two pairs of a page (results `56`, `25`), `ans` evaluated to `5`, the result of the last remaining pair: **`Ans` follows the remaining history**. Variables set by a deleted entry were not tested. H5-g-1.

### H5 h: clearing: **not run**

### H5 i: ctrl+Z after Del
Restores the deleted pair (see H1 h). H5-i-1, H5-i-2 (the keypad `del` click deleting a pair is also shown there).

### Note on the Delete key
The forward Delete key deleted a pair twice, then **did nothing** on the result `25` of a one-line pair, while Backspace and the keypad `del` always worked. The cause is not known (focus, or a real difference). Treat the Delete key as unreliable in this run and use Backspace/`del` as the confirmed keys.

---

## H6. Repeating an entry that uses `Ans`

### H6 a: Newton's method (Simon's version)
Entries: `f(x):=x^2-2` [Done], `df(x):=derivative(f(x),x)` [Done; displayed as d/dx(f(x))], `1.0` (shown `1.`), `ans-f(ans)/df(ans)` then **empty Return x5**. Results as shown (Float 8): **1.5, 1.4166667, 1.4142157, 1.4142136, 1.4142136**. It reaches 1.4142136 on the 4th press; the 5th press gives the same value to 8 digits (so five presses confirm convergence). In the history each line is shown with the **full-precision previous value in place of `ans`**: `1.-f(1.)/df(1.)`, `1.5-f(1.5)/df(1.5)`, `1.4166666666667-f(1.4166666666667)/df(1.4166666666667)` (14 digits), and so on; a long input line puts the result on its own line at the right. H6-a-1 to H6-a-6.
Matches CASSim (built 4)? **confirmed** (empty Return repeats and uses the new Ans each time). The version with `|x=ans` was not run.

### H6 b: counter
`3` [Ret], `ans+1` [Ret], [Ret], [Ret]: results 3, 4, 5, 6. Lines show `3+1`, `4+1`, `5+1`. H6-b-1.
### H6 c: Up then Return
Up selects the last **result** (`6`), Return **brings it down** into the entry line (no evaluation); a second Return evaluates it as a new pair `6` / `6`. This is **not** the same as an empty Return (which would have given 7). H6-c-1, H6-c-2.
### H6 d: no `Ans` in the entry
`2+3` [Ret], [Ret]: the entry is repeated and a **second pair `2+3` / `5` is added**. So the rule is "empty Return repeats the last entry", with or without `Ans`.
Matches CASSim (built 4: "otherwise nothing")? **differs.** H6-d-1.
### H6 e: random
`randInt(1,6)` [Ret] then four empty Returns gave 6, 6, 1, 4: it **re-runs**. H6-e-1.
### H6 f: ctrl+Enter on the empty line
After `5`, `ans+1`: ctrl+Enter on the empty line added a pair `6+1` / **`7.`** (decimal point: an approximate value, using the previous result). H6-f-1.
Matches CASSim (assumption)? **confirmed.**
### H6 g: `+1` typed on an empty line
`+1` becomes `Ans+1` in the entry line; Return gave `7.+1` / `8.`; an empty Return then gave `8.+1` / `9.` (repeat; stays decimal). H6-g-1, H6-g-2.
### H6 h: select then Return
With a line selected, Return brings down (see H6 c and H4); empty entry plus nothing selected means repeat. Confirmed.
### H6 i: `Ans` inside a function call
`f(ans)` worked as above (a).

---

## H7. Entry line editing: **mostly not run**
- `5)` [Ret]: the stray `)` is accepted and evaluated as `5` (no error).
- `sin(` auto-close and bracket completion, wrap, symbol rewriting, autocomplete, `:` statements: not run. Seen incidentally: `pi` becomes `π`, `sqrt(2)/2` is displayed as a stacked fraction with a √ in the history; the entry `(x^2)/(sqrt(3)+1)` loses its outer brackets; `ans` is replaced by its value; `1.0` is shown as `1.`.

## H8. Remaining shortcut gaps: partly seen under H2 c (ctrl+1, ctrl+7, Home/End); shift+Esc, ctrl+. , ctrl+K/H/J, ctrl+B/R/G/T and the keypad legends not run.

---

## H9. Layout rules of the history area

### Handheld view
- Short input and short result (`2+3` / `5`): **one row**, result at the right edge. 2D results (E2, E3) also sit on the one row beside a short input. H1-d-1, H2-a-1.
- Pairs are separated by **alternating light-grey banding** (every other pair shaded), not by a drawn rule. No thin line was seen between pairs.
- Selection highlight: light blue box around the **item only**, small padding.
- Long input: the input is **cut off at the right edge with a small ▸ marker** (not wrapped), and the result goes on its own line, right aligned, below. In the handheld view about 33 characters of `1+2+3+...` showed before the marker (H9-handheld-1.png). A long **fraction** entry (Newton lines) is drawn 2D and the result is moved under it, right aligned (H6-a-4 to H6-a-6).
- Warning triangle, scroll threshold, and Float/Fix on earlier lines: **not tested**.

### Computer view (Computer-page-size document)
- Same rules, wider: one row for short pairs, banding, result at the far right. A 50-term and a 30-term sum were typed: both inputs are truncated with the ▸ marker at the right edge (about 65 characters shown), results `465` and `1275` on their own line at the right. H9-computer-1, H9-computer-2.
- The on-screen menu key did not respond in the Computer-size document in an earlier run (skill note); this time keys and a click on the page menu worked (Add Calculator chosen by a click).

Not measured: pixel spacings, colours, the exact threshold at which a pair stops sharing a row (only that a ~30-character input with a 3-digit result put the result on its own line in the handheld view), the scroll point.

---

## Built list (CASSim today) against the emulator

| # | Built | Result |
|---|---|---|
| 1 | Up/Down walk history, result then entry; highlight behind the item only | **confirmed** |
| 2 | Left/Right/Home/End/shift inside a line; Enter brings down the selected part or the whole line; click selects whole line | **confirmed** for keys and bring-down (character unit, inserted at cursor, replaces a selection). Home with a line selected jumps to the first row instead (differs). Mouse clicks **not tested**. |
| 3 | Del/Backspace on a selected line deletes the pair; on an empty entry line deletes last result and restores input | selected line **confirmed**; empty entry line **differs** (nothing happens) |
| 4 | Empty Enter repeats the last entry if it has `Ans`, otherwise nothing | `Ans` case **confirmed**; otherwise **differs** (repeats any entry; random entries re-run) |
| 5 | ctrl+Z / ctrl+Y undo typing only, not evaluations; keypad has no ctrl+Z | **differs**: undo/redo cross evaluations, errors, deletes and even page creation; stores are not undone. Keypad not tested |
| 6 | Enter closes brackets; entry shown with π, ∞, √, ⅇ; operator-first gets `Ans` | `π`, √ template and `Ans` insertion **confirmed**; bracket closing not tested; **new**: `ans` is replaced by its value in the history; a stray `)` is ignored |
| 7 | ctrl+C/X/V | **not tested** (ctrl+V not used) |
| 8 | Input and result share one line when short; thin rule separates pairs; scroll at ~3/4 | one line **confirmed**; **differs** on the separator (banding, no rule); scroll **not tested**; long inputs truncate with ▸ |

## Also seen, not covered by any test
- Undo history includes page creation (the Add Calculator page can be undone and redone).
- `ans` in a history line is replaced by the value (full precision, not Float 8): the entry that is restored by undo or brought down contains the number.
- An error shows a modal dialog; after OK the history keeps the entry with the error text as a quoted string result.
- Entries that include `:=` show "Done" in the result column; `df(x):=derivative(f(x),x)` is displayed as d/dx(f(x)).
- Keys sent while Claude's own window had focus were dropped; the tool does not always say so. A pending modal dialog silently swallows later keys.
- ctrl+1 moves to the entry line (the "last line").

## Tests run on the emulator
H1 a–h, j; H2 a, b, d, e (partly), f, g, k, l, c (ctrl+7, ctrl+1, Home, End); H4 a–j; H5 a, b, c, e, g, i; H6 a–i; H9 (partly, both views); H7 (one row).
## Not run
H1 i, k, l, m; H2 c (ctrl+9, ctrl+3), h, j; all of H3; H4 k–o; H5 d, f, h, j; H7 a–c, e–l; H8 b–f; H9 b, c, e–i (thresholds, spacing, colours, scrolling, warning triangle, Float/Fix).
