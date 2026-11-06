# Emulator check: keyboard shortcuts and remaining editor gaps (S1 to S9)

Run on the TI-Nspire CX CAS Premium Teacher Software, Handheld page size, Radian, Automatic, Real, Float 8. One fresh page per test; a new Problem (Insert > Problem) was started each time the 50-page limit was reached. Observations only; nothing in the repo other than these results and `docs/testing/shortcut-shots/` was changed.

Screenshots are in `docs/testing/shortcut-shots/`, cropped to the handheld screen. Names follow `S<n>-<letter>-before.png` / `-after.png`. Where a test has more than two shots, or only one, the name carries a short suffix (for example `S1-h-typed.png`, `S2-ctrlEq-menu.png`).

## How keys were sent
- **Computer keyboard** (sent as key presses): ctrl+/, ctrl+Q, ctrl+L, ctrl+K, ctrl+H, ctrl+. , ctrl+space, ctrl+Return (approximate), ctrl+A, ctrl+Up, ctrl+C / X / V / Z / Y, ctrl+I, shift+Left, Tab, shift+Tab, alt+Return, shift+Return, shift+Escape, Escape, Backspace, shift+Backspace, Delete, shift+Delete, Home, the arrow keys.
- **On-screen keypad** (mouse clicks; ctrl and shift layers via the on-screen ctrl and shift keys): ctrl+÷ (fraction), ctrl+x² (square root), ctrl+^ (nth root), ctrl+10ˣ (log template), ctrl+eˣ (ln), ctrl+× (string), ctrl+( , ctrl+) , ctrl+= (menu), ctrl+(−) (Ans), ctrl+var (store arrow), ctrl+enter (approximate), ctrl+7 / 8 / 1 / 2 / 9 / 3, shift+− , shift++ , shift+÷, shift+del, enter, shift+enter, the EE key, the eˣ key, and the digits and letters used.
- **Typed text** (computer keyboard): `<=`, `/=`, `=>`, `@i`, `pi`, `infinity`, `5%`.
- Every key combination sent was accepted by the emulator; none was taken by the OS. Several simply did nothing in the emulator: those are marked "no visible effect", not guessed at.
- Timing quirk: a keypad click followed at once by typed text can be processed after the text (the EE key first landed after the `6`, giving `3.146ᴇ`). A short wait after each keypad click fixed it. Not a CAS behaviour.

## S1. Fraction template shortcuts

### S1 a: 12.5, ctrl+/, 3
Keys: 1 2 . 5 ctrl+/ 3 (computer keyboard)
Entry line (before Return): fraction with `12.5` on top, `3` in the denominator, cursor at the end of the denominator; S1-a-before.png
Result (after Return): `4.1666667`; S1-a-after.png
Matches docs/design/shortcuts.md? yes: ctrl+/ makes the fraction and takes the preceding term (the whole number 12.5).

### S1 b: 12.5, ctrl+÷ (keypad), 3
Keys: 1 2 . 5, keypad ctrl then ÷, 3
Entry line (before Return): same layout as (a); S1-b-before.png
Result (after Return): `4.1666667`, the same as (a); S1-b-after.png
Matches docs/design/shortcuts.md? yes: ctrl+÷ and ctrl+/ both give the fraction.

### S1 c: 2+3, ctrl+/, 4
Keys: 2 + 3 ctrl+/ 4 (computer keyboard; I typed `4` in the denominator)
Entry line (before Return): `2+` then a fraction `3` over `4`; only `3` was taken; cursor in the denominator; S1-c-before.png
Result (after Return): `11/4`; S1-c-after.png
Matches docs/design/shortcuts.md? yes: takes the preceding term, stops at `+`.

### S1 d: 2*3, ctrl+/, 4
Keys: 2 * 3 ctrl+/ 4 (computer keyboard)
Entry line (before Return): `2·3` over `4`; the whole product is the numerator; S1-d-before.png
Result (after Return): `3/2`; S1-d-after.png
Matches docs/design/shortcuts.md? yes: same as the palette, whole product on top.

### S1 e: (a+b), ctrl+/, 2
Keys: ( a + b ) ctrl+/ 2 (computer keyboard)
Entry line (before Return): `a+b` over `2`; the brackets are dropped; S1-e-before.png
Result (after Return): `a+b` over `2`; S1-e-after.png
Matches docs/design/shortcuts.md? yes (brackets dropped for a bare bracketed sum).

