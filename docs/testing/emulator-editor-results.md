# Emulator check: how the TI-Nspire 2D entry editor behaves

Run on the TI-Nspire CX CAS Premium Teacher Software (Handheld page size, OS 6.0.3.374) on Simon's computer, driven by computer use. Observations only; nothing has been tidied to match the "built" column.

## Setup and method
- Document Settings set first: Angle **Radian**, Calculation Mode **Automatic**, Real or Complex **Real**, Display Digits **Float 8**. The title bar shows RAD in every screenshot; results such as `0.33333333` are consistent with Float 8.
- A fresh Calculator page per test (ctrl+i, then 1). The emulator allows only **50 pages per problem**, so the run continued in Problem 2 and then Problem 3 (page numbers in the screenshots are 1.x, 2.x, 3.x).
- Cursor: it shows as a thin vertical bar in the screenshots, so no marker was needed. A marker letter (`q`, `r`) was used only in T10a (Home/End).
- Screenshots are cropped to the handheld screen, in `docs/testing/editor-shots/`. Names are `T<number>-<letter>-before.png` (entry line before Return) and `-after.png` (after Return). Extra suffixes are used where a test has more than one view: `-tpl-` is the same test entered with the **fraction template from the palette** instead of the typed `/`; `-Tab`, `-Right`, etc. name the key pressed for slot-movement shots.
- **Key finding that affects every T1 and T2 row:** on this emulator the typed `/` key and the keypad ÷ key produce a **linear** `a/b` in the entry line (no 2D fraction while editing). The line is pretty-printed as a stacked fraction only in the history after Return. A true stacked fraction in the entry line comes only from the **Templates palette** (key at the keypad row 4, left of the "(" key area; screenshot `T7-palette.png`). Both routes were run for T1; the typed route is the base row, the template route is marked "template".
- Keypad quirk: the on-screen key click is unreliable inside the palette (it often only highlights). Reliable method used: click the template key, wait 1 s, press Up twice then Left twelve times (to reach item 1), then Right/Down to the item, then Return. The palette highlight starts on the last item used.

## T1. What does `/` take as the numerator?

### T1 a: 1/3
Keys: 1 / 3
Entry line (before Return): linear text `1/3`, cursor at end; `T1-a-before.png`. Keypad ÷ gives the same (`T1-a-div-before.png`).
Result (after Return): stacked fraction 1 over 3 in history, result column shows 1 over 3; `T1-a-after.png`.
Matches the current editor? no — the typed `/` stays linear while editing; only the template (and the history echo) is stacked.

### T1 b: 12.5/3
Entry line (before Return): typed: linear `12.5/3`. Template: `12.5` on top, `3` below, cursor in the denominator; `T1-b-before.png`, `T1-b-tpl-before.png`.
Result (after Return): `12.5` over `3`, result `4.1666667`; `T1-b-after.png`.
Matches the current editor? yes (template) — the whole decimal number goes on top.

### T1 c: x/y
Entry line (before Return): typed: linear `x/y`. Template: `x` over `y`; `T1-c-before.png`, `T1-c-tpl-before.png`.
Result (after Return): `x` over `y`; `T1-c-after.png`.
Matches the current editor? yes (template).

### T1 d: xy/3
Entry line (before Return): template: `xy` over `3`; `T1-d-tpl-before.png`. Typed: linear `xy/3`.
Result (after Return): `xy` over `3`; `T1-d-after.png`. `xy` is one variable.
Matches the current editor? yes (template).

### T1 e: 2x/3
Entry line (before Return): template: `2x` over `3`; typed: linear `2x/3`.
Result (after Return): `2·x` over `3` (a dot appears between 2 and x); `T1-e-after.png`.
Matches the current editor? yes (template).

### T1 f: (a+b)/2
Entry line (before Return): template: numerator `a+b` with **no brackets**, `2` below; typed: linear `(a+b)/2`; `T1-f-tpl-before.png`, `T1-f-before.png`.
Result (after Return): `a+b` over `2`, no brackets; `T1-f-after.png`.
Matches the current editor? no — brackets are dropped for a plain sum (see T2 for when they are kept).

### T1 g: sin(x)/2
Entry line (before Return): template: `sin(x)` over `2`; typed: linear.
Result (after Return): `sin(x)` over `2`; `T1-g-after.png`.
Matches the current editor? yes (template).

### T1 h: 2+3/4
Entry line (before Return): template: `2+` then `3` over `4`, only `3` on top; typed: linear `2+3/4`.
Result (after Return): `2+3/4` stacked, result `11/4`; `T1-h-after.png`.
Matches the current editor? yes.

