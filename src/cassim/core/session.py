"""The engine's public API: one calculator session, as specified in docs/testing/TESTING.md."""

from dataclasses import dataclass, replace

from cassim.core import ast
from cassim.core.compat import sympy_adapter as cas
from cassim.core.errors import TIError
from cassim.core.evaluator import Evaluator
from cassim.core.format import to_latex, to_text
from cassim.core.parser import parse
from cassim.core.scope import Scope
from cassim.core.settings import Calc, Settings, updated
from cassim.core.valueops import map_value, raw_of
from cassim.core.values import (
    Bool,
    Expr,
    ListValue,
    MatrixValue,
    Shown,
    Str,
    Unevaluated,
    Value,
    Void,
)


@dataclass(frozen=True, slots=True)
class Result:
    text: str
    latex: str
    value: Value | None
    error: str | None


class Session:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings if settings is not None else Settings()
        self._ans: Value | None = None
        self.scope = Scope()

    def eval(self, line: str, *, approximate: bool = False) -> Result:
        """Evaluate one entry line. TI errors come back in `Result.error`.

        `approximate=True` is Ctrl+Enter on the handheld: the same as wrapping the entry in
        `approx(...)`, whatever the Calculation Mode is. On an empty line it gives the previous
        result (`Ans`) as a decimal, and does nothing if there is no previous result.
        """
        if approximate and not line.strip():
            if self._ans is None:
                return Result("", "", None, None)
            line = "ans"
        try:
            tree: ast.Line = parse(line)
            value = Evaluator(self.settings, self._ans, self.scope).line(tree)
        except TIError as error:
            return Result(error.message, "", None, error.message)
        if value is None:
            return Result("", "", None, None)
        if approximate:
            value = _approximated(value, self.settings)
        if not isinstance(value, Void):
            self._ans = value
        return Result(to_text(value, self.settings), to_latex(value), value, None)

    def new_problem(self) -> None:
        self._ans = None
        self.scope.clear()

    def set(self, **changes: str) -> None:
        self.settings = updated(self.settings, changes)


def _approximated(value: Value, settings: Settings) -> Value:
    """The decimal form of a result; text, truth values and `Done` are left as they are."""
    if isinstance(value, Void | Str | Bool | Unevaluated):
        return value
    decimal = replace(settings, calc=Calc.APPROXIMATE)
    return map_value(lambda v: Expr(cas.finish(raw_of(v), decimal)), value)


def same_value(left: Value, right: Value, tolerance: float | None = None) -> bool:
    """Decide whether two values are mathematically equal, element by element."""
    left = left.value if isinstance(left, Shown) else left
    right = right.value if isinstance(right, Shown) else right
    if isinstance(left, Expr) and isinstance(right, Expr):
        return cas.equal(left.raw, right.raw, tolerance)
    if isinstance(left, ListValue) and isinstance(right, ListValue):
        pairs = zip(left.items, right.items, strict=False)
        return len(left.items) == len(right.items) and all(
            same_value(a, b, tolerance) for a, b in pairs
        )
    if isinstance(left, MatrixValue) and isinstance(right, MatrixValue):
        return same_value(
            ListValue(tuple(ListValue(row) for row in left.rows)),
            ListValue(tuple(ListValue(row) for row in right.rows)),
            tolerance,
        )
    return left == right
