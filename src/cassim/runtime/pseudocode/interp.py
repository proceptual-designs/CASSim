"""Tree-walking interpreter for the pseudocode dialect.

It records a `Step` per executed line (steps.py) so a run can be stepped forwards and backwards
without re-executing, and it enforces the run limits of FR-SET-009. Errors are reported in
pseudocode terms with a line number.
"""

import cmath
import math
import random
import re
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from difflib import get_close_matches
from fractions import Fraction
from typing import TypeGuard

from cassim.runtime.pseudocode import arith
from cassim.runtime.pseudocode.errors import (
    PseudocodeError,
    PseudocodeRuntimeError,
    RunLimitError,
)
from cassim.runtime.pseudocode.settings import Settings
from cassim.runtime.pseudocode.steps import Change, RunResult, Step
from cassim.runtime.pseudocode.tree import (
    Append,
    Assign,
    Binary,
    Break,
    Call,
    Compare,
    Constant,
    Define,
    Expr,
    ExprStmt,
    For,
    ForEach,
    FuncAssign,
    If,
    Index,
    Input,
    ListLit,
    Name,
    Num,
    Param,
    Paren,
    Print,
    Program,
    RepeatTimes,
    RepeatUntil,
    Return,
    Stmt,
    Str,
    Unary,
    While,
)

_MISSING = object()
_INT = re.compile(r"[+-]?\d+")
_DECIMAL = re.compile(r"[+-]?(\d+\.?\d*|\.\d+)([Eeᴇ][+-]?\d+)?")
_FRACTION = re.compile(r"([+-]?\d+)\s*/\s*(\d+)")
_MULTIPLY = {"*": "×", "/": "/", "÷": "÷", "+": " + ", "-": " − ", "^": "^", "div": " div ",
             "mod": " mod ", "and": " and ", "or": " or "}  # fmt: skip


class _Return(Exception):
    def __init__(self, value: object) -> None:
        super().__init__()
        self.value = value


class _Break(Exception):
    pass


class _Cancelled(Exception):
    pass


class Scope:
    __slots__ = ("parent", "vars")

    def __init__(self, parent: Scope | None = None) -> None:
        self.parent = parent
        self.vars: dict[str, object] = {}

    def get(self, name: str) -> object:
        scope: Scope | None = self
        while scope is not None:
            if name in scope.vars:
                return scope.vars[name]
            scope = scope.parent
        return _MISSING

    def names(self) -> set[str]:
        out: set[str] = set()
        scope: Scope | None = self
        while scope is not None:
            out.update(scope.vars)
            scope = scope.parent
        return out


@dataclass(slots=True)
class UserFunc:
    name: str
    params: tuple[Param, ...]
    body: list[Stmt]
    scope: Scope

    def describe(self) -> str:
        params = ", ".join(param.name for param in self.params)
        return f"function {self.name}({params})"


@dataclass(slots=True)
class ExprFunc:
    """A function made from an expression: an expression-form argument, or `P(x) ← …`."""

    name: str
    params: tuple[str, ...]
    expr: Expr
    scope: Scope

    def describe(self) -> str:
        return f"function {self.name}({', '.join(self.params)})"


@dataclass(slots=True)
class Builtin:
    name: str
    fn: Callable[[Interpreter, list[object]], object]

    def describe(self) -> str:
        return f"function {self.name}"


type Function = UserFunc | ExprFunc | Builtin


def infer_input(text: str, settings: Settings) -> object:
    """`input x` reads a line and infers its type: anything that can be a number is one."""
    s = text.strip()
    if _INT.fullmatch(s):
        return int(s)
    if _DECIMAL.fullmatch(s):
        return arith.parse_literal(s.replace("ᴇ", "E"), settings)
    m = _FRACTION.fullmatch(s)
    if m and int(m.group(2)) != 0:
        if settings.number == "approx":
            return int(m.group(1)) / int(m.group(2))
        return arith.norm(Fraction(int(m.group(1)), int(m.group(2))))
    return text


def _is_function(v: object) -> TypeGuard[UserFunc | ExprFunc | Builtin]:
    return isinstance(v, UserFunc | ExprFunc | Builtin)