### T1 i: -3/4
Entry line (before Return): a leading `-` on an empty line inserts `Ans`: typed gives `Ans−3/4`, template gives `Ans−` then 3 over 4; `T1-i-before.png`, `T1-i-tpl-before.png`.
Result (after Return): error dialog "Undefined Ans" (no previous result on a fresh page); `T1-i-after.png`.
Matches the current editor? unsure — the editor has no `Ans` insertion; the minus is never "on top".

### T1 j: 2*3/4
Entry line (before Return): `2·3` is shown with a centred dot; template: the **whole `2·3`** on top, `4` below (the template absorbs the product); typed: linear `2·3/4`.
Result (after Return): `2·3` over `4`, result `3/2`; `T1-j-after.png`.
Matches the current editor? no — the whole product goes on top (`*` does not stop it); only `+` and `−` stop it.

### T1 k: x^2 [R] /3
Entry line (before Return): `x²` on top, `3` below; typed route: linear `x²/3`.
Result (after Return): `x²` over `3`; `T1-k-after.png`.
Matches the current editor? yes.

### T1 l: 1/2 [R] /3
Entry line (before Return): typed route: stacked `1/2` followed by linear `/3`; template route: a stacked fraction `1/2` as the numerator over `3`; `T1-l-before.png`, `T1-l-tpl-before.png`.
Result (after Return): nested fraction (1/2) over 3, result `1/6`; `T1-l-after.png`.
Matches the current editor? yes (template).

### T1 m: √(2) [R] /3
Entered with the palette square-root template (key described in T7), then `2`, `[R]`, `/3`.
Entry line (before Return): `√2` over `3` (template); typed route linear `√2/3`.
Result (after Return): `√2` over `3`; `T1-m-after.png`.
Matches the current editor? yes.

### T1 n: /3 on an empty line
Entry line (before Return): typed: `Ans/3` (Ans inserted). Template on an empty line: an **empty numerator box** over `3`.
Result (after Return): typed: error "Undefined Ans"; template: error "Syntax" (`T1-n-after.png`, `T1-n-tpl-after.png`).
Matches the current editor? no — the editor takes nothing on an empty line; the emulator inserts `Ans` (typed) or leaves an empty box (template). Both fail on Return.

### T1 o: 2+/3
Entry line (before Return): typed: linear `2+/3`. Template: `2+` then a fraction with an empty numerator box over `3`.
Result (after Return): error "Syntax" in both; `T1-o-after.png`, `T1-o-tpl-after.png`.
Matches the current editor? unsure — the emulator keeps an empty numerator box and fails on Return.

## T2. Brackets
### T2 a: (a+b)^2 [R] /c
Entry line (before Return): typed: linear `(a+b)²/c`. Template: `(a+b)²` over `c`, **brackets kept** because of the power; `T2-a-before.png`, `T2-b-tpl-before.png`.
Result (after Return): `(a+b)²` over `c`; `T2-a-after.png`.
Matches the current editor? unsure — see T1 f: brackets are dropped for a plain sum, kept when a power follows.

## T3. Backspace around templates (starting from the template fraction `1/2 [R]`)
### T3 a: [BS]
Entry line: the whole fraction is **selected** (highlighted); nothing deleted yet; `T3-a-before.png`, `T3-a-after.png`.
Matches the current editor? no — the editor steps into the last slot.

### T3 b: [BS] [BS]
After the second press the fraction is **deleted** and the line is empty; `T3-b-after.png`.
Matches the current editor? no.

### T3 c: [BS] x3
A third press has no further effect (empty line); `T3-c-after.png`, `T3-c2-after.png`.
Matches the current editor? no — the fraction is removed on the second press.

### T3 d: 12/34, [L] to the start of the denominator, [BS]
Entry line after: the fraction dissolves into `12|34` (cursor between the digits, `1234` run together); a further BS gives `1|34`; `T3-d-before.png`, `T3-d-after.png`, `T3-d-after2.png`.
Matches the current editor? yes — Backspace at the start of the denominator dissolves the fraction and keeps its contents.

### T3 e: 12/34 [U] [L] [L] [BS]
Backspace at the start of the numerator **selects the whole fraction** (highlighted) rather than dissolving it; `T3-e-before.png`, `T3-e-after.png`.
Matches the current editor? no — it does not dissolve at the start of the numerator.