### S1 e2: (a+b)^2 [R], ctrl+/, c
Keys: ( a + b ) ^ 2 Right ctrl+/ c
Entry line (before Return): `(a+b)²` over `c`; brackets and power both kept; S1-e2-before.png
Result (after Return): `(a+b)²` over `c`; S1-e2-after.png
Matches docs/design/shortcuts.md? yes (nothing in the sheet to contradict; brackets are kept before a power).

### S1 f: ctrl+/ on an empty line
Keys: ctrl+/ (computer keyboard), then `3` in the numerator, Return
Entry line (before Return): an empty fraction, two empty boxes, cursor in the numerator; not `Ans`; S1-f-before.png
Result (after Return): with `3` over an empty box, a Syntax error dialog; S1-f-after.png
Matches docs/design/shortcuts.md? yes: empty numerator and denominator boxes.

### S1 g: 1, ctrl+/, 2, [R], ctrl+/, 3
Keys: 1 ctrl+/ 2 Right ctrl+/ 3
Entry line (before Return): the second ctrl+/ takes the whole first fraction as its numerator: (1/2) over 3; cursor in the lower denominator; S1-g-before.png
Result (after Return): `1/6`; S1-g-after.png
Matches docs/design/shortcuts.md? yes: nesting works, the previous fraction is absorbed.

### S1 h: select `ab` with shift+Left, ctrl+/
Keys: a b shift+Left shift+Left ctrl+/ then `9`
Entry line (before Return): `ab` is the numerator, the denominator is an empty box with the cursor in it; S1-h-before.png (just after ctrl+/), S1-h-typed.png (after typing 9)
Result (after Return): `ab/9`; S1-h-after.png
Matches docs/design/shortcuts.md? yes: a selection becomes the numerator.

## S2. Other template keys

Slots were filled with `a`, `b`, `c` (and `d`); `c` or `b` ended up outside the template where a template has fewer slots.

### S2 a: sqrt, keypad ctrl+x² (the `√` label)
Keys: keypad ctrl, then x²; a Tab b
Entry line (before Return): `√a` then `b` outside; the radicand slot is first and only; S2-sqrtkey-before.png
Result (after Return): `√a · b`; S2-sqrtkey-after.png
Matches docs/design/shortcuts.md? yes in effect, but the key is the x² key, not a letter "Q".

### S2 a2: computer ctrl+Q
Keys: ctrl+Q after `ab`
Entry line (before Return): `ab`, no template; S2-ctrlQ-before.png
Result (after Return): no visible effect, `ab` stays; S2-ctrlQ-after.png
Matches docs/design/shortcuts.md? no: ctrl+Q does nothing on the computer keyboard.

### S2 b: nth root, keypad ctrl+^
Keys: keypad ctrl, then ^; a Tab b Tab c
Entry line (before Return): index `a`, radicand `b`, then `c` outside; slot order index, radicand; S2-nthroot-before.png
Result (after Return): the CAS rewrites the root as a power in the result (shown as 1 over a power of b); S2-nthroot-after.png
Matches docs/design/shortcuts.md? differs on the key: it is the ^ key, not "ctrl+L".

### S2 b2: computer ctrl+L
Keys: ctrl+L on an empty line
Entry line (before Return): the variable list opens (f1 to f7 in this document); S2-ctrlL-before.png
Result (after Return): not run (menu open)
Matches docs/design/shortcuts.md? yes for the "Variable list" row; no for the nth-root row: on the computer ctrl+L is the variable list.

### S2 c: ctrl+× (keypad)
Keys: keypad ctrl, then ×
Entry line (before Return): a string template `" "` with an empty box between quotes; not a palette; S2-ctrlTimes-before.png
Result (after Return): not run
Matches docs/design/shortcuts.md? no: it gives the string (text) template, not the template palette.

### S2 d: ctrl+K (computer)
Keys: ctrl+K on an empty line
Entry line (before Return): nothing opens; S2-ctrlK-before.png
Result (after Return): not run
Matches docs/design/shortcuts.md? no: no symbol palette and no select-page effect was visible. The keypad ctrl+K was not tested.

### S2 e: derivative, keypad shift + −
Keys: keypad shift, then −; a Tab b Tab c
Entry line (before Return): `d/da (b)` then `c` outside; slot order: variable, then expression; S2-shiftMinus-before.png
Result (after Return): `d/da (b)·c` gives `0`; S2-shiftMinus-after.png
Matches docs/design/shortcuts.md? yes (derivative template).