class Interpreter:
    def __init__(
        self,
        program: Program,
        settings: Settings | None = None,
        inputs: Iterable[str] = (),
        *,
        trace: bool = True,
        cancelled: Callable[[], bool] | None = None,
    ) -> None:
        self.program = program
        self.settings = settings or Settings()
        self.inputs = iter(inputs)
        self.trace = trace
        self.globals = Scope()
        self.scope = self.globals
        self.output: list[str] = []
        self.steps: list[Step] = []
        self.depth = 0
        self.iterations = 0
        self.loops: list[list[int]] = []
        self.loop_entries = 0
        self.body_runs = 0
        self.max_loop_depth = 0
        self.functions: list[str] = []
        self.user_calls = 0
        self.memo: dict[int, object] = {}
        self.rng = random.Random(self.settings.seed)
        self.cancelled = cancelled

    # ------------------------------------------------------------------ running

    def run(self) -> RunResult:  # noqa: PLR0912
        limit = sys.getrecursionlimit()
        sys.setrecursionlimit(max(limit, 30_000))
        halt, error, error_line = "finished", None, 0
        try:
            for stmt in self.program.body:
                if isinstance(stmt, Define):
                    self.exec_define(stmt)
            self.exec_block(self.program.body)
        except _Return:
            pass
        except RunLimitError as e:
            halt = "event_cap" if e.limit == "events" else "step_limit"
            error, error_line = e.message, e.line
        except PseudocodeError as e:
            halt, error, error_line = "error", e.message, e.line
        except RecursionError:
            halt, error = "error", "the program recurses too deeply"
        except _Cancelled:
            halt, error, error_line = "cancelled", "stopped", 0
        finally:
            sys.setrecursionlimit(limit)
        last = self.steps[-1].line if self.steps else 0
        self.steps.append(
            Step(len(self.steps), error_line or last, "halt", 0, calc=error or "finished")
        )
        functions: dict[str, str] = {}
        variables: dict[str, object] = {}
        for name, value in self.globals.vars.items():
            if _is_function(value):
                functions[name] = value.describe()
            else:
                variables[name] = value
        change_counts: dict[str, int] = {}
        for step in self.steps:
            for change in step.changes:
                change_counts[change.name] = change_counts.get(change.name, 0) + 1
        constants = tuple(name for name in variables if change_counts.get(name, 0) == 1)
        return RunResult(
            self.output, self.steps, self.program.warnings, halt, error, error_line, variables,
            self.loop_entries, self.max_loop_depth, self.body_runs, constants, functions,
        )  # fmt: skip

    def record(  # noqa: PLR0913
        self,
        line: int,
        kind: str,
        *,
        changes: tuple[Change, ...] = (),
        cond: tuple[str, bool] | None = None,
        calc: str = "",
        output: str | None = None,
        function: str | None = None,
    ) -> None:
        if not self.trace:
            return
        if self.cancelled is not None and self.cancelled():
            raise _Cancelled
        if len(self.steps) >= self.settings.max_events:
            raise RunLimitError(
                f"stopped: the trace is limited to {self.settings.max_events} steps", line, "events"
            )
        loop = (self.loops[-1][0], self.loops[-1][1]) if self.loops else None
        if function is None:
            function = self.functions[-1] if self.functions else ""
        self.steps.append(
            Step(
                len(self.steps), line, kind, self.depth, changes, cond, calc, output, loop, function
            )
        )

    def run_body(self, body: list[Stmt]) -> None:
        """One pass through a loop body."""
        self.body_runs += 1
        self.exec_block(body)

    def exec_block(self, body: list[Stmt]) -> None:
        for stmt in body:
            self.exec(stmt)

    def exec(self, s: Stmt) -> None:
        saved, self.memo = self.memo, {}
        try:
            self._exec(s)
        except PseudocodeError as e:
            if not e.line:
                e.line = s.line
            raise
        except ZeroDivisionError:
            raise PseudocodeRuntimeError("division by zero", s.line) from None
        except OverflowError:
            raise PseudocodeRuntimeError("a number is too large", s.line) from None
        finally:
            self.memo = saved

    def _exec(self, s: Stmt) -> None:  # noqa: PLR0912
        match s:
            case Assign():
                self.exec_assign(s)
            case FuncAssign():
                self.scope.vars[s.name] = ExprFunc(s.name, s.params, s.body, self.scope)
                self.record(
                    s.line,
                    "assign",
                    calc=f"{s.name}({', '.join(s.params)}) ← {self.render(s.body)}",
                )
            case Input():
                self.exec_input(s)
            case Print():
                self.exec_print(s)
            case Append():
                target = self.eval(s.target)
                value = self.eval(s.value)
                if not isinstance(target, list):
                    raise PseudocodeRuntimeError("append needs a list")
                target.append(value)
                self.record(s.line, "assign", calc=f"append {self.tfmt(value)}")
            case ExprStmt():
                before = self.user_calls
                value = self.eval(s.expr)
                if self.user_calls == before:
                    self.record(s.line, "call", calc=self.render(s.expr))
                del value
            case Return():
                value = None if s.value is None else self.eval(s.value)
                shown = "" if s.value is None else self.render(s.value)
                result = "" if value is None else self.tfmt(value)
                calc = result if shown == result or not shown else f"{shown} = {result}"
                self.record(s.line, "return", calc=calc)
                raise _Return(value)
            case Break():
                raise _Break
            case If():
                self.exec_if(s)
            case While():
                self.exec_while(s)
            case For():
                self.exec_for(s)
            case ForEach():
                self.exec_foreach(s)
            case RepeatTimes():
                self.exec_repeat_times(s)
            case RepeatUntil():
                self.exec_repeat_until(s)
            case Define():
                self.exec_define(s)

    # ------------------------------------------------------------------ statements

    def exec_define(self, s: Define) -> None:
        self.scope.vars[s.name] = UserFunc(s.name, s.params, s.body, self.scope)

    def set_var(self, name: str, value: object) -> Change:
        old = self.scope.vars.get(name, _MISSING)
        self.scope.vars[name] = value
        return Change(name, None if old is _MISSING else old, value, old is not _MISSING)

    def exec_assign(self, s: Assign) -> None:
        value = self.eval(s.value)
        if value is None:
            raise PseudocodeRuntimeError("that function returned no value")
        shown, result = self.render(s.value), self.tfmt(value)
        if isinstance(s.target, Name):
            change = self.set_var(s.target.name, value)
            label = s.target.name
        else:
            seq, idx = self.list_slot(self.eval(s.target.target), self.eval(s.target.index))
            old = list(seq)
            seq[idx] = value
            label = f"{self.render(s.target.target)}[{self.render(s.target.index)}]"
            name = s.target.target.name if isinstance(s.target.target, Name) else label
            change = Change(name, old, seq)
        calc = f"{label} = {result}" if shown == result else f"{label} = {shown} = {result}"
        self.record(s.line, "assign", changes=(change,), calc=calc)

    def exec_input(self, s: Input) -> None:
        try:
            text = next(self.inputs)
        except StopIteration:
            raise PseudocodeRuntimeError("the program asked for input but none was given") from None
        value = infer_input(text, self.settings)
        if isinstance(s.target, Name):
            change = self.set_var(s.target.name, value)
        else:
            seq, idx = self.list_slot(self.eval(s.target.target), self.eval(s.target.index))
            old = list(seq)
            seq[idx] = value
            change = Change(str(self.render(s.target.target)), old, seq)
        self.record(s.line, "input", changes=(change,), calc=f"input {self.tfmt(value)}")

    def exec_print(self, s: Print) -> None:
        parts: list[str] = []
        for item in s.items:
            value = self.eval(item)
            if _is_function(value) or value is None:
                raise PseudocodeRuntimeError("cannot print a function")
            parts.append(self.fmt(value))
        text = " ".join(parts)
        self.output.append(text)
        self.record(s.line, "print", output=text, calc=text)

    def exec_if(self, s: If) -> None:
        for cond, body, line in s.branches:
            result = self.condition(cond, line, "if")
            if result:
                self.exec_block(body)
                return
        if s.orelse is not None:
            self.exec_block(s.orelse)

    def condition(self, cond: Expr, line: int, kind: str) -> bool:
        saved, self.memo = self.memo, {}
        try:
            result = arith.truthy(self.eval(cond))
            if self.trace:
                self.record(line, "condition", cond=(self.render(cond), result), calc=kind)
            return result
        finally:
            self.memo = saved

    def enter_loop(self, line: int) -> None:
        self.loops.append([line, 0])
        self.loop_entries += 1
        self.max_loop_depth = max(self.max_loop_depth, len(self.loops))

    def next_pass(self, line: int) -> None:
        self.loops[-1][1] += 1
        self.iterations += 1
        if self.loops[-1][1] > self.settings.max_iterations:  # per loop run, not across loops
            raise RunLimitError(
                f"stopped after {self.settings.max_iterations} loop passes "
                "(the loop limit; change it in the settings)",
                line,
                "iterations",
            )

    def exec_while(self, s: While) -> None:
        self.enter_loop(s.line)
        try:
            while True:
                self.next_pass(s.line)
                if not self.condition(s.cond, s.line, "while"):
                    break
                try:
                    self.run_body(s.body)
                except _Break:
                    break
        finally:
            self.loops.pop()

    def exec_for(self, s: For) -> None:
        start = self.eval(s.start)
        stop = self.eval(s.stop)
        step = 1 if s.step is None else self.eval(s.step)
        try:
            lo = arith.real_value("from", start)
            hi = arith.real_value("to", stop)
            by = arith.real_value("step", step)
        except PseudocodeRuntimeError as e:
            raise PseudocodeRuntimeError(f"a for loop: {e.message}", s.line) from None
        if by == 0:
            raise PseudocodeRuntimeError("the step of a for loop cannot be 0", s.line)
        count = self.pass_count(lo, hi, by)
        self.enter_loop(s.line)
        try:
            for k in range(count):
                self.next_pass(s.line)
                value = start if k == 0 else arith.add(start, arith.mul(k, step))
                change = self.set_var(s.var, value)
                self.record(s.line, "loop", changes=(change,), calc=f"{s.var} = {self.tfmt(value)}")
                try:
                    self.run_body(s.body)
                except _Break:
                    break
        finally:
            self.loops.pop()

    @staticmethod
    def pass_count(start: float | Fraction, stop: float | Fraction, step: float | Fraction) -> int:
        quotient = (stop - start) / step
        if isinstance(quotient, float):
            quotient += 1e-9 * max(1.0, abs(quotient))  # 0.1 + 0.1 + ... should reach the stop
        return max(0, math.floor(quotient) + 1)

    def exec_foreach(self, s: ForEach) -> None:
        seq = self.eval(s.iterable)
        if not isinstance(seq, list | str):
            raise PseudocodeRuntimeError("for each needs a list", s.line)
        self.enter_loop(s.line)
        try:
            for item in list(seq):
                self.next_pass(s.line)
                change = self.set_var(s.var, item)
                self.record(s.line, "loop", changes=(change,), calc=f"{s.var} = {self.tfmt(item)}")
                try:
                    self.run_body(s.body)
                except _Break:
                    break
        finally:
            self.loops.pop()

    def exec_repeat_times(self, s: RepeatTimes) -> None:
        n = self.eval(s.count)
        if not isinstance(n, int) or isinstance(n, bool):
            raise PseudocodeRuntimeError("repeat needs a whole number of times", s.line)
        self.enter_loop(s.line)
        try:
            for k in range(1, n + 1):
                self.next_pass(s.line)
                self.record(s.line, "loop", calc=f"pass {k} of {n}")
                try:
                    self.run_body(s.body)
                except _Break:
                    break
        finally:
            self.loops.pop()

    def exec_repeat_until(self, s: RepeatUntil) -> None:
        self.enter_loop(s.line)
        try:
            while True:
                self.next_pass(s.line)
                try:
                    self.run_body(s.body)
                except _Break:
                    break
                if self.condition(s.cond, s.until_line, "until"):
                    break
        finally:
            self.loops.pop()

    # ------------------------------------------------------------------ expressions

    def fmt(self, v: object) -> str:
        return arith.format_value(v, self.settings)

    def tfmt(self, v: object) -> str:
        """A value for a trace cell, with a true minus sign."""
        return arith.format_value(v, self.settings, minus=arith.MINUS)

    def list_slot(self, seq: object, index: object) -> tuple[list[object], int]:
        if not isinstance(seq, list):
            raise PseudocodeRuntimeError("only lists can be indexed")
        if not isinstance(index, int) or isinstance(index, bool):
            raise PseudocodeRuntimeError("a list index must be a whole number")
        i = index - self.settings.index_base
        if not 0 <= i < len(seq):
            raise PseudocodeRuntimeError(
                f"index {index} is outside the list (it has {len(seq)} items)"
            )
        return seq, i

    def eval(self, e: Expr) -> object:  # noqa: PLR0911, PLR0912
        match e:
            case Num():
                return arith.parse_literal(e.text, self.settings)
            case Str():
                return e.value
            case Constant(name="ⅇ"):
                return math.e
            case Constant(name="π"):
                return math.pi
            case Name():
                return self.eval_name(e)
            case Paren():
                return self.eval(e.inner)
            case Unary():
                v = self.eval(e.operand)
                match e.op:
                    case "-":
                        return arith.neg(v)
                    case "not":
                        return not arith.truthy(v)
                    case "abs":
                        return BUILTINS["abs"].fn(self, [v])
                    case _:
                        return BUILTINS["sqrt"].fn(self, [v])
            case Binary():
                return self.eval_binary(e)
            case Compare():
                left = self.eval(e.first)
                for op, right_expr in zip(e.ops, e.rest, strict=True):
                    right = self.eval(right_expr)
                    if not arith.compare(op, left, right):
                        return False
                    left = right
                return True
            case Call():
                value = self.eval_call(e)
                self.memo[id(e)] = value
                return value
            case Index():
                seq, i = self.list_slot(self.eval(e.target), self.eval(e.index))
                value = seq[i]
                self.memo[id(e)] = value
                return value
            case ListLit():
                return [self.eval(x) for x in e.items]

    def eval_binary(self, e: Binary) -> object:  # noqa: PLR0911
        op = e.op
        if op in ("and", "or"):
            left = arith.truthy(self.eval(e.left))
            if (op == "and") != left:
                return left
            return arith.truthy(self.eval(e.right))
        if op == "^" and isinstance(e.left, Name):
            parts = self.split_name(e.left.name)
            if parts is not None:  # `ax²` is a × x², the power binds to the last letter
                head = parts[0]
                for v in parts[1:-1]:
                    head = arith.mul(head, v)
                return arith.mul(head, arith.power(parts[-1], self.eval(e.right), self.settings))
        left = self.eval(e.left)
        right = self.eval(e.right)
        match op:
            case "+":
                return arith.add(left, right)
            case "-":
                return arith.sub(left, right)
            case "*":
                return arith.mul(left, right)
            case "/" | "÷":
                return arith.div(left, right, self.settings)
            case "div":
                return arith.floordiv(left, right)
            case "mod":
                return arith.mod(left, right)
            case _:
                return arith.power(left, right, self.settings)

    def split_name(self, name: str) -> list[object] | None:
        """`ax` as a product of the variables a and x, when `ax` itself is not defined."""
        if not self.program.split_names:
            return None
        return self.product_parts(name)

    def product_parts(self, name: str) -> list[object] | None:
        if len(name) < 2 or self.scope.get(name) is not _MISSING:  # noqa: PLR2004
            return None
        values: list[object] = []
        for ch in name:
            v = self.scope.get(ch)
            if v is _MISSING or not arith.is_number(v):
                return None
            values.append(v)
        return values

    def eval_name(self, e: Name) -> object:
        name = e.name
        v = self.scope.get(name)
        if v is _MISSING:
            v = self.special_name(name)
        if v is _MISSING:
            parts = self.split_name(name)
            if parts is not None:
                v = parts[0]
                for p in parts[1:]:
                    v = arith.mul(v, p)
        if v is _MISSING:
            raise self.undefined(name, e.line)
        if not _is_function(v):
            self.memo[id(e)] = v
        return v

    def special_name(self, name: str) -> object:  # noqa: PLR0911
        lowered = name.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        if name in ("π", "pi"):
            return math.pi
        if name == "ⅇ" or (name == "e" and self.settings.euler_e):
            return math.e
        if name in ("ⅈ", "i"):
            return 1j
        if name in ("∞", "inf"):
            return math.inf
        builtin = BUILTINS.get(lowered)
        return builtin if builtin is not None else _MISSING

    def undefined(self, name: str, line: int) -> PseudocodeRuntimeError:
        known = sorted(n for n in self.scope.names() if not n.startswith("_"))
        close = get_close_matches(name, known, n=1, cutoff=0.6)
        if not close:
            close = [n for n in known if n.lower() == name.lower()]
        hint = f", did you mean {close[0]}?" if close else ""
        if not self.program.split_names and self.product_parts(name) is not None:
            hint = f", did you mean {'*'.join(name)}? (write a product with * or a space)"
        return PseudocodeRuntimeError(f"{name} is not defined{hint}", line)

    # ------------------------------------------------------------------ calls

    def eval_call(self, e: Call) -> object:
        target = self.scope.get(e.name)
        if target is _MISSING:
            target = BUILTINS.get(e.name) or BUILTINS.get(e.name.lower()) or _MISSING
        if isinstance(target, UserFunc):
            return self.call_user(target, e)
        if isinstance(target, ExprFunc):
            return self.call_expr(target, [self.eval(a) for a in e.args], e.line)
        if isinstance(target, Builtin):
            return target.fn(self, [self.eval(a) for a in e.args])
        # A defined number followed by brackets is a product: `x(a+b)`, `a(x)`.
        value = target if target is not _MISSING else self.special_name(e.name)
        if value is _MISSING:
            parts = self.split_name(e.name)
            if parts is not None:
                value = parts[0]
                for p in parts[1:]:
                    value = arith.mul(value, p)
        if value is _MISSING:
            raise self.undefined(e.name, e.line)
        if len(e.args) != 1:
            raise PseudocodeRuntimeError(f"{e.name} is not a function", e.line)
        return arith.mul(value, self.eval(e.args[0]))

    def call_expr(self, f: ExprFunc, args: list[object], line: int) -> object:
        if len(args) != len(f.params):
            raise PseudocodeRuntimeError(
                f"{f.name} takes {len(f.params)} argument(s), got {len(args)}", line
            )
        local = Scope(f.scope)
        local.vars.update(zip(f.params, args, strict=True))
        saved, self.scope = self.scope, local
        try:
            return self.eval(f.expr)
        finally:
            self.scope = saved

    def call_function(self, f: object, args: list[object], line: int) -> object:
        if isinstance(f, ExprFunc):
            return self.call_expr(f, args, line)
        if isinstance(f, Builtin):
            return f.fn(self, args)
        raise PseudocodeRuntimeError("that is not a function", line)

    def call_user(self, f: UserFunc, call: Call) -> object:
        if self.depth + 1 > self.settings.max_depth:
            raise RunLimitError(
                f"stopped: {f.name} called itself more than {self.settings.max_depth} deep "
                "(the recursion limit; change it in the settings)",
                call.line,
                "depth",
            )
        params, arg_exprs = f.params, call.args
        if len(arg_exprs) > len(params):
            raise PseudocodeRuntimeError(
                f"{f.name} takes {len(params)} argument(s), got {len(arg_exprs)}", call.line
            )
        caller = self.scope
        local = Scope(f.scope)
        variables = {p.sig[0] for p in params if p.sig}
        for idx, p in enumerate(params):
            arg = arg_exprs[idx] if idx < len(arg_exprs) else None
            if p.sig is not None and arg is not None:
                local.vars[p.name] = self.function_argument(p, arg, params, arg_exprs, call.line)
            elif p.name in variables and isinstance(arg, Name):
                continue  # the variable of an expression-form function argument
            elif arg is not None:
                local.vars[p.name] = self.eval(arg)
            elif p.default is not None:
                self.scope = local
                try:
                    local.vars[p.name] = self.eval(p.default)
                finally:
                    self.scope = caller
            else:
                raise PseudocodeRuntimeError(f"{f.name} needs a value for {p.name}", call.line)
        shown = ", ".join(self.render(a) for a in arg_exprs)
        self.user_calls += 1
        bound = tuple(
            Change(name, None, value, existed=False)
            for name, value in local.vars.items()
            if not _is_function(value)
        )
        self.record(call.line, "call", changes=bound, calc=f"{f.name}({shown})", function=f.name)
        self.depth += 1
        self.functions.append(f.name)
        saved_loops, self.loops = self.loops, []
        self.scope = local
        try:
            self.exec_block(f.body)
            return None
        except _Return as r:
            return r.value
        finally:
            self.scope = caller
            self.loops = saved_loops
            self.functions.pop()
            self.depth -= 1

    def function_argument(
        self, p: Param, arg: Expr, params: tuple[Param, ...], arg_exprs: tuple[Expr, ...], line: int
    ) -> object:
        """Bind a parameter written `f(x)`: a named function, or an expression in a variable."""
        assert p.sig is not None
        if isinstance(arg, Name):
            existing = self.scope.get(arg.name)
            if _is_function(existing):
                return existing
            if (
                existing is _MISSING
                and self.special_name(arg.name) is not _MISSING
                and _is_function(self.special_name(arg.name))
            ):
                return self.special_name(arg.name)
        var = p.sig[0]
        for j, other in enumerate(params):
            if other.name == var and j < len(arg_exprs):
                named = arg_exprs[j]
                if not isinstance(named, Name):
                    raise PseudocodeRuntimeError(
                        f"the variable for {p.name}({var}) must be a name, as in {var}", line
                    )
                var = named.name
        stray = sorted(n for n in self.free_names(arg) if n != var)
        if stray:
            raise PseudocodeRuntimeError(
                f"the expression for {p.name} uses {stray[0]} but its variable is {var}", line
            )
        return ExprFunc(p.name, (var,), arg, self.scope)

    def free_names(self, e: Expr) -> set[str]:
        """Names in `e` that are neither defined nor built in: the variables of an expression."""
        found: set[str] = set()

        def walk(node: Expr) -> None:
            match node:
                case Name():
                    n = node.name
                    known = (
                        self.scope.get(n) is not _MISSING or self.special_name(n) is not _MISSING
                    )
                    if not known and self.split_name(n) is None:
                        found.add(n)
                case Paren():
                    walk(node.inner)
                case Unary():
                    walk(node.operand)
                case Binary():
                    walk(node.left)
                    walk(node.right)
                case Compare():
                    walk(node.first)
                    for r in node.rest:
                        walk(r)
                case Call():
                    for a in node.args:
                        walk(a)
                case Index():
                    walk(node.target)
                    walk(node.index)
                case ListLit():
                    for a in node.items:
                        walk(a)

        walk(e)
        return found

    # ------------------------------------------------------------------ rendering with values

    def render(self, e: Expr) -> str:  # noqa: PLR0911, PLR0912
        """The expression with the values of its variables and calls substituted (trace cells)."""
        if not self.trace:
            return ""
        match e:
            case Num():
                return e.text.replace("-", "−")
            case Str():
                return f'"{e.value}"'
            case Constant():
                return e.name
            case Name():
                if id(e) in self.memo:
                    return self.tfmt(self.memo[id(e)])
                return e.name
            case Paren():
                return f"({self.render(e.inner)})"
            case Unary():
                inner = self.render(e.operand)
                return {"-": f"−{inner}", "not": f"not {inner}", "abs": f"|{inner}|"}.get(
                    e.op, f"√({inner})"
                )
            case Binary():
                op = "×" if e.op == "*" else _MULTIPLY.get(e.op, e.op)
                return f"{self.render(e.left)}{op}{self.render(e.right)}"
            case Compare():
                text = self.render(e.first)
                for op, right in zip(e.ops, e.rest, strict=True):
                    text += f" {op} {self.render(right)}"
                return text
            case Call():
                if id(e) in self.memo and not _is_function(self.memo[id(e)]):
                    return self.tfmt(self.memo[id(e)])
                return f"{e.name}({', '.join(self.render(a) for a in e.args)})"
            case Index():
                if id(e) in self.memo:
                    return self.tfmt(self.memo[id(e)])
                return f"{self.render(e.target)}[{self.render(e.index)}]"
            case ListLit():
                return "[" + ", ".join(self.render(x) for x in e.items) + "]"
        return ""


