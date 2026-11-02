"""The ONLY module allowed to touch SymPy internals; TI-compat fixes live here."""

import math
import operator
import re
from collections.abc import Callable, Iterable
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from itertools import pairwise

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
# One-argument functions, by the name typed. Angle handling is the catalog's business.
FUNCTIONS: dict[str, Callable[[Raw], Raw]] = {
    "sqrt": sp.sqrt,
    "√": sp.sqrt,
    "exp": sp.exp,
    "ln": sp.log,
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "sec": sp.sec,
    "csc": sp.csc,
    "cot": sp.cot,
    "sinh": sp.sinh,
    "cosh": sp.cosh,
    "tanh": sp.tanh,
    "sech": sp.sech,
    "csch": sp.csch,
    "coth": sp.coth,
    "arcsin": sp.asin,
    "arccos": sp.acos,
    "arctan": sp.atan,
    "arcsec": sp.asec,
    "arccsc": sp.acsc,
    "arccot": sp.acot,
    "arcsinh": sp.asinh,
    "arccosh": sp.acosh,
    "arctanh": sp.atanh,
    "abs": sp.Abs,
    "sign": sp.sign,
    "floor": sp.floor,
    "int": sp.floor,
    "ceiling": sp.ceiling,
    "conj": sp.conjugate,
    "real": sp.re,
    "imag": sp.im,
    "angle": sp.arg,
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
# `x>=a` read the other way round is `a<=x`; these give the symbol for that reading.
_LOWER_BOUNDS = {">=": "≤", ">": "<"}
_UPPER_BOUNDS = {"<=": "≤", "<": "<"}
_CHAIN_LENGTH = 2
_CONSTANTS: dict[str, Raw] = {
    "pi": sp.pi,
    "π": sp.pi,
    "ⅇ": sp.E,
    "ⅈ": sp.I,
    "∞": sp.oo,
    "infinity": sp.oo,
    "undef": sp.nan,
}
# How TI prints a function SymPy calls something else. Every inverse is `sin⁻¹`, `sinh⁻¹`, ...;
# `arcsin` is the same function typed on a plain keyboard (see `to_ascii`).
_FUNCTION_NAMES = {
    "log": "ln",
    "Abs": "abs",
    "asin": "sin⁻¹",
    "acos": "cos⁻¹",
    "atan": "tan⁻¹",
    "asec": "sec⁻¹",
    "acsc": "csc⁻¹",
    "acot": "cot⁻¹",
    "asinh": "sinh⁻¹",
    "acosh": "cosh⁻¹",
    "atanh": "tanh⁻¹",
    "re": "real",
    "im": "imag",
    "arg": "angle",
    "conjugate": "conj",
}

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
    """Build `left op right`. An equation with symbols in it stays as typed, even if SymPy would
    call it false, as `x=-1+2ⅈ` for a real symbol `x`; the answers of `cSolve` rely on this."""
    if op in ("=", "≠") and (left.free_symbols or right.free_symbols) and left != right:
        return (sp.Eq if op == "=" else sp.Ne)(left, right, evaluate=False)
    return _RELATIONS[op](left, right)


def boolean(value: bool) -> Raw:
    return sp.true if value else sp.false


def logic(op: str, left: Raw, right: Raw) -> Raw:
    return sp.And(left, right) if op == "and" else sp.Or(left, right)


def logic_all(relations: list[Raw]) -> Raw:
    return sp.And(*relations)


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


def real_float(raw: Raw) -> float | None:
    """A finite real number as a float, or None if `raw` is not one."""
    value = number_value(raw)
    return None if value is None or value.imag else value.real


def bound_float(raw: Raw) -> float | None:
    """Like `real_float`, but ∞ and -∞ are allowed, as for the limits of a probability."""
    if raw == sp.oo:
        return math.inf
    if raw == -sp.oo:
        return -math.inf
    return real_float(raw)


def to_fraction(raw: Raw) -> Fraction | None:
    """An exact number as a Fraction (a decimal is read as the decimal it shows), else None."""
    if raw.is_Rational:
        return Fraction(int(raw.p), int(raw.q))
    if raw.is_Float:
        return Fraction(Decimal(str(raw)))
    return None


def from_float(value: float) -> Raw:
    return sp.Float(value, 15)


def equal(left: Raw, right: Raw, tolerance: float | None = None) -> bool:
    """Decide mathematical equality, within a relative tolerance if one is given."""
    if left == right:
        return True
    if isinstance(left, sp.core.relational.Relational):
        left = left.canonical
        right = right.canonical if isinstance(right, sp.core.relational.Relational) else right
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


# Two exact numbers that SymPy cannot prove equal are still equal if they agree this closely.
_NUMERIC_AGREEMENT = 1e-30
_AGREEMENT_DIGITS = 60


def _close(left: Raw, right: Raw, tolerance: float | None) -> bool:
    a, b = number_value(left), number_value(right)
    if tolerance is not None and a is not None and b is not None:
        return abs(a - b) <= tolerance * max(abs(a), abs(b), 1.0)
    # Logarithms of products and quotients are equal once expanded: ln(a/b) is ln(a)-ln(b).
    difference = sp.simplify(sp.expand_log(left - right, force=True))
    if tolerance is not None and not difference.is_number:
        difference = sp.simplify(difference.evalf())
        coefficients = [abs(c) for c in difference.atoms(sp.Float)]
        return all(c <= tolerance for c in coefficients)
    if difference == 0:
        return True
    if difference.is_number:
        return bool(abs(difference.evalf(_AGREEMENT_DIGITS)) < _NUMERIC_AGREEMENT)
    return False


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
            (sp.Piecewise, self._when),
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

    def _chain(self, raw: Raw) -> ast.Expr | None:
        """Show `x>=-3 and x<=1` as the chained relation `-3≤x≤1`, as TI does."""
        parts = [
            r.canonical if isinstance(r, sp.core.relational.Relational) else r for r in raw.args
        ]
        lows = [r for r in parts if getattr(r, "rel_op", None) in _LOWER_BOUNDS]
        highs = [r for r in parts if getattr(r, "rel_op", None) in _UPPER_BOUNDS]
        if len(raw.args) != _CHAIN_LENGTH or len(lows) != 1 or len(highs) != 1:
            return None
        low, high = lows[0], highs[0]
        if low.lhs != high.lhs:
            return None
        rest = ((_LOWER_BOUNDS[low.rel_op], self.node(low.lhs)),)
        rest += ((_RELATION_TEXT[high.rel_op], self.node(high.rhs)),)
        return ast.Compare(self.node(low.rhs), rest)

    def _logic(self, op: str, raw: Raw) -> ast.Expr:
        if op == "and" and (chain := self._chain(raw)) is not None:
            return chain
        first, *rest = _ordered(op, raw.args)
        result = self.node(first)
        for arg in rest:
            result = ast.Binary(op, result, self.node(arg))
        return result

    def _when(self, raw: Raw) -> ast.Expr:
        args: list[ast.Expr] = []
        for value, condition in raw.args:
            if condition is not sp.true:
                args.append(self.node(condition))
            args.append(self.node(value))
        return ast.Call("when", tuple(args))

    def _call(self, raw: Raw) -> ast.Expr:
        name = str(raw.func)
        args = tuple(self.node(arg) for arg in raw.args)
        return ast.Call(_FUNCTION_NAMES.get(name, name), args)


def _root_key(clause: Raw) -> tuple[tuple[float, float], str]:
    """Order roots by value, and symbolic ones by their text (so `-√(a)` comes before `√(a)`)."""
    target = clause
    if isinstance(clause, sp.And):
        target = next((a for a in clause.args if isinstance(a, sp.Eq)), clause)
    rhs = getattr(target, "rhs", clause)
    # With the parameters taken as zero, `2*π*@n1+π/6` sorts by its π/6.
    at_zero = rhs.subs({symbol: 0 for symbol in rhs.free_symbols})
    usable = at_zero.is_number and at_zero.is_finite
    return (_real_key(at_zero) if usable else (math.inf, 0.0), str(rhs))


def _ordered(op: str, args: tuple[Raw, ...]) -> list[Raw]:
    """Order the parts of `and` and `or` as TI reads them: roots rising, variables by name."""
    relational = sp.core.relational.Relational
    if op == "or" and all(isinstance(arg, relational | sp.And) for arg in args):
        return sorted(args, key=_root_key)
    if not all(isinstance(arg, relational) for arg in args):
        return list(args)
    if op == "and":
        # The equation for the unknown comes first, then conditions on parameters.
        return sorted(args, key=lambda arg: (not isinstance(arg, sp.Eq), str(arg.lhs)))
    return sorted(args, key=_root_key)


def to_ast(raw: Raw, decimal_text: Callable[[Decimal], str]) -> ast.Expr:
    return _Printer(decimal_text).node(raw)


# Functions whose SymPy result is not the form TI shows


def inverse_hyperbolic(name: str, raw: Raw) -> Raw:
    """`arcsinh(1)` stays as typed in Auto, where SymPy would give `ln(1+√(2))`."""
    if name != "arcsinh" or raw.is_Float or raw.free_symbols or raw == 0:
        return FUNCTIONS[name](raw)
    return sp.asinh(raw, evaluate=False)


def hyperbolic(name: str, raw: Raw) -> Raw:
    """`sinh(ln(2))` is `3/4`, but `sinh(1)` stays as typed."""
    result = FUNCTIONS[name](raw)
    if raw.free_symbols or raw.is_Float:
        return result
    rewritten = result.rewrite(sp.exp)
    return rewritten if rewritten.is_Rational else result


def log(value: Raw, base: Raw | None) -> Raw:
    """`log(x)` is the common logarithm; `log(x,b)` uses base `b`."""
    return sp.log(value, 10 if base is None else base)


def integer_part(raw: Raw) -> Raw:
    return sp.sign(raw) * sp.floor(sp.Abs(raw))


def fractional_part(raw: Raw) -> Raw:
    return raw - integer_part(raw)


def round_to(raw: Raw, places: int) -> Raw:
    """Round half away from zero to `places` decimals, giving a decimal number."""
    step = Decimal(1).scaleb(-places)
    return sp.Float(str(Decimal(str(raw.evalf(30))).quantize(step, ROUND_HALF_UP)), 15)


def permutations(n: Raw, k: Raw) -> Raw:
    return sp.factorial(n) / sp.factorial(n - k)


def combinations(n: Raw, k: Raw) -> Raw:
    return sp.binomial(n, k)


def gcd(left: Raw, right: Raw) -> Raw:
    return sp.gcd(left, right)


def lcm(left: Raw, right: Raw) -> Raw:
    return sp.lcm(left, right)


def modulo(left: Raw, right: Raw) -> Raw:
    return sp.Mod(left, right)


def exact(raw: Raw) -> Raw:
    return sp.nsimplify(raw, rational=True)


def integer_value(raw: Raw) -> int | None:
    return int(raw) if raw.is_Integer else None


def when(condition: Raw, then: Raw, otherwise: Raw | None) -> Raw:
    """A piecewise value that is still undecided because the condition is symbolic."""
    if otherwise is None:
        return sp.Piecewise((then, condition))
    return sp.Piecewise((then, condition), (otherwise, True))


# Algebra


def expand(raw: Raw) -> Raw:
    return sp.expand(raw)


def factor(raw: Raw) -> Raw:
    return sp.factor(raw)


def partial_fractions(raw: Raw) -> Raw:
    return sp.apart(raw)


def common_denominator(raw: Raw) -> Raw:
    return sp.together(raw)


# Lists and statistics


def add_all(items: list[Raw]) -> Raw:
    return sp.Add(*items)


def multiply_all(items: list[Raw]) -> Raw:
    return sp.Mul(*items)


def _sorted(items: list[Raw]) -> list[Raw]:
    return sorted(items, key=lambda item: float(item.evalf()))


def sort_order(items: list[Raw], *, descending: bool = False) -> list[int]:
    """The indices that put `items` in order; ties keep their place."""
    keys = [float(item.evalf()) for item in items]
    return sorted(range(len(items)), key=keys.__getitem__, reverse=descending)


def smallest(items: list[Raw]) -> Raw:
    return _sorted(items)[0]


def largest(items: list[Raw]) -> Raw:
    return _sorted(items)[-1]


def mean(items: list[Raw]) -> Raw:
    return sp.Add(*items) / len(items)


def median(items: list[Raw]) -> Raw:
    ordered = _sorted(items)
    middle, odd = divmod(len(ordered), 2)
    return ordered[middle] if odd else (ordered[middle - 1] + ordered[middle]) / 2


def variance(items: list[Raw], *, sample: bool) -> Raw:
    centre = mean(items)
    total = sp.Add(*[(item - centre) ** 2 for item in items])
    return total / (len(items) - 1 if sample else len(items))


def standard_deviation(items: list[Raw], *, sample: bool) -> Raw:
    return sp.sqrt(variance(items, sample=sample))


def running_sums(items: list[Raw]) -> list[Raw]:
    total: Raw = sp.Integer(0)
    sums: list[Raw] = []
    for item in items:
        total = total + item
        sums.append(total)
    return sums


# Matrices and vectors


def matrix_determinant(rows: list[list[Raw]]) -> Raw:
    return sp.Matrix(rows).det()


def matrix_power(rows: list[list[Raw]], exponent: int) -> list[list[Raw]]:
    return (sp.Matrix(rows) ** exponent).tolist()


def matrix_rref(rows: list[list[Raw]]) -> list[list[Raw]]:
    return sp.Matrix(rows).rref()[0].tolist()


def matrix_identity(size: int) -> list[list[Raw]]:
    return sp.eye(size).tolist()


def matrix_solve(coefficients: list[list[Raw]], constants: list[list[Raw]]) -> list[list[Raw]]:
    return (sp.Matrix(coefficients).inv() * sp.Matrix(constants)).tolist()


def cross_product(left: list[Raw], right: list[Raw]) -> list[Raw]:
    return list(sp.Matrix(left).cross(sp.Matrix(right)))


def dot_product(left: list[Raw], right: list[Raw]) -> Raw:
    return sp.Matrix(left).dot(sp.Matrix(right))


def vector_norm(items: list[Raw]) -> Raw:
    return sp.sqrt(sp.Add(*[sp.Abs(item) ** 2 for item in items]))


# Solving

# A root is kept if the equation holds to this much when it is put back in.
_ROOT_CHECK = 1e-9


def as_equation(raw: Raw) -> Raw:
    """`solve(expr,x)` with no `=` means `expr=0`."""
    return raw if isinstance(raw, Boolean) else sp.Eq(raw, 0, evaluate=False)


def with_trig_in_radians(raw: Raw, to_radians: Callable[[Raw], Raw]) -> Raw:
    """Convert the arguments of trig functions of a variable from the document's angle unit.

    Trig of a symbol is left alone when it is entered, so that `sin(x)` prints as typed. A solver
    reads it as radians, so the conversion is done here, just before solving.
    """
    trig = (sp.sin, sp.cos, sp.tan, sp.sec, sp.csc, sp.cot)

    def convert(call: Raw) -> Raw:
        return call.func(to_radians(call.args[0]))

    return raw.replace(lambda e: isinstance(e, trig) and bool(e.args[0].free_symbols), convert)


def _real_key(root: Raw) -> tuple[float, float]:
    """Sort numbers by real part, then imaginary part descending; symbolic roots go last."""
    if not root.is_number:
        return (math.inf, 0.0)
    value = complex(root.evalf())
    return (value.real, -value.imag)


def _sorted_roots(roots: Iterable[Raw]) -> list[Raw]:
    return sorted(roots, key=_real_key)


def _holds(equation: Raw, variable: Raw, root: Raw) -> bool:
    """Does `root` really satisfy `equation`? SymPy sometimes returns a root that is not real."""
    if not isinstance(equation, sp.Eq) or (equation.free_symbols - {variable}):
        return True
    residual = (equation.lhs - equation.rhs).subs(variable, root).evalf()
    if residual.has(sp.nan, sp.zoo) or not residual.is_number:
        return False
    value = complex(residual)
    return abs(value.imag) <= _ROOT_CHECK and abs(value.real) <= _ROOT_CHECK


def _constraint_set(constraint: Raw, variable: Raw) -> Raw:
    if isinstance(constraint, sp.And):
        return sp.Intersection(*[_constraint_set(c, variable) for c in constraint.args])
    if isinstance(constraint, sp.Or):
        return sp.Union(*[_constraint_set(c, variable) for c in constraint.args])
    return sp.solveset(constraint, variable, sp.S.Reals)


def _family(found: Raw, variable: Raw) -> Raw | None:
    """An infinite set of solutions as `x=2*@n1*π+π/6 or ...`, with @n1 any integer."""
    pieces = found.args if isinstance(found, sp.Union) else (found,)
    if not all(isinstance(p, sp.ImageSet) and p.base_set == sp.S.Integers for p in pieces):
        return None
    counter = symbol("@n1")
    clauses = []
    for piece in pieces:
        parameter, formula = piece.lamda.variables[0], piece.lamda.expr
        clauses.append(sp.Eq(variable, sp.expand(formula.subs(parameter, counter)), evaluate=False))
    return sp.Or(*clauses)


def _needs_nonnegative(root: Raw) -> list[Raw]:
    """`a>=0` for each square root (or other even root) of an expression in a parameter."""
    conditions = []
    for power in root.atoms(sp.Pow):
        exponent = power.exp
        if exponent.is_Rational and exponent.q % 2 == 0 and power.base.free_symbols:
            conditions.append(sp.Ge(power.base, 0))
    return conditions


def _as_condition(found: Raw, variable: Raw, equation: Raw) -> Raw | None:
    """Turn a solution set into the condition TI shows, or None if it is not a finite answer."""
    if isinstance(found, sp.Intersection):
        # {-b/a} intersected with the reals: the answer is the finite part.
        finite = [part for part in found.args if isinstance(part, sp.FiniteSet)]
        found = finite[0] if finite else found
    if found == sp.S.EmptySet:
        return sp.false
    if isinstance(found, sp.FiniteSet):
        roots = [r for r in _sorted_roots(found) if _holds(equation, variable, r)]
        clauses = [
            sp.And(sp.Eq(variable, r, evaluate=False), *_needs_nonnegative(r)) for r in roots
        ]
        return sp.Or(*clauses) if clauses else sp.false
    if found in (sp.S.Reals, sp.S.Complexes):
        return sp.true
    family = _family(found, variable)
    if family is not None:
        return family
    if found.has(sp.ImageSet, sp.ConditionSet) or isinstance(found, sp.Intersection):
        return None
    return found.as_relational(variable).replace(
        lambda e: isinstance(e, sp.core.relational.Relational), lambda e: e.canonical
    )


def solve_equation(
    equation: Raw,
    variable: Raw,
    constraints: Iterable[Raw],
    to_radians: Callable[[Raw], Raw] | None,
    *,
    complex_roots: bool,
) -> Raw | None:
    """Solve for one variable. `constraints` restrict the real answers, as `|x>0` does."""
    equation = as_equation(equation)
    if to_radians is not None:
        equation = with_trig_in_radians(equation, to_radians)
    try:
        found = sp.solveset(equation, variable, sp.S.Complexes if complex_roots else sp.S.Reals)
        if not complex_roots:
            for constraint in constraints:
                if constraint.free_symbols <= {variable}:
                    found = found.intersect(_constraint_set(constraint, variable))
    except NotImplementedError, ValueError, TypeError:
        return None
    return _as_condition(found, variable, equation)


def solve_system(equations: list[Raw], variables: list[Raw]) -> Raw | None:
    try:
        solutions = sp.solve([as_equation(e) for e in equations], variables, dict=True)
    except NotImplementedError:
        return None
    if not solutions:
        return sp.false
    cases = [
        sp.And(*[sp.Eq(v, solution[v], evaluate=False) for v in variables if v in solution])
        for solution in solutions
    ]
    return sp.Or(*cases)


def roots_of(
    expression: Raw, variable: Raw, to_radians: Callable[[Raw], Raw] | None, *, complex_roots: bool
) -> list[Raw] | None:
    """The zeros of an expression as a sorted list, or None if they are not a finite set."""
    found = solve_equation(expression, variable, [], to_radians, complex_roots=complex_roots)
    if found is None:
        return None
    if found == sp.false:
        return []
    clauses = found.args if isinstance(found, sp.Or) else (found,)
    if not all(isinstance(clause, sp.Eq) for clause in clauses):
        return None
    return _sorted_roots(clause.rhs for clause in clauses)


def polynomial_roots(expression: Raw, variable: Raw) -> list[Raw] | None:
    """The real roots of a polynomial, repeated by multiplicity, in increasing order."""
    found = sp.roots(sp.Poly(expression, variable), filter="R")
    roots: list[Raw] = []
    for root, multiplicity in found.items():
        roots.extend([root] * multiplicity)
    return _sorted_roots(roots)


def polynomial_value(coefficients: list[Raw], point: Raw) -> Raw:
    """Horner's rule, with the highest power's coefficient first as `polyEval` has it."""
    total: Raw = sp.Integer(0)
    for coefficient in coefficients:
        total = total * point + coefficient
    return total


# Calculus


def substitute(raw: Raw, variable: Raw, value: Raw) -> Raw:
    return raw.subs(variable, value)


def differentiate(expression: Raw, variable: Raw, order: int) -> Raw:
    return sp.diff(expression, variable, order)


def _inverse_hyperbolics_as_logs(raw: Raw) -> Raw:
    """TI writes `ln(2+√(5))`, where SymPy writes `asinh(2)`."""
    return raw.replace(
        lambda e: isinstance(e, sp.asinh), lambda e: sp.log(e.args[0] + sp.sqrt(e.args[0] ** 2 + 1))
    )


def _logs_of_absolute_values(raw: Raw) -> Raw:
    """An antiderivative such as `ln(x)` is written `ln(abs(x))` unless the argument is positive."""
    return raw.replace(
        lambda e: isinstance(e, sp.log) and not e.args[0].is_positive,
        lambda e: sp.log(sp.Abs(e.args[0])),
    )


def _without_abs(expression: Raw, variable: Raw, lower: Raw, upper: Raw) -> Raw | None:
    """Integrate across the points where an `abs(...)` changes sign, one piece at a time."""
    bars = expression.atoms(sp.Abs)
    breaks = {lower, upper}
    for bar in bars:
        found = sp.solveset(bar.args[0], variable, sp.Interval(lower, upper))
        if not isinstance(found, sp.FiniteSet):
            return None
        breaks.update(found)
    points = sorted(breaks, key=lambda point: float(point.evalf()))
    total: Raw = sp.Integer(0)
    for start, end in pairwise(points):
        middle = (start + end) / 2
        signs = {bar: sp.sign(bar.args[0].subs(variable, middle)) * bar.args[0] for bar in bars}
        total += sp.integrate(expression.xreplace(signs), (variable, start, end))
    return total


def integrate(expression: Raw, variable: Raw, lower: Raw | None, upper: Raw | None) -> Raw | None:
    """An antiderivative (no constant) or a definite integral; None if SymPy cannot do it."""
    if lower is None or upper is None:
        result = sp.integrate(expression, variable)
    else:
        result = sp.integrate(expression, (variable, lower, upper))
        if result.has(sp.Integral) and expression.has(sp.Abs):
            result = _without_abs(expression, variable, lower, upper) or result
    if result.has(sp.Integral):
        return None
    result = _inverse_hyperbolics_as_logs(result)
    return result if lower is not None else _logs_of_absolute_values(result)


def limit(expression: Raw, variable: Raw, point: Raw, direction: int | None) -> Raw | None:
    """A limit; `direction` is 1 from the right, -1 from the left and None for both sides."""
    side = "+-" if direction is None else "+" if direction > 0 else "-"
    result = sp.limit(expression, variable, point, side)
    return None if result.has(sp.Limit) else result


def taylor(expression: Raw, variable: Raw, order: int, point: Raw) -> Raw:
    return sp.series(expression, variable, point, order + 1).removeO()


def tangent_line(expression: Raw, variable: Raw, point: Raw) -> Raw:
    slope = sp.diff(expression, variable).subs(variable, point)
    return sp.expand(expression.subs(variable, point) + slope * (variable - point))


def normal_line(expression: Raw, variable: Raw, point: Raw) -> Raw:
    slope = sp.diff(expression, variable).subs(variable, point)
    return sp.expand(expression.subs(variable, point) - (variable - point) / slope)


def implicit_derivative(equation: Raw, variable: Raw, dependent: Raw) -> Raw:
    """dy/dx of an equation in x and y."""
    expression = equation.lhs - equation.rhs if isinstance(equation, sp.Eq) else equation
    return sp.idiff(expression, dependent, variable)


def numerical_integral(expression: Raw, variable: Raw, lower: Raw, upper: Raw) -> Raw:
    return sp.Integral(expression, (variable, lower, upper)).evalf()


_GUESSES = (1, 0, -1, 2, -2, 10, -10)


def numerical_root(equation: Raw, variable: Raw, guess: Raw | None) -> Raw | None:
    expression = equation.lhs - equation.rhs if isinstance(equation, sp.Eq) else equation
    for start in (guess,) if guess is not None else _GUESSES:
        try:
            return sp.nsolve(expression, variable, start)
        except ValueError, ZeroDivisionError, NotImplementedError:
            continue
    return None


def extremum(
    expression: Raw, variable: Raw, constraints: Iterable[Raw], *, maximum: bool
) -> Raw | None:
    """The `x=a` where `expression` is greatest (or least) in the domain, or None if none is."""
    domain: Raw = sp.S.Reals
    for constraint in constraints:
        if constraint.free_symbols <= {variable}:
            domain = domain.intersect(_constraint_set(constraint, variable))
    critical = sp.solveset(sp.diff(expression, variable), variable, domain)
    if critical != sp.S.EmptySet and not isinstance(critical, sp.FiniteSet):
        return None
    candidates = list(critical)
    reaches: list[float] = []  # what the expression approaches at an unbounded end
    for piece in domain.args if isinstance(domain, sp.Union) else (domain,):
        if not isinstance(piece, sp.Interval):
            return None
        for end, is_open in ((piece.start, piece.left_open), (piece.end, piece.right_open)):
            if end.is_finite and not is_open:
                candidates.append(end)
            elif not end.is_finite:
                reaches.append(float(sp.limit(expression, variable, end).evalf()))
    if not candidates:
        return None
    values = {c: float(expression.subs(variable, c).evalf()) for c in candidates}
    pick = max if maximum else min
    best = pick(candidates, key=values.__getitem__)
    # A value approached but never reached beats every candidate if it is more extreme.
    if reaches and pick([values[best], *reaches]) != values[best]:
        return None
    return sp.Eq(variable, best, evaluate=False)


def function_of(name: str, variable: Raw) -> Raw:
    return undefined_function(name, (variable,))


def derivative_of_function(name: str, variable: Raw, order: int) -> Raw:
    return function_of(name, variable).diff(variable, order)


_CONSTANT_NAME = re.compile(r"C\d+")


def solve_ode(conditions: Raw, variable: Raw, name: str) -> Raw | None:
    """Solve an ordinary differential equation, with initial values if they are given.

    `conditions` is the equation, or the equation and `y(a)=b` joined by `and`. The constants of
    integration are named `c1`, `c2`, ... as TI names them.
    """
    parts = conditions.args if isinstance(conditions, sp.And) else (conditions,)
    equations = [p for p in parts if isinstance(p, sp.Eq) and p.has(sp.Derivative)]
    initial = {
        p.lhs: p.rhs
        for p in parts
        if isinstance(p, sp.Eq) and isinstance(p.lhs, sp.core.function.AppliedUndef)
    }
    if len(equations) != 1:
        return None
    try:
        solution = sp.dsolve(
            sp.Eq(equations[0].lhs, equations[0].rhs),
            function_of(name, variable),
            ics=initial or None,
        )
    except NotImplementedError, ValueError:
        return None
    if isinstance(solution, list):
        return None
    return sp.Eq(symbol_named(name), _renumbered(solution.rhs), evaluate=False)


def _renumbered(expression: Raw) -> Raw:
    """Name the constants c1, c2, ... in the order their terms print, as TI does."""
    constants = [s for s in expression.free_symbols if _CONSTANT_NAME.fullmatch(s.name)]
    terms = [t for t in sp.expand(expression).as_ordered_terms() if t.free_symbols & set(constants)]

    def shape(term: Raw) -> str:
        return str(term.xreplace({c: sp.Integer(1) for c in constants}))

    renamed: dict[Raw, Raw] = {}
    for term in sorted(terms, key=shape):
        for constant in sorted(term.free_symbols & set(constants), key=lambda s: s.name):
            if constant not in renamed:
                renamed[constant] = sp.Symbol(f"c{len(renamed) + 1}", real=True)
    return expression.xreplace(renamed)


def symbol_named(name: str) -> Raw:
    return symbol(name)


# Conversions and presentation

APPROX_FRACTION_TOLERANCE = 5e-14


def nearby_fraction(raw: Raw, tolerance: float) -> Raw:
    """The simplest fraction within `tolerance` of a number."""
    return sp.nsimplify(raw, tolerance=tolerance, rational=True)


def polar_parts(raw: Raw) -> tuple[Raw, Raw]:
    """(modulus, argument in radians) of a complex number."""
    return sp.Abs(raw), sp.arg(raw)


def polar_expression(modulus: Raw, argument: Raw) -> Raw:
    """`r*ⅇ^(ⅈ*θ)`, kept as a product so that it is not expanded back to `a+bⅈ`."""
    return sp.Mul(modulus, sp.exp(sp.I * argument, evaluate=False), evaluate=False)


def rectangular(raw: Raw) -> Raw:
    return sp.expand(raw, complex=True)


def cylindrical(x: Raw, y: Raw) -> tuple[Raw, Raw]:
    return sp.sqrt(x**2 + y**2), sp.atan2(y, x)


def spherical(x: Raw, y: Raw, z: Raw) -> tuple[Raw, Raw, Raw]:
    radius = sp.sqrt(x**2 + y**2 + z**2)
    return radius, sp.atan2(y, x), sp.acos(z / radius)


def proper_fraction_text(raw: Raw) -> tuple[Raw, Raw]:
    """Split a rational number into its integer part and fractional part, both of its sign."""
    whole = integer_part(raw)
    return whole, raw - whole


def factor_over_gaussian_integers(raw: Raw) -> Raw:
    return sp.factor(raw, extension=sp.I)


def expand_trig(raw: Raw) -> Raw:
    return sp.expand_trig(raw)


def collect_trig(raw: Raw) -> Raw:
    return sp.fu(raw)


def _eigen_key(value: Raw) -> tuple[float, float]:
    number = complex(value.evalf())
    return (-number.real, -number.imag)


def eigenvalues(rows: list[list[Raw]]) -> list[Raw]:
    """Eigenvalues as decimals, repeated by multiplicity, largest first."""
    found = sp.Matrix(rows).eigenvals()
    values = [value.evalf() for value, count in found.items() for _ in range(count)]
    return sorted(values, key=_eigen_key)


def eigenvectors(rows: list[list[Raw]]) -> list[list[Raw]]:
    """Unit eigenvectors as the columns of a matrix, in the order of `eigenvalues`."""
    columns: list[tuple[Raw, list[Raw]]] = []
    for value, count, vectors in sp.Matrix(rows).eigenvects():
        for vector in vectors[:count]:
            length = sp.sqrt(sum((abs(entry) ** 2 for entry in vector), sp.Integer(0)))
            columns.append((value.evalf(), [(entry / length).evalf() for entry in vector]))
    columns.sort(key=lambda column: _eigen_key(column[0]))
    return [list(row) for row in zip(*[vector for _, vector in columns], strict=True)]