### S2 f: integral, keypad shift + +
Keys: keypad shift, then +; a Tab b Tab c Tab d
Entry line (before Return): definite integral with lower limit `a`, upper limit `b`, integrand `c`, variable `d`; slot order lower, upper, integrand, variable; S2-shiftPlus-before.png
Result (after Return): `-(a-b)·c`; S2-shiftPlus-after.png
Matches docs/design/shortcuts.md? yes (definite integral template).

### S2 g: log, keypad ctrl+10ˣ
Keys: keypad ctrl, then 10ˣ; a Tab b
Entry line (before Return): `log` with subscript base `a` and argument `(b)`; S2-ctrlLog-before.png
Result (after Return): `log_a(b)`; S2-ctrlLog-after.png
Matches docs/design/shortcuts.md? differs: it is a base-and-argument template `log_a(b)`, not a bare `log( )`, and the key is 10ˣ.

### S2 h: ln, keypad ctrl+eˣ
Keys: keypad ctrl, then eˣ; a Tab b
Entry line (before Return): `ln(a)` then `b` outside; S2-ctrlLn-before.png
Result (after Return): `ln(a)·b`; S2-ctrlLn-after.png
Matches docs/design/shortcuts.md? yes (ln( ) on the eˣ key).

### S2 i: ctrl+( and ctrl+) (keypad)
Keys: keypad ctrl then ( , a Tab b; and keypad ctrl then ) , a Tab b
Entry line (before Return): ctrl+( gives `[a]b` (square brackets); ctrl+) gives `{a}b` (curly braces); S2-ctrlParen-before.png, S2-ctrlParenR-before.png
Result (after Return): after shots only; S2-ctrlParen-after.png, S2-ctrlParenR-after.png
Matches docs/design/shortcuts.md? yes.

### S2 j: ctrl+= (keypad)
Keys: x, keypad ctrl then =
Entry line (before Return): a menu opens: `> < ≠ ≥ ≤ |`; Down moves the selection; Return or a click inserts it; S2-ctrlEq-menu.png, S2-ctrlEq-afterDown.png, S2-ctrlEq-before.png
Result (after Return): `x>2`; S2-ctrlEq-after.png
Matches docs/design/shortcuts.md? yes: the six entries are `>`, `<`, `≠`, `≥`, `≤`, `|`.

### S2 k: shift+÷ (keypad), the `\` symbol
Keys: keypad shift, then ÷, `a`
Entry line (before Return): `\a`; S2-shiftDiv-before.png
Result (after Return): Syntax error; S2-shiftDiv-after.png
Matches docs/design/shortcuts.md? yes: it inserts a backslash (which the CAS cannot evaluate).

Computer keyboard also has: ctrl+/ (fraction), ctrl+L (variable list). The other S2 keys exist only on the keypad.

## S3. Ans, store and clear

### S3 a: ctrl+minus on an empty line (keypad ctrl then (−))
Entry line (before Return): `Ans` is inserted; S3-ctrlMinus-before.png
Result (after Return): result shown in S3-ctrlMinus-after.png
Matches docs/design/shortcuts.md? yes.

### S3 b: store arrow
Keys: keypad ctrl then var (the key shows `sto→` above it); also computer ctrl+H
Entry line (before Return): keypad: `→` is inserted; S3-store-keypad-before.png. Computer ctrl+H: no visible effect; S3-ctrlH-before.png
Result (after Return): see S3-store-keypad-after.png
Matches docs/design/shortcuts.md? yes for the keypad (ctrl+var, there is no "h" key); no for computer ctrl+H.

### S3 c: ctrl+. on a half-typed entry (computer)
Entry line (before Return): the entry stays as it is; S3-ctrlDot-before.png
Result (after Return): not cleared; S3-ctrlDot-after.png
Matches docs/design/shortcuts.md? no: "Clear entry" did not work.

### S3 d: a, ctrl+space, b
Keys: a ctrl+space b (computer keyboard; re-checked at the end of the run: `a_b`)
Entry line (before Return): `a_b`, an underscore between the letters; S3-ctrlSpace-before.png
Result (after Return): `a_b` evaluates as a name; S3-ctrlSpace-after.png
Matches docs/design/shortcuts.md? yes.