### T3 f: Delete (shift+BS) in front of a template
`1/2 [R]` then shift+BS: the whole fraction is highlighted (`T3-f-shiftBS.png`). A second variant (`T3-f-Delete.png`) shows only `1` highlighted. Unsure what the second key combination was reading as; treat the forward delete as **not reliably tested**.
Matches the current editor? unsure.

## T4. Up and Down
### T4 a: 12/34 [U] then 5
`[U]` from the end of the denominator moves to the end of the numerator (`12|`); typing 5 gives `125`; `T4-a-after-Up.png`, `T4-a-typed5.png`.
Matches the current editor? yes (position kept).

### T4 b: [D] then 6
Down from the numerator goes to the denominator end; typing 6 gives `346`; `T4-b-typed6.png`.
Matches the current editor? yes.

### T4 c: [U] again in the numerator
Typing 7 after another Up gives `1257`, i.e. Up had no effect and the cursor stayed in the numerator; `T4-c-typed7.png`.
Matches the current editor? yes.

### T4 d: Up on an empty entry line with two previous entries
First Up **selects the last result** (highlighted `4`), second Up selects the **last entry expression** `2+2`. Return then copies it into the entry line (`2+2`, not evaluated); a second Return evaluates it and adds a new history row; `T4-d-Up1.png`, `T4-d-Up2.png`, `T4-d-Return1.png`, `T4-d-Return2.png`.
Matches the current editor? no — Up on an empty line recalls history.

### T4 e: 1+2 then [U] [D]
Up and Down on a one-line entry do nothing visible; typing 9 afterwards gives `1+29`; `T4-e-Up.png`, `T4-e-typed9.png`.
Matches the current editor? yes.

### T4 f (extra): Down from the start of a numerator
Down moved to the **start** of the denominator (typed `x` appears before `34`); `T4-f-Down-from-numStart.png`. Column position is kept.

## T5. Powers
### T5 a: x^2 then +1 (no [R])
`+1` lands in the exponent: `x²⁺¹`, result `x³`; `T5-a-before.png`, `T5-a-after.png`.
Matches the current editor? yes.

### T5 b: x^2 [R] +1
Normal exit: `x²+1`, result `x²+1`; `T5-b-after.png`.
Matches the current editor? yes.

### T5 c: sin(x)^2
Drawn as `(sin(x))²` with extra brackets; result `(sin(x))²`; `T5-c-before.png`, `T5-c-after.png`.
Matches the current editor? unsure — extra brackets appear around the function.

### T5 d: (x+1)^2 [R] *3
Drawn `(x+1)²·3`; result `3·(x+1)²`; `T5-d-before.png`, `T5-d-after.png`.
Matches the current editor? yes.

### T5 e: x^-1 and x^(-1)
`x^-1` is drawn `x⁻¹`, `x^(-1)` is drawn with brackets in the exponent `x^(−1)`; both give `1/x`; `T5-e1-*.png`, `T5-e2-*.png`.
Matches the current editor? yes.

### T5 f: ^2 on an empty line
`Ans²` is inserted; Return gives "Undefined Ans" on a fresh page; `T5-f-before.png`, `T5-f-after.png`.
Matches the current editor? no — the editor makes an exponent with no base.

### T5 g: x^2^3
Drawn as `x` with `2` as exponent and `3` as an exponent of that `2` (a tower); result `x⁸`; `T5-g-before.png`, `T5-g-after.png`.
Matches the current editor? unsure.

### T5 h: 2^3 [R] /4
Power in the numerator: `2³` over `4`, result `2`; `T5-h-before.png`, `T5-h-after.png`.
Matches the current editor? yes.

### T5 i: the x² key
The x² key inserts a superscript `2` directly (`x²`, cursor inside the exponent, red cursor); result `x²`; `T5-i-before.png`, `T5-i-after.png`.
Matches the current editor? unsure.

## T6. Roots
### T6 a: √ key, 2, [R], *3
`√2·3` with the `3` outside the root; result `3·√2`; `T6-a-before.png`, `T6-a-after.png`. `[R]` is needed to leave the radicand.
Matches the current editor? yes.

### T6 b: √ 2 *3 (no [R])
`*3` stays under the root: `√(2·3)`, result `√6`; `T6-b-before.png`, `T6-b-after.png`.
Matches the current editor? yes.

### T6 c: nth root from the palette
Slot order: **index first** (`a`), then radicand (`b`). `[R]` moves from the index to the radicand; the entry reads `ᵃ√b`; the result is shown stacked (see `T6-c-after.png`); `T6-c-first.png`, `T6-c-before.png`.
Matches the current editor? unsure — no editor rule for slot order.

