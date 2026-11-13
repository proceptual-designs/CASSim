"""AST to Value, mode-aware."""

from collections.abc import Callable, Generator
from contextlib import contextmanager
from itertools import pairwise
from typing import Any

from cassim.core import angles, ast, builtin_names, catalog, errors
from cassim.core.catalog.conversions import polar_form
from cassim.core.catalog.matrices import matrix_power
from cassim.core.compat import sympy_adapter as cas
from cassim.core.errors import TIError
from cassim.core.scope import Function, Scope
from cassim.core.settings import Angle, CasMode, Domain, Settings, variable_key
from cassim.core.valueops import as_expr, cell_of, map_value, raw_of, raw_rows
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


def _logic(op: str, left: Value, right: Value) -> Value:
    """`and`/`or`: element by element over lists, bitwise on integers, else logical."""
    if isinstance(left, ListValue) and isinstance(right, ListValue):
        if len(left.items) != len(right.items):
            raise TIError(errors.DIMENSION_MISMATCH)
        pairs = zip(left.items, right.items, strict=True)
        return ListValue(tuple(_logic(op, a, b) for a, b in pairs))
    if isinstance(left, ListValue):
        return map_value(lambda item: _logic(op, item, right), left)
    if isinstance(right, ListValue):
        return map_value(lambda item: _logic(op, left, item), right)
    result = cas.logic(op, as_expr(left).raw, as_expr(right).raw)
    if result is None:
        raise TIError(errors.DATA_TYPE)
    return Expr(result) if result.is_Integer else _from_truth(result)


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
        # The `|` bindings in force, which also reach into stored values and Ans.
        self._substitutions: list[dict[str, Value]] = []
        self._non_real = False
        self.warnings: list[str] = []  # for the entry's warning triangle (FR-CALC-007)
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

    def _key(self, name: str) -> str:
        return variable_key(self._settings, name)

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
        self._non_real = False
        return map_value(self._finish, self.expr(node))

    def note_non_real(self) -> None:
        self._non_real = True

    def _variable_name(self, node: ast.Expr) -> str:
        """The key for a name being stored to; constants and built-ins are refused."""
        if isinstance(node, ast.Name):
            text = node.text
        elif isinstance(node, ast.Call):
            text = node.func
        else:
            raise _unsupported("indexed assignment")
        folded = text.casefold()
        function = catalog.is_builtin(folded) or builtin_names.is_function_name(folded)
        if function and isinstance(node, ast.Name):
            # The handheld reads a function's name as the start of a call: `count:={5,3,1,1}`
            # gives "Missing (" (emulator check 6), for functions CASSim has not built too.
            raise TIError(errors.MISSING_OPEN_PAREN)
        if function or folded in _RESERVED or cas.is_constant(folded):
            raise TIError(errors.RESERVED_NAME)
        return self._key(text)

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
        params = tuple(self._key(arg.text) for arg in target.args if isinstance(arg, ast.Name))
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
                self._scope.delete(self._key(arg.text))
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
        finished = Expr(cas.finish(value.raw, self._settings))
        if self._non_real and cas.is_non_real_number(finished.raw):
            raise TIError(errors.NON_REAL)  # only ever set in Real mode
        if self._non_real and errors.NON_REAL_CALCULATION not in self.warnings:
            # a non-real step with a real answer, as in √(-1)·√(-1): kept, with a warning
            self.warnings.append(errors.NON_REAL_CALCULATION)
        # In Polar mode a complex number is written as r*ⅇ^(ⅈ*θ).
        if self._settings.domain == Domain.POLAR:
            return polar_form(finished, self._settings)
        return finished

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
        folded = node.text.casefold()
        if folded in {"true", "false"}:
            return Bool(folded == "true")
        if cas.is_constant(folded):
            return Expr(cas.constant(folded))
        name = self._key(node.text)
        bound = self.lookup(name)
        if bound is not None:
            return bound if self._in_frame(name) else self._substituted(bound)
        if folded == "ans" and self._ans is not None:
            return self._substituted(self._ans)
        return Expr(cas.symbol(name))

    def _in_frame(self, name: str) -> bool:
        return any(name in frame for frame in self._frames)

    def _substituted(self, value: Value) -> Value:
        """Apply the enclosing `|` bindings to a stored value or Ans: `Ans|x=1` with Ans `x^2`."""
        for bindings in self._substitutions:
            for name, replacement in bindings.items():
                symbol = cas.symbol(name)
                new = raw_of(as_expr(replacement))
                value = map_value(
                    lambda v, s=symbol, r=new: Expr(cas.substitute(raw_of(v), s, r)), value
                )
        return value

    def _arguments(self, node: ast.Call) -> list[Value]:
        return [self.expr(arg) for arg in node.args]

    def _call(self, node: ast.Call) -> Value:
        name = self._key(node.func)
        stored = self._scope.get(name)
        if isinstance(stored, Function):
            return self._user_call(stored, node)
        entry = catalog.lookup(node.func)
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
            self.lookup(self._key(inner.text) + "'" * count)
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
            equality = _equality(part, self._key)
            if equality is not None:
                bindings[equality[0]] = self.expr(equality[1])
            else:
                relations.append(as_expr(self.expr(part)).raw)
        mark = len(self._constraints)
        self._constraints.extend(relations)
        self._substitutions.append(bindings)
        try:
            with self.bound(bindings):
                return self.expr(node.left)
        finally:
            del self._constraints[mark:]
            self._substitutions.pop()

    def _binary(self, node: ast.Binary) -> Value:
        if node.op == "|":
            return self._constrain(node)
        left, right = self.expr(node.left), self.expr(node.right)
        op = _ELEMENTWISE.get(node.op, node.op)
        if op == "^" and isinstance(left, Expr) and isinstance(right, Expr):
            return Expr(self._power(left.raw, right.raw))
        if op in cas.ARITHMETIC:
            return _combine(op, left, right)
        if op in ("and", "or"):
            return _logic(op, left, right)
        if op == "&" and isinstance(left, Str) and isinstance(right, Str):
            return Str(left.value + right.value)
        raise _unsupported(f"the {node.op} operator here")

    def _power(self, base: Raw, exponent: Raw) -> Raw:
        """`base^exponent`. In Real mode an odd root of a negative number is real, and a complex
        result from real operands (the square root of -4, written (-4)^(1/2)) is flagged."""
        if self._settings.domain == Domain.REAL and base.is_real is True and exponent.is_real:
            real = cas.real_power(base, exponent)
            if real is not None:
                return real
            result = cas.ARITHMETIC["^"](base, exponent)
            if cas.is_non_real_number(result):
                self.note_non_real()
            return result
        return cas.ARITHMETIC["^"](base, exponent)

    def _compare(self, node: ast.Compare) -> Value:
        terms = [self.expr(node.first)] + [self.expr(term) for _, term in node.rest]
        relations = [
            cas.relation(op, as_expr(a).raw, as_expr(b).raw)
            for (op, _), (a, b) in zip(node.rest, pairwise(terms), strict=True)
        ]
        # A chain like `0≤x≤2*π` means every link holds.
        return _from_truth(relations[0] if len(relations) == 1 else cas.logic_all(relations))

    def _convert(self, node: ast.Convert) -> Value:
        target = node.target
        name = target.text if isinstance(target, ast.Name) else target.func
        run = catalog.lookup_conversion(name)
        if run is None:
            raise _unsupported(f"▶{target}")
        args = [] if isinstance(target, ast.Name) else self._arguments(target)
        return run(self, self.expr(node.value), args)


def _conjuncts(node: ast.Expr) -> list[ast.Expr]:
    """Split `a and b and c` into its parts."""
    if isinstance(node, ast.Binary) and node.op == "and":
        return _conjuncts(node.left) + _conjuncts(node.right)
    return [node]


def _equality(node: ast.Expr, key: Callable[[str], str]) -> tuple[str, ast.Expr] | None:
    """Read `x=value` into (name, value)."""
    if isinstance(node, ast.Compare) and len(node.rest) == 1:
        (op, value), name = node.rest[0], node.first
        if op == "=" and isinstance(name, ast.Name):
            return key(name.text), value
    return None