# ---------------------------------------------------------------------------------------- built-ins


def _arity(name: str, args: list[object], low: int, high: int | None = None) -> None:
    high = low if high is None else high
    if not low <= len(args) <= high:
        want = str(low) if low == high else f"{low} to {high}"
        raise PseudocodeRuntimeError(f"{name} takes {want} argument(s), got {len(args)}")


def _real(name: str, v: object) -> float:
    return float(arith.real_value(name, v))


def _number(name: str, v: object) -> arith.Number:
    if not arith.is_number(v):
        raise PseudocodeRuntimeError(f"{name} needs a number")
    return v


def _sqrt(it: Interpreter, args: list[object]) -> object:
    _arity("sqrt", args, 1)
    x = _number("sqrt", args[0])
    if isinstance(x, complex):
        return cmath.sqrt(x)
    if x < 0:
        if it.settings.complex_domain:
            return cmath.sqrt(x)
        raise PseudocodeRuntimeError("sqrt of a negative number (Real domain)")
    if isinstance(x, int | Fraction):
        f = Fraction(x)
        n, d = math.isqrt(f.numerator), math.isqrt(f.denominator)
        if n * n == f.numerator and d * d == f.denominator:
            return arith.norm(Fraction(n, d))
    return math.sqrt(x)


def _abs(_: Interpreter, args: list[object]) -> object:
    _arity("abs", args, 1)
    x = _number("abs", args[0])
    return abs(x) if isinstance(x, complex) else arith.norm(abs(x))


