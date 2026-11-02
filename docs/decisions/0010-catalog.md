# 0010. The catalog (M1d, in slices)

Date: 2026-11-02. Status: accepted; the choices under "To check on the simulator" are provisional.
Code: `src/cassim/core/catalog/`, `core/valueops.py`, `core/angles.py`, `core/compat/sympy_adapter.py`. Tests: `tests/unit/test_catalog.py`.

M1d is built in slices, one commit each, so that every slice leaves the corpus and the tests green. Slice 1 is the registry plus the functions that need no new maths engine. Slice 2 is solving, slice 3 calculus and slice 4 distributions and finance and slice 5 statistics. The last slice is conversions and the long tail.

## Decisions

- **One registry, grouped by area.** `catalog/registry.py` holds the table; `elementary`, `algebra`, `lists`, `matrices` and `control` fill it when the package is imported. The evaluator looks a call up there after user functions (so a stored function cannot shadow a built-in: storing to a built-in name is refused).
- **Eager and lazy entries.** An eager entry gets evaluated values (`sin`, `det`). A lazy entry gets the syntax tree and decides what to evaluate: `seq` binds its index, and `when` runs only the chosen branch, which is what lets `u(n):=when(n=1,2,u(n-1)+3)` end. A command (`SortA`) is a third kind.
- **Arity is checked in one place**, before arguments are evaluated: "Too few/many arguments".
- **`cas=True` marks functions CAS Off and Exact Arithmetic refuse outright** (`expand`, `exact`). Other functions are refused only when their result is symbolic, which the existing `finish` rule already does.
- **Catalog modules never touch SymPy.** Everything goes through `sympy_adapter.py`, which is now long. It is still the single place SymPy is imported; if it grows past comfort, the plan is to turn it into a package of the same name (`compat/sympy_adapter/`) so the import path does not change.
- **Angle modes**: a forward trig function converts a *numeric* argument to radians (a symbolic one is left alone); an inverse trig function converts a *numeric* result back to the document's unit. Hyperbolic functions take no angle.
- **TI print names.** The adapter prints `sin⁻¹`, `sinh⁻¹`, `abs`, `real`, `imag`, `angle`, `conj` and `when`. Input still reads `arcsin` and so on (the lexer folds `sin⁻¹` to `arcsin`).
- **`arcsinh(1)` stays unevaluated** in Auto (exact nonzero argument), as the corpus shows. `sinh(ln(2))` is rewritten to `3/4` only when the rewrite is rational, so `sinh(1)` stays as typed.
- **`log(x)` is base 10** and `log(x,b)` is base `b`. `ln` is natural.
- **`Unevaluated` is a value**: a call to a name that is not a function, with a list, matrix or string argument, is echoed as typed (`transpose([1,2;3,4])`). With plain arguments it is a symbolic function application as before. Arithmetic on an `Unevaluated` value reports "Data type" for now.
- **Statistics use exact arithmetic** (`mean({1,2,3,4})` is `5/2`; `stDevSamp` is `4*√(14)/7`). Quartiles, the TI median-of-halves rule, arrive with `OneVar`.
- **Matrix powers**: an integer power is repeated multiplication, a negative one an inverse ("Singular matrix" if the determinant is 0); other exponents are a "Domain error" until needed.
- **`SortA`/`SortD`** sort the stored list named, and reorder any further lists to match the first. A literal gives "Argument must be a variable name" (corpus).

## To check on the simulator

| Entry | Now | Why it is a guess |
|---|---|---|
| Error codes and wording for "Singular matrix", "Memory", "Recursion is too deep" | ours, negative codes | not captured |
| `sin(1)` in Degree, Auto | `sin(π/180)`; the corpus wants `sin(1)` | TI keeps `sin(1)` and still treats it as degrees. Doing this properly needs an angle-aware function class in the adapter, so that `approx(sin(1))` is `0.01745...`. Left as an expected failure (`m15.settings.degree-auto-methods`) |
| `propFrac(7/3)` | `7/3`; the corpus wants `2+1/3` | needs an unevaluated sum; the final-form rule would collapse it |
| `round(2.5)` | `3.` (half away from zero) | assumed |
| `cross` product of two 2-element vectors | a 3-element result with 0, 0, z | assumed |
| `norm` of a matrix | Frobenius norm | assumed |
| `mean`, `median` of an empty list | "Domain error" | TI's wording not captured |

