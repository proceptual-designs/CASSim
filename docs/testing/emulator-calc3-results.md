# Emulator check 5: Calculator page leftovers (Part B)

Run on the TI-Nspire CX CAS Premium Teacher Software 6.0.3.374 (CX II-T CAS handheld view), Handheld-page-size Document1, 250% zoom, 2026-11-12.
Settings: Radian, Automatic, Real, Float 8 (RAD in the title bar), CAS On. Page used: a new Calculator page in the same Problem as Part E and F (variables `xs`, `ys`, `d1`, `cat`, `c`, `v`, `f1`, `f2`, `m1` and the `stat…` variables exist; `d2` was deleted by F18). Observations only. Screenshots in `pages-shots-5/` (zoomed to the handheld screen).

## B item 4: Menu leaves with small examples (typed with the CAS spellings below; `^` left with Right; `infinity` typed)

| Typed | Displayed (verbatim) | Screenshot |
|---|---|---|
| `getNum(2/3)` | `2` | B4-getnum-getdenom-completesquare.png |
| `getDenom(2/3)` | `3` | same |
| `completeSquare(x^2+4x+1,x)` | `(x+2)²-3` | same |
| `polyRoots(x^2-1,x)` | `{-1,1}` | B4-polyroots-cpolyroots-polyremainder.png |
| `cPolyRoots(x^2+1,x)` | `{-ⅈ,ⅈ}` | same |
| `polyRemainder(x^2+1,x-1,x)` | `2` | same |
| `polyQuotient(x^2+1,x-1,x)` | `x+1` | B4-polyquotient-polygcd-polycoeffs.png |
| `polyGcd(x^2-1,x-1)` | `x-1` | same |
| `polyCoeffs(3x^2+2,x)` | `{3,0,2}` | same |
| `polyDegree(3x^2+2,x)` | `2` | B4-polydegree-arclen.png |
| `arcLen(x^2,x,0,1)` | `ln(√5+2)/4+√5/2` (stacked fractions: ln(√5 +2) over 4, plus √5 over 2) | same |
| `series(sin(x),x,5)` | `x-x³/6+x⁵/120` | B4-series-dominantterm.png |
| `dominantTerm(x^3+x,x,infinity)` | `x³`; the history line shows a yellow warning triangle at its left (its text was not opened) and the `∞` in the argument | same |
| `centralDiff(x^2,x)` | `2.·x` | B4-centraldiff-nfmin-nfmax.png |
| `nfMin(x^2-2x,x)` | `0.99999986` | same |
| `nfMax(-x^2,x)` | `0.` | same |
| `newMat(2,3)` | `[[0 0 0][0 0 0]]` (2x3 matrix of zeros) | B4-newmat-diag-colaugment.png |
| `diag([1,2;3,4])` | `[1 4]` (a 1x2 row matrix) | same |
| `colAugment([1,2],[3,4])` | `[[1 2][3 4]]` (no error: the second row matrix is appended below) | same |
| `constructMat(i+j,i,j,2,2)` | `[[2 3][3 4]]` | B4-constructmat-ref.png |
| `ref([1,2;3,4])` | `[[1 4/3][0 1]]` (4/3 drawn as a stacked fraction) | same |

Spelling confirmed by typing: `polyGcd(` and `polyCoeffs(` (the history shows `polyGcd` and `polyCoeffs`; the typed spelling is accepted exactly like this).

## B item 5: Recall Definition and Insert Comment
- Actions menu (Menu 1): `1 Define`, `2 Recall Definition`, `3 Delete Variable`, `4 Clear a-z…`, `5 Clear History`, `6 Insert Comment`, `7 Library ▶`, `8 Lock ▶` (separators before 3 and before 6 and before 7). Screenshot B5-actions-menu.png.
- Recall Definition (Menu 1 2) opened a list with a function icon `f(x)` beside each name: `f`, `f1`, `f2`, `m1`, `stat.stat`, `stat1.stat`, `stat2.stat`, `stat3.regeqn`, `stat3.stat`, `stat4.stat`, `stat5.stat`, `stat6.stat` … (scrolls). **The plain variables `a:=3` and the matrix `m:=[1,2;3,4]` and the expression variable `g:=x+1` were NOT in the list**; only function-type variables (user functions, plotted functions, `stat…` variables) were. Screenshot B5-recall-definition-list.png.
- Insert Comment (Menu 1 6): the entry line takes text; typing `note one` and Return gave a history line **`©note one`** (a © sign before the text, no result line). Screenshot B5-insert-comment.png. Up from an empty line (twice) went to the matrix result above, skipping the comment; Return then pasted the matrix result `[[1 2][3 4]]` onto the entry line. Whether a comment line can be brought down: not tested further. Screenshot B5-up-up-return-pastes-matrix.png.

## B item 8: New questions from check 4
- Units (Automatic mode): `3_m` gave `3.·_m` (check 4); `3_m+2_m` gave `5.·_m`; `2_km▸_m` (typed `2_km@>_m`) gave `2000.·_m`; `_c` gave `2.9979246ᴇ8·_m/_s` (a stacked fraction `_m` over `_s`); `_g` gave `9.80665·_m/_s²`. The entry line draws the typed `3_m` as `3·_m`, and the unit names are italic only for `_km`'s `m`. Exact mode: not run. Screenshot B8-units-results.png.
- `g:=x+1` then `g` gave `x+1`. `f` alone (where `f(x):=x^2`) opened an error dialog **"Error" / "Argument Error"** and the history line shows `"Error: Argument Error"`. Screenshot B8-solve-g-f-argument-error.png.
- `a or b` (with `b:=5`, `a` undefined) opened an error dialog **"Error" / "Argument must be a Boolean expression or integer"**; the history line shows `"Error: Argument must be a Boolean expressi▸` cut off by an arrow. Screenshot B8-a-or-b-error-dialog.png.
- `SOLVE(x=1,x)` gave `solve(x=1,x)` in the history and result `x=1` (the name is case-insensitive and drawn lowercase). `Sin(x)` gave `sin(x)` and result `sin(x)`. `not true` gave `false`. `2 xor 3` gave `1`. Screenshot B8-sin-not-xor.png, B8-solve-g-f-argument-error.png.

## Lists

**Run on the emulator:** B4 (the 21 small examples), B5 (Recall Definition list, Insert Comment), B8 (units in Automatic, `g`, `f`, `a or b`, `SOLVE`, `Sin`, `not true`, `2 xor 3`).

**Not run (reason):**
- B1 history plan rows (H1 to H9), B2 editor plan rows, B3 every row of `simulator-todo.md`: time.
- B4 menu routes: Algebra > 8 Polynomial Tools scrolled to the end and 1 Find Roots of Polynomial… dialog; Statistics routes for Sample, Multiple Linear Regression, Correlation Matrix, Fill, Difference List, Mid; Matrix & Vector scrolled past A Element Operations, 9 Row Operations, Trace, LU, QR, Characteristic Polynomial, Norms and Dimensions submenus: time.
- B6 menu scrolling with ctrl keys, wheel, arrow click and drag in long menus: time.
- B7 Part A leftovers (`stat.x̄`, Define from the Actions menu, a library call): time.
- B8 units in Exact mode: Document Settings were not changed.

**Also seen, not covered:**
- `dominantTerm(…,∞)` shows a warning triangle in the history.
- A later typed line is swallowed when an error dialog is open: press Return (OK) first.
