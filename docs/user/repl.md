# Using CASSim at the command line

CASSim has a text interface that behaves like the Calculator page of a TI-Nspire CX CAS. You type an entry, press Enter, and see the result. It is the quickest way to try the engine before the graphical app exists, and it is handy for checking an answer or running a set of entries from a file.

You do not need to know Python to use it.

## Starting it

Open a terminal in the CASSim folder (`C:\dev\CASSim`) and run:

```powershell
uv run cassim
```

You will see a short banner and a `cassim>` prompt. Type entries as you would on the handheld. Type `:quit` to leave (Ctrl-D also works; in a plain console without completion it is Ctrl-Z then Enter).

```
cassim> solve(x^2-4=0,x)
x=-2 or x=2
cassim> derivative(x^3,x)
3*x^2
cassim> integral(x^2,x,0,3)
9
```

Other ways to start it:

| Command | What it does |
|---|---|
| `uv run cassim --course methods` | Start with the settings of a course: `general` (Degree, Approximate), `methods` (Radian, Auto), `specialist` (Radian, Auto, Rectangular) or `none` (the defaults). |
| `uv run cassim --set angle=degree` | Change a setting at the start. Repeat `--set` for more. |
| `uv run cassim -c "solve(x^2=2,x)"` | Work out one entry, print the result and exit. |
| `uv run cassim run lesson.tib` | Run the entries in a file (see [Scripts](#scripts)). |
| `uv run cassim --ascii` | Print results in plain keyboard spelling (see [Spellings](#typing-the-special-symbols)). |

If the maths symbols (`ⅇ`, `π`, `√`) come out as question marks or boxes, use Windows Terminal (the default on Windows 11) or add `--ascii`.

## Typing entries

Entries follow the TI syntax. A few things that are worth knowing:

- **Case does not matter** for names, as on the handheld: `A` and `a` are the same variable, and `Solve(` works.
- **Implied multiplication** works: `2x` is `2*x`, but `2e3` is `2*e3`, because `e` is an ordinary variable. For Euler's number use `@e` (see below) and for powers of ten use `3.14@E6`.
- **Several statements on one line** are separated by `:`. The result shown is the last one's: `a:=2:a^10` gives `1024`.
- **Division by zero and `ln(0)`** give `undef`, not an error. An undefined variable just echoes back.
- **Lists** use braces `{1,2,3}`, **matrices** use `[1,2;3,4]` (a semicolon starts a new row).
- **`Ans`** holds the last result; `ans*2` doubles it.

### Typing the special symbols

The handheld has keys for symbols that a plain keyboard does not. At the prompt, type the spelling on the left; CASSim shows the symbol on the right.

| You type | You see | Meaning |
|---|---|---|
| `pi` | `π` | pi |
| `@e` | `ⅇ` | Euler's number (plain `e` is just a variable) |
| `@i` | `ⅈ` | the imaginary unit (plain `i` is just a variable) |
| `infinity` | `∞` | infinity |
| `3.14@E6` | `3140000.` | the exponent marker `ᴇ` |
| `<=`, `>=`, `/=` | `≤`, `≥`, `≠` | comparisons |
| `->` | `→` | store: `5->a` is the same as `a:=5` |
| `sqrt(2)` | `√(2)` | square root |
| `@>` | `▶` | conversion: `255@>Base16` |
| `@t` | `ᵀ` | transpose: `[1,2;3,4]@t` |
| `@d`, `@r`, `@g` | `°`, `ʳ`, `ᵍ` | degree, radian and gradian marks |
| `sin^-1(x)`, `arcsin(x)` or `sin⁻¹(x)` | `sin⁻¹(x)` | inverse sine. All three spellings mean the same, for the other trig and hyperbolic functions too. `sin(x)^-1` is still `1/sin(x)`. |

With `--ascii`, results are printed back in the typed spellings (`pi`, `sqrt(2)`, `arcsin(x)`), which is useful if you want to paste them somewhere.

### Giving an answer as a decimal (Ctrl+Enter)

On the handheld, **Ctrl+Enter** works out an entry and shows the answer as a decimal, whatever the Calculation Mode is. It is the same as wrapping the entry in `approx(...)`.

At the prompt, put `:approx` in front of the entry:

```
cassim> 1/3
1/3
cassim> :approx 1/3
0.33333333
cassim> :approx solve(x^2=2,x)
x=-1.4142136 or x=1.4142136
```

With a real terminal you can press **Alt+Enter** instead of typing `:approx`. **Ctrl+Enter** works too in terminals that report it as a separate key; many send a plain Enter, which the program cannot tell apart, so use Alt+Enter or `:approx` if Ctrl+Enter does nothing. In practice: **Alt+Enter works in the VS Code terminal, Ctrl+Enter works in Windows Terminal, and `:approx` works everywhere.**

**On an empty line**, it gives the previous answer as a decimal, as on the handheld: enter `1/3`, then press Alt+Enter (or Ctrl+Enter) on the empty prompt, or type `:approx` alone. If there is no previous answer yet, nothing happens. `Done` is not an answer, so it is skipped.

Only the answer is changed: `:approx a:=1/3` shows `0.33333333`, but `a` still holds the exact `1/3`. The decimal answer becomes `Ans`. The graphical app will have the real Ctrl+Enter key, using the same engine option (`Session.eval(line, approximate=True)`).

## Variables and functions

```
cassim> a:=5
5
cassim> 7->b
7
cassim> a*b
35
cassim> f(x):=x^2-3x
Done
cassim> f(4)
4
cassim> Define g(x,y)=x*y+1
Done
cassim> g(2,3)
7
cassim> DelVar a,b
Done
```

- `:=`, `->` and `Define` store values and functions. A function keeps its definition and is worked out each time you call it, so it sees the *current* values of other variables.
- **`DelVar name`** removes a variable or function. **`ClearAZ`** removes every single-letter variable.
- All variables belong to the current **Problem**. `:new` starts a fresh Problem and clears them, like adding a Problem on the handheld.
- You cannot store to a name that already means something (`pi`, `sin`, `ans`, ...).
- **Watch for variables left over from earlier work.** If `x` still holds a list (say from the regression example below), an entry that uses `x` as the unknown can fail with "Data type". `solve(...,x)` and `derivative(...,x)` treat the unknown as a symbol, but a condition after `|` or an ordinary entry uses the stored value. Clear it with `DelVar x`, or start fresh with `:new`.
- **`|` (such that)** substitutes a value or limits a search: `x^2+1|x=3` gives `10`, and `solve(x^2=4,x)|x>0` gives `x=2`.

## Settings

Settings are the same ones as in Document Settings. Show them with `:settings`; change them with `:set`:

```
cassim> :set angle=degree calc=approximate
angle=degree  calc=approximate  domain=real  digits=float8  cas_mode=on  exp_format=normal  case=insensitive  pretty=off  ascii=off
cassim> sin(30)
0.5
```

| Setting | Values | Notes |
|---|---|---|
| `angle` | `radian`, `degree`, `gradian` | `sin(30)` is `1/2` in `degree`. Inverse functions answer in the same unit. |
| `calc` | `auto`, `exact`, `approximate` | `auto` keeps exact results until a decimal appears; `approximate` turns everything into decimals. |
| `domain` | `real`, `rectangular`, `polar` | `polar` writes complex results as `r*ⅇ^(ⅈ*θ)`. |
| `digits` | `float1` to `float12`, `fix0` to `fix12` | Display digits, as in Float 8 or Fix 2. |
| `cas_mode` | `on`, `exact_arithmetic`, `off` | Off and Exact Arithmetic refuse symbolic work: `solve`, `expand`, and a result containing a variable give "CAS computations are restricted". |
| `exp_format` | `normal`, `scientific`, `engineering` | How decimals with large or small exponents are shown. |
| `case` | `insensitive`, `sensitive` | `insensitive` (the default, as on the handheld) makes `x` and `X` one variable. `sensitive` makes them two, for variables and your own functions (`f` and `F`). Built-in names (`sin`, `Pi`, `solve`) and the `stat.` results stay case insensitive. Switching back to `insensitive` merges names that differ only in case; the later one wins. |
| `pretty` | `off`, `on` | `on` draws results in two dimensions, like SymPy's `pprint` (see below). |
| `ascii` | `off`, `on` | `on` spells results with keyboard characters (`pi`, `sqrt(2)`, `@e`, `arcsin`) so they can be copied and pasted back in. The same as starting with `--ascii`. In the graphical app this is a Document Setting. |

Both `:set angle=degree` and `:set angle degree` work.

### Pretty printing

`:set pretty=on` draws fractions, powers, roots and matrices over several lines. Digits, `ⅇ`, `π` and `sin⁻¹` follow the same rules as the one-line text:

```
cassim> :set pretty=on
cassim> (x+1)^2/3 + sqrt(x+1)
                  2
  ▁▁▁▁▁    (x + 1)
√ x + 1 + ──────────
              3
```

With `--ascii` it draws with plain characters (`-` for the bar, `\/` for roots, `/ | \` for brackets). `:set pretty=off` goes back to one line. Only what is printed changes: results, `Ans` and stored variables are the same either way.

## What it can do

Everything here uses the TI names. Press **Tab** after the first letters of a name to complete it.

- **Algebra:** `expand`, `factor`, `cFactor`, `propFrac`, `comDenom`, `tExpand`, `tCollect`, `exact`, `approx`.
- **Solving:** `solve`, `cSolve`, `zeros`, `cZeros`, `polyRoots`, `nSolve`. Systems work: `solve({x+y=3,x-y=1},{x,y})`. A condition after `|` restricts the answers: `solve(sin(x)=0.5,x)|0<=x<=2*pi`.
- **Calculus:** `derivative(f(x),x)`, `derivative(f(x),x,2)`, `integral(f(x),x)`, `integral(f(x),x,a,b)`, `limit`, `taylor`, `fMax`, `fMin`, `tangentLine`, `impDif`, `nInt`, `nDerivative`, `deSolve(y'=y and y(0)=2,x,y)`.
- **Lists and statistics:** `seq`, `sum`, `product`, `mean`, `median`, `stDevSamp`, `stDevPop`, `cumulativeSum`, `SortA`, `SortD`, `dim`.
- **Matrices and vectors:** `det`, `rref`, `identity`, `simult`, `eigVl`, `eigVc`, `dotP`, `crossP`, `norm`, `unitV`, and powers such as `[1,2;3,4]^-1`.
- **Probability:** `normPdf`, `normCdf`, `invNorm`, `binomPdf`, `binomCdf`, `invBinom`, `geomPdf`, `poissPdf`, `tCdf`, `invT`, `chi2Cdf`, `fCdf`, and more.
- **Finance:** `tvmN`, `tvmI`, `tvmPV`, `tvmPmt`, `tvmFV`, `eff`, `nom`, `amortTbl`.
- **Conversions:** `x@>Base16`, `@>DD`, `@>DMS`, `@>Rad`, `@>Grad`, `@>Polar`, `@>Rect`, `@>Cylind`, `@>Sphere`, `@>approxFraction(0.001)`, `@>Decimal`.
- **Random numbers:** `rand`, `randInt`, `randNorm`, `randBin`, `RandSeed`.

A name that is not a function is not an error: `stdDev({1,2,3})` echoes back unevaluated, exactly as on the handheld.

### Statistics and regression

`OneVar`, `TwoVar` and the regression commands (`LinRegMx`, `LinRegBx`, `QuadReg`, `CubicReg`, `QuartReg`, `ExpReg`, `PowerReg`, `LnReg`, `MedMed`, `Logistic`, `LogisticD`, `SinReg`) put their results in `stat.` variables:

```
cassim> x:={1,2,3,4,5}
{1,2,3,4,5}
cassim> y:={2,4,5,4,5}
{2,4,5,4,5}
cassim> LinRegMx x,y
Done
cassim> stat.m
0.6
cassim> stat.b
2.2
cassim> stat.r²
0.6
cassim> stat.results
["Title","Linear Regression (mx+b)";"RegEqn","m*x+b";"m",0.6;"b",2.2;"r²",0.6;"r",0.77459667;"Resid","{...}"]
```

Quartiles follow the school convention (the median of the lower and upper halves), so the first quartile of `{1,4,9,16,25,36,49,64}` is `6.5`, not the `7.75` a spreadsheet gives.

Other `stat.` variables include `stat.n`, `stat.v` (mean of x), `stat.sx`, `stat.σx`, `stat.minx`, `stat.q1x`, `stat.medx`, `stat.q3x`, `stat.maxx`, `stat.a`, `stat.b`, `stat.c`, `stat.d`, `stat.resid` and `stat.values`.

## Commands for the REPL itself

These start with a colon and are not part of the TI language.

| Command | What it does |
|---|---|
| `:help` | Show a short reminder. |
| `:settings` | Show the current settings. |
| `:set key=value ...` | Change settings. |
| `:approx ENTRY` | Give ENTRY as a decimal, like Ctrl+Enter. |
| `:vars` | List the variables and functions you have defined. |
| `:new` | Start a new Problem and clear the variables. |
| `:quit` | Leave (so does Ctrl-D). |

## Scripts

A script is a plain text file with one entry per line. Blank lines and lines starting with `//` are skipped. Settings commands work too.

```
// lesson.tib: the cubic from Exercise 4
:set angle=radian
f(x):=x^3-3*x
solve(f(x)=0,x)
derivative(f(x),x)
integral(f(x),x,0,2)
```

```powershell
uv run cassim run lesson.tib
```

CASSim prints each entry with its result. Useful options:

| Option | Effect |
|---|---|
| `--quiet` | Print only the results, not the entries. |
| `--keep-going` | Carry on after an error. Without it the script stops at the first error. |
| `--course`, `--set`, `--ascii` | As above, placed before `run`: `uv run cassim --course methods run lesson.tib`. |

Use `-` instead of a file name to read entries from standard input. The exit status is `0` if every entry worked, `1` if an entry gave an error, and `2` if the file or an option was wrong, so scripts can be used in automated checks.

## When something goes wrong

| You see | It means |
|---|---|
| `Error: Syntax error` | The entry is not valid TI syntax. Check brackets and operators. |
| `Error: Too few arguments` / `Too many arguments` | A function got the wrong number of arguments. |
| `Error: Data type` | A function got something of the wrong kind, such as a text string where a number is needed. |
| `Error: Domain error` | The values are outside what the function accepts (for example `invNorm(1.5)`). |
| `Error: CAS computations are restricted...` | `cas_mode` is `off` or `exact_arithmetic`. Use `:set cas_mode=on`. |
| `Error: Not implemented yet: ...` | CASSim does not do that yet. Programs (`If`, `For`, `While`, `Local`) are not available. |

CASSim aims to match the **values** the handheld gives. Where it prints a result slightly differently (for example the order of terms in a sum), the answers are mathematically the same. If you find a result that differs from the TI-Nspire, please note the entry and the settings; it is a bug worth recording.

## Not available yet

- Programs and functions with control flow (`If`, `For`, `While`, `Local`, `Return`, `Disp`).
- Graphs, tables, the spreadsheet and Data & Statistics plots. Those arrive with the graphical app.
- Library functions (`.tns` files).
