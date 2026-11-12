# 0030: Calculator random numbers repeat the handheld's sequence

Status: accepted 2026-11-12. Requirements: FR-CAT-002. Pseudocode random numbers are a separate matter (FR-PSE-007 keeps CPython's `random`).

## Context

Emulator check 5 (`docs/testing/emulator-catalog2-results.md`, C3) recorded what the Teacher Software gives after `RandSeed`:

| Typed | Shown |
|---|---|
| `RandSeed 1147`, `randInt(3,10,4)` | `{4,8,6,4}` |
| `RandSeed 1147`, `randBin(80,.5,3)` | `{44,34,47}` |
| `RandSeed 1`, `randBin(10,0.5,3)` | `{6,6,3}` |
| `RandSeed 1`, `randNorm(0,1,3)` | `{0.62742879,-0.17147098,-0.55931652}` |
| `RandSeed 1147`, `randNorm(0,1)`, `randNorm(3,4.5)` | 0.49254098, -3.5435597 |
| `RandSeed 1147`, `randPoly(x,5)` | `-2·x⁵+3·x⁴-6·x³+4·x-6` |
| `RandSeed 1147`, `randMat(3,3)` | `[[8,-3,6],[-2,3,-6],[0,4,-6]]` |

CASSim used Python's `random.Random`, so a seeded entry gave different numbers from a student's handheld. Teachers set `RandSeed` so a class gets the same numbers, so matching matters.

## Decision

The calculator's generator is L'Ecuyer's published combined multiplicative generator (CACM 31(6), 1988: multipliers 40014 and 40692, moduli 2147483563 and 2147483399). `RandSeed n` sets the two states to `40014·n mod 2147483563` and `n mod 2147483399`, and `RandSeed 0` to 12345 and 67890. Each command uses it as follows:

- `rand()`: `(s₁ - s₂)/2147483563`, plus 1 if negative.
- `randInt(a,b)`: `a + int((b-a+1)·rand())`.
- `randBin(n,p)`: the number of `n` draws with `rand() < p`.
- `randNorm(μ,σ)`: Marsaglia's polar method on `v = 2·rand()-1` pairs, rejecting `s ≥ 1`, and keeping only the **second** value of the pair: `μ + σ·v₂·√(-2 ln s / s)`.

Every value in the table above that uses these four commands is reproduced exactly; the tests are in `tests/unit/test_conversions.py`. `randPoly` and `randMat` are not built yet (command matrix: todo). The recorded values fit `randInt(-9,9)` draws, with `randPoly` filling coefficients from the constant term upwards and `randMat` filling from the last element backwards. Check this when they are built.

The generator starts from a random seed, so an unseeded session is not repeatable, as before. A `RandSeed` argument that is not an integer still reseeds at random (not observed on the device).

## Clean room

This was found by comparing observed outputs with published algorithms (decision 0028). No TI software was inspected. The guide's printed `randBin(80,.5,3)` value `{47.,41.,46.}` disagrees with the emulator; we match the emulator.
