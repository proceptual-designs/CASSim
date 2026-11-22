"""The ONLY module allowed to touch SymPy internals; TI-compat fixes live here."""

import math
import operator
import re
from collections.abc import Callable, Iterable
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from itertools import pairwise
from typing import Any

import sympy as sp
from sympy.core.function import AppliedUndef
from sympy.core.relational import Relational
from sympy.logic.boolalg import And, Boolean, Not, Or
from sympy.printing.latex import LatexPrinter

from cassim.core import ast
from cassim.core.compat.math_source import check_math_source
from cassim.core.settings import CasMode, Settings
from cassim.core.values import Raw

ARITHMETIC: dict[str, Callable[[Raw, Raw], Raw]] = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "^": operator.pow,
}


def _keeps_decimal(function: Callable[[Raw], Raw]) -> Callable[[Raw], Raw]:
    """A rounding function that gives a decimal for a decimal argument: `floor(2.7)` is `2.`."""

    def apply(raw: Raw) -> Raw:
        result = function(raw)
        return sp.Float(result, 15) if raw.is_Float and result.is_Integer else result

    return apply


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
    "floor": _keeps_decimal(sp.floor),
    "int": _keeps_decimal(sp.floor),
    "ceiling": _keeps_decimal(sp.ceiling),
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


def replace_calls(raw: Raw, name: str, value_of: Callable[[Raw], Raw | None]) -> Raw:
    """`raw` with each call `name(k)` of an undefined function replaced by `value_of(k)`, where
    that is not None: the earlier terms in a recursive sequence, `u(n-1)` in `seqgen`."""

    def wanted(node: Raw) -> bool:
        return (
            isinstance(node, AppliedUndef)
            and str(node.func) == name
            and len(node.args) == 1
            and value_of(node.args[0]) is not None
        )

    return raw.replace(wanted, lambda node: value_of(node.args[0]))


def calls(raw: Raw, name: str) -> bool:
    """Whether `raw` still holds a call to the undefined function `name`."""
    return any(str(node.func) == name for node in raw.atoms(AppliedUndef))


def integer(value: int) -> Raw:
    return sp.Integer(value)


def fraction(numerator: int, denominator: int) -> Raw:
    return sp.Rational(numerator, denominator)


def decimal(text: str, *, exact: bool) -> Raw:
    """Read a decimal literal: as a fraction in Exact mode, otherwise as a float."""
    plain = text.replace("ᴇ", "e")
    return sp.Rational(plain) if exact else sp.Float(plain, 15)


def approximate(raw: Raw) -> Raw:
    """The decimal form, also of a relation (`x=√(2)`) or a combination of them with and/or."""
    if isinstance(raw, sp.And | sp.Or):
        return raw.func(*(approximate(arg) for arg in raw.args))
    if isinstance(raw, sp.core.relational.Relational):
        return raw.func(approximate(raw.lhs), approximate(raw.rhs), evaluate=False)
    return raw.evalf()


def relation(op: str, left: Raw, right: Raw) -> Raw:
    """Build `left op right`. An equation with symbols in it stays as typed, even if SymPy would
    call it false, as `x=-1+2ⅈ` for a real symbol `x`; the answers of `cSolve` rely on this."""
    if op in ("=", "≠") and (left.free_symbols or right.free_symbols) and left != right:
        return (sp.Eq if op == "=" else sp.Ne)(left, right, evaluate=False)
    return _RELATIONS[op](left, right)


def boolean(value: bool) -> Raw:
    return sp.true if value else sp.false


_BITWISE = {"and": operator.and_, "or": operator.or_, "xor": operator.xor}
_LOGICAL = {"and": sp.And, "or": sp.Or, "xor": sp.Xor}


def logic(op: str, left: Raw, right: Raw) -> Raw | None:
    """`and`/`or`/`xor`: bitwise on two integers (`3 or 4` is 7, `2 xor 3` is 1), else logical;
    None if neither fits."""
    if left.is_Integer and right.is_Integer:
        return sp.Integer(_BITWISE[op](int(left), int(right)))
    try:
        return _LOGICAL[op](left, right)
    except TypeError:  # a number or expression that is not true or false
        return None


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
        # evalf() turns a decimal zero into an exact 0; the handheld shows `0.` (check 6, D19).
        return raw if raw.is_Float else raw.evalf()
    if raw.is_number and raw.is_real is False:
        return _complex_form(raw)
    # Numbers are always in simplest form: (1+ⅈ)^2 is 2*ⅈ, while (x+1)^2 stays as typed.
    return sp.expand(raw) if raw.is_number else raw


_INVERSE_FUNCTIONS = (sp.asin, sp.acos, sp.acot, sp.asec, sp.acsc, sp.asinh, sp.acosh, sp.atanh)


def _complex_form(raw: Raw) -> Raw:
    """A non-real number as a+bⅈ: (-8)^(1/3) is 1+√3·ⅈ, and sin⁻¹(2) is π/2-ln(2+√3)·ⅈ."""
    source = raw.rewrite(sp.log) if raw.has(*_INVERSE_FUNCTIONS) else raw
    tidy = sp.expand_complex(source)
    return sp.expand(raw) if tidy.has(sp.re, sp.im) else tidy