Extra: typing `sqrt(` gives a plain function with round brackets (`sqrt(2)`), not a radicand slot; it displays `√2` after Return (`T6-typed-sqrt-*.png`).

## T7. Palette and other templates
Opened with the template key on the keypad (not the Menu key). The palette has **25 items** in three rows (`T7-palette.png`, `T7-palette-open-emptyline.png`): row 1: fraction, exponent `x^□`, square root, nth root, `e^□`, log with base, 2-piece, N-piece, 2-equation system, N-equation system, absolute value; row 2: degrees-minutes-seconds, 2×2 matrix, 1×2 matrix, 2×1 matrix, m×n matrix (dialog), sum Σ, product Π, d/dx, d²/dx², dⁿ/dxⁿ, definite integral; row 3: indefinite integral, limit, subscript box. Slot orders below were found by typing `a`, `b`, `c` … in each slot and pressing **Tab**; screenshots `T7-<name>-Tab.png` (finished entry). Results after Return were **not captured** for the templates in this section except where stated; the "Right" shots (`-Right.png`) show what Right does.
- fraction: numerator, then denominator, then out (Tab); Right from the numerator **leaves the fraction** (`T7-frac-Right.png`); Down goes to the denominator. 
- exponent (`x^`): base then exponent, Tab and Right both leave the exponent; on an empty line the base is `Ans`.
- `e^`: exponent, then out.
- square root: radicand, then out.
- nth root: index, radicand, out.
- abs: one slot, then out.
- log with base: base, argument, out.
- 2-piece piecewise: value 1, condition 1, value 2, condition 2, out (`T7-pw2-Tab.png`). How to add a row: not tested.
- 2-equation system: eq 1, eq 2, out.
- DMS: degrees, minutes, seconds, out.
- Σ and Π: variable, lower, upper, body, out.
- d/dx: variable, expression, out; d²/dx²: variable, expression; dⁿ/dxⁿ: variable, n, expression.
- definite ∫: lower, upper, integrand, variable of integration; indefinite ∫: integrand, variable.
- limit: variable, value, direction (superscript), expression.
- subscript box: base, subscript.
- 2×2, 1×2, 2×1: cells row by row, then out. m×n opens a "Create a Matrix" dialog (see T8).
- N-piece and N-equation templates (dialogs) were **not tested**; the mouse and the keyboard navigation inside templates (mouse clicks on slots, Up/Down in multi-slot templates) were **not tested**.

## T8. Matrices and lists
### T8 a: matrix template
Palette item m×n opens "Create a Matrix": **rows** and **columns**, both default 3; type the number, Tab, number, Return. A 2×3 matrix shows empty slots as dashed boxes (`T8-a-dialog.png`, `T8-a-dialog-filled.png`, `T8-a-after.png`). The maximum size was not tried.
Matches the current editor? n/a (not implemented).

### T8 b: filling cells
**Tab** moves cell by cell, row by row (`1 2 3 / 4 5 6`); a Tab at the last cell then typing puts the text **outside** the matrix (`T8-b-Tab.png`, `T8-b-Tab-extra.png`). **Right** moves along a row but at the end of the row it **exits the matrix** instead of going to the next row (`T8-b-Right.png`, `T8-b-Right-extra.png`).

### T8 c: adding rows and columns later
**Not tested.**

### T8 d: linear `[1,2;3,4]` and `{1,2,3}`
While typing, `[1,2;3,4]` is drawn linearly with square brackets and the `;` shown as typed (`T8-d-matrix-before.png`); `{1,2,3}` is drawn linearly with braces (`T8-d-list-before.png`). After Return the matrix is typeset as a 2×2 matrix (1 2 / 3 4) in both the history and the result column (`T8-d-matrix-after.png`), and the list stays `{1,2,3}` (`T8-d-list-after.png`).

### T8 e: a fraction in a matrix cell
Typing `1/2` in a cell stays linear (`1/2`). `[R]` moves to the next cell in the **same row**; at the end of the row `[R]` exits the matrix. Return on the incomplete matrix gave "Syntax"; `T8-e-typed.png`, `T8-e-Right.png`, `T8-e-Tab.png`, `T8-e-after.png`. A template fraction inside a cell was **not tested**.

