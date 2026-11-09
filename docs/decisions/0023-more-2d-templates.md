# 0023 More 2D templates: roots, logs, piecewise, systems, calculus (M2g)

Date: 2026-11-08. Status: built and checked against the TI-Nspire CX CAS Premium Teacher Software
(Cowork run 2: `docs/testing/emulator-templates-results.md`, screenshots in
`docs/testing/template-shots/`; brief `emulator-templates-capture.md`).

## What
The editor (`device/editor.py`) had fraction, power, square root and matrix templates. It now has every
template on the device's templates key except subscript, each a `Kind` with its slots in the device's
Tab order:

| Kind | Slots (Tab order, from the device) | Text the engine reads | Keys and menus |
|---|---|---|---|
| nth root | index, radicand | `root(radicand,index)` | ctrl+^; templates grid |
| log with base | base, argument | `log(argument,base)` | ctrl+10ˣ; templates grid |
| absolute value | argument | `abs(argument)` | templates grid |
| piecewise | rows of value, condition | `piecewise(v1,c1,v2,c2,…)` | grid (2 pieces); N pieces dialog |
| system | rows of one equation | `{eq1,eq2,…}` | grid (2); N equations dialog; Solve System… |
| d/d□, d²/d□² | variable, expression | `derivative(expr,var[,2])` | shift+−; Calculus 1; grid; Derivative at a Point… |
| dⁿ/d□ⁿ | order, variable, expression | `derivative(expr,var,n)` | grid |
| definite ∫ | lower, upper, integrand, variable | `∫(f,var,lower,upper)` | shift++; Calculus 3; grid |
| indefinite ∫ | integrand, variable | `∫(f,var)` | grid |
| Σ and Π | variable, lower, upper, expression | `Σ(expr,var,low,high)` | Calculus 5 and 6; grid |
| limit | variable, point, direction, expression | `limit(expr,var,point[,±1])` | Calculus 4; grid |
| degrees-minutes-seconds | degrees, minutes, seconds | `(d°m's")` | grid |

The device run confirmed the Tab order of every template except the nth derivative, whose order (order,
variable, expression) is read from its empty-state screenshot. The limit has a direction slot after the
point (`+` or `−`, may stay empty), shown as a superscript: `0⁺`. Subscript (`a₁`) stays greyed: on the
device it makes a variable distinct from a typed `a_1`, and CASSim's parser has no such names.

## How
- The editor keeps a table of the linear form (`_CALLS`) and of the LaTeX (`_LATEX`) per kind, so a new
  template is a row in each table. A function-like template after a term gets an explicit `*`
  (`x|y|` is `x*abs(y)`, not `xabs(`).
- Piecewise and system templates are grids like a matrix (`GRIDS`, with their fixed column count): Up
  and Down move between rows, Backspace at the start of a cell steps back a cell. `Template.cols` holds
  the column count; files store it as before.
- The entry line draws each kind from small parts (`app/entry.py` `_Parts`): slots at a size (bounds,
  indices and the limit's direction smaller), and signs, bars and braces that click to the template as a
  whole (decision 0019).
- Template specs for the `template` key action take one number for rows: `system:3`, `piecewise:2`.
- Dialogs can replay key actions (`Wizard.steps`): Derivative at a Point pastes d/dx(□)|x=v with the
  variable filled in and the cursor in the box; Solve System pastes `solve(` and Solve System of Linear
  Equations `linSolve(`, each with the system template and `,{x,y})`, the cursor in the first equation.
  The N-piece and N-equation dialogs are "Create Piecewise Function" and "Create a System of Equations",
  one field each, default 3, as on the device.

## Engine
- `root(x,n)`: an odd root of a negative number is real (`root(-8,3)` is −2); in Real mode an even root
  of a negative number is "Non-real result" (new error, TI number 800), as on the device.
- `piecewise(v1,c1,…,[otherwise])`: the first true piece; only the chosen piece is evaluated; no true
  piece gives `undef`; symbolic conditions keep the choice.
- `linSolve(system,{x,y})` gives the values as a list (`{2,1}`); the system may be a list, the system
  template or equations joined with `and`. No solution gives "No solution found".
- `invBinomN(area,p,x)`: the fewest trials with P(X≤x) below the area. The device gives 12 for
  (0.5, 0.5, 5), where P(X≤5) is exactly 0.5 at 11 trials, so a tie moves on.
- `undef` is drawn as undef in the history (SymPy's LaTeX printed `NaN`).

## Other device facts applied (run 2, part 2)
- Distributions: χ² Cdf and F Cdf start Lower Bound at 0 (t Cdf at −∞); F is spelt `FPdf`, `FCdf`;
  Inverse Binomial's dialog is titled "Num Successes"; Inverse Binomial N (D) is now real, titled "Num
  Trials" (Cumulative Prob, Prob Success, Successes). The "Display Result: Matrix Form" box is not built.
- Calculus > D Differential Equation Solver… is a dialog: Equation, Independent Var, Dependent Var, two
  optional Conditions; it pastes and runs `deSolve(eq and cond1 and cond2,x,y)`.
- Finance Solver: changing PpY changes CpY (`Wizard.copies`). The device also stores `tvm.n`, `tvm.i`,
  … after a calculation; CASSim now does too (display fixes branch).
- Doc > Insert continues B Program Editor ▶ (New…, Open…, Import…, View…) and C Add Python ▶ (New…,
  Open…, Shell); Functions & Programs > Mode's eight submenus are listed (Display Digits: Float, Float1 to
  Float12, Fix0 to Fix12). All greyed.

## Found, not changed here
- In Real mode `√(-4)` gives `2·ⅈ` and `(-8)^(1/3)` gives `2·(-1)^(1/3)`; the device gives "Non-real
  result" for an even root and −2 for an odd one (decision 0008 deferred this).
- Typed `>=` stays as `>=` in the history entry; the device shows `≥` after Enter.
- `deSolve` with two conditions on a second-order equation leaves `c1` (`y''=-y and y(0)=1 and y'(0)=0`
  gives `y=c1·sin(x)+cos(x)`): the derivative condition is not applied.
- The LaTeX of a symbolic piecewise result is SymPy's ("for x < 0 / otherwise"); the device echoes the
  pieces with their conditions.

## Display fixes (2026-11-09)

- History and result LaTeX: `ans`, `and`, `or`, `xor` and `not` are upright bold (they are names, not
  variables), and a space is kept (`\ `) so `and` no longer runs into its equations. `@e` and `@i` are drawn
  as bold upright **e** and **i** in the entry and history; results draw ⅇ and ⅈ the same way. Bold was
  chosen because KaTeX has no glyph for U+2147/U+2148.
- Conditions in results read `x=1 and y=0 or ...` as on the handheld. Document Settings has a new
  "Join conditions with" choice (`logic`: `words` default, or `symbols` for ∧ ∨).
- `solve` and `cSolve` take the unknowns as `x,y` as well as `{x,y}`; a repeated unknown is "Too many arguments".
- The Finance Solver stores `tvm.n`, `tvm.i`, `tvm.pv`, `tvm.pmt`, `tvm.fv`, `tvm.ppy`, `tvm.cpy`, `tvm.pmtat`
  after each calculation (names from the simulator capture). Whole values are stored as integers, the rest as
  decimals (the device keeps decimals, `tvm.pmt = 0.`).
- Screen: 6 px above the first line; the blank space under the entry is 56 px (a quarter of the screen), so
  the list scrolls once about three quarters of it is used.