## S4. Approximate shortcut

### S4 a: 1/3 then ctrl+enter
Keys: `1` ctrl+/ `3` Right, then keypad ctrl and enter; and computer ctrl+Return
Entry line (before Return): `1/3` as a fraction template
Result (after Return): both give `0.33333333` in a new history row; the entry line is left empty; S4-keypad-after.png, S4-computer-after.png
Matches docs/design/shortcuts.md? yes for ctrl+enter and ctrl+Return. The keypad `ctrl+·` was not used for this (the keypad shows `≈` over enter).

## S5. Moving and selecting

### S5 a: 1+2+3 then ctrl+8, ctrl+2 (keypad)
Entry line: ctrl+8 puts the cursor at the start of the line, ctrl+2 at the end; S5-a-ctrl8.png, S5-a-ctrl2.png
Matches docs/design/shortcuts.md? yes (swapped label order in the sheet: 8 is start, 2 is end).

### S5 b: ctrl+7 and ctrl+1 (keypad) with several entries
Entry line: ctrl+7 selects the first history row; ctrl+1 had no visible effect; S5-b-ctrl7.png, S5-b-ctrl1.png
Matches docs/design/shortcuts.md? unsure/partly: ctrl+7 works as "first line"; ctrl+1 did not visibly go to the last line.

### S5 c: ctrl+9 and ctrl+3 on a long history (keypad)
Entry line: ctrl+9 scrolls the history up, ctrl+3 scrolls to the bottom; S5-c-ctrl9.png, S5-c-ctrl3.png
Matches docs/design/shortcuts.md? yes in effect (scroll the history).

### S5 d: 12 ctrl+/ 34, then shift+Left three times
Entry line: the whole fraction is selected; S5-d-before.png
Matches docs/design/shortcuts.md? yes (shift+arrows select; a template is selected as one unit).

### S5 e: a+b, ctrl+A, type 9
Entry line: ctrl+A selects the whole entry; typing `9` replaces it; S5-e-selected.png, S5-e-typed.png
Matches docs/design/shortcuts.md? yes.

### S5 f: Tab through the slots, then shift+Tab back
Entry line: Tab moves numerator, denominator, then out of the fraction to the right; shift+Tab reverses it exactly (back into the denominator, the numerator, then out to the left of the fraction); S5-f-TabTab.png, S5-f-shiftTab1.png, S5-f-shiftTab2.png, S5-f-shiftTab3.png
Matches docs/design/shortcuts.md? yes.

### S5 g: ctrl+Up (computer)
Entry line: the page sorter opens (the document hierarchy); S5-g-afterReturn.png shows the page after Return; S5-g-ctrlUp.png, S5-g-afterReturn.png
Matches docs/design/shortcuts.md? yes ("move up the document hierarchy").

### S5 h: Left from the start of a denominator
Keys: 1 ctrl+/ 2 [L] [L] (a letter typed to mark the cursor)
Entry line: one Left reaches the start of the denominator; the next Left leaves the fraction on the left, not to the end of the numerator; S5-h-L.png, S5-h-LL.png
Matches docs/design/shortcuts.md? not in the sheet (new observation).

## S6. Matrix rows and columns

### S6 a: 2x2 matrix, Return
Keys: insert 2x2 matrix from the palette; 1 Tab 2 Tab 3 Tab 4; Return (and keypad enter)
Entry line: Return and keypad enter do NOT add a row: they evaluate the matrix; S6-a-filled.png, S6-a-Return.png, S6-a-typed5.png, S6-a-Return2.png
Matches docs/design/shortcuts.md? no: "Return adds a row (hand)" is not what happens here.

### S6 b: alt+Return, shift+Return, keypad shift+enter
Entry line: alt+Return inserts a new row above the current one; shift+Return inserts a column to the left of the current cell; keypad shift+enter put the column to the right when the cursor was at the end of the cell. S6-b-altReturn.png, S6-b-typedx.png, S6-b-shiftReturn.png, S6-b-typedy.png, S6-b-Return.png, S6-b-keypadEnter-after.png, S6-b-keypadShiftEnter-after.png
Matches docs/design/shortcuts.md? yes for alt+Return and shift+Return/enter, with the placement detail above.

