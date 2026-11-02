# 0010. The catalog (M1d, in slices)

Date: 2026-11-02. Status: accepted; the choices under "To check on the simulator" are provisional.
Code: `src/cassim/core/catalog/`, `core/valueops.py`, `core/angles.py`, `core/compat/sympy_adapter.py`. Tests: `tests/unit/test_catalog.py`.

M1d is built in slices, one commit each, so that every slice leaves the corpus and the tests green. Slice 1 (this record) is the registry plus the functions that need no new maths engine. Later slices: solve and friends, calculus, distributions and finance, then statistics and the regression commands.

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