def real_power(base: Raw, exponent: Raw) -> Raw | None:
    """The real value of a negative number to a fraction with an odd denominator, which Real mode
    takes: (-8)^(1/3) is -2 and (-8)^(2/3) is 4. None when this does not apply."""
    if not (base.is_number and base.is_negative and exponent.is_Rational and exponent.q % 2):
        return None
    return (-1) ** exponent.p * (-base) ** exponent


def is_symbolic(raw: Raw) -> bool:
    return bool(raw.free_symbols or raw.atoms(AppliedUndef))


def is_undefined(raw: Raw) -> bool:
    """Whether `raw` is `undef`, as from 1/0 (a spreadsheet cell shows #UNDEF)."""
    return raw is sp.nan


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


_GRAPH_FUNCTIONS: dict[Any, str] = {
    sp.sin: "sin",
    sp.cos: "cos",
    sp.tan: "tan",
    sp.asin: "asin",
    sp.acos: "acos",
    sp.atan: "atan",
    sp.sinh: "sinh",
    sp.cosh: "cosh",
    sp.tanh: "tanh",
    sp.asinh: "asinh",
    sp.acosh: "acosh",
    sp.atanh: "atanh",
    sp.exp: "exp",
    sp.log: "log",
    sp.Abs: "fabs",
    sp.floor: "floor",
    sp.ceiling: "ceil",
    sp.Min: "min",
    sp.Max: "max",
}
_GRAPH_MATH_NAMES = frozenset(_GRAPH_FUNCTIONS.values()) | {
    "pi",
    "e",
    "inf",
    "nan",
}
_GRAPH_BINARY_OPERATORS = {
    "==": "==",
    "!=": "!=",
    "<": "<",
    "<=": "<=",
    ">": ">",
    ">=": ">=",
}


class _GraphMathPrinter:
    def __init__(self, variable: Raw) -> None:
        self.variable = variable

    def emit(self, raw: Raw) -> str:
        for printer in (
            self._constant,
            self._relation,
            self._logic,
            self._piecewise,
            self._arithmetic,
            self._function,
        ):
            source = printer(raw)
            if source is not None:
                return source
        msg = f"unsupported graph expression: {raw}"
        raise ValueError(msg)

    def _constant(self, raw: Raw) -> str | None:
        if raw == self.variable:
            return "x"
        for value, source in (
            (sp.true, "True"),
            (sp.false, "False"),
            (sp.pi, "math.pi"),
            (sp.E, "math.e"),
            (sp.oo, "math.inf"),
            (-sp.oo, "-math.inf"),
            (sp.nan, "math.nan"),
        ):
            if raw is value:
                return source
        if raw.is_Rational:
            return str(int(raw)) if raw.is_Integer else f"({int(raw.p)} / {int(raw.q)})"
        if raw.is_Float:
            value = float(raw)
            return (
                repr(value)
                if math.isfinite(value)
                else "math.nan"
                if math.isnan(value)
                else "math.inf"
                if value > 0
                else "-math.inf"
            )
        if raw.is_Symbol:
            msg = f"graph expressions may only use the variable {self.variable}"
            raise ValueError(msg)
        return None

    def _relation(self, raw: Raw) -> str | None:
        if not isinstance(raw, Relational):
            return None
        operation = _GRAPH_BINARY_OPERATORS.get(raw.rel_op)
        if operation is None:
            msg = f"unsupported graph relation: {raw.rel_op}"
            raise ValueError(msg)
        return f"({self.emit(raw.lhs)} {operation} {self.emit(raw.rhs)})"

    def _logic(self, raw: Raw) -> str | None:
        if isinstance(raw, And):
            return "(" + " and ".join(self.emit(part) for part in raw.args) + ")"
        if isinstance(raw, Or):
            return "(" + " or ".join(self.emit(part) for part in raw.args) + ")"
        if isinstance(raw, Not):
            return f"(not {self.emit(raw.args[0])})"
        return None

    def _piecewise(self, raw: Raw) -> str | None:
        if raw.func is not sp.Piecewise:
            return None
        result = "math.nan"
        for value, condition in reversed(raw.args):
            if condition is sp.true:
                result = self.emit(value)
            else:
                result = f"({self.emit(value)} if {self.emit(condition)} else {result})"
        return result

    def _arithmetic(self, raw: Raw) -> str | None:
        if raw.is_Add:
            return "(" + " + ".join(self.emit(part) for part in raw.args) + ")"
        if raw.is_Mul:
            return "(" + " * ".join(self.emit(part) for part in raw.args) + ")"
        if raw.is_Pow:
            base, exponent = raw.args
            return f"({self.emit(base)} ** {self.emit(exponent)})"
        return None

    def _function(self, raw: Raw) -> str | None:
        function_name = _GRAPH_FUNCTIONS.get(raw.func)
        if function_name is None:
            return None
        args = ", ".join(self.emit(arg) for arg in raw.args)
        if function_name in {"min", "max"}:
            return f"{function_name}({args})"
        return f"math.{function_name}({args})"