## Not done in slice 1

`solve`, `cSolve`, `zeros`, `cFactor`, `tExpand`, `tCollect`, `eigVl`, `eigVc`, `randInt`, calculus, distributions, finance, statistics commands, and the conversions after `▶` (all later slices of M1d).

## Slice 2: solving

Code: `catalog/solving.py`, the "Solving" section of the adapter, `Evaluator._constrain`. Tests: `tests/unit/test_solving.py`.

- **`solve`, `cSolve`, `zeros`, `cZeros`, `polyRoots`, `polyEval`.** `solve` and friends are lazy: the unknown is read from the argument list as typed, and the equation is evaluated with the unknown bound to a plain symbol, so a stored value (`x:=5`) does not leak in. This also settles the design note in 0009 for `derivative`.
- **Answers are conditions, not sets.** A finite answer is `x=a or x=b` (roots in increasing order, complex ones by real part then imaginary part descending), a range is a relation or chain (`-3≤x≤1`, `x<-2 or x>2`), no solution is `false`, every value is `true`. A system gives `x=2 and y=1`, or several such cases joined by `or`.
- **A `|` condition that is not `x=value` becomes the domain.** `Evaluator` keeps those relations while the left side is evaluated, and `solve` intersects its real answers with them. An enclosing condition that nothing uses is ignored (`x^2|x>0` is `x^2`). The solution is found over the reals and then intersected, because SymPy misses roots when given a bounded domain directly.
- **Degree and gradian mode.** `sin(x)` of a symbol is kept as typed when entered, so `solve` converts the argument of trig functions of the unknown to radians just before solving; the bounds stay plain numbers. Other consumers of such expressions (calculus) must do the same.
- **Roots are checked.** SymPy returns `x=-1` for `ln(x)+ln(x-1)=ln(2)`; every finite root is put back into the equation and dropped if it is not real or does not hold.
- **An equation with symbols is never decided by SymPy.** `x=ⅈ` for a real symbol `x` would be `false`, which would erase every `cSolve` answer, so `relation()` builds `Eq`/`Ne` with `evaluate=False` when either side has symbols and the sides differ (`x=x` is still `true`).
- **Relations are compared in canonical form**, so `2<x` equals `x>2`; and a pair of bounds on one expression prints as a chain.
- **Chained relations** (`0≤x≤2*π`) evaluate to the conjunction of their links.
- **CAS Off and Exact Arithmetic** refuse all of these.

### To check on the simulator

| Entry | Now | Why it is a guess |
|---|---|---|
| `solve(sin(x)=1/2,x)` with no domain | echoed unevaluated | TI gives the family `x=2*@n1*π+π/6 or ...`; the `family` compare mode is not implemented (`methods.solve.trig-general-solution`) |
| `solve(x^2=a,x)` | `x=-√(a) or x=√(a)` | TI adds the condition `a≥0` to each root (`m4.solve.parametric-and-system`) |
| `zeros` with no finite answer | echoed unevaluated | assumed |
| `polyRoots` | real roots, with multiplicity | the Reference Guide's wording was not checked against the CAS build |
| a system with no unique answer that SymPy cannot solve | "Domain error" | assumed |

## Slice 3: calculus

Code: `catalog/calculus.py` and the "Calculus" section of the adapter. Tests: `tests/unit/test_calculus.py`.