### S6 c: fraction in a matrix cell
Keys: `1` ctrl+/ `2` Right
Entry line: Right leaves the fraction and the cursor stays in the same cell; S6-c-fraction-in-cell.png, S6-c-fraction-in-cell-Right.png
Matches docs/design/shortcuts.md? not in the sheet.

### S6 d: m x n limits
Entry line: 10 by 10 is accepted; typing 100 in either field is clamped to 99; the maximum is 99 by 99; S6-d-10x10-dialog.png, S6-d-10x10-after.png, S6-d-100-dialog.png, S6-d-100-after.png, S6-d-clamp-rows.png, S6-d-clamp-cols.png
Matches docs/design/shortcuts.md? not in the sheet.

## S7. Copy, cut, paste, undo, redo

### S7 a: copy and paste a fraction
Keys: 1 ctrl+/ 2 Right, shift+Left to select, ctrl+C, clear, ctrl+V
Entry line: the pasted result is a stacked 2D fraction, not text; S7-a-selected.png, S7-a-cleared.png, S7-a-pasted.png, S7-a-after.png
Matches docs/design/shortcuts.md? yes.

### S7 b: ctrl+X, ctrl+Z, ctrl+Y, shift+Esc
Entry line: ctrl+X cuts the selected template; in my run ctrl+Z and ctrl+Y appeared to act on the document (page insert/remove), but Simon reports they act on the entry line (see the correction below); shift+Escape had no visible effect on the entry line; S7-b-cut.png, S7-b-ctrlZ.png, S7-b-ctrlY.png, S7-b-shiftEsc.png
Matches docs/design/shortcuts.md? my run was inconclusive for ctrl+Z, ctrl+Y (see the correction below); unsure for shift+Esc.

### S7 c: ctrl+Z after typing and after a template insert, with nothing to undo
Entry line: ctrl+Z and ctrl+Y were pressed after typing, after a template insert and with nothing to undo; I saw no entry-line undo, but see the correction below; S7-c-ctrlZ-empty.png, S7-c-ctrlZ-afterTyping.png, S7-c-template-ctrlZ.png, S7-c-template-ctrlZ2.png, S7-c-ctrlY.png, S7-c-shiftEsc.png
Matches docs/design/shortcuts.md? yes, per Simon's correction below.

**Correction (Simon) and retest:** ctrl+Z and ctrl+Y act on the entry line, and undo groups edits by operator. Retested on a fresh page (computer keyboard) with `ab+c`: ctrl+Z gives `ab+`, then `ab`, then an empty line (three steps: `c`, `+`, `ab`); ctrl+Y then restores `ab`, `ab+`, `ab+c`. Simon's description is confirmed. My earlier page-level observation in S7 b and c was wrong. S7-d-typed.png, S7-d-undo1.png, S7-d-undo2.png, S7-d-undo3.png, S7-d-redo1.png, S7-d-redo2.png, S7-d-redo3.png

## S8. Backspace, delete and Esc

### S8 a: forward delete
Keys, with the cursor between `a` and `b` in `ab`: computer Delete gives `a|` (the letter after the cursor goes); keypad shift then del gives `a|b` (no visible deletion); computer shift+Backspace acted as a plain Backspace (deleted `a`). In front of a fraction `3/4` at the start of the line: computer Delete selects the whole fraction (highlight; I did not press a second Delete); keypad shift+del leaves the fraction unchanged. In a numerator `12/34` (cursor after the 1): computer Delete deletes the 2. Shots: S8-a-Delete-letter.png, S8-a-shiftDel-letter.png, S8-b-shiftBS-computer-between.png, S8-a-Delete-beforeTemplate.png, S8-a-shiftDel-beforeTemplate.png, S8-a-Delete-inNumerator.png
Matches docs/design/shortcuts.md? not in the sheet (Delete works on the computer keyboard; keypad shift+del did nothing visible here).

### S8 b: clearing a half-typed entry
Keys: Escape on `abc`; keypad shift then del (labelled `clear`); computer shift+Delete; ctrl+A then Backspace.
Result: Escape leaves `abc`; keypad shift+del and computer shift+Delete leave `abc`; ctrl+A then Backspace clears the line (checked on the earlier page). So the only key combination that clears a line is ctrl+A, Backspace. S8-c-Esc-after.png, S8-c-keypadShiftDel-clear.png, S8-c-shiftDelete-computer.png
Matches docs/design/shortcuts.md? no for ctrl+. (see S3 c).

