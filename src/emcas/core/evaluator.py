"""AST to Value, mode-aware."""

from collections.abc import Callable
from typing import Any

from emcas.core import ast, errors
from emcas.core.compat import sympy_adapter as cas
from emcas.core.errors import TIError
from emcas.core.settings import Angle, CasMode, Settings
from emcas.core.values import Bool, Expr, ListValue, MatrixValue, Raw, Str, Value

_ELEMENTWISE = {".+": "+", ".-": "-", ".*": "*", "./": "/", ".^": "^"}
_TRIG = frozenset({"sin", "cos", "tan"})
_ANGLE_FULL_TURN_HALF = {Angle.DEGREE: 180, Angle.GRADIAN: 200}
# How many of each unit make a half turn, for the post operators.
_POST_UNITS = {"°": Angle.DEGREE, "ᴳ": Angle.GRADIAN, "ʳ": Angle.RADIAN}


def _unsupported(what: str) -> TIError:
    return TIError(errors.NOT_IMPLEMENTED, f"Not implemented yet: {what}")


def _as_expr(value: Value) -> Expr:
    if isinstance(value, Expr):
        return value
    if isinstance(value, Bool):
        return Expr(cas.boolean(value.value))
    raise TIError(errors.DATA_TYPE)


def _from_truth(raw: Raw) -> Value:
    decided = cas.truth(raw)
    return Expr(raw) if decided is None else Bool(decided)


def _map(function: Callable[[Value], Value], value: Value) -> Value:
    """Apply `function` to a value, or to each element of a list or matrix."""
    if isinstance(value, ListValue):
        return ListValue(tuple(_map(function, item) for item in value.items))
    if isinstance(value, MatrixValue):
        return MatrixValue(
            tuple(tuple(_as_expr(function(cell)) for cell in row) for row in value.rows)
        )
    return function(value)


def _arithmetic(op: str, left: Value, right: Value) -> Value:
    return Expr(cas.ARITHMETIC[op](_as_expr(left).raw, _as_expr(right).raw))


def _elementwise_lists(op: str, left: ListValue, right: ListValue) -> Value:
    if len(left.items) != len(right.items):
        raise TIError(errors.DIMENSION_MISMATCH)
    pairs = zip(left.items, right.items, strict=True)
    return ListValue(tuple(_combine(op, a, b) for a, b in pairs))


def _matrix_sum(op: str, left: MatrixValue, right: MatrixValue) -> Value:
    if [len(row) for row in left.rows] != [len(row) for row in right.rows]:
        raise TIError(errors.DIMENSION_MISMATCH)
    rows = zip(left.rows, right.rows, strict=True)
    return MatrixValue(
        tuple(
            tuple(_as_expr(_arithmetic(op, a, b)) for a, b in zip(*pair, strict=True))
            for pair in rows
        )
    )


def _matrix_product(left: MatrixValue, right: MatrixValue) -> Value:
    if len(left.rows[0]) != len(right.rows):
        raise TIError(errors.DIMENSION_MISMATCH)
    product = cas.matrix_product(_raw_rows(left), _raw_rows(right))
    return MatrixValue(tuple(tuple(Expr(cell) for cell in row) for row in product))


def _raw_rows(matrix: MatrixValue) -> list[list[Raw]]:
    return [[cell.raw for cell in row] for row in matrix.rows]


def _combine_matrices(op: str, left: MatrixValue, right: MatrixValue) -> Value:
    if op in ("+", "-"):
        return _matrix_sum(op, left, right)
    if op == "*":
        return _matrix_product(left, right)
    raise _unsupported(f"matrix {op}")


def _combine(op: str, left: Value, right: Value) -> Value:
    """Apply an arithmetic operator, broadcasting a scalar over a list or matrix."""
    if isinstance(left, Str) or isinstance(right, Str):
        raise TIError(errors.DATA_TYPE)
    if isinstance(left, MatrixValue) and isinstance(right, MatrixValue):
        return _combine_matrices(op, left, right)
    if isinstance(left, ListValue) and isinstance(right, ListValue):
        return _elementwise_lists(op, left, right)
    if op == "^" and isinstance(left, MatrixValue):
        raise _unsupported("matrix powers")  # m^-1 is an inverse, not an elementwise power
    if op in ("/", "^") and isinstance(right, MatrixValue):
        raise _unsupported(f"{op} by a matrix")
    if isinstance(left, ListValue | MatrixValue):
        return _map(lambda item: _combine(op, item, right), left)
    if isinstance(right, ListValue | MatrixValue):
        return _map(lambda item: _combine(op, left, item), right)
    return _arithmetic(op, left, right)


