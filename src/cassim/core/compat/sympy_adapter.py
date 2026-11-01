"""The ONLY module allowed to touch SymPy internals; TI-compat fixes live here."""

import operator
from collections.abc import Callable
from decimal import Decimal

import sympy as sp
from sympy.core.function import AppliedUndef
from sympy.logic.boolalg import Boolean

from cassim.core import ast
from cassim.core.settings import CasMode, Settings
from cassim.core.values import Raw

ARITHMETIC: dict[str, Callable[[Raw, Raw], Raw]] = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "^": operator.pow,
}
FUNCTIONS: dict[str, Callable[[Raw], Raw]] = {
    "sqrt": sp.sqrt,
    "√": sp.sqrt,
    "exp": sp.exp,
    "ln": sp.log,
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
}
_RELATIONS: dict[str, Callable[[Raw, Raw], Raw]] = {
    "=": sp.Eq,
    "≠": sp.Ne,
    "<": sp.Lt,
    "≤": sp.Le,
    ">": sp.Gt,
    "≥": sp.Ge,
}
_RELATION_TEXT = {"==": "=", "!=": "≠", "<": "<", "<=": "≤", ">": ">", ">=": "≥"}
_CONSTANTS: dict[str, Raw] = {
    "pi": sp.pi,
    "π": sp.pi,
    "ⅇ": sp.E,
    "ⅈ": sp.I,
    "∞": sp.oo,
    "infinity": sp.oo,
    "undef": sp.nan,
}
_FUNCTION_NAMES = {"log": "ln", "asin": "arcsin", "acos": "arccos", "atan": "arctan"}

is_constant = _CONSTANTS.__contains__
factorial = sp.factorial
pi = sp.pi


def constant(name: str) -> Raw:
    return _CONSTANTS[name]


def symbol(name: str) -> Raw:
    # TI variables are real unless the entry says otherwise, as in `z_`.
    return sp.Symbol(name, real=True)


def undefined_function(name: str, args: tuple[Raw, ...]) -> Raw:
    function: Raw = sp.Function(name)
    return function(*args)


def integer(value: int) -> Raw:
    return sp.Integer(value)


def fraction(numerator: int, denominator: int) -> Raw:
    return sp.Rational(numerator, denominator)


def decimal(text: str, *, exact: bool) -> Raw:
    """Read a decimal literal: as a fraction in Exact mode, otherwise as a float."""
    plain = text.replace("ᴇ", "e")
    return sp.Rational(plain) if exact else sp.Float(plain, 15)


def approximate(raw: Raw) -> Raw:
    return raw.evalf()


def relation(op: str, left: Raw, right: Raw) -> Raw:
    return _RELATIONS[op](left, right)


def boolean(value: bool) -> Raw:
    return sp.true if value else sp.false


def logic(op: str, left: Raw, right: Raw) -> Raw:
    return sp.And(left, right) if op == "and" else sp.Or(left, right)


def is_boolean(raw: Raw) -> bool:
    return isinstance(raw, Boolean)


def truth(raw: Raw) -> bool | None:
    """Return the value of a decided relation, or None if it is still symbolic."""
    if raw == sp.true:
        return True
    return False if raw == sp.false else None


def matrix_product(left: list[list[Raw]], right: list[list[Raw]]) -> list[list[Raw]]:
    return (sp.Matrix(left) * sp.Matrix(right)).tolist()


def _is_decimal_result(raw: Raw, settings: Settings) -> bool:
    if settings.calc == "approximate" or raw.has(sp.Float):
        return True
    return settings.cas_mode == CasMode.OFF and not raw.is_Rational


def finish(raw: Raw, settings: Settings) -> Raw:
    """Apply the rules that decide a result's final form.

    A float anywhere makes the whole result approximate, which SymPy does not do by itself: it
    leaves `√(2)+0.5` as a sum. CAS Off keeps fractions but no other exact form.
    """
    if isinstance(raw, sp.And | sp.Or):
        return raw.func(*(finish(arg, settings) for arg in raw.args))
    if raw.has(sp.zoo, sp.nan):
        return sp.nan
    if _is_decimal_result(raw, settings):
        return raw.evalf()
    # Numbers are always in simplest form: (1+ⅈ)^2 is 2*ⅈ, while (x+1)^2 stays as typed.
    return sp.expand(raw) if raw.is_number else raw


def is_symbolic(raw: Raw) -> bool:
    return bool(raw.free_symbols or raw.atoms(AppliedUndef))


def number_value(raw: Raw) -> complex | None:
    """Return a numeric value as a complex number, or None if `raw` is not a finite number."""
    if not raw.is_number or raw.has(sp.oo, sp.nan, sp.zoo, -sp.oo):
        return None
    return complex(raw)


def equal(left: Raw, right: Raw, tolerance: float | None = None) -> bool:
    """Decide mathematical equality, within a relative tolerance if one is given."""
    if left == right:
        return True
    if isinstance(left, sp.core.relational.Relational):
        return (
            type(left) is type(right)
            and equal(left.lhs, right.lhs, tolerance)
            and equal(left.rhs, right.rhs, tolerance)
        )
    if isinstance(left, sp.And | sp.Or):
        return (
            type(left) is type(right)
            and len(left.args) == len(right.args)
            and all(any(equal(a, b, tolerance) for b in right.args) for a in left.args)
        )
    if is_boolean(left) or is_boolean(right):
        return False
    return _close(left, right, tolerance)