### S8 c: Backspace at the start, in an empty exponent, in an empty radicand
Result: Backspace at the start of the line does nothing; `x^` then Backspace removes the empty exponent and leaves `x`, a second Backspace removes `x`; the empty square-root template is removed by one Backspace and a second does nothing. S8-d-BS-at-start.png, S8-e-BS-empty-exponent-1.png, S8-e-BS-empty-exponent-2.png, S8-f-BS-empty-radicand-1.png, S8-f-BS-empty-radicand-2.png

## S9. Symbols

### S9 a: 3.14 EE 6
Keys: 3 . 1 4, keypad EE key, 6
Entry line (before Return): `3.14ᴇ6`, the `ᴇ` drawn as a small capital E at line height; S9-a-before.png
Result (after Return): `3140000.`; S9-a-after.png

### S9 b: 5%
Keys: 5 % (typed)
Entry line (before Return): `5%`; S9-b-before.png
Result (after Return): `1/20`; S9-b-after.png

### S9 c: x≤2
Keys: typed `x<=2`; and keypad ctrl+= then ≤ chosen from the menu, then 2
Entry line (before Return): typed form shows `x<=2`; menu form shows `x≤2`; S9-c-before.png, S9-c2-menu.png, S9-c2-before.png
Result (after Return): `x≤2` both ways; S9-c-after.png, S9-c2-after.png

### S9 d: x≠2
Keys: typed `x/=2`
Entry line (before Return): `x/=2`; S9-d-before.png
Result (after Return): `x≠2`; S9-d-after.png

### S9 e: a=>b
Keys: typed `a=>b`
Entry line (before Return): `a=>b`; S9-e-before.png
Result (after Return): `a ⇒ b` in the entry; the answer is `not a or b`; S9-e-after.png

### S9 f: ⅇ through the keypad eˣ key
Keys: keypad eˣ, then `1`
Entry line (before Return): bold `e` with a superscript slot holding 1; S9-f-before.png
Result (after Return): bold `e` (ⅇ); S9-f-after.png

### S9 g: ⅈ through typed `@i`
Entry line (before Return): `@i` as typed; S9-g-before.png
Result (after Return): bold italic `i` (ⅈ); S9-g-after.png

### S9 h: π through typed `pi`
Entry line (before Return): `pi` as typed letters; S9-h-before.png
Result (after Return): `π`; S9-h-after.png

### S9 i: ∞ through typed `infinity`
Entry line (before Return): `infinity` as typed letters; S9-i-before.png
Result (after Return): `∞`; S9-i-after.png

## Every row of docs/design/shortcuts.md

