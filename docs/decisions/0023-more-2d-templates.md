# 0023 More 2D templates: roots, logs, piecewise, systems, calculus (M2g)

Date: 2026-11-08. Status: built. Slot orders for d/dx and ∫ are from the shortcuts run (S2); the
others are CASSim's best reading of the device and are being checked in the Cowork run briefed in
`docs/testing/emulator-templates-capture.md`.

## What
The editor (`device/editor.py`) had fraction, power, square root and matrix templates. It now also has
the device's other templates, each a `Kind` with its slots in Tab order:

| Kind | Slots (Tab order) | Text the engine reads | Keys and menus |
|---|---|---|---|
| nth root | index, radicand | `root(radicand,index)` | ctrl+^; templates grid |
| log with base | base, argument | `log(argument,base)` | ctrl+10ˣ; templates grid |
| absolute value | argument | `abs(argument)` | templates grid |
| piecewise | rows of value, condition | `piecewise(v1,c1,v2,c2,…)` | grid (2 pieces), N pieces… dialog |
| system | rows of one equation | `{eq1,eq2,…}` | grid (2 equations), N equations… dialog, Solve System… |
| d/d□ and d²/d□² | variable, expression | `derivative(expr,var[,2])` | shift+−; Calculus 1; grid; Derivative at a Point… |
| definite ∫ | lower, upper, integrand, variable | `∫(f,var,lower,upper)` | shift++; Calculus 3; grid |
| indefinite ∫ | integrand, variable | `∫(f,var)` | grid |
| Σ and Π | variable, lower, upper, expression | `Σ(expr,var,low,high)` | Calculus 5 and 6; grid |
| limit | variable, point, expression | `limit(expr,var,point)` | Calculus 4; grid |

Still greyed in the grid: nth derivative, degrees-minutes-seconds, subscript.

## How
- The editor keeps a table of the linear form (`_CALLS`) and of the LaTeX (`_LATEX`) per kind, so a new
  template is a row in each table, not a branch through the code. A function-like template after a term
  gets an explicit `*` (`x|y|` is `x*abs(y)`, not `xabs(`).
- Piecewise and system templates are grids like a matrix (`GRIDS`, with their fixed column count): Up
  and Down move between rows, Backspace at the start of a cell steps back a cell. `Template.cols` holds
  the column count; files store it as before, so saved documents keep these templates.
- The entry line draws each kind from small parts (`app/entry.py` `_Parts`): slots at a size (bounds and
  indices at 0.6), and signs, bars and braces that click to the template as a whole, as the fraction bar
  does (decision 0019).
- Template specs for the `template` key action take one number for rows: `system:3`, `piecewise:2`.
- Dialogs can replay key actions (`Wizard.steps`), so Derivative at a Point pastes d/dx(□)|x=v with
  the variable filled in and the cursor in the box, and Solve System pastes `solve(` + the system
  template + `,{x,y})` with the cursor in the first equation, as the device does.

## Engine
- `root(x,n)`: an odd root of a negative number is real (`root(-8,3)` is −2), as on TI.
- `piecewise(v1,c1,…,[otherwise])`: the first true piece; only the chosen piece is evaluated; no true
  piece gives `undef`; symbolic conditions keep the choice (drawn as cases).
- `undef` is now drawn as undef in the history (SymPy's LaTeX printed `NaN`).

## Found, not changed here
- In Real mode `√(-4)` gives `2·ⅈ` and `(-8)^(1/3)` gives `2·(-1)^(1/3)`; the device gives a "Non-real
  result" error and −2. Typed `>=` stays as `>=` in the history entry (the device shows `≥`).
- The LaTeX of a symbolic piecewise result is SymPy's ("for x < 0 / otherwise"); the device's style is
  in the Cowork run.
