# Keyboard shortcuts (FR-CALC-004, FR-DEV-001)

The shortcuts of the TI-Nspire CX family that the device model should map. This is the working table; `Check` says what still needs the emulator (brief: `docs/testing/emulator-shortcuts-capture.md`; results: `docs/testing/emulator-shortcuts-results.md`, run 2026-11-06).

Sources:
- **A** `references/TI-Nspire CX II Family Shortcuts 2026.pdf` (TI, with thanks to Neale Woods).
- **B** `references/TI Shortcuts and Tips.pdf` (TI 2017, Woods and Bird; reuse for non-commercial educational purposes with acknowledgement).
- **C** TI's online keyboard-shortcuts page (education.ti.com, Nspire eGuide, "Keyboard shortcuts"). Its table is the only source for the template and keypad-layer shortcuts below. The page text has some garbled symbols and a few duplicated rows, so its entries are unverified until run on the emulator.
- **S** Simon: ctrl+/ on a computer keyboard, ctrl+÷ on the handheld keypad, give the fraction template (2026-11-06).

Mac users substitute Cmd for ctrl. "Hand" is the handheld keypad (in CASSim, Handheld mode), "Comp" a computer keyboard. A tick means the source says it works there. Plain `/`, `÷`, `^` and `√` are not shortcuts: see decision 0017.

