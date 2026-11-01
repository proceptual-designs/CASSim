# VCE command priority list and corpus coverage

Generated from the corpus (`corpus/seed/*.yaml`, excluding CAS Off / Exact Arithmetic cases). A count is the number of cases whose steps use the command at least once. Zero means a gap: no simulator capture yet.

Priorities (P1 = needed on every exam day, P2 = frequent, P3 = occasional) are a first draft for Simon to adjust.

## General Mathematics

| Priority | Commands | Used for | Corpus cases (per command) |
|---|---|---|---|
| P1 | `solve / nSolve` | equations, inequalities, numerical roots | solve 24, nSolve 1 |
| P1 | `round, floor, abs, sqrt, mod` | number handling | round 2, floor 1, abs 4, sqrt 14, mod 1 |
| P1 | `sin, cos, tan, arcsin ...` | trigonometry (degrees in General preset) | sin 17, cos 5, tan 3, arcsin 3 |
| P1 | `mean, median, OneVar` | one-variable statistics | mean 1, median 1, OneVar 1 |
| P2 | `TwoVar` | two-variable statistics | TwoVar 1 |
| P1 | `LinRegMx, QuadReg, ExpReg, PowerReg` | regression models | LinRegMx 1, QuadReg 1, ExpReg 1, PowerReg 1 |
| P1 | `tvmN, tvmI, tvmPV, tvmFV` | finance solver | tvmN 1, tvmI 1, tvmPV 1, tvmFV 2 |
| P2 | `amortTbl` | loan amortisation table | amortTbl 1 |
| P1 | `binomPdf, binomCdf, normCdf, invNorm` | probability | binomPdf 2, binomCdf 2, normCdf 2, invNorm 3 |
| P1 | `nCr, seq, sum, cumulativeSum` | counting, sequences, recursion | nCr 1, seq 4, sum 4, cumulativeSum 1 |
| P3 | `SortA, dim` | list handling | SortA 2, dim 1 |
| P2 | `factor, expand` | algebra | factor 6, expand 6 |

## Mathematical Methods

| Priority | Commands | Used for | Corpus cases (per command) |
|---|---|---|---|
| P1 | `solve, zeros, nSolve, cSolve` | equations; exact and numerical | solve 24, zeros 1, nSolve 1, cSolve 4 |
| P1 | `factor, expand, comDenom, propFrac, tExpand, tCollect` | algebraic and trig forms | factor 6, expand 6, comDenom 2, propFrac 2, tExpand 1, tCollect 1 |
| P1 | `Define, :=, when` | functions, piecewise, recursion | Define 1, when 3 |
| P1 | `derivative, nDerivative, tangentLine` | differentiation | derivative 7, nDerivative 1, tangentLine 1 |
| P1 | `integral, nInt` | definite and indefinite integrals, area | integral 12, nInt 1 |
| P1 | `fMax, fMin` | optimisation | fMax 2, fMin 1 |
| P2 | `limit, taylor` | limits, series | limit 5, taylor 1 |
| P1 | `exp, ln, log` | exponential and log functions | exp 10, ln 5, log 1 |
| P1 | `arcsin, arccos, arctan` | inverse trig | arcsin 3, arccos 1, arctan 1 |
| P1 | `binomPdf, binomCdf, normPdf, normCdf, invNorm, invBinom, geomPdf` | distributions | binomPdf 2, binomCdf 2, normPdf 1, normCdf 2, invNorm 3, invBinom 1, geomPdf 1 |
| P2 | `OneVar, LinRegMx` | sample statistics, regression | OneVar 1, LinRegMx 1 |
| P2 | `seq, sum, product, nCr` | sequences and counting | seq 4, sum 4, product 1, nCr 1 |
| P2 | `deSolve` | differential equations | deSolve 4 |

## Specialist Mathematics

| Priority | Commands | Used for | Corpus cases (per command) |
|---|---|---|---|
| P1 | `cSolve, cZeros, cFactor` | complex roots and factorisation | cSolve 4, cZeros 1, cFactor 2 |
| P1 | `conj, angle, real, imag, abs, Polar, Rect` | complex number forms | conj 1, angle 1, real 1, imag 1, abs 4, Polar 1, Rect 1 |
| P1 | `crossP, dotP, norm, unitV` | vector algebra | crossP 2, dotP 1, norm 1, unitV 1 |
| P1 | `det, rref, simult, identity, augment, eigVl, eigVc` | matrices | det 3, rref 2, simult 1, identity 1, augment 1, eigVl 1, eigVc 1 |
| P1 | `integral, derivative, impDif` | calculus incl. volume, arc length, implicit differentiation | integral 12, derivative 7, impDif 1 |
| P2 | `deSolve` | first and second order ODEs | deSolve 4 |
| P2 | `limit, taylor` | limits, series | limit 5, taylor 1 |
| P2 | `sec, csc, cot, sinh, cosh` | reciprocal and hyperbolic trig | sec 1, csc 1, cot 1, sinh 1, cosh 1 |
| P3 | `tExpand, tCollect, propFrac, comDenom` | forms | tExpand 1, tCollect 1, propFrac 2, comDenom 2 |
| P1 | `solve, nSolve, factor, expand` | algebra core | solve 24, nSolve 1, factor 6, expand 6 |

## Known gaps and notes

- `TwoVar` returns its results in `stat.values` (a column), not `stat.results`.
- The list statistics functions are `stDevSamp`, `stDevPop`, `varSamp`, `varPop`. `stdDev`, `variance`, `sort` and `transpose` are not functions in this build (echoed unevaluated); use `SortA` (needs a variable name) and the `ᵀ` operator.
- Priorities are not yet checked against the VCE study designs or the exam-style question banks.