def _close(left: Raw, right: Raw, tolerance: float | None) -> bool:
    a, b = number_value(left), number_value(right)
    if tolerance is not None and a is not None and b is not None:
        return abs(a - b) <= tolerance * max(abs(a), abs(b), 1.0)
    difference = sp.simplify(left - right)
    if tolerance is not None and not difference.is_number:
        difference = sp.simplify(difference.evalf())
        coefficients = [abs(c) for c in difference.atoms(sp.Float)]
        return all(c <= tolerance for c in coefficients)
    return difference == 0


def latex(raw: Raw) -> str:
    return sp.latex(raw)


def _negate(node: ast.Expr) -> ast.Expr:
    """Negate by signing the leftmost factor, so `-x/2` does not print as `-(x/2)`."""
    if isinstance(node, ast.Binary) and node.op in ("*", "/"):
        return ast.Binary(node.op, _negate(node.left), node.right)
    return ast.Unary("-", node)


class _Printer:
    """Build the AST of a result, so the parser's printer decides the parentheses."""

    def __init__(self, decimal_text: Callable[[Decimal], str]) -> None:
        self._decimal_text = decimal_text

    def node(self, raw: Raw) -> ast.Expr:
        if raw.is_Number or raw.is_NumberSymbol or raw is sp.I:
            return self._number(raw)
        for kind, build in self._builders():
            if isinstance(raw, kind):
                return build(raw)
        return ast.Name(str(raw))

    def _builders(self) -> tuple[tuple[type | tuple[type, ...], Callable[[Raw], ast.Expr]], ...]:
        return (
            (sp.Add, self._sum),
            (sp.Mul, self._product),
            (sp.exp, lambda raw: ast.Binary("^", ast.Name("ⅇ"), self.node(raw.exp))),
            (sp.Pow, self._power),
            (sp.core.relational.Relational, self._relation),
            (sp.And, lambda raw: self._logic("and", raw)),
            (sp.Or, lambda raw: self._logic("or", raw)),
            ((sp.Function,), self._call),
        )

    def _number(self, raw: Raw) -> ast.Expr:
        if raw.is_Float:
            text = self._decimal_text(abs(Decimal(str(raw))))
            return _negate(ast.Number(text)) if raw < 0 else ast.Number(text)
        if raw.is_Integer:
            number = ast.Number(str(abs(raw)))
            return _negate(number) if raw < 0 else number
        if raw.is_Rational:
            quotient = ast.Binary("/", ast.Number(str(abs(raw.p))), ast.Number(str(raw.q)))
            return _negate(quotient) if raw < 0 else quotient
        names = {sp.pi: "π", sp.E: "ⅇ", sp.I: "ⅈ", sp.oo: "∞", sp.nan: "undef"}
        return _negate(ast.Name("∞")) if raw == -sp.oo else ast.Name(names[raw])

    def _sum(self, raw: Raw) -> ast.Expr:
        first, *rest = raw.as_ordered_terms()
        total = self.node(first)
        for term in rest:
            if term.could_extract_minus_sign():
                total = ast.Binary("-", total, self.node(-term))
            else:
                total = ast.Binary("+", total, self.node(term))
        return total

    def _product(self, raw: Raw) -> ast.Expr:
        coefficient, _ = raw.as_coeff_Mul()
        if coefficient.is_negative:
            return _negate(self.node(-raw))
        numerator, denominator = raw.as_numer_denom()
        if denominator != 1:
            return ast.Binary("/", self.node(numerator), self.node(denominator))
        first, *rest = raw.as_ordered_factors()
        product = self.node(first)
        for factor in rest:
            product = ast.Binary("*", product, self.node(factor))
        return product

    def _power(self, raw: Raw) -> ast.Expr:
        base, exponent = raw.as_base_exp()
        if exponent == sp.Rational(1, 2):
            return ast.Call("√", (self.node(base),))
        if exponent.is_negative:
            return ast.Binary("/", ast.Number("1"), self.node(1 / raw))
        return ast.Binary("^", self.node(base), self.node(exponent))

    def _relation(self, raw: Raw) -> ast.Expr:
        return ast.Compare(self.node(raw.lhs), ((_RELATION_TEXT[raw.rel_op], self.node(raw.rhs)),))

    def _logic(self, op: str, raw: Raw) -> ast.Expr:
        first, *rest = raw.args
        result = self.node(first)
        for arg in rest:
            result = ast.Binary(op, result, self.node(arg))
        return result

    def _call(self, raw: Raw) -> ast.Expr:
        name = str(raw.func)
        args = tuple(self.node(arg) for arg in raw.args)
        return ast.Call(_FUNCTION_NAMES.get(name, name), args)


def to_ast(raw: Raw, decimal_text: Callable[[Decimal], str]) -> ast.Expr:
    return _Printer(decimal_text).node(raw)