## 1. Entry and templates (the editor)
| Keys | Action | Hand | Comp | Source | CASSim | Check |
|---|---|---|---|---|---|---|
| ctrl+/ | Fraction template (takes the preceding term) | ✓ (ctrl+÷) | ✓ | C, S | M2d, Must | Confirmed (S1): both work; takes the preceding term or whole product, stops at `+`, drops brackets on a bare `(a+b)` but keeps them before a power, a selection becomes the numerator, empty line gives an empty fraction (cursor in numerator), nests |
| ctrl+Q | Square root | ✓ | | C | M2d | Differs (S2): keypad ctrl+x² gives the template; computer ctrl+Q does nothing |
| ctrl+L | nth root | ✓ | | C | M2d | Differs (S2): keypad ctrl+^ gives it (slots index, radicand); computer ctrl+L opens the variable list |
| shift+minus | Derivative template | ✓ | | A, B, C | M2d | Confirmed (S2): slots variable, then expression |
| shift+plus | Integral template | ✓ | | A, B, C | M2d | Confirmed (S2): definite; slots lower, upper, integrand, variable |
| ctrl+* (keypad ×) | Template palette | ✓ | | C | M2d | Differs (S2): gives a string template `" "`, not the palette |
| ctrl+K | Symbol palette | ✓ | | C | M2e, Should | Differs (S2): no visible effect from the computer keyboard or the keypad |
| ctrl+( , ctrl+) | `[ ]` and `{ }` | ✓ | | C | M2d | Confirmed (S2) |
| ctrl+= | Inequality menu | ✓ | | C | M2e, Could | Confirmed (S2): menu `> < ≠ ≥ ≤ \|` |
| ctrl+S (keypad) | log( ) | ✓ | | C | M2d | Differs (S2): the key is ctrl+10ˣ and it gives a `log_a(b)` template (base slot, then argument) |
| ctrl+U (keypad) | ln( ) | ✓ | | C | M2d | Confirmed (S2): the key is ctrl+eˣ |
| ctrl+minus (keypad) | `Ans` | ✓ | | C | M2d | Confirmed (S3): keypad ctrl+(−) |
| ctrl+h / ctrl+Ë (keypad) | Store arrow `→` (and `=:`) | ✓ | | C | M2d | Confirmed (S3): keypad ctrl+var; computer ctrl+H does nothing |
| ctrl+space | Underscore | ✓ | ✓ | A, B, C | M2d | Confirmed (S3), computer keyboard |
| ctrl+· (keypad) | Approximate: force a decimal result | ✓ | ✓ | C | M2d | Differs (S4): keypad ctrl+enter and computer ctrl+Return both give `0.33333333` in a new history row; ctrl+· not used |
| ctrl+. | Clear entry (hand) / manual data capture | ✓ | | C | M2d | Differs (S3, S8): no effect; the only clear found is ctrl+A then Backspace |
| shift+/ | `\` symbol | ✓ | | C | M2d | Confirmed (S2): keypad shift+÷; Syntax on Return |

## 2. Moving and selecting
| Keys | Action | Hand | Comp | Source | CASSim | Check |
|---|---|---|---|---|---|---|
| Tab | Next field or slot (template slots in order, then out) | ✓ | ✓ | A, B, C | M2d | Confirmed in templates (results T7, T8) |
| shift+Tab | Previous field or slot | ✓ | ✓ | A, B, C | M2d | Confirmed (S5): exact reverse of Tab |
| shift+arrows | Select | ✓ | ✓ | A, B, C | M2d | Confirmed (S5): a template is selected as one unit |
| ctrl+A | Select all | ✓ | ✓ | A, B, C | M2d | Confirmed (S5): typing replaces |
| ctrl+7 / ctrl+8 | Jump to first line / start of line | ✓ | ✓ | A, B, C | M2d | Confirmed (S5): ctrl+7 selects the first history row, ctrl+8 start of line |
| ctrl+1 / ctrl+2 | Jump to last line / end of line | ✓ | ✓ | A, B, C | M2d | Confirmed (S5): ctrl+2 end of line; ctrl+1 returns the cursor to the entry line (last line) |
| ctrl+3 / ctrl+9 | Page down / page up | ✓ | ✓ | A, B, C | M2c | Confirmed (S5): scroll the history (ctrl+3 to the bottom) |
| ctrl+up | Move up the document hierarchy | ✓ | ✓ | C | M2c, Could | Confirmed (S5): opens the page sorter |
| Up on an empty entry line | Select last result, then last entry; Return copies | ✓ | ✓ | emulator | M2c | Confirmed (T4d) |

## 3. Matrices
| Keys | Action | Hand | Comp | Source | Check |
|---|---|---|---|---|---|
| Return (in a matrix) | Add a row | ✓ | | A, B | Differs (S6): Return and keypad enter evaluate the matrix |
| alt+Enter | Add a row | | ✓ | A, B, C | Confirmed (S6): row inserted above the current one |
| shift+Return | Add a column | ✓ | | A | Confirmed (S6): column inserted to the left |
| shift+Enter | Add a column | | ✓ | A, B, C | Confirmed (S6): keypad version put the column to the right when the cursor was at the end of the cell |
| Tab | Next cell, row by row; past the last cell leaves | ✓ | ✓ | emulator | Confirmed (T8b) |

## 4. Editing, document and page
| Keys | Action | Source | CASSim | Check |
|---|---|---|---|---|
| ctrl+C, ctrl+X, ctrl+V | Copy, cut, paste | A, B, C | M2d | Confirmed (S7): paste keeps the 2D template |
| ctrl+Z, ctrl+Y | Undo, redo | A, B, C | M2d | Confirmed (S7 d): entry-line undo grouped by operator (`ab+c` is 3 steps: `ab`, `+`, `c`); a template insert and each slot entry are separate steps; with an empty undo history ctrl+Z falls through and undoes the page insert |
| shift+Esc | Redo (hand) | B | M2d, Could | Differs (S7): no redo; redo is ctrl+Y |
| ctrl+I | Insert page | A, B, C | M2c | Used in the capture runs |
| ctrl+Left / ctrl+Right | Previous / next page | CASSim | FR-DOC-001 | Keyboard and keypad |
| ctrl+N, ctrl+O, ctrl+S, ctrl+W | New, open, save, close document | A, B, C | M2c | not needed on the emulator |
| ctrl+L | Variable list (Calc); store or link a variable (L&S) | A, B, C | M2c | Confirmed (S2) for Calculator |
| ctrl+R | Recalculate (L&S) | A, B, C | M5 | |
| ctrl+G | Go to cell or line; toggle the graph entry line | A, B, C | M3, M4 | |
| ctrl+T | Toggle table | A, B | M3 | |
| ctrl+M | Insert math box (Notes) | A, B, C | Could | |
| ctrl+E | Insert chem box (Notes) | A, B, C | Won't | |
| ctrl+F, ctrl+H | Find, replace (program editor) | A | M7 | |
| ctrl+B, ctrl+R | Check syntax and store, run (program editor) | A | M7 | |
| ctrl+4, ctrl+6, ctrl+K, ctrl+Tab | Split screen, select page | A, B, C | M2e | |

## 5. Typed spellings (the parser reads these; no device model needed)
`pi` π, `theta` θ, `infinity` ∞, `<=` ≤, `>=` ≥, `/=` ≠, `=>` ⇒, `<=>` ⇔, `=:` →, `abs(` , `sqrt(`, `sumSeq(`, `prodSeq(`, `arcsin(`, `@e`, `@E`, `@t`, `@r`, `@d`, `@g`, `@<`, `@>`, `@i`, `@c1`, `@n1`. Already in the corpus and `to_ascii` (decision 0007).

## 6. Handheld key combinations not on the sheets
The handheld's blue ctrl layer and shift layer are drawn from the keypad (FR-DEV-005). Items in section 1 marked with a keypad label (ctrl+Q, ctrl+L, ctrl+S, ctrl+U, ctrl+h) refer to the letter printed under the key, not a computer key, so the Handheld key map must be built from the keypad and not from this table alone.

## Other findings from the shortcuts run (S5 to S9)
- Clearing an entry: only ctrl+A then Backspace worked. Esc, keypad shift+del and computer shift+Delete did nothing visible. Computer Delete deletes forward, and in front of a template selects it.
- Backspace: nothing at the start of the line; in an empty exponent or radicand it removes the template.
- Left from the start of a denominator leaves the fraction on the left. Tab runs numerator, denominator, out; shift+Tab reverses it.
- Matrix size limit is 99 by 99. A fraction in a cell exits with Right and stays in the cell.
- Symbols: EE key gives `ᴇ` (3.14ᴇ6 is 3140000.); `@E` is scientific notation, typed letters `EE` are not (Simon); `5%` gives 1/20; `<=`, `/=`, `=>` become ≤, ≠, ⇒ on Return; `pi`, `infinity`, `@i` become π, ∞, ⅈ; keypad eˣ gives bold ⅇ.
- A keypad click followed at once by typed text can be reordered; wait after a keypad click.

- Delete in front of a template: first Delete selects it, a second leaves only its first slot's content (`3/4` becomes `3`, selected).

## Built from the follow-up run (2026-11-12)
- ctrl+Z and ctrl+Y step through typing, evaluations and deleted pairs (a store is not undone). With nothing left to undo on the page, ctrl+Z undoes the page insert and ctrl+Y redoes it. Loading a document starts with no undo (emulator check 3, H1).
- Home with a history line picked goes to the first line (H2 c).
- The keypad has ctrl+Z and ctrl+Y as well as ctrl+esc; shift+esc is not bound.
- Keypad ctrl+7 picks the first history row and ctrl+1 returns to the entry line. They are not bound on the computer keyboard, where a browser keeps ctrl+1 to ctrl+8 for its tabs.
- The second Delete on a highlighted template keeps its first slot's content, selected. Seen on the emulator for a fraction only; CASSim does the same for every template.
- ctrl+K is not bound (no effect on the emulator).

## Implementation notes
- Bindings are data (profile registry), not code (FR-DEV-007). The editor exposes the actions: `insert_template(kind)`, `tab()`, `left()` and so on.
- A computer keyboard has two forms of some keys (Return versus Enter, ctrl+Enter, alt+Enter); the Handheld and Computer maps are separate tables.
- The computer map includes ctrl+N, ctrl+O, ctrl+S and ctrl+L, but browsers can intercept them;
  use the on-screen menus when they do. Browser-reserved ctrl+W, ctrl+P and ctrl+T are not bound.

## Selection and clipboard in CASSim (computer keyboard)
- shift+Left/Right select a node at a time (a template is one node); ctrl+shift+Left/Right select a word; shift+Home/End select to the start or end of the row; ctrl+A selects the line. ctrl+Left/Right move between pages. The word-selection and Home/End keys are standard text-editing conventions, not from TI's tables, and are not checked on the emulator.
- ctrl+C, ctrl+X, ctrl+V: the calculator's clipboard keeps templates, so a pasted fraction is stacked (S7), and it is shared by all pages of a document. The text is also put on the system clipboard; on paste, system text that matches the calculator's clipboard brings the templates back, any other text is typed in (newlines become spaces).
- Spreadsheet formulas: after `=` or an operator, arrow keys point to a cell and Shift+arrow extends
  the reference to a range. Click a cell to insert a reference at the caret. Mouse-drag range
  selection is not yet reliable in the browser; use Shift+arrow to select a range.
  F2 switches between pointing and editing text; F4 cycles a cell reference through relative,
  absolute and mixed forms. These two keys retain their Menu/Doc roles outside formula editing.
  Click the entry bar to edit the selected cell, with the caret initially at the end.

## Menus (M2c)
- Computer: `F2` opens the Menu (commands), `F4` opens Doc, `Escape` closes. Pressing the other menu key switches directly between Menu and Doc. Up/Down move, Enter or Right opens, Left goes back, the item's number or letter chooses it. These keys are CASSim's own choice, not checked against the Nspire software (Unsure); shift+F10 opens the spreadsheet context menu.
- Handheld keypad: the `esc`, `doc` and `menu` keys do the same.
- Doc > 4 Insert > 1 Problem / 3 Calculator and Doc > 7 Settings & Status > 2 Document Settings follow the routes used on the simulator. The Calculator Menu follows the handheld's numbering (M2f, decision 0022; unverified), and every row can be clicked or tapped.
- Keypad keys added in M2f (decision 0022): var, ctrl+var `→`, ctrl+del clear, ctrl+= relations, trig, templates, catalog, ctrl+catalog symbols, eˣ/ln, 10ˣ/log, ctrl+esc undo, ctrl+doc add page, ctrl+▲ sorter, ctrl+◀/▶ pages, ?!▸, π▸, shift+letter capitals. Computer: ctrl+L variables, ctrl+↑ sorter.
- CASSim additions: keypad shift+doc and computer ctrl+alt+I open the new Problem page-type picker.
  The doc key shows `+problem` in orange when shift is pending instead of the blue `+page`.
  Ctrl+alt can overlap AltGr on some layouts; browser and platform shortcuts can also intercept keys.
- CASSim addition: repeat the keypad π, trig or templates key to move to the next grid item,
  wrapping to the first; Enter chooses it. Ctrl then catalog can also cycle the Symbols grid.