def _exp(it: Interpreter, args: list[object]) -> object:
    _arity("exp", args, 1)
    x = _number("exp", args[0])
    try:
        return cmath.exp(x) if isinstance(x, complex) else math.exp(float(x))
    except OverflowError:
        raise PseudocodeRuntimeError("exp: the result is too large") from None


def _log(name: str, fn: Callable[[float], float]) -> Callable[[Interpreter, list[object]], object]:
    def run(it: Interpreter, args: list[object]) -> object:
        _arity(name, args, 1)
        x = _number(name, args[0])
        if isinstance(x, complex) or (x <= 0 and it.settings.complex_domain):
            return cmath.log(x) / (cmath.log(10) if name == "log10" else 1)
        if x <= 0:
            raise PseudocodeRuntimeError(f"{name} needs a positive number")
        return fn(float(x))

    return run


def _trig(name: str, fn: Callable[[float], float]) -> Callable[[Interpreter, list[object]], object]:
    def run(it: Interpreter, args: list[object]) -> object:
        _arity(name, args, 1)
        x = _real(name, args[0])
        return fn(math.radians(x) if it.settings.angle == "degree" else x)

    return run


def _inverse_trig(
    name: str, fn: Callable[[float], float]
) -> Callable[[Interpreter, list[object]], object]:
    def run(it: Interpreter, args: list[object]) -> object:
        _arity(name, args, 1)
        x = _real(name, args[0])
        if name != "atan" and not -1 <= x <= 1:
            raise PseudocodeRuntimeError(f"{name} needs a number from -1 to 1")
        result = fn(x)
        return math.degrees(result) if it.settings.angle == "degree" else result

    return run