- **`derivative`, `integral`, `limit`, `taylor`, `fMax`, `fMin`, `tangentLine`, `normalLine`, `impDif`, `nDerivative`, `nInt`, `nSolve`, `deSolve`.** All are lazy: the variable is read from the argument list as typed and the expression is evaluated with it bound to a plain symbol.
- **A value the variable already had is put in afterwards.** `df(x):=derivative(f(x),x)` evaluates its body with `x` bound to the argument, so `derivative` differentiates first and then substitutes: `df(3)` is `6`, `df(a+1)` is `3*(a+1)^2`, and `derivative(...)|x=2` works for the same reason. Host gained `lookup(name)` for this. The side effect, `x:=4` then `derivative(x^2,x)` giving `8`, is a guess (below).
- **CAS Off**: a symbolic `derivative` reports "Use Derivative at a Point" (the corpus wording); a definite `integral` is allowed and comes out as a decimal; `limit`, `taylor`, `fMax`, `fMin`, `tangentLine`, `normalLine`, `impDif` and `deSolve` are refused.
- **`limit`** takes a direction (1 right, -1 left); with none it is two-sided, so `limit(1/x,x,0)` is `undef`. A limit SymPy cannot find is echoed.
- **`integral`** gives no constant. An antiderivative writes `ln(abs(x))` where the argument is not known to be positive, as TI does (`ln(x^2+1)` stays). `asinh` in a result is rewritten as `ln`. A definite integral of `abs(...)` is split at the sign changes, because SymPy leaves it unevaluated. An integral SymPy cannot do is echoed.
- **`fMax` and `fMin`** return the location (`x=2`), look at critical points and closed finite ends of the domain given by `|`, and give up (echo) if the expression approaches a more extreme value at an unbounded end.
- **`deSolve`** binds `y`, `y'`, `y''`... to a SymPy function and its derivatives while the equation is evaluated (the evaluator reads `y'` only from such bindings). Initial values `y(a)=b` come after `and`. Constants are named `c1`, `c2`, ... in the order their terms print (cosine before sine, for example).
- **Equality of answers** now expands logarithms before comparing, so `ln(a/b)` equals `ln(a)-ln(b)`.

### To check on the simulator

| Entry | Now | Why it is a guess |
|---|---|---|
| `x:=4` then `derivative(x^2,x)` | `8` | TI may refuse a stored variable as the differentiation variable |
| `y'(0)=...` as an initial condition | not supported (`y'(0)` parses as `y'*0`) | needs a parser decision |
| `nSolve` start points | tries 1, 0, -1, 2, -2, 10, -10 | TI's method is not known |
| `fMin(x^3,x)` | echoed | TI may give `x=-∞` or an error |
| calculus in Degree mode | trig is treated as radians | `d/dx sin(x)` in Degree mode needs the angle-aware function class (see slice 1) |
| `integral(sin(x)/x,x,1,2)` | `Si(2)-Si(1)` from SymPy | TI probably gives a decimal or leaves it |

## Slice 4: distributions and finance

Code: `catalog/distributions.py`, `catalog/finance.py`, `core/compat/distributions.py`, `core/compat/finance.py`. Tests: `tests/unit/test_distributions_finance.py`.

- **No SciPy for this.** The continuous distributions (normal, t, chi-square, F) use mpmath, which SymPy already needs, at 30 digits; inverses use `erfinv` for the normal and bisection for the rest. They agree with SciPy to 12 digits on the reference values fixed in the tests. SciPy stays optional and lazy, for the regression fitting in slice 5 if it is needed.
- **Discrete distributions** (`binomPdf/Cdf`, `invBinom`, `geomPdf/Cdf`, `poissPdf/Cdf`) are computed with exact arithmetic, so `binomPdf(10,1/2,5)` is `63/256` and `binomPdf(10,0.5,5)` is `0.24609375`. Poisson always gives a decimal.
- **Argument shapes** follow the TI forms: `normCdf(lower,upper[,μ,σ])`, `binomCdf(n,p[,lower],upper)`, `binomPdf(n,p)` with no `x` lists every k, a list `x` gives a list, `∞` is allowed as a bound.
- **Distributions work in CAS Off**, as the corpus shows; they are not marked `cas`.
- **Finance**: `tvmN/I/PV/Pmt/FV` take the four unknown-complement values and then `[PpY, CpY, PmtAt]` (defaults 1, 1, end). The per-period rate is `(1+I/(100·CpY))^(CpY/PpY)-1`. `tvmI` brackets a sign change on a grid of rates and bisects. `eff`, `nom`, `amortTbl`, `bal`, `ΣInt` and `ΣPrn` are included; the table rounds the payment and every amount to 2 decimals (the corpus values are consistent with that) and the first payment at the start of a period pays no interest.