| Section | Keys | Result | Notes |
|---|---|---|---|
| 1 | ctrl+/ (ctrl+÷) | **confirmed** | Both give the fraction (S1). |
| 1 | ctrl+Q | **differs** | Keypad: ctrl+x² gives the sqrt template; computer ctrl+Q no visible effect (S2 a). |
| 1 | ctrl+L (nth root) | **differs** | Keypad ctrl+^ gives the nth root; computer ctrl+L opens the variable list (S2 b). |
| 1 | shift+minus | **confirmed** | Derivative template, slots variable then expression. |
| 1 | shift+plus | **confirmed** | Definite integral, slots lower, upper, integrand, variable. |
| 1 | ctrl+* (palette) | **differs** | Gives the string template `" "`. |
| 1 | ctrl+K (symbol palette) | **differs** | Computer ctrl+K no visible effect; keypad not tested. |
| 1 | ctrl+( , ctrl+) | **confirmed** | `[ ]` and `{ }`. |
| 1 | ctrl+= | **confirmed** | Menu `> < ≠ ≥ ≤ \|`. |
| 1 | ctrl+S (keypad) log( ) | **differs** | Key is ctrl+10ˣ; gives `log_a(b)` with a base slot. |
| 1 | ctrl+U (keypad) ln( ) | **confirmed** | Key is ctrl+eˣ. |
| 1 | ctrl+minus (keypad) Ans | **confirmed** | |
| 1 | ctrl+h / ctrl+Ë store arrow | **confirmed** | Keypad ctrl+var inserts `→`; computer ctrl+H no visible effect. |
| 1 | ctrl+space | **confirmed** | Underscore. |
| 1 | ctrl+· approximate | **differs** | The key is ctrl+enter (keypad) and ctrl+Return (computer); ctrl+· not used. |
| 1 | ctrl+. clear entry | **differs** | No visible effect. |
| 1 | shift+/ backslash | **confirmed** | Keypad shift+÷ gives `\`. |
| 2 | Tab | **confirmed** | S5 f. |
| 2 | shift+Tab | **confirmed** | Exact reverse of Tab. |
| 2 | shift+arrows | **confirmed** | S5 d: the template is selected as a unit. |
| 2 | ctrl+A | **confirmed** | Select all; typing replaces. |
| 2 | ctrl+7 / ctrl+8 | **confirmed** | ctrl+7 selects the first history row; ctrl+8 start of line. |
| 2 | ctrl+1 / ctrl+2 | **differs** | ctrl+2 end of line; ctrl+1 had no visible effect. |
| 2 | ctrl+3 / ctrl+9 | **confirmed** | Scroll the history (3 to the bottom). |
| 2 | ctrl+up | **confirmed** | Opens the page sorter. |
| 2 | Up on an empty line | **not tested** | Confirmed in the first run (T4d). |
| 3 | Return in a matrix | **differs** | Evaluates; does not add a row. |
| 3 | alt+Enter | **confirmed** | Adds a row above. |
| 3 | shift+Return | **confirmed** | Adds a column to the left. |
| 3 | shift+Enter | **confirmed** | Keypad: column to the right at the end of a cell. |
| 3 | Tab | **not tested** | Confirmed in the first run (T8b). |
| 4 | ctrl+C, ctrl+X, ctrl+V | **confirmed** | Paste keeps the 2D template. |
| 4 | ctrl+Z, ctrl+Y | **confirmed** | Entry-line undo/redo, grouped by operator (`ab+c` = 3 steps). Retested: undo gives `ab+`, `ab`, empty; redo restores them (S7-d). |
| 4 | shift+Esc | **not tested** | Pressed; no visible effect, so no conclusion. |
| 4 | ctrl+I | **confirmed** | Used to add every page in this run. |
| 4 | ctrl+N, ctrl+O, ctrl+S, ctrl+W | **not tested** | |
| 4 | ctrl+L | **confirmed** | Variable list (computer). |
| 4 | ctrl+R, ctrl+G, ctrl+T, ctrl+M, ctrl+E | **not tested** | |
| 4 | ctrl+F, ctrl+H; ctrl+B, ctrl+R | **not tested** | Program editor. |
| 4 | ctrl+4, ctrl+6, ctrl+K, ctrl+Tab | **not tested** | ctrl+K alone: see section 1. |
| 5 | Typed spellings | **confirmed** for `pi`, `infinity`, `<=`, `/=`, `=>`, `@i`; **not tested** for the rest | See S9. |
| 6 | Handheld key combinations | **confirmed** | Keypad ctrl and shift layers worked; the table must use the keypad labels (x², ^, 10ˣ, eˣ, ×, var, enter, (−), ÷), not letters. |

## Anything else noticed
- A bare `Delete` key works on the computer keyboard; the keypad's shift+del (label "clear") did nothing visible.
- The only way found to clear an entry is ctrl+A then Backspace.
- ctrl+Z / ctrl+Y: Simon says they act on the entry line, grouped by operator (`ab+c` is 3 undo steps). Retested and confirmed (S7-d); my first S7 reading was wrong.
- Scientific notation: `1@E5` is scientific notation; typing the letters `1EE5` is not. The keypad EE key inserts the `ᴇ` form (S9 a).
- Return and keypad enter in a matrix evaluate it instead of adding a row; rows and columns come from alt+Return and shift+Return.
- The ctrl+(−) `Ans` and ctrl+var `→` keys need the keypad; their computer equivalents did nothing.
- The matrix dialog is limited to 99 by 99.
- The Create-a-Matrix dialog is not closed by Escape (use Cancel); a keyboard shortcut sent while it is open gives a Windows "Close any open dialogs" message.
- A keypad click followed at once by typed text can reorder the two (see EE).

## What was run and what was not
Run: S1 a to h (including e2), S2 a to k, S3 a to d, S4, S5 a to h, S6 a to d, S7 a to c, S8 a to c, S9 a to i.
Not run: ctrl+K on the keypad; ctrl+N, O, S, W, R, G, T, M, E, F, H, B, 4, 6, Tab; the typed spellings not listed in S9; the second Delete on a selected template; keypad `ctrl+·` for approximate.
