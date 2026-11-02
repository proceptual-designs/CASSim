"""AST to Value, mode-aware."""

from collections.abc import Callable, Generator
from contextlib import contextmanager
from itertools import pairwise
from typing import Any

from cassim.core import angles, ast, catalog, errors
from cassim.core.catalog.matrices import matrix_power
from cassim.core.compat import sympy_adapter as cas
from cassim.core.errors import TIError
from cassim.core.scope import Function, Scope
from cassim.core.settings import Angle, CasMode, Settings
from cassim.core.valueops import as_expr, cell_of, map_value, raw_rows
from cassim.core.values import (
    Bool,
    Expr,
    ListValue,
    MatrixValue,
    Raw,
    Str,
    Unevaluated,
    Value,
    Void,
)

_ELEMENTWISE = {".+": "+", ".-": "-", ".*": "*", "./": "/", ".^": "^"}
# The unit each angle post operator means.
_POST_UNITS = {"°": Angle.DEGREE, "ᵍ": Angle.GRADIAN, "ʳ": Angle.RADIAN}
# Names that mean something already, so a variable or function cannot take them.
_RESERVED = frozenset({"true", "false", "ans"})
# How many user-function calls may be open at once. Each takes several Python frames.
_MAX_CALL_DEPTH = 50


def _unsupported(what: str) -> TIError:
    return TIError(errors.NOT_IMPLEMENTED, f"Not implemented yet: {what}")


def _from_truth(raw: Raw) -> Value:
    decided = cas.truth(raw)
    return Expr(raw) if decided is None else Bool(decided)


def _arithmetic(op: str, left: Value, right: Value) -> Value:
    return Expr(cas.ARITHMETIC[op](as_expr(left).raw, as_expr(right).raw))


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
            tuple(as_expr(_arithmetic(op, a, b)) for a, b in zip(*pair, strict=True))
            for pair in rows
        )
    )


def _matrix_product(left: MatrixValue, right: MatrixValue) -> Value:
    if len(left.rows[0]) != len(right.rows):
        raise TIError(errors.DIMENSION_MISMATCH)
    product = cas.matrix_product(raw_rows(left), raw_rows(right))
    return MatrixValue(tuple(tuple(Expr(cell) for cell in row) for row in product))


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
        return matrix_power(left, right)  # m^-1 is an inverse, not an elementwise power
    if op in ("/", "^") and isinstance(right, MatrixValue):
        raise _unsupported(f"{op} by a matrix")
    if isinstance(left, ListValue | MatrixValue):
        return map_value(lambda item: _combine(op, item, right), left)
    if isinstance(right, ListValue | MatrixValue):
        return map_value(lambda item: _combine(op, left, item), right)
    return _arithmetic(op, left, right)


def _transpose(value: Value) -> Value:
    if not isinstance(value, MatrixValue):
        raise TIError(errors.DATA_TYPE)
    return MatrixValue(tuple(zip(*value.rows, strict=True)))