def math_source(expression: Raw, variable: Raw) -> str:
    """Print a real-valued expression as a checked Python expression over `math`."""
    if not variable.is_Symbol:
        msg = "the graph variable must be a symbol"
        raise ValueError(msg)
    source = _GraphMathPrinter(variable).emit(expression)
    check_math_source(source)
    return source


def compile_math(expression: Raw, variable: Raw) -> tuple[str, Callable[[float], float]]:
    """Compile a checked math expression for local graph sampling in the UI worker."""
    source = math_source(expression, variable)
    from cassim.core.compat.math_source import compile_math_source  # noqa: PLC0415

    function = compile_math_source(source)
    return source, function


_check_math_source = check_math_source


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


class _TILatexPrinter(LatexPrinter):
    """SymPy's LaTeX printer with TI's conventions: bold upright ⅇ, bold italic ⅈ, `ln`, `sin⁻¹`,
    `undef`, and `and`/`or` between conditions (`∧`/`∨` when `symbols_for_logic`)."""

    symbols_for_logic = False
    decimal_text: Callable[[Decimal], str] | None = None

    def _print_Float(self, expr: Raw) -> str:
        if self.decimal_text is None:
            return super()._print_Float(expr)
        sign = "-" if expr < 0 else ""
        text = self.decimal_text(abs(Decimal(str(expr))))
        mantissa, marker, exponent = text.partition("ᴇ")
        if marker:
            return rf"{sign}{mantissa} \cdot 10^{{{exponent}}}"
        return sign + text

    def _print(self, expr: Any, **kwargs: Any) -> str:  # noqa: ANN401
        if expr is sp.E:
            return r"\mathbf{e}"
        if expr is sp.I:
            return r"\boldsymbol{i}"
        if expr is sp.nan:
            return r"\text{undef}"  # SymPy would print NaN
        if isinstance(expr, sp.exp):
            return rf"\mathbf{{e}}^{{{self._print(expr.exp)}}}"
        return super()._print(expr, **kwargs)

    def _joined(self, expr: Any, word: str, symbol: str, inner: type) -> str:  # noqa: ANN401
        """The arguments of an `And` or `Or`; the other connective inside is bracketed."""
        parts = [
            rf"\left({self._print(arg)}\right)" if isinstance(arg, inner) else self._print(arg)
            for arg in expr.args
        ]
        joint = rf" {symbol} " if self.symbols_for_logic else rf"\ \mathbf{{{word}}}\ "
        return joint.join(parts)

    def _print_And(self, e: Any) -> str:  # noqa: ANN401
        return self._joined(e, "and", r"\wedge", sp.Or)

    def _print_Or(self, e: Any) -> str:  # noqa: ANN401
        return self._joined(e, "or", r"\vee", sp.And)


_LATEX_SETTINGS = {"inv_trig_style": "power", "ln_notation": True}


def latex(
    raw: Raw, *, decimal_text: Callable[[Decimal], str] | None = None, logic_symbols: bool = False
) -> str:
    printer = _TILatexPrinter(_LATEX_SETTINGS)
    printer.decimal_text = decimal_text
    printer.symbols_for_logic = logic_symbols
    return printer.doprint(raw)


def _negate(node: ast.Expr) -> ast.Expr:
    """Negate by signing the leftmost factor, so `-x/2` does not print as `-(x/2)`."""
    if isinstance(node, ast.Binary) and node.op in ("*", "/"):
        return ast.Binary(node.op, _negate(node.left), node.right)
    return ast.Unary("-", node)


def _unevaluated_product(factors: list[Raw]) -> Raw:
    if not factors:
        return sp.Integer(1)
    return factors[0] if len(factors) == 1 else sp.Mul(*factors, evaluate=False)


def _split_quotient(raw: Raw) -> tuple[Raw, Raw]:
    """A product's numerator and denominator as TI shows them. Unlike SymPy's `as_numer_denom`,
    `ⅇ^(-a)` stays on top (`2·ⅇ^(-a)`, not `2/ⅇ^a`) and a number is not multiplied into a
    bracket (`-6·(x³-1)`, not `-6·x³+6`)."""
    top: list[Raw] = []
    bottom: list[Raw] = []
    factors: list[Raw] = list(sp.Mul.make_args(raw))
    for factor in factors:
        if factor.is_Rational and not factor.is_Integer:
            if factor.p != 1:
                top.append(sp.Integer(factor.p))
            bottom.append(sp.Integer(factor.q))
        elif factor.is_Pow and factor.exp.is_number and factor.exp.is_negative:
            bottom.append(sp.Pow(factor.base, -factor.exp))
        else:
            top.append(factor)
    return _unevaluated_product(top), _unevaluated_product(bottom)