## T9. Multiplication and symbols
- `2*3`: drawn `2·3` (centred dot), result `6`; `T9-a-before.png`, `T9-a-after.png`.
- `2x`: drawn `2·x` (a dot is inserted); `x*y`: `x·y`; `xy`: `xy` with no dot, so `xy` and `x*y` **look different**; `2(3)`: `2·3`, result `6`; `2π`: `2·π`; `T9-b-multi.png`.
- `3.14ᴇ6`: typing the `ᴇ` character is **not accepted** (a box is drawn, "Syntax" on Return); the EE key was not tried; `T9-c-EE.png`, `T9-c-EE-after.png`.
- `5%` and `x≤2`: the typed characters were entered into an already broken line, so the result is **not conclusive** (`T9-pct.png`). Treated as not tested.

## T10. Editing keys
### T10 a: Home and End
`Home` jumps to the start of the line and `End` to the end (marker letters `q` and `r`); `T10-a-Home.png`, `T10-a-End.png`. ctrl+Left/ctrl+Right were not tried.
Matches the current editor? unsure.

### T10 b: shift+Left twice on 123, then 9
Selection is replaced: result `19`; `T10-b-after.png`.

### T10 c: copy and paste a fraction
**Not tested.**

### T10 d: Return with the cursor inside a denominator
Evaluates the whole entry (every template T1 row was submitted with the cursor in the denominator); `T10-d-after.png`.

### T10 e: ctrl+Enter on 1/3
Result `0.33333333`; `T10-e-after.png`.

### T10 f: Esc on a half-typed entry
`a+b/` then Esc: the entry line is **not cleared**; `T10-f-after.png`.

## The current editor's assumptions against what was found
| # | Assumption | Result | Detail |
|---|---|---|---|
| 1 | `/` takes the run before the cursor; stops at an operator; nothing on an empty line | **differs** | Typed `/` is linear in the entry line. The template takes digits, `.`, letters, function calls, brackets, powers, roots, finished fractions and also a whole `2*3`; it stops at `+` and `−`. On an empty line the typed key inserts `Ans`, the template leaves an empty numerator box (both give an error). |
| 2 | Bracketed numerator keeps its brackets | **differs** | Dropped for `(a+b)/2`; kept when a power follows, `(a+b)²/c`. |
| 3 | Backspace after a template steps into its last slot; at the start of a slot dissolves it | **differs** | Backspace after a template selects the whole template; a second press deletes it. At the start of the denominator it dissolves (keeps contents); at the start of the numerator it selects the whole fraction. |
| 4 | Up/Down between rows, position kept; nothing on a plain line | **confirmed** with an addition | Up on an **empty** entry line selects the last result, then the last entry; Return copies it into the entry line. |
| 5 | `^` stays open until `[R]`; `^` on an empty line gives an exponent with no base | **differs** (second half) | Stays open until `[R]` (Tab also exits) is confirmed; `^2` on an empty line gives `Ans²`. |
| 6 | `√` opens a radicand slot that stays open until `[R]` | **confirmed** | Typed `sqrt(` is a plain function. |
| 7 | `[R]` in a numerator goes to the denominator then out; `[L]` reverses | **differs** | `[R]` from the numerator leaves the fraction; Tab goes numerator, denominator, out; Down goes to the denominator. `[L]` reverse not tested. |
| 8 | `*` is a centred dot; `ⅇ ⅈ π ∞` are symbols | **confirmed** (partly) | `*`, `2x`, `2(3)`, `2π` all show a dot; `xy` has none. Only `π` tested of the symbols; `ⅇ ⅈ ∞` not tested. |
| 9 | Matrices and lists not implemented | n/a | Findings are in T7 and T8. |

## Also seen, not covered by the tests
- 50-page limit per problem (error "Maximum number of pages per problem is 50.").
- An operator at the start of the line inserts `Ans`; with no previous result the dialog "Undefined Ans" appears and needs OK.
- The palette highlight starts on the last item used; arrows clamp at the edges.
- Matrix: Tab beyond the last cell leaves the matrix.
- Repeated presses of a template key cycling through templates (reported by Simon), the keypad's ctrl/shift layers, and mouse navigation inside templates were **not investigated**.

## What was run
Run on the emulator: T1 (a–o, both routes), T2, T3 (a–e; f unclear), T4 (a–f), T5 (a–i), T6 (a–c), T7 (slot order for most templates by Tab), T8 (a, b, e), T9 (partly), T10 (a, b, d, e, f). Not run: T3 f (unclear), T7 piecewise "add a row" and N-templates and results after Return, T8 c, T9 `%` and `≤`, T10 c, mouse navigation, the keypad survey.