def _floor_like(
    name: str, fn: Callable[[arith.Real], int]
) -> Callable[[Interpreter, list[object]], object]:
    def run(_: Interpreter, args: list[object]) -> object:
        _arity(name, args, 1)
        x = _number(name, args[0])
        if isinstance(x, int):
            return x
        return fn(arith.real_value(name, x))

    return run


def _round(_: Interpreter, args: list[object]) -> object:
    _arity("round", args, 1, 2)
    x = _number("round", args[0])
    digits = 0
    if len(args) == 2:  # noqa: PLR2004
        d = args[1]
        if not isinstance(d, int) or isinstance(d, bool):
            raise PseudocodeRuntimeError("round: the number of places must be a whole number")
        digits = d
    return arith.round_half_up(arith.real_value("round", x), digits)


def _items(name: str, args: list[object]) -> list[object]:
    first = args[0] if len(args) == 1 else None
    items = list(first) if isinstance(first, list) else list(args)
    if not items:
        raise PseudocodeRuntimeError(f"{name} needs at least one value")
    return items


def _min(_: Interpreter, args: list[object]) -> object:
    items = _items("min", args)
    best = items[0]
    for v in items[1:]:
        if arith.compare("<", v, best):
            best = v
    return best


def _max(_: Interpreter, args: list[object]) -> object:
    items = _items("max", args)
    best = items[0]
    for v in items[1:]:
        if arith.compare(">", v, best):
            best = v
    return best