def _surds_after_variables(factors: list[Raw]) -> list[Raw]:
    """A product's factors with any surd (√3) moved after the last factor with a variable:
    TI writes `h^3*√(3)` (emulator check 6, K4). Products with no variable keep their order."""
    surds = [f for f in factors if f.is_Pow and f.base.is_Rational and not f.free_symbols]
    variables = [i for i, f in enumerate(factors) if f.free_symbols]
    if not surds or not variables:
        return factors
    rest = [f for f in factors if not any(f is s for s in surds)]
    last = max(i for i, f in enumerate(rest) if f.free_symbols)
    return [*rest[: last + 1], *surds, *rest[last + 1 :]]


class _Printer:
    """Build the AST of a result, so the parser's printer decides the parentheses."""

    def __init__(self, decimal_text: Callable[[Decimal], str]) -> None:
        self._decimal_text = decimal_text

    def node(self, raw: Raw) -> ast.Expr:
        if raw is sp.true or raw is sp.false:
            return ast.Name("true" if raw is sp.true else "false")
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
            # `a!` stays postfix, as typed (emulator check 6, A10 shows `a!=b`).
            (sp.factorial, lambda raw: ast.Postfix("!", self.node(raw.args[0]))),
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
        # Highest degree first, as TI orders terms: `t^2+k`, `x^3+a*x+2`. A negative leading
        # term is taken out: `-(3*c1-1)`, `-(√3+2)` (emulator check 6, K4 and K7).
        first, *rest = raw.as_ordered_terms(order="grlex")
        if first.could_extract_minus_sign() and not first.is_number:
            return ast.Unary("-", self.node(-raw))
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
        numerator, denominator = _split_quotient(raw)
        if denominator != 1:
            return ast.Binary("/", self.node(numerator), self.node(denominator))
        # A surd after the variables: TI writes `h^3*√(3)` (emulator check 6, K4).
        first, *rest = _surds_after_variables(raw.as_ordered_factors())
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
    """`iPart`: the whole part, a decimal for a decimal argument (`iPart(-2.3)` is `-2.`)."""
    return _keeps_decimal(lambda value: sp.sign(value) * sp.floor(sp.Abs(value)))(raw)


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


def nth_root(raw: Raw, index: Raw) -> Raw:
    """`root(x, n)`: an odd root of a negative number is real (root(-8,3) is -2), as on TI."""
    if index.is_integer and index.is_odd and raw.is_negative:
        return -sp.root(-raw, index)
    return sp.root(raw, index)


def is_non_real_number(raw: Raw) -> bool:
    """A number with an imaginary part (ⅈ, 2·ⅈ), as opposed to a real or a symbolic value."""
    return bool(raw.is_number and raw.is_real is False and not raw.has(sp.nan, sp.zoo))


def piecewise(pieces: list[tuple[Raw, Raw]], otherwise: Raw | None) -> Raw:
    """A piecewise value whose conditions are still symbolic: (value, condition) in order, then
    the value when none holds."""
    tail = [(otherwise, sp.true)] if otherwise is not None else []
    return sp.Piecewise(*pieces, *tail)


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


_QUADRATIC_DEGREE = 2


def _square_target(variable: Raw) -> tuple[Raw, Raw] | None:
    if isinstance(variable, sp.Symbol):
        return variable, sp.Integer(1)
    if (
        isinstance(variable, sp.Pow)
        and isinstance(variable.base, sp.Symbol)
        and variable.exp.is_Rational
        and variable.exp != 0
    ):
        return variable.base, variable.exp
    return None


def _quadratic_coefficients(
    expression: Raw, targets: list[tuple[Raw, Raw]]
) -> dict[tuple[int, ...], Raw] | None:
    coefficients: dict[tuple[int, ...], Raw] = {}
    for term in sp.Add.make_args(sp.expand(expression)):
        exponents: list[int] = []
        monomial = sp.Integer(1)
        powers = term.as_powers_dict()
        for target, target_power in targets:
            exponent = powers.get(target, sp.Integer(0))
            degree = sp.cancel(exponent / target_power)
            if degree.is_Integer is not True or degree < 0:
                return None
            exponents.append(int(degree))
            monomial *= target**exponent
        if sum(exponents) > _QUADRATIC_DEGREE:
            return None
        coefficient = sp.cancel(term / monomial)
        if any(coefficient.has(target) for target, _ in targets):
            return None
        key = tuple(exponents)
        coefficients[key] = coefficients.get(key, sp.Integer(0)) + coefficient
    return coefficients


def _complete_square_parts(
    expression: Raw, targets: list[tuple[Raw, Raw]]
) -> tuple[list[Raw], Raw] | None:
    residual = sp.expand(expression)
    squares: list[Raw] = []
    for position, (base, power) in enumerate(targets):
        coefficients = _quadratic_coefficients(residual, targets)
        if coefficients is None:
            return None
        quadratic = tuple(_QUADRATIC_DEGREE if i == position else 0 for i in range(len(targets)))
        linear = tuple(1 if i == position else 0 for i in range(len(targets)))
        leading = sp.cancel(coefficients.get(quadratic, sp.Integer(0)))
        middle = sp.cancel(coefficients.get(linear, sp.Integer(0)))
        if leading == 0:
            return None

        term = base**power
        squares.append(leading * (term + middle / (2 * leading)) ** 2)
        residual = sp.expand(
            residual - leading * term**2 - middle * term - middle**2 / (4 * leading)
        )
    return squares, residual