class Evaluator:
    """Evaluate one entry line under fixed settings."""

    def __init__(
        self, settings: Settings, ans: Value | None = None, scope: Scope | None = None
    ) -> None:
        self._settings = settings
        self._ans = ans
        self._scope = scope if scope is not None else Scope()
        # Bindings from a user-function call or a `|` constraint; the last one wins.
        self._frames: list[dict[str, Value]] = []
        # Relations from enclosing `|` constraints that no binding consumes, such as `x>0`.
        self._constraints: list[Raw] = []
        self._calls = 0
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

    @property
    def settings(self) -> Settings:
        return self._settings

    @property
    def scope(self) -> Scope:
        return self._scope

    @property
    def constraints(self) -> tuple[Raw, ...]:
        return tuple(self._constraints)

    @contextmanager
    def bound(self, bindings: dict[str, Value]) -> Generator[None]:
        """Evaluate with these names bound to values, as for a `seq` index or a `|` constraint."""
        self._frames.append(bindings)
        try:
            yield
        finally:
            self._frames.pop()

    def lookup(self, name: str) -> Value | None:
        for frame in reversed(self._frames):
            if name in frame:
                return frame[name]
        stored = self._scope.get(name)
        return None if stored is None or isinstance(stored, Function) else stored

    def line(self, line: ast.Line) -> Value | None:
        result: Value | None = None
        for statement in line.statements:
            result = self._statement(statement)
        return result

    def _statement(self, statement: ast.Stmt) -> Value:
        if isinstance(statement, ast.Assign):
            return self._assign(statement.target, statement.value)
        if isinstance(statement, ast.Store):
            return self._assign(statement.target, statement.value)
        if isinstance(statement, ast.Define):
            return self._define(statement)
        if isinstance(statement, ast.Command):
            return self._command(statement)
        return self._evaluated(statement)

    def _evaluated(self, node: ast.Expr) -> Value:
        return map_value(self._finish, self.expr(node))

    def _variable_name(self, node: ast.Expr) -> str:
        """The key for a name being stored to; constants and built-ins are refused."""
        if isinstance(node, ast.Name):
            name = node.text.casefold()
        elif isinstance(node, ast.Call):
            name = node.func.casefold()
        else:
            raise _unsupported("indexed assignment")
        if name in _RESERVED or cas.is_constant(name) or catalog.is_builtin(name):
            raise TIError(errors.RESERVED_NAME)
        return name

    def _assign(self, target: ast.Expr, body: ast.Expr) -> Value:
        """`target:=body` and `body→target`: a variable gets the value, a function the body."""
        name = self._variable_name(target)
        if isinstance(target, ast.Call):
            self._scope.define(name, self._make_function(target, body))
            return Void()
        value = self._evaluated(body)
        self._scope.define(name, value)
        return value

    def _make_function(self, target: ast.Call, body: ast.Expr) -> Function:
        params = tuple(arg.text.casefold() for arg in target.args if isinstance(arg, ast.Name))
        if len(params) != len(target.args) or len(set(params)) != len(params):
            raise TIError(errors.SYNTAX)
        return Function(params, body)

    def _define(self, statement: ast.Define) -> Value:
        if statement.visibility is not None:
            raise _unsupported(statement.visibility)
        self._assign(statement.target, statement.body)
        return Void()

    def _command(self, statement: ast.Command) -> Value:
        if statement.name == "DelVar":
            for arg in statement.args:
                if not isinstance(arg, ast.Name):
                    raise TIError(errors.SYNTAX)
                self._scope.delete(arg.text)
            return Void()
        if statement.name == "ClearAZ":
            self._scope.clear_az()
            return Void()
        run = catalog.lookup_command(statement.name)
        if run is None:
            raise _unsupported(statement.name)
        return run(self, statement.args)

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
        bound = self.lookup(name)
        if bound is not None:
            return bound
        if name == "ans" and self._ans is not None:
            return self._ans
        return Expr(cas.symbol(name))

    def _arguments(self, node: ast.Call) -> list[Value]:
        return [self.expr(arg) for arg in node.args]

    def _call(self, node: ast.Call) -> Value:
        name = node.func.casefold()
        stored = self._scope.get(name)
        if isinstance(stored, Function):
            return self._user_call(stored, node)
        entry = catalog.lookup(name)
        if entry is None:
            return self._unresolved(name, node)
        if entry.cas and self._settings.cas_mode != CasMode.ON:
            raise TIError(errors.CAS_RESTRICTED)
        if len(node.args) < entry.low:
            raise TIError(errors.TOO_FEW_ARGUMENTS)
        if entry.high is not None and len(node.args) > entry.high:
            raise TIError(errors.TOO_MANY_ARGUMENTS)
        if isinstance(entry, catalog.LazyEntry):
            return entry.run(self, node.args)
        return entry.run(self, self._arguments(node))

    def _unresolved(self, name: str, node: ast.Call) -> Value:
        """A call to a name that is not a function stays as typed, with its arguments evaluated."""
        args = self._arguments(node)
        if all(isinstance(arg, Expr | Bool) for arg in args):
            return Expr(cas.undefined_function(name, tuple(as_expr(arg).raw for arg in args)))
        return Unevaluated(name, tuple(args))

    def _user_call(self, function: Function, node: ast.Call) -> Value:
        args = self._arguments(node)
        if len(args) < len(function.params):
            raise TIError(errors.TOO_FEW_ARGUMENTS)
        if len(args) > len(function.params):
            raise TIError(errors.TOO_MANY_ARGUMENTS)
        if self._calls >= _MAX_CALL_DEPTH:
            raise TIError(errors.RECURSION)
        # The body sees its parameters and the Problem's variables, not the caller's bindings.
        caller, self._frames = self._frames, [dict(zip(function.params, args, strict=True))]
        self._calls += 1
        try:
            return self.expr(function.body)
        finally:
            self._calls -= 1
            self._frames = caller

    def _from_unit(self, raw: Raw, unit: Angle) -> Raw:
        """Convert an angle typed in `unit` to the document's angle mode."""
        return angles.convert(raw, unit, self._settings.angle)

    def _index(self, node: ast.Index) -> Value:
        base = self.expr(node.base)
        if not isinstance(base, ListValue) or len(node.subscripts) != 1:
            raise _unsupported("this subscript")
        position = cas.number_value(as_expr(self.expr(node.subscripts[0])).raw)
        if position is None or position.imag or int(position.real) != position.real:
            raise TIError(errors.DOMAIN)
        if not 1 <= position.real <= len(base.items):
            raise TIError(errors.DOMAIN)
        return base.items[int(position.real) - 1]

    def _matrix(self, node: ast.Matrix) -> Value:
        if len({len(row) for row in node.rows}) != 1:
            raise TIError(errors.INVALID_LIST_OR_MATRIX)
        return MatrixValue(
            tuple(tuple(cell_of(self.expr(cell)) for cell in row) for row in node.rows)
        )

    def _unary(self, node: ast.Unary) -> Value:
        if node.op == "-":
            return _combine("*", Expr(cas.integer(-1)), self.expr(node.operand))
        if node.op == "not":
            value = self.expr(node.operand)
            if isinstance(value, Bool):
                return Bool(not value.value)
        raise _unsupported(f"the {node.op} operator here")

    def _prime(self, node: ast.Postfix) -> Value:
        """`y'` and `y''` mean a derivative only where a differential equation binds them."""
        count, inner = 1, node.operand
        while isinstance(inner, ast.Postfix) and inner.op == "'":
            count, inner = count + 1, inner.operand
        bound = (
            self.lookup(inner.text.casefold() + "'" * count)
            if isinstance(inner, ast.Name)
            else None
        )
        if bound is None:
            raise _unsupported("the ' operator here")
        return bound

    def _postfix(self, node: ast.Postfix) -> Value:
        if node.op == "'":
            return self._prime(node)
        value = self.expr(node.operand)
        if node.op == "ᵀ":
            return _transpose(value)
        if node.op == "!":
            return map_value(lambda v: Expr(cas.factorial(as_expr(v).raw)), value)
        if node.op == "%":
            return _combine("/", value, Expr(cas.integer(100)))
        if node.op in _POST_UNITS:
            unit = _POST_UNITS[node.op]
            return map_value(lambda v: Expr(self._from_unit(as_expr(v).raw, unit)), value)
        raise _unsupported(f"the {node.op} operator here")

    def _constrain(self, node: ast.Binary) -> Value:
        """`expr|x=value` binds a variable for `expr`; other conditions such as `x>0` are kept
        for the functions that solve within a domain, and `expr` itself is not changed by them.
        """
        bindings: dict[str, Value] = {}
        relations: list[Raw] = []
        for part in _conjuncts(node.right):
            equality = _equality(part)
            if equality is not None:
                bindings[equality[0]] = self.expr(equality[1])
            else:
                relations.append(as_expr(self.expr(part)).raw)
        mark = len(self._constraints)
        self._constraints.extend(relations)
        try:
            with self.bound(bindings):
                return self.expr(node.left)
        finally:
            del self._constraints[mark:]

    def _binary(self, node: ast.Binary) -> Value:
        if node.op == "|":
            return self._constrain(node)
        left, right = self.expr(node.left), self.expr(node.right)
        op = _ELEMENTWISE.get(node.op, node.op)
        if op in cas.ARITHMETIC:
            return _combine(op, left, right)
        if op in ("and", "or"):
            return _from_truth(cas.logic(op, as_expr(left).raw, as_expr(right).raw))
        if op == "&" and isinstance(left, Str) and isinstance(right, Str):
            return Str(left.value + right.value)
        raise _unsupported(f"the {node.op} operator here")

    def _compare(self, node: ast.Compare) -> Value:
        terms = [self.expr(node.first)] + [self.expr(term) for _, term in node.rest]
        relations = [
            cas.relation(op, as_expr(a).raw, as_expr(b).raw)
            for (op, _), (a, b) in zip(node.rest, pairwise(terms), strict=True)
        ]
        # A chain like `0≤x≤2*π` means every link holds.
        return _from_truth(relations[0] if len(relations) == 1 else cas.logic_all(relations))

    def _convert(self, node: ast.Convert) -> Value:
        if isinstance(node.target, ast.Name) and node.target.text.casefold() == "decimal":
            return map_value(lambda v: Expr(cas.approximate(as_expr(v).raw)), self.expr(node.value))
        raise _unsupported(f"▶{node.target}")


def _conjuncts(node: ast.Expr) -> list[ast.Expr]:
    """Split `a and b and c` into its parts."""
    if isinstance(node, ast.Binary) and node.op == "and":
        return _conjuncts(node.left) + _conjuncts(node.right)
    return [node]


def _equality(node: ast.Expr) -> tuple[str, ast.Expr] | None:
    """Read `x=value` into (name, value)."""
    if isinstance(node, ast.Compare) and len(node.rest) == 1:
        (op, value), name = node.rest[0], node.first
        if op == "=" and isinstance(name, ast.Name):
            return name.text.casefold(), value
    return None
