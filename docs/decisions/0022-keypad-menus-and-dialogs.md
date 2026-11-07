# 0022 Keypad layout, Nspire menus, syntax hints and command dialogs (M2f)

Date: 2026-11-07, revised 2026-11-08. Status: built and checked against the TI-Nspire CX CAS Premium
Teacher Software (Claude Cowork run, `docs/testing/emulator-menus-results.md`, screenshots in
`docs/testing/menu-shots/`). What is still CASSim's own choice is marked **CASSim** below.

Simon asked for the keyboard and menus to mimic the Nspire closely, menus that work by touch and
mouse, a syntax hint on menu commands, dialogs for the multi-argument commands, and greyed
placeholders so the menu numbers match the device (muscle memory matters).

## Keypad (FR-DEV-005)

`profiles/nspire.py` `KEYPAD` follows the CX II layout in CASSim's own drawing (no TI artwork): esc
and tab left of a touchpad (arrows round a centre click), doc and menu right of it; ctrl, shift, var,
del; the paired function keys (`=` trig, `^` x², eˣ 10ˣ, `(` `)`) left of the digits and
templates/catalog, × ÷, + − right of them; enter; then the letter block (EE, a to z, ?!▸, π▸, `,`, ⏎,
space). Scratchpad, home and the flag key have nothing to do yet and are gaps.

`Key` has `width`, `height` (key units) and `style` (the theme colours it); a key with no name is a gap.
A key `w` units wide is `w·(KEY_W+gap) − gap` pixels, so half keys and letter keys line up with the
digit columns (`app/layout.py` `key_span`). Each key shows its ctrl label (blue) and shift label (amber)
above the main label; a tooltip lists them for mouse and long press.