def complete_square(raw: Raw, variables: list[Raw]) -> Raw | None:
    """Complete each requested variable's pure quadratic terms, leaving cross terms intact."""
    is_equation = isinstance(raw, sp.Equality)
    if raw.is_Equality and not is_equation:
        return None
    expression = raw.lhs - raw.rhs if is_equation else raw

    targets = [_square_target(variable) for variable in variables]
    if not targets or any(target is None for target in targets):
        return None
    typed_targets = [target for target in targets if target is not None]
    if len({base for base, _ in typed_targets}) != len(typed_targets):
        return None

    parts = _complete_square_parts(expression, typed_targets)
    if parts is None:
        return None
    squares, residual = parts
    left = sp.Add(*squares)
    if is_equation:
        return sp.Eq(left, -residual, evaluate=False)
    return sp.Add(left, residual)


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


def _numeric_root_objects(raw: Raw) -> Raw:
    """A root SymPy can only name (`CRootOf(x**7+...)`) as its decimal value, as TI gives it."""
    return raw.replace(lambda e: isinstance(e, sp.CRootOf), lambda e: e.evalf(15))


def _finite_part(found: Raw) -> Raw:
    """{-b/a} intersected with the reals: the answer is the finite part."""
    if isinstance(found, sp.Intersection):
        finite = [part for part in found.args if isinstance(part, sp.FiniteSet)]
        return finite[0] if finite else found
    return found


def _without_excluded(found: Raw) -> Raw:
    """Roots less the points where the equation is undefined (a zero denominator): SymPy gives
    them as a set difference, which TI does not show."""
    if not isinstance(found, sp.Complement):
        return found
    kept, excluded = (_finite_part(part) for part in found.args)
    if not isinstance(kept, sp.FiniteSet) or not isinstance(excluded, sp.FiniteSet):
        return found
    return sp.FiniteSet(*[root for root in kept.args if root not in excluded.args])


def _plausibly_real(root: Raw, *, complex_roots: bool) -> bool:
    """A root in a parameter written with ⅈ (the other two roots of a cubic) is not real."""
    return complex_roots or not (root.free_symbols and root.has(sp.I))


def _as_condition(
    found: Raw, variable: Raw, equation: Raw, *, complex_roots: bool = False
) -> Raw | None:
    """Turn a solution set into the condition TI shows, or None if it is not a finite answer."""
    found = _finite_part(_without_excluded(_finite_part(found)))
    if found == sp.S.EmptySet:
        return sp.false
    if isinstance(found, sp.FiniteSet):
        candidates = [
            _numeric_root_objects(r)
            for r in found.args
            if _plausibly_real(r, complex_roots=complex_roots)
        ]
        roots = [r for r in _sorted_roots(candidates) if _holds(equation, variable, r)]
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
    condition = found.as_relational(variable).replace(
        lambda e: isinstance(e, sp.core.relational.Relational), lambda e: e.canonical
    )
    # Only relations joined by and/or can be shown; never SymPy's `~(Eq(...))`.
    return None if condition.has(sp.Not) else condition


def _unconditioned(found: Raw, variable: Raw) -> Raw:
    """`sin(x)=y` is solved only for |y|<=1, a condition on the parameter that TI leaves unsaid."""
    if isinstance(found, sp.ConditionSet) and variable not in found.condition.free_symbols:
        return found.args[2]
    return found


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
        found = _unconditioned(found, variable)
        if not complex_roots:
            for constraint in constraints:
                if constraint.free_symbols <= {variable}:
                    found = found.intersect(_constraint_set(constraint, variable))
    except NotImplementedError, ValueError, TypeError:
        return None
    condition = _as_condition(found, variable, equation, complex_roots=complex_roots)
    bounds = [c for c in constraints if variable in c.free_symbols and c.free_symbols - {variable}]
    if condition is None or not bounds or complex_roots:
        return condition
    return _within_parametric_bounds(condition, variable, bounds)


def _within_parametric_bounds(condition: Raw, variable: Raw, bounds: list[Raw]) -> Raw:
    """Keep the roots that meet bounds with a parameter, `|0<x<h/2`, taking the parameters as
    positive, as TI does: a root kept that way gets `and h>0` (emulator check 6, K4)."""
    clauses = condition.args if isinstance(condition, sp.Or) else (condition,)
    kept: list[Raw] = []
    for clause in clauses:
        parts = conjuncts(clause)
        root = next((p.rhs for p in parts if isinstance(p, sp.Eq) and p.lhs == variable), None)
        if root is None:
            kept.append(clause)
            continue
        parameters = sorted(root.free_symbols, key=str)
        positive = {p: sp.Dummy(str(p), positive=True) for p in parameters}
        held = [sp.simplify(b.subs(variable, root).subs(positive)) for b in bounds]
        if any(h == sp.false for h in held):
            continue
        if all(h == sp.true for h in held) and parameters:
            parts += [sp.Gt(p, 0) for p in parameters]
        kept.append(sp.And(*parts))
    return sp.Or(*kept) if kept else sp.false


