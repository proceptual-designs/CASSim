# 0008. Values, modes and number display (M1b)

Date: 2026-11-01. Status: accepted; the choices under "To check on the simulator" are provisional.
Code: `src/cassim/core/{settings,values,evaluator,session,format}.py`, `core/compat/sympy_adapter.py`. Tests: `tests/unit/test_session.py`. Harness: `tools/replay.py`, `tests/corpus/test_replay.py`.

## Decisions

- **`Expr` holds an opaque SymPy object**, and only the adapter looks inside it. Numbers, symbolic expressions and undecided relations are all `Expr`.
- **Results print through the parser's AST.** The adapter turns a result into AST nodes, so one printer decides parentheses for input and output.
- **Final form is decided once**, in `finish`: a float anywhere makes the whole result decimal (SymPy leaves `√(2)+0.5` as a sum), Approximate decimalises everything, CAS Off keeps fractions but no other exact form, and `zoo` and `nan` both become `undef`. Exact numbers are expanded, so `(1+ⅈ)^2` is `2*ⅈ`, while `(x+1)^2` stays as typed.
- **Undefined names echo in lower case**, as the simulator does. Catalog functions not yet written echo too until M1d, except that a list or matrix argument currently gives "Data type".
- **Language from later milestones reports "Not implemented yet"** instead of guessing. This covers most commands, most conversions and matrix powers (assignment, `Define` and `=` constraints arrived in M1c, decision 0009). Broadcasting `^` over a matrix gave a wrong `[1,2;3,4]^-1`, so it is refused until M1d.
- **The corpus harness reports every case but enforces only reviewed ones.** `python -m tools.replay` runs everything; `pending` cases cannot fail the build unless they crash the engine. Statuses change only after Simon's review.
- **Error codes are from the guide.** The restricted-mode error has no code in guide 3.2, and the simulator's number was not captured.

## To check on the simulator

| Entry | Now | Why it is a guess |
|---|---|---|
| `0.002` in Float 3, and `0.0009` | `0.002`, `9.ᴇ-4` | The switch to `ᴇ` below 0.001 fits `1.23ᴇ-4`, but one case does not fix it |
| `0.05` and `0.009` in Fix 2 | `0.05`, `9.00ᴇ-3` | The rule "smaller than one unit of the last place" fits only `5.00ᴇ-3` |
| `1ᴇ12` in Fix 2 | `1.00ᴇ12` | The upper limit for fixed form is assumed |
| `1ᴇ5` in Auto | decimal `100000.` | Could stay an exact integer |
| `sin(x)` then `x:=30` in Degree | settled in M1c: `sin(x)` gives `1/2` because `x` is read before the angle conversion | Assumed from how TI evaluates stored values (0009) |
| `100°` in Gradian mode | `1000/9` | Follows the Radian and Degree rule by analogy |
| `(-8)^(1/3)` in Real mode | SymPy's complex principal root | TI probably gives `-2`; fix in M1d |
| `sqrt(-1)` in Real mode | computes `ⅈ` | Corpus shows a warning triangle, which is not modelled |

## Not done in M1b

- Polar complex display: values are right, but they print in rectangular form. Replay's symbolic comparison will not notice, so a `text` case is needed.
- The `exp_format` setting (Normal, Scientific, Engineering), the 2D layout tree, and base display (`▶Base16`).
- The `family` comparison mode for `@n1` solutions.
