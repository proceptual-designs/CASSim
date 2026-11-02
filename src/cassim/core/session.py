"""The engine's public API: one calculator session, as specified in docs/testing/TESTING.md."""

from dataclasses import dataclass

from cassim.core import ast
from cassim.core.compat import sympy_adapter as cas
from cassim.core.errors import TIError
from cassim.core.evaluator import Evaluator
from cassim.core.format import to_latex, to_text
from cassim.core.parser import parse
from cassim.core.scope import Scope
from cassim.core.settings import Settings, updated
from cassim.core.values import Expr, ListValue, MatrixValue, Shown, Value, Void


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

    def eval(self, line: str) -> Result:
        """Evaluate one entry line. TI errors come back in `Result.error`."""
        try:
            tree: ast.Line = parse(line)
            value = Evaluator(self.settings, self._ans, self.scope).line(tree)
        except TIError as error:
            return Result(error.message, "", None, error.message)
        if value is None:
            return Result("", "", None, None)
        if not isinstance(value, Void):
            self._ans = value
        return Result(to_text(value, self.settings), to_latex(value), value, None)

    def new_problem(self) -> None:
        self._ans = None
        self.scope.clear()

    def set(self, **changes: str) -> None:
        self.settings = updated(self.settings, changes)


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