def conjuncts(raw: Raw) -> list[Raw]:
    """The parts of `a and b and c`, or just `raw`: a system can be typed either way."""
    return list(raw.args) if isinstance(raw, sp.And) else [raw]


def linear_solve(equations: list[Raw], variables: list[Raw]) -> list[Raw] | None:
    """The values of a linear system's unknowns in order, or None if it has no solution. A system
    with infinitely many keeps the free unknowns in the answer."""
    try:
        found = sp.linsolve([as_equation(e) for e in equations], variables)
    except ValueError, NotImplementedError, sp.PolynomialError:
        return None
    if not found:
        return None
    return list(next(iter(found)))


def solve_system(equations: list[Raw], variables: list[Raw]) -> Raw | None:
    """Solve a system. One with more equations than unknowns that holds only for a value of
    another variable solves for that too, as TI does: `[2+l;r-l;-3+4·l]=[4;3;t]` in l and t
    gives `l=2 and r=5 and t=5` (emulator check 6, K6)."""
    system = [as_equation(e) for e in equations]
    try:
        solutions = sp.solve(system, variables, dict=True)
        if not solutions and len(system) > len(variables):
            others = set().union(*(e.free_symbols for e in system)) - set(variables)
            variables = sorted([*variables, *others], key=str)
            solutions = sp.solve(system, variables, dict=True)
    except NotImplementedError:
        return None
    if not solutions:
        return sp.false
    cases = [
        sp.And(
            *[
                sp.Eq(v, _numeric_root_objects(solution[v]), evaluate=False)
                for v in variables
                if v in solution
            ]
        )
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
    """A derivative in TI's simplified form: a polynomial expanded (`12·x²-300·x+1250`), and a
    sum of quotients over one denominator with common factors cancelled (`1/(x+1)`,
    `k/(t²+k)^(3/2)`, `-6·(x³-1)/(x³+a·x+2)²`; emulator check 6, K4, K5 and K7)."""
    derived = sp.diff(expression, variable, order)
    if derived.has(sp.Derivative, AppliedUndef, sp.Piecewise) or isinstance(derived, Boolean):
        return derived
    return _tidy_derivative(derived)


def _tidy_derivative(derived: Raw) -> Raw:
    symbols = derived.free_symbols
    if symbols and derived.is_polynomial(*symbols):
        # Multiplied out when that is no longer: the product rule's sum of products is, but
        # `6·x·(x²+1)²` stays.
        expanded = sp.expand(derived)
        return expanded if sp.count_ops(expanded) <= sp.count_ops(derived) else derived
    numerator, denominator = sp.fraction(sp.together(derived))
    if denominator == 1 or denominator.has(sp.exp) or not denominator.free_symbols:
        return derived
    if denominator.is_polynomial(*symbols) and numerator.is_polynomial(*symbols):
        quotient = sp.factor(numerator) / sp.factor(denominator)
        numerator, denominator = sp.fraction(quotient)
    numerator = sp.expand(numerator)
    # A negative leading coefficient comes out: `-6·(x³-1)`, not `6·(1-x³)`.
    sign = -1 if _leading_term(numerator).could_extract_minus_sign() else 1
    tidy = sign * sp.factor_terms(sign * numerator) / denominator
    return tidy if sp.count_ops(tidy) <= sp.count_ops(derived) else derived


def _leading_term(raw: Raw) -> Raw:
    """The term of highest total degree (of a polynomial), else the first term."""
    terms = sp.Add.make_args(raw)
    if raw.free_symbols and raw.is_polynomial(*raw.free_symbols):
        return max(terms, key=lambda term: sp.Poly(term, *raw.free_symbols).total_degree())
    return terms[0]


def tidy_substitution(raw: Raw) -> Raw:
    """A result with values put in, multiplied out when that is shorter: `v(x)|x=...` gives
    `h³·√3/9`, not a product of brackets (emulator check 6, K4). `(x+1)^2` stays as it is."""
    if isinstance(raw, Boolean) or not raw.free_symbols or raw.has(AppliedUndef):
        return raw
    expanded = sp.expand(raw)
    return expanded if sp.count_ops(expanded) < sp.count_ops(raw) else raw


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


def _generic_case(result: Raw, variable: Raw) -> Raw:
    """TI integrates with the parameters taken as generic: `∫sin(a·x)dx` is `-cos(a·x)/a`, where
    SymPy adds the special case a=0. A piecewise part whose conditions are only on parameters
    becomes its first piece; one that depends on the variable (from the integrand) stays."""

    def parametric(node: Raw) -> bool:
        return isinstance(node, sp.Piecewise) and all(
            condition is sp.true or variable not in condition.free_symbols
            for _, condition in node.args
        )

    return result.replace(parametric, lambda node: node.args[0][0])


# Functions an exact definite integral may show; anything else (Si, erf, ...) gives a decimal.
_ELEMENTARY = (
    sp.exp,
    sp.log,
    sp.sin,
    sp.cos,
    sp.tan,
    sp.asin,
    sp.acos,
    sp.atan,
    sp.sinh,
    sp.cosh,
    sp.tanh,
    sp.asinh,
    sp.Abs,
)
# An exact value with more operations than this is shown as a decimal (emulator check 6, K7:
# TI gives `∫₀² π·f1(x)²dx` as 2.2880103, not a sum of logarithms and inverse tangents).
_LONGEST_EXACT_INTEGRAL = 20


def _wants_decimal(result: Raw, expression: Raw, variable: Raw, bounds: tuple[Raw, Raw]) -> bool:
    """Whether a definite integral between numbers is better given as a decimal."""
    if expression.free_symbols - {variable} or not all(bound.is_number for bound in bounds):
        return False
    if result.has(sp.Integral):
        return True
    functions = {type(node) for node in result.atoms(sp.Function)}
    if any(not issubclass(kind, _ELEMENTARY) for kind in functions):
        return True
    return sp.count_ops(result) > _LONGEST_EXACT_INTEGRAL


def integrate(expression: Raw, variable: Raw, lower: Raw | None, upper: Raw | None) -> Raw | None:
    """An antiderivative (no constant) or a definite integral; None if SymPy cannot do it.

    A definite integral between numbers with no usable closed form is a decimal, as TI gives
    `∫₀^π 5·√(5-4·cos(3·t/2))dt` as 36.607844 and `∫₁² sin(x)/x dx` as 0.65932991.
    """
    if lower is None or upper is None:
        result = sp.integrate(expression, variable)
    else:
        result = sp.integrate(expression, (variable, lower, upper))
        if result.has(sp.Integral) and expression.has(sp.Abs):
            result = _without_abs(expression, variable, lower, upper) or result
        if _wants_decimal(result, expression, variable, (lower, upper)):
            return numerical_integral(expression, variable, lower, upper)
    if result.has(sp.Integral):
        return None
    if not expression.has(sp.Piecewise, sp.Abs, sp.sign, sp.Heaviside, sp.floor, sp.ceiling):
        result = _generic_case(result, variable)
    result = _inverse_hyperbolics_as_logs(result)
    return result if lower is not None else _logs_of_absolute_values(result)


def series_total(
    expression: Raw, variable: Raw, lower: Raw, upper: Raw, *, product: bool
) -> Raw | None:
    """`sumSeq` or `prodSeq`; None if SymPy has no closed form."""
    bounds = (variable, lower, upper)
    result = sp.product(expression, bounds) if product else sp.summation(expression, bounds)
    return None if result.has(sp.Sum, sp.Product) else result


def limit(expression: Raw, variable: Raw, point: Raw, direction: int | None) -> Raw | None:
    """A limit; `direction` is 1 from the right, -1 from the left and None for both sides."""
    side = "+-" if direction is None else "+" if direction > 0 else "-"
    try:
        result = sp.limit(expression, variable, point, side)
    except ValueError:  # the one-sided limits differ, as for sign(x) at 0: TI gives undef
        return sp.nan
    if result.has(sp.AccumBounds):  # it oscillates, as sin(x) at ∞ does: TI gives undef
        return sp.nan
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


# The search for real roots when there is no exact answer: samples over [-_SEARCH_SPAN, ...].
_SEARCH_SPAN = 100.0
_SEARCH_SAMPLES = 20000
_BISECTIONS = 100
# A refined point is a root if the expression is this small there (relative to its size).
_ROOT_RESIDUAL = 1e-9


def _bisected(function: Callable[[float], float], low: float, high: float) -> float:
    below = function(low) < 0
    for _ in range(_BISECTIONS):
        middle = (low + high) / 2
        if (function(middle) < 0) == below:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def numeric_solutions(equation: Raw, variable: Raw) -> Raw | None:
    """Real roots found by a bounded numeric search, for an equation in one unknown that has no
    exact answer: `x=-0.750403` for `ⅇ^(-2x)-2ⅇ^(-x)+1=x+2`. None if there is none to find."""
    if not isinstance(equation, sp.Eq):
        return None
    difference = equation.lhs - equation.rhs
    if difference.free_symbols != {variable} or difference.atoms(AppliedUndef):
        return None
    function = sp.lambdify(variable, difference, "math")

    def sample(point: float) -> float | None:
        try:
            value = float(function(point))
        except ValueError, ZeroDivisionError, OverflowError, TypeError:
            return None
        return value if math.isfinite(value) else None

    step = 2 * _SEARCH_SPAN / _SEARCH_SAMPLES
    points = [-_SEARCH_SPAN + k * step for k in range(_SEARCH_SAMPLES + 1)]
    roots: list[float] = []
    for left, right in pairwise(points):
        low, high = sample(left), sample(right)
        if low is None or high is None or (low < 0) == (high < 0):
            continue
        root = _bisected(lambda p: sample(p) or 0.0, left, right)
        residual = sample(root)
        scale = max(abs(low), abs(high), 1.0)
        if residual is not None and abs(residual) <= _ROOT_RESIDUAL * scale:
            roots.append(root)
    if not roots:
        return None
    clauses = [sp.Eq(variable, sp.Float(root, 15), evaluate=False) for root in roots]
    return sp.Or(*clauses)


_GUESSES = (1, 0, -1, 2, -2, 10, -10)


def numerical_root(equation: Raw, variable: Raw, guess: Raw | None) -> Raw | None:
    expression = equation.lhs - equation.rhs if isinstance(equation, sp.Eq) else equation
    for start in (guess,) if guess is not None else _GUESSES:
        try:
            return sp.nsolve(expression, variable, start)
        except ValueError, ZeroDivisionError, NotImplementedError:
            continue
    return None


_TRIG = (sp.sin, sp.cos, sp.tan, sp.sec, sp.csc, sp.cot)
# Samples per period for the numeric search of a periodic function's extremum.
_PERIOD_SAMPLES = 2000
# Extrema whose values agree this closely are the same extremum, repeated.
_SAME_EXTREMUM = 1e-9


def _period(expression: Raw, variable: Raw) -> Raw | None:
    """The period of a trigonometric expression in `variable`, or None if it is not periodic."""
    if not expression.has(*_TRIG):
        return None
    try:
        # Decimals as fractions, so that `cos(0.5·x)` has a period too.
        period = sp.periodicity(sp.nsimplify(expression, rational=True), variable)
    except NotImplementedError, ValueError, TypeError:
        return None
    return period if period is not None and period.is_positive else None


def _refined(slope: Callable[[float], float], low: float, high: float) -> float:
    """A zero of `slope` between two points where it changes sign, by bisection."""
    for _ in range(80):
        middle = (low + high) / 2
        if (slope(low) <= 0) == (slope(middle) <= 0):
            low = middle
        else:
            high = middle
    return (low + high) / 2


def _periodic_extremum(expression: Raw, variable: Raw, period: Raw, *, maximum: bool) -> Raw | None:
    """The extremum of a periodic function by a bounded numeric search over one period each
    side of 0: the best value, at the point nearest 0 where it is reached (TI gives
    `fMin(sin(x/2)+cos(2·x),x)` as `x=-1.65576`). It always returns, unlike solving f'=0."""
    sign = -1.0 if maximum else 1.0
    value = sp.lambdify(variable, sign * expression, "math")
    slope = sp.lambdify(variable, sign * sp.diff(expression, variable), "math")
    span = float(period)
    count = 2 * _PERIOD_SAMPLES
    points = [-span + 2 * span * k / count for k in range(count + 1)]
    found: list[tuple[float, float]] = []
    for left, right in pairwise(points):
        try:
            if slope(left) < 0 <= slope(right):
                where = _refined(slope, left, right)
                found.append((value(where), where))
        except ValueError, ZeroDivisionError, OverflowError:
            continue
    if not found:
        return None
    best = min(height for height, _ in found)
    nearest = min((where for height, where in found if height - best <= _SAME_EXTREMUM), key=abs)
    return sp.Eq(variable, sp.Float(nearest, 15), evaluate=False)


def _domain_ends(
    expression: Raw, variable: Raw, domain: Raw
) -> tuple[list[Raw], list[float]] | None:
    """The closed ends of the domain, and what the expression approaches at its unbounded ends;
    None if the domain is not intervals or the expression oscillates at an end."""
    closed: list[Raw] = []
    reaches: list[float] = []
    for piece in domain.args if isinstance(domain, sp.Union) else (domain,):
        if not isinstance(piece, sp.Interval):
            return None
        for end, is_open in ((piece.start, piece.left_open), (piece.end, piece.right_open)):
            if end.is_finite and not is_open:
                closed.append(end)
            elif not end.is_finite:
                reach = sp.limit(expression, variable, end)
                if reach.has(sp.AccumBounds):  # it oscillates, so there may be no extremum
                    return None
                reaches.append(float(reach.evalf()))
    return closed, reaches


def extremum(
    expression: Raw, variable: Raw, constraints: Iterable[Raw], *, maximum: bool
) -> Raw | None:
    """The `x=a` where `expression` is greatest (or least) in the domain, or None if none is."""
    domain: Raw = sp.S.Reals
    for constraint in constraints:
        if constraint.free_symbols <= {variable}:
            domain = domain.intersect(_constraint_set(constraint, variable))
    if domain == sp.S.Reals and expression.free_symbols == {variable}:
        period = _period(expression, variable)
        if period is not None:
            return _periodic_extremum(expression, variable, period, maximum=maximum)
    critical = sp.solveset(sp.diff(expression, variable), variable, domain)
    if critical != sp.S.EmptySet and not isinstance(critical, sp.FiniteSet):
        return None
    ends = _domain_ends(expression, variable, domain)
    if ends is None:
        return None
    closed, reaches = ends
    candidates = [*critical, *closed]
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


def remainder(left: Raw, right: Raw) -> Raw:
    """`remain(a,b)`: the remainder of a/b, with the sign of `a`."""
    return left - right * integer_part(left / right)


def is_prime(raw: Raw) -> bool | None:
    """Whether a whole number is prime; None if `raw` is not a whole number."""
    return bool(sp.isprime(raw)) if raw.is_Integer else None