### To check on the simulator

| Entry | Now | Why it is a guess |
|---|---|---|
| `tvm*` with `PmtAt` 1 | annuity-due formula | only the end-of-period case is in the corpus |
| `amortTbl` with `PmtAt` 1, or a non-default `round` | as described above | not in the corpus |
| `binomPdf(10,1/2,5)` | exact `63/256` | TI may give a decimal |
| `invBinom` when the area is not reached | `n` | assumed |
| `tvmN` for an impossible loan | "Domain error" | TI's wording not captured |

## Slice 5: statistics and regression

Code: `catalog/statistics.py`, `core/compat/statistics.py`. Tests: `tests/unit/test_statistics.py`.

- **`OneVar`, `TwoVar`, `LinRegBx`, `LinRegMx`, `QuadReg`, `CubicReg`, `QuartReg`, `ExpReg`, `PowerReg`, `LnReg`, `MedMed`, `Logistic`, `LogisticD`, `SinReg`.** Arguments are `[count,] X[, Y][, Freq]`; a leading plain number is TI's count of lists and is ignored, and a frequency may be a list or one number.
- **Results go to `stat.` variables**: `stat.results` (a matrix of label and value, with strings in the first column), `stat.values` (one row, title first), and one variable for each number (`stat.a`, `stat.r²`, `stat.sx`, `stat.q1x`, ...). Matrices can now hold strings for this reason (`Cell = Expr | Str`); arithmetic on one gives "Data type". The `Resid` cell shows `"{...}"` as on the calculator, and the residuals are in `stat.resid`.
- **Quartiles use the school convention** (median of the halves, the median left out when n is odd): `6.5` and `42.5` for the squares to 64, not NumPy's `7.75` and `39.25`. Checked with Hypothesis properties.
- **No NumPy or SciPy.** Sums, quartiles, straight-line and polynomial fits are exact (`Fraction`, Gauss-Jordan on the normal equations), so exact data gives exact coefficients. Exponential, power and logarithmic fits straighten the data with logarithms and use the line's `r`. `Logistic` and `LogisticD` use Levenberg-Marquardt from a first guess found by straightening; `SinReg` scans frequencies (for a fixed frequency the model is linear) and refines with a golden-section search. `SinReg` reports `b` in radians per unit of x whatever the angle mode, as the corpus shows.
- **Corpus edit**: four steps (`cl:=`, `cv:=`, `cg:=`, `cd:=` in `029_more_regressions` and `032_logisticd`) compared the whole data list with what was readable on screen (the notes say only the first four to eight values were visible). They are now `compare: ignore`; the `stat.` steps that follow are what the cases test.

### To check on the simulator

| Entry | Now | Why it is a guess |
|---|---|---|
| Titles and `RegEqn` text for `Logistic`, `LogisticD`, `SinReg`, `LnReg`, `MedMed`, `CubicReg`, `QuartReg` | plausible wording | only the labels in the corpus are verified |
| `stat.values` for `OneVar` | one row, as for `TwoVar` | only `TwoVar` is in the corpus |
| `MedMed` group sizes for n = 3k+1 and 3k+2 | k,k+1,k and k+1,k,k+1 | the usual rule; only n = 6 is in the corpus |
| `Logistic` first guess and stopping rule | see above | TI's own algorithm differs, so noisy data may converge to a different local fit |
| `r` and `r²` for the transformed fits | of the straightened line | matches the corpus for exact data only |
| the `Save RegEqn` / category / include arguments | ignored | not implemented |
