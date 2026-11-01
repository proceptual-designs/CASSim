# 0009. Variables, user functions and constraints (M1c)

Date: 2026-11-02. Status: accepted; the choices under "To check on the simulator" are provisional.
Code: `src/cassim/core/{scope,evaluator,session}.py`. Tests: `tests/unit/test_scope.py`. Corpus: `scope.*`, `m12.state.*`.

## Decisions

- **One namespace per Problem.** `Scope` holds variables and user functions together, case-insensitively, as TI does (a function is a variable of type function). `Session.new_problem()` clears it; adding a page keeps it.
- **`:=`, `→` and `Define` share one path.** A variable target evaluates the value and stores it; a function target `f(x,y)` stores the parameter names and the body *as typed*. Variable assignments return the stored value, function definitions and `Define` return `Done`.
- **`Done` is a value** (`Void`). It prints as `Done`, and it does not replace `Ans`.
- **Functions are evaluated at each call.** The body is evaluated with the parameters bound to the evaluated arguments, so `g(a+1)` substitutes a symbolic argument, and global variables are read at the call (`a:=3` after defining `f(x):=a*x` changes `f`). A body cannot see the caller's parameters, only its own and the Problem's variables.
- **Recursion is capped** at 50 open user-function calls (`Recursion is too deep`), so a runaway definition fails cleanly instead of overflowing the Python stack, which is smaller under Pyodide.
- **`expr|x=value`** evaluates `expr` with each named variable temporarily bound (`and` joins several). The binding is made before evaluation, so `sin(x)|x=30` is right in Degree mode and a stored `x` is overridden for that entry only. Inequality, `or` and other constraints report "Not implemented yet" until `solve` and friends exist (M1d), because they are consumed by those functions.
- **Reserved names** (`pi`, `ⅇ`, `true`, `ans`, built-in functions, ...) cannot be stored to. `DelVar` takes names only; `ClearAZ` deletes the single letters a to z, functions included.

## To check on the simulator

| Entry | Now | Why it is a guess |
|---|---|---|
| Storing to a reserved name (`pi:=3`) | error "Invalid variable name: that name is reserved", code -3 | Wording and number not captured |
| Runaway recursion | error "Recursion is too deep", code -4, at depth 50 | TI's own limit and message not captured |
| `delVar nothing` (undefined) | `Done` | TI may report an error |
| `a:=x+1` then `x:=2`, then `a` | `x+1` (values are fixed when stored) | TI may re-evaluate and give `3` |
| `a:=5` then `a(2)` | `a(2)`, an undefined function call | TI may treat it as `a*2` |
| `x^2|x=3` when `x:=5` is stored | `9` | Believed right |
| `derivative(x^2*sin(x),x)|x=2` | needs M1d: the binding is applied before evaluation, so `derivative` must read its variable from the argument list and not from the bound value | Design constraint for M1d |

## Not done in M1c

- `Local` and the library namespace (`lib\fn`, `LibPub`, `LibPriv`): they only matter inside programs and libraries (M5).
- Indexed assignment (`l[2]:=5`) and `CopyVar`/`Lock`/`unLock`.
- Inequality constraints, which arrive with `solve` in M1d.
- `when`, which the recursion and piecewise corpus cases need, is a catalog function and arrives in M1d.