def _transpose(value: Value) -> Value:
    if not isinstance(value, MatrixValue):
        raise TIError(errors.DATA_TYPE)
    return MatrixValue(tuple(zip(*value.rows, strict=True)))


class Evaluator:
    """Evaluate one entry line under fixed settings."""

    def __init__(self, settings: Settings, ans: Value | None = None) -> None:
        self._settings = settings
        self._ans = ans
        self._dispatch: dict[type, Callable[[Any], Value]] = {
            ast.Number: self._number,
            ast.Dms: self._dms,
            ast.String: lambda node: Str(node.value),
            ast.Name: self._name,
            ast.Call: self._call,
            ast.Index: self._index,
            ast.ListLit: lambda node: ListValue(tuple(self.expr(i) for i in node.items)),
            ast.Matrix: self._matrix,
            ast.Unary: self._unary,
            ast.Postfix: self._postfix,
            ast.Binary: self._binary,
            ast.Compare: self._compare,
            ast.Convert: self._convert,
        }

    def line(self, line: ast.Line) -> Value | None:
        result: Value | None = None
        for statement in line.statements:
            result = self._statement(statement)
        return result

    def _statement(self, statement: ast.Stmt) -> Value:
        if isinstance(statement, ast.Assign | ast.Store | ast.Define | ast.Command):
            raise _unsupported(type(statement).__name__)
        return _map(self._finish, self.expr(statement))

    def _finish(self, value: Value) -> Value:
        if not isinstance(value, Expr):
            return value
        if self._settings.cas_mode != CasMode.ON and cas.is_symbolic(value.raw):
            raise TIError(errors.CAS_RESTRICTED)
        return Expr(cas.finish(value.raw, self._settings))

    def expr(self, node: ast.Expr) -> Value:
        return self._dispatch[type(node)](node)

    def _number(self, node: ast.Number) -> Value:
        text = node.text
        if text[:2].lower() == "0b":
            return Expr(cas.integer(int(text[2:], 2)))
        if text[:2].lower() == "0h":
            return Expr(cas.integer(int(text[2:], 16)))
        if "." not in text and "ᴇ" not in text:
            return Expr(cas.integer(int(text)))
        return Expr(cas.decimal(text, exact=self._settings.calc == "exact"))

    def _dms(self, node: ast.Dms) -> Value:
        degrees, rest = node.text.split("°")
        minutes, _, seconds = rest.partition("'")
        total = cas.decimal(degrees, exact=True) + cas.decimal(minutes, exact=True) / 60
        total += cas.decimal(seconds.rstrip('"') or "0", exact=True) / 3600
        return Expr(self._from_unit(total, Angle.DEGREE))

    def _name(self, node: ast.Name) -> Value:
        name = node.text.casefold()
        if name in {"true", "false"}:
            return Bool(name == "true")
        if cas.is_constant(name):
            return Expr(cas.constant(name))
        if name == "ans" and self._ans is not None:
            return self._ans
        return Expr(cas.symbol(name))

    def _arguments(self, node: ast.Call) -> list[Value]:
        return [self.expr(arg) for arg in node.args]

    def _call(self, node: ast.Call) -> Value:
        name = node.func.casefold()
        if name == "approx":
            return _map(lambda v: Expr(cas.approximate(_as_expr(v).raw)), self._one_arg(node))
        if name in cas.FUNCTIONS:
            function = self._function(name)
            return _map(lambda v: Expr(function(_as_expr(v).raw)), self._one_arg(node))
        args = tuple(_as_expr(value).raw for value in self._arguments(node))
        return Expr(cas.undefined_function(name, args))

    def _one_arg(self, node: ast.Call) -> Value:
        if not node.args:
            raise TIError(errors.TOO_FEW_ARGUMENTS)
        if len(node.args) > 1:
            raise TIError(errors.TOO_MANY_ARGUMENTS)
        return self.expr(node.args[0])

    def _function(self, name: str) -> Callable[[Raw], Raw]:
        function = cas.FUNCTIONS[name]
        if name not in _TRIG:
            return function

        def trig(raw: Raw) -> Raw:
            # A symbolic argument stays as typed, so sin(x) in Degree mode prints as sin(x).
            is_number = cas.number_value(raw) is not None
            return function(self._to_radians(raw) if is_number else raw)

        return trig

    def _to_radians(self, raw: Raw) -> Raw:
        half_turn = _ANGLE_FULL_TURN_HALF.get(self._settings.angle)
        return raw if half_turn is None else raw * cas.pi / half_turn

    def _from_unit(self, raw: Raw, unit: Angle) -> Raw:
        """Convert an angle typed in `unit` to the document's angle mode."""
        if unit == self._settings.angle:
            return raw
        half_turns = raw / _ANGLE_FULL_TURN_HALF[unit] if unit != Angle.RADIAN else raw / cas.pi
        target = _ANGLE_FULL_TURN_HALF.get(self._settings.angle)
        return half_turns * (cas.pi if target is None else target)

    def _index(self, node: ast.Index) -> Value:
        base = self.expr(node.base)
        if not isinstance(base, ListValue) or len(node.subscripts) != 1:
            raise _unsupported("this subscript")
        position = cas.number_value(_as_expr(self.expr(node.subscripts[0])).raw)
        if position is None or position.imag or int(position.real) != position.real:
            raise TIError(errors.DOMAIN)
        if not 1 <= position.real <= len(base.items):
            raise TIError(errors.DOMAIN)
        return base.items[int(position.real) - 1]

    def _matrix(self, node: ast.Matrix) -> Value:
        if len({len(row) for row in node.rows}) != 1:
            raise TIError(errors.INVALID_LIST_OR_MATRIX)
        return MatrixValue(
            tuple(tuple(_as_expr(self.expr(cell)) for cell in row) for row in node.rows)
        )

    def _unary(self, node: ast.Unary) -> Value:
        if node.op == "-":
            return _combine("*", Expr(cas.integer(-1)), self.expr(node.operand))
        if node.op == "not":
            value = self.expr(node.operand)
            if isinstance(value, Bool):
                return Bool(not value.value)
        raise _unsupported(f"the {node.op} operator here")

    def _postfix(self, node: ast.Postfix) -> Value:
        value = self.expr(node.operand)
        if node.op == "ᵀ":
            return _transpose(value)
        if node.op == "!":
            return _map(lambda v: Expr(cas.factorial(_as_expr(v).raw)), value)
        if node.op == "%":
            return _combine("/", value, Expr(cas.integer(100)))
        if node.op in _POST_UNITS:
            unit = _POST_UNITS[node.op]
            return _map(lambda v: Expr(self._from_unit(_as_expr(v).raw, unit)), value)
        raise _unsupported(f"the {node.op} operator here")

    def _binary(self, node: ast.Binary) -> Value:
        left, right = self.expr(node.left), self.expr(node.right)
        op = _ELEMENTWISE.get(node.op, node.op)
        if op in cas.ARITHMETIC:
            return _combine(op, left, right)
        if op in ("and", "or"):
            return _from_truth(cas.logic(op, _as_expr(left).raw, _as_expr(right).raw))
        if op == "&" and isinstance(left, Str) and isinstance(right, Str):
            return Str(left.value + right.value)
        raise _unsupported(f"the {node.op} operator here")

    def _compare(self, node: ast.Compare) -> Value:
        if len(node.rest) > 1:
            raise _unsupported("a chained relation")
        op, right = node.rest[0]
        left_value, right_value = self.expr(node.first), self.expr(right)
        return _from_truth(cas.relation(op, _as_expr(left_value).raw, _as_expr(right_value).raw))

    def _convert(self, node: ast.Convert) -> Value:
        if isinstance(node.target, ast.Name) and node.target.text.casefold() == "decimal":
            return _map(lambda v: Expr(cas.approximate(_as_expr(v).raw)), self.expr(node.value))
        raise _unsupported(f"▶{node.target}")
