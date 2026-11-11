"""The engine's public API: one calculator session, as specified in docs/testing/TESTING.md."""

from dataclasses import replace

from cassim.core import ast, catalog, errors
from cassim.core.compat import sympy_adapter as cas
from cassim.core.errors import TIError
from cassim.core.evaluator import Evaluator
from cassim.core.format import to_ascii, to_latex, to_text
from cassim.core.parser import parse
from cassim.core.results import Result, VariableInfo
from cassim.core.scope import Function, Scope
from cassim.core.settings import Ascii, Calc, Case, Logic, Settings, updated, variable_key
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

__all__ = ["Result", "Session", "VariableInfo"]  # the two rows are defined in `results`


class Session:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings if settings is not None else Settings()
        self._ans: Value | None = None
        self.scope = Scope()

    @property
    def settings(self) -> Settings:
        return self._settings

    @settings.setter
    def settings(self, settings: Settings) -> None:
        if settings.case is Case.INSENSITIVE and self._settings.case is Case.SENSITIVE:
            self.scope.fold_names()
        self._settings = settings

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
            if value is None:
                return Result("", "", None, None)
            if approximate:
                value = _approximated(value, self.settings)
            text = to_text(value, self.settings)
            if self.settings.ascii is Ascii.ON:
                text = to_ascii(text)
            latex = to_latex(value, logic_symbols=self.settings.logic is Logic.SYMBOLS)
            full = text
            if self.settings.digits != "float14":
                full = to_text(value, replace(self.settings, digits="float14"))
                full = to_ascii(full) if self.settings.ascii is Ascii.ON else full
        except TIError as error:
            return Result(error.message, "", None, error.message)
        except RecursionError:
            # A result with thousands of terms nests deeper than Python's stack allows.
            message = TIError(errors.MEMORY).message
            return Result(message, "", None, message)
        if not isinstance(value, Void):
            self._ans = value
        return Result(text, latex, value, None, full)

    def set_ans(self, line: str | None) -> None:
        """Make `Ans` the value of `line`, the last result left in the history after an undo or a
        delete (emulator check 3, H5 g). None clears it. A line that fails changes nothing."""
        if line is None:
            self._ans = None
        elif line.strip():
            self.eval(line)

    def is_function(self, name: str) -> bool:
        """Whether `name` is a built-in command or a user function defined in this Problem."""
        return catalog.is_builtin(name.casefold()) or isinstance(
            self.scope.get(variable_key(self.settings, name)), Function
        )

    def variables(self) -> list[VariableInfo]:
        """The Problem's variables and user functions, sorted by name (the variable list)."""
        rows: list[VariableInfo] = []
        for name in sorted(self.scope.names()):
            item = self.scope.get(name)
            if isinstance(item, Function):
                head = f"{name}({','.join(item.params)})"
                rows.append(
                    VariableInfo(name, head, rf"\mathbf{{{name}}}({','.join(item.params)})", True)
                )
            elif item is not None:
                rows.append(VariableInfo(name, to_text(item, self.settings), to_latex(item), False))
        return rows

    def store_numbers(self, numbers: dict[str, float]) -> None:
        """Set variables to numbers from outside the entry line, as a dialog does (`tvm.n`).
        Whole numbers are stored as integers, the rest as decimals."""
        for name, number in numbers.items():
            raw = cas.integer(int(number)) if number.is_integer() else cas.from_float(number)
            self.scope.define(variable_key(self.settings, name), Expr(raw))

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
