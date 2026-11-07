# 0022 Keypad layout, Nspire menus, syntax hints and command dialogs (M2f)

Date: 2026-11-07. Status: built; the menu numbering and the dialogs need checking on the simulator.

Simon asked for the keyboard and menus to mimic the Nspire closely, menus that work by touch and
mouse, a syntax hint on menu commands, and dialogs for the multi-argument commands, as the CAS has.

## Keypad (FR-DEV-005)

`profiles/nspire.py` `KEYPAD` now follows the CX II layout in CASSim's own drawing (no TI artwork):
esc and tab left of a touchpad (arrows round a centre click), doc and menu right of it; ctrl, shift,
var, del; the paired function keys (`=` trig, `^` x², eˣ 10ˣ, `(` `)`) left of the digits and
templates/catalog, × ÷, + − right of them; enter; then the letter block (EE, a to z, ?!▸, π▸, `,`, ⏎,
space). Scratchpad, home and the flag key have nothing to do yet and are gaps.

`Key` gained `width`, `height` (key units) and `style` (the theme colours it); a key with no name is a
gap. A key `w` units wide is `w·(KEY_W+gap) − gap` pixels, so half keys and letter keys line up with the
digit columns (`app/layout.py` `key_span`). Each key shows its ctrl label (blue) and shift label (amber)
above the main label; a tooltip lists them for mouse and long press.

System Settings > Keypad letters chooses the letter block: ABC (the CX II's alphabetical
block, the default) or QWERTY (ten keys across, with EE, `,`, ?!▸, π▸, ⏎ and space round it). The
profile supplies both keypads (`Profile.keypads`), so the app holds no layout of its own; an unknown
saved name falls back to ABC.

New handheld bindings, from the key labels and `docs/design/shortcuts.md`: ctrl+esc undo, ctrl+doc
add page, ctrl+▲ page sorter, ctrl+◀/▶ previous/next page, var (variables menu), ctrl+var `→`, ctrl+del
clear the entry line, ctrl+= relations menu, trig menu, templates menu, ctrl+templates `:=`, catalog,
ctrl+catalog symbols, eˣ `ⅇ^`, ctrl+eˣ `ln(`, 10ˣ `10^`, ctrl+10ˣ `log(`, ctrl+( `[`, ctrl+) `{`,
shift+÷ `\`, shift++ `∫(`, shift+− `derivative(`, ?!▸ punctuation menu, π▸ symbols menu, ⏎ enter, and
shift then a letter types the capital. Computer keyboard: ctrl+L variables (confirmed S2), ctrl+↑ page
sorter.

**Unsure, check on the simulator:** what ctrl+del, the touchpad centre, ⏎ and π▸ do in a Calculator
page; the order of the trig, templates, punctuation and symbol lists. CASSim's templates key gives a list,
not the handheld's grid. ctrl+^ (nth root), ctrl+× (string) and the log template have no engine or
editor support yet, so those layers are unlabelled.

## Menus (FR-DEV-001, FR-CALC-005)

`profiles/nspire_menus.py` holds Doc, the Calculator Menu, and the trig, templates, catalog,
relations, punctuation and symbols menus; `var` builds the variables menu from the Problem. The
Calculator Menu keeps the handheld's numbers (`menu 3 1` is Solve, `menu 5 5 2` Normal Cdf…).
Items the engine cannot do yet are left out rather than greyed, and the rest keep their real numbers,
so some numbers are skipped (Algebra has no 5 until `completeSquare` exists). The numbering is
reconstructed from the Reference Guide and memory of OS 5/6 and is **unverified**: Simon, please check
each top-level menu against the simulator. Left out for now: Recall Definition, Clear History, Insert
Comment, Library, Lock; Approximate to Fraction as a function; getNum/getDenom; Complete the Square;
Convert Expression (▶ln, ▶exp...); Arc Length; Random Sample; Confidence Intervals; Stat Tests; Fill;
Difference List; Row operations; Functions & Programs (M7).

Doc keeps the simulator routes (4 Insert > 1 Problem / 3 Calculator, 7 Settings & Status). File, Edit
and View are CASSim's own; page moves now sit under Edit after the real Undo to Paste.

Touch and mouse: every row of every open level is clickable (`MenuState.pick`): a submenu opens, a leaf
runs, a click on an open submenu's parent row or on a submenu's `◀` title closes that level, and a click
outside the panels closes the menu. Long lists show a window round the highlight with clickable
"▲ more"/"▼ more" rows (5 rows in Handheld, 16 in Computer). Submenus cascade to the right of their
parent, overlapping it as on the handheld.

The Catalog is every command with a hint, a submenu per first letter keyed by the letter (so typing `s`
jumps to S), plus one for Σ ∫ χ² √. A test checks every hinted name is known to the engine.

## Syntax hints (FR-CAT-004)

`profiles/nspire_syntax.py` holds a short TI-style syntax per command (`solve(Equation, Var)`,
`normCdf(Lower, Upper, [μ], [σ])`). Handheld mode shows the highlighted row's hint at the foot of the
menu; Computer mode shows hints beside every row; both show it as a tooltip.

## Dialogs (wizards)

`device/wizard.py` is a dialog as data: named fields (text, a drop-down of choices, or a whole number
in a range) and either a `str.format` pattern, a `build` function or a template spec, with `run` to press
Enter afterwards. The GUI draws it (`ui.wizard_dialog`); `AppState.finish_wizard` pastes the result, and
a field that will not do is reported in the dialog. Built: Derivative at a Point…, Numerical Derivative
at a Point…, Solve System of (Linear) Equations…, Find Roots of Polynomial…, Create Matrix…, One- and
Two-Variable Statistics…, the twelve regressions…, Finance Solver…, and the nineteen distributions…
(Normal Pdf to Geometric Cdf).

Choices made without the simulator (**unsure**): the distribution, stats and Finance Solver dialogs paste
and run at once; stats and regressions append `: stat.results` so the table shows; empty trailing
arguments are dropped; Lower Bound defaults to `-9ᴇ999`; the system dialog pastes the list form
`solve({eq1,eq2},{x,y})` (the `and` form crashes the engine, see below) rather than the handheld's system
template; Find Roots asks for the coefficients in one box instead of a second dialog; Finance Solver is a
one-shot dialog, not the handheld's live solver; regressions do not offer "Save RegEqn to" (`CopyVar` is
not implemented).

Dialog output is pasted with the new `Editor.insert_linear`, in which `^` takes only its operand
(`x^2-3*x+2` is x² − 3x + 2, not x^(2−3x+2)) and a `▮` marks where the cursor is left. Pasting text from
the system clipboard uses it too, which fixes the same problem there.

## Found on the way (not fixed here)

- `solve(x+y=3 and x-y=1,{x,y})` raises an uncaught `AttributeError` in `sympy_adapter.solve_system`.
- The LaTeX of an approximate result ignores Float 8 (`normCdf(-1,1,0,1)` draws 0.682689492137086;
  its text is 0.68268949).
- In Computer mode the screen shrank to its lines (on `main` too); it now gets a height from the window
  (`layout.computer_screen_height`), since a menu drawn on it was clipped.