System Settings > Keypad letters chooses ABC (the CX II's block, the default) or QWERTY (ten across).
The profile supplies both (`Profile.keypads`); an unknown saved name falls back to ABC.

Bindings, checked on the device (results part 3) unless marked: ctrl+del clears the entry line; the
touchpad centre and ⏎ do nothing on a Calculator page (outside a menu); ctrl+× gives a pair of quotes,
ctrl+( `[ ]` and ctrl+) `{ }`, each with the cursor inside; ctrl+esc undoes; π▸ opens the symbols grid;
shift then a letter types the capital; ctrl+= opens the relations grid (the computer keyboard's ctrl+=
types `≠`, as the Teacher Software does). Also ctrl+doc add page, ctrl+▲ page sorter, ctrl+◀/▶ pages,
var, ctrl+var `→`, eˣ `ⅇ^`, ctrl+eˣ `ln(`, 10ˣ `10^`, shift+÷ `\`, shift++ `∫(`, shift+− `derivative(`.
ctrl+^ (the nth-root template) and ctrl+10ˣ (the log-base template) are templates the editor lacks; ctrl+10ˣ
types `log(` meanwhile and ctrl+^ is unbound.

## Menus (FR-DEV-001, FR-CALC-005)

`profiles/nspire_menus.py` holds every menu as the device shows it: the Calculator Menu (all nine
groups to every leaf), Doc, the trig, templates, relations, punctuation and symbol keys, and the
Catalog. `var` builds the variables menu from the Problem.

Every device item is present, in order, with its number. Items CASSim cannot do yet are greyed
placeholders (`todo`): highlighted and named, hint "Not in CASSim yet", nothing happens when chosen
and the menu stays open. A device submenu none of whose items exists yet (`todo_sub`: Library, Lock,
Convert Expression, Confidence Intervals, Stat Tests, Row and Element Operations, Cash Flows, Days
between Dates, most of Functions & Programs) still opens and shows its items greyed. When a command is
built, its `todo` becomes a real item with the same key. Tests pin the routes the device run settled.

Changes the device run made to the first reconstruction: Number has no Prime Number Test or Base (they
stay in the Catalog); distributions run A Binomial Pdf, B Binomial Cdf, C Inverse Binomial, D Inverse
Binomial N, E–G F, H–I Geometric, J–K Poisson; Stat Calculations adds G Correlation Matrix; List Math is
flat (7 to A are the standard deviations and variances); List Operations is Sort×2, Cumulative Sum, Fill,
Sequence, Difference List, Augment, List▶Matrix, Matrix▶List, Left, Mid, Right; Numerical Calculations
has five items and Numerical Derivative at a Point is not a dialog; Matrix Create, Norms, Dimensions,
Advanced and Vector follow the device; Doc is File, Edit, View, Insert, Page Layout, Refresh Libraries,
Settings & Status, Login, Press-to-Test with the device's submenus. **CASSim:** Doc > View > Back and
Forward go to the previous and next page; Settings & Status > 3 Handheld Setup… opens CASSim's System
Settings; File > Save and Save As both download the file; CASSim's page moves and share link come after
the device's items (hint "CASSim").

Shapes, as on the device: trig (6 × 2, no hyperbolic row), templates (25 icons, 11 wide), relations
(3 × 2), punctuation (6 wide) and π▸ symbols (5 wide) are grids (`MenuItem.columns`): arrows move in
two dimensions, cells have no keys, the hint names the cell. The Catalog has six tabs (keys 1 to 6) and
opens on tab 1, one alphabetical list of every command with its hint, where a typed letter jumps to its
first entry (`MenuItem.jump`) and a digit changes tab. Tab 4 is the device's symbol grid (11 wide; the
first seven rows and the Greek letters, the rest left out), tab 5 the templates grid; tabs 2, 3 and 6 are
placeholders. The variables menu is alphabetical with no keys and jumps by letter. Template cells CASSim
has no 2D template for (nth root, piecewise, N-equation system, degrees-minutes-seconds, nth
derivative, subscript) are greyed; the others paste the template or its linear form.

Touch and mouse: every row or cell of every open level is clickable (`MenuState.pick`); a click on a
submenu's `◀` title or its parent row closes it; a click outside closes the menu. Long lists and grids
show a window round the highlight with clickable "▲ more"/"▼ more" (5 rows in Handheld, 16 in Computer).
Submenus cascade to the right, except grids, which stay at the left so they fit the screen.

## Syntax hints (FR-CAT-004)

`profiles/nspire_syntax.py` has a hint per command. Those the device run read (results part 5) are
copied as the device writes them, first form only (`solve(Equation,Var)`,
`normCdf(lowBound,upBound[,μ[,σ]])`); the rest follow the Reference Guide. Handheld mode shows the
highlighted item's hint at the foot of the menu; Computer mode shows hints beside every row; both show
it as a tooltip.

## Dialogs (wizards)

`device/wizard.py` is a dialog as data: named fields (text, a drop-down, or a whole number in a range)
and a `str.format` pattern, a `build` function or a template spec, with `run` to press Enter after
pasting. The GUI draws it (`ui.wizard_dialog`); `AppState.finish_wizard` pastes the result; a field
that will not do is reported in the dialog. Dialog output is pasted with `Editor.insert_linear`, in which
`^` takes only its operand and a `▮` marks where the cursor is left (system-clipboard paste uses it too).

Matching the device: the distribution, One- and Two-Variable and regression dialogs paste and run on OK,
and stats and regressions show `stat.results` at once; Derivative at a Point, Solve System of Equations
and Create Matrix only paste (cursor in the first slot); Find Roots of Polynomial pastes `polyRoots(…)`
without running it; Normal Cdf's Lower Bound starts as `-∞` and Upper Bound blank; Binomial Pdf's X Value
is optional (blank gives the whole list).

**CASSim** differences, for now: Derivative at a Point pastes `derivative(□,x)|x=v` (the device's d/dx
template) and has no "nth Derivative" choice; Solve System pastes `solve({□,□},{x,y})` (the device's
system template); Find Roots asks for the coefficients in one box (the device asks the degree, then one
box per coefficient); One-Variable Statistics skips the device's "Num of Lists" step and Category fields;
regressions do not offer "Save RegEqn to" (`CopyVar` is not implemented); Inverse Binomial has no
"Display Result" option; the Differential Equation Solver types `deSolve(` instead of opening the
device's dialog.

**Finance Solver is live** (Simon, 2026-11-08; matches the device): boxes N, I (%), PV, Pmt, FV start at
0, PpY and CpY at 1, PmtAt END. Put the cursor in a box and press Enter (or click Calculate) and that box
is worked out from the others. Closing it pastes nothing, as on the device. The calculation uses the same
pure-float code as the `tvm*` functions (`core/compat/finance.py`) in the app process; boxes accept
decimals, `ᴇ` and `a/b`; answers show 9 significant digits. **CASSim:** the device also stores the values
in `tvm.n`, `tvm.i`, ...; CASSim does not yet.

## Found on the way

- `solve(x+y=3 and x-y=1,{x,y})` crashed. Fixed: with several unknowns, `solve` and `cSolve` split an
  `and` into its equations (`sympy_adapter.conjuncts`), so the Boolean and list forms agree.
- The LaTeX of an approximate result shows more digits than Float 8. Simon: fine as it is (2026-11-08).
- In Computer mode the screen shrank to its lines (on `main` too); it now gets a height from the window
  (`layout.computer_screen_height`), since a menu drawn on it was clipped.
