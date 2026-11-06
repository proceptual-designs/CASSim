# Keyboard shortcuts (FR-CALC-004, FR-DEV-001)

The shortcuts of the TI-Nspire CX family that the device model should map. This is the working table; `Check` says what still needs the emulator (brief: `docs/testing/emulator-shortcuts-capture.md`).

Sources:
- **A** `references/TI-Nspire CX II Family Shortcuts 2026.pdf` (TI, with thanks to Neale Woods).
- **B** `references/TI Shortcuts and Tips.pdf` (TI 2017, Woods and Bird; reuse for non-commercial educational purposes with acknowledgement).
- **C** TI's online keyboard-shortcuts page (education.ti.com, Nspire eGuide, "Keyboard shortcuts"). Its table is the only source for the template and keypad-layer shortcuts below. The page text has some garbled symbols and a few duplicated rows, so its entries are unverified until run on the emulator.
- **S** Simon: ctrl+/ on a computer keyboard, ctrl+÷ on the handheld keypad, give the fraction template (2026-11-06).

Mac users substitute Cmd for ctrl. "Hand" is the handheld keypad (in CASSim, Handheld mode), "Comp" a computer keyboard. A tick means the source says it works there. Plain `/`, `÷`, `^` and `√` are not shortcuts: see decision 0017.

## 1. Entry and templates (the editor)
| Keys | Action | Hand | Comp | Source | CASSim | Check |
|---|---|---|---|---|---|---|
| ctrl+/ | Fraction template (takes the preceding term) | ✓ (ctrl+÷) | ✓ | C, S | M2d, Must | Run: does ctrl+÷ and ctrl+/ both work; what is captured |
| ctrl+Q | Square root | ✓ | | C | M2d | key letter is a keypad label; verify |
| ctrl+L | nth root | ✓ | | C | M2d | verify; clashes with "display variable list" |
| shift+minus | Derivative template | ✓ | | A, B, C | M2d | Run |
| shift+plus | Integral template | ✓ | | A, B, C | M2d | Run |
| ctrl+* (keypad ×) | Template palette | ✓ | | C | M2d | Run; A/B do not list it |
| ctrl+K | Symbol palette | ✓ | | C | M2e, Should | Run (A/B give ctrl+K as "select page") |
| ctrl+( , ctrl+) | `[ ]` and `{ }` | ✓ | | C | M2d | Run |
| ctrl+= | Inequality menu | ✓ | | C | M2e, Could | Run |
| ctrl+S (keypad) | log( ) | ✓ | | C | M2d | Run; conflicts with "save" on a computer |
| ctrl+U (keypad) | ln( ) | ✓ | | C | M2d | Run |
| ctrl+minus (keypad) | `Ans` | ✓ | | C | M2d | Run |
| ctrl+h / ctrl+Ë (keypad) | Store arrow `→` (and `=:`) | ✓ | | C | M2d | Run |
| ctrl+space | Underscore | ✓ | | A, B, C | M2d | Run |
| ctrl+· (keypad) | Approximate: force a decimal result | ✓ | ✓ | C | M2d | Run (ctrl+Enter is the computer form) |
| ctrl+. | Clear entry (hand) / manual data capture | ✓ | | C | M2d | duplicated in C; verify |
| shift+/ | `\` symbol | ✓ | | C | M2d | Run |

## 2. Moving and selecting
| Keys | Action | Hand | Comp | Source | CASSim | Check |
|---|---|---|---|---|---|---|
| Tab | Next field or slot (template slots in order, then out) | ✓ | ✓ | A, B, C | M2d | Confirmed in templates (results T7, T8) |
| shift+Tab | Previous field or slot | ✓ | ✓ | A, B, C | M2d | Run |
| shift+arrows | Select | ✓ | ✓ | A, B, C | M2d | Partly (T10b) |
| ctrl+A | Select all | ✓ | ✓ | A, B, C | M2d | Run |
| ctrl+7 / ctrl+8 | Jump to first line / start of line | ✓ | ✓ | A, B, C | M2d | Run (Home confirmed, T10a) |
| ctrl+1 / ctrl+2 | Jump to last line / end of line | ✓ | ✓ | A, B, C | M2d | Run |
| ctrl+3 / ctrl+9 | Page down / page up | ✓ | ✓ | A, B, C | M2c | Run |
| ctrl+up | Move up the document hierarchy | ✓ | ✓ | C | M2c, Could | Run |
| Up on an empty entry line | Select last result, then last entry; Return copies | ✓ | ✓ | emulator | M2c | Confirmed (T4d) |

## 3. Matrices
| Keys | Action | Hand | Comp | Source | Check |
|---|---|---|---|---|---|
| Return (in a matrix) | Add a row | ✓ | | A, B | Run (hand) |
| alt+Enter | Add a row | | ✓ | A, B, C | Run |
| shift+Return | Add a column | ✓ | | A | Run |
| shift+Enter | Add a column | | ✓ | A, B, C | Run |
| Tab | Next cell, row by row; past the last cell leaves | ✓ | ✓ | emulator | Confirmed (T8b) |

## 4. Editing, document and page
| Keys | Action | Source | CASSim | Check |
|---|---|---|---|---|
| ctrl+C, ctrl+X, ctrl+V | Copy, cut, paste | A, B, C | M2d | Copy and paste of a template not tested |
| ctrl+Z, ctrl+Y | Undo, redo | A, B, C | M2d | Run |
| shift+Esc | Redo (hand) | B | M2d, Could | Run |
| ctrl+I | Insert page | A, B, C | M2c | Used in the capture runs |
| ctrl+N, ctrl+O, ctrl+S, ctrl+W | New, open, save, close document | A, B, C | M2c | not needed on the emulator |
| ctrl+L | Variable list (Calc); store or link a variable (L&S) | A, B, C | M2c | Run |
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

## Implementation notes
- Bindings are data (profile registry), not code (FR-DEV-007). The editor exposes the actions: `insert_template(kind)`, `tab()`, `left()` and so on.
- A computer keyboard has two forms of some keys (Return versus Enter, ctrl+Enter, alt+Enter); the Handheld and Computer maps are separate tables.
- Do not bind browser-reserved combinations (ctrl+W, ctrl+N, ctrl+S, ctrl+P, ctrl+T) in the web build; use the on-screen menu for those. Record the list here when the key handler exists.