def _sum(_: Interpreter, args: list[object]) -> object:
    _arity("sum", args, 1)
    if not isinstance(args[0], list):
        raise PseudocodeRuntimeError("sum needs a list")
    total: object = 0
    for v in args[0]:
        total = arith.add(total, v)
    return total


def _len(_: Interpreter, args: list[object]) -> object:
    _arity("len", args, 1)
    if not isinstance(args[0], list | str):
        raise PseudocodeRuntimeError("len needs a list or text")
    return len(args[0])


def _rand(it: Interpreter, args: list[object]) -> object:
    _arity("rand", args, 0)
    return it.rng.random()


def _randint(it: Interpreter, args: list[object]) -> object:
    _arity("randint", args, 2)
    lo, hi = args
    if not (isinstance(lo, int) and isinstance(hi, int)) or hi < lo:
        raise PseudocodeRuntimeError("randint needs whole numbers a ≤ b")
    return it.rng.randint(lo, hi)


def _seed(it: Interpreter, args: list[object]) -> object:
    _arity("seed", args, 1)
    it.rng.seed(args[0] if isinstance(args[0], int) else None)
    return None


def _complex(_: Interpreter, args: list[object]) -> object:
    _arity("complex", args, 2)
    return complex(_real("complex", args[0]), _real("complex", args[1]))


def _builtins() -> dict[str, Builtin]:
    table: dict[str, Callable[[Interpreter, list[object]], object]] = {
        "sqrt": _sqrt, "√": _sqrt, "abs": _abs, "exp": _exp,
        "loge": _log("loge", math.log), "ln": _log("ln", math.log),
        "log10": _log("log10", math.log10),
        "sin": _trig("sin", math.sin), "cos": _trig("cos", math.cos), "tan": _trig("tan", math.tan),
        "asin": _inverse_trig("asin", math.asin), "acos": _inverse_trig("acos", math.acos),
        "atan": _inverse_trig("atan", math.atan),
        "floor": _floor_like("floor", math.floor), "ceil": _floor_like("ceil", math.ceil),
        "round": _round, "min": _min, "max": _max, "sum": _sum, "len": _len,
        "rand": _rand, "randint": _randint, "randominteger": _randint, "seed": _seed,
        "complex": _complex,
    }  # fmt: skip
    return {name: Builtin(name, fn) for name, fn in table.items()}


BUILTINS: dict[str, Builtin] = _builtins()
