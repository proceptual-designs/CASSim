"""Read and evaluate an entry: a tokenizer and a Pratt parser over the editor's items
(SDD-14 section 6.1). Nothing is passed to Python's `eval`.

Priority, highest first: brackets and functions; postfix keys (x², x⁻¹, x!, %, °, ʳ, ᵍ, x̂, ŷ)
and powers; the negative sign; nPr and nCr; multiplication with the × left out (so 1÷2π is
1÷(2π)); × and ÷; + and −; then the relations of VERIFY mode. Templates (fractions, roots, |x|,
log■□) are single operands. A missing `)` at the end of the entry is allowed.
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Literal

from cassim.devices.scientific import values as v
from cassim.devices.scientific.editor import Item, Tmpl, Tok
from cassim.devices.scientific.values import CalcError, Exact, Number, syntax_error

AngleUnit = Literal["DEG", "RAD", "GRA"]

MAX_FACTORIAL = 69
MAX_INTEGER = 10**10

BP_REL = 5
BP_ADD = 10
BP_MUL = 20
BP_IMPLIED = 25
BP_PERM = 30
BP_NEG = 40
BP_POSTFIX = 60


@dataclass(frozen=True)
class Percent:
    """`a%`: a hundredth of a, which + and − read as a change by that share (200+10% is 220)."""

    share: Number


@dataclass(frozen=True)
class Pair:
    """The two answers of Pol( and Rec(."""

    first_name: str
    first: Number
    second_name: str
    second: Number


type Value = Number | Percent | Pair | bool


@dataclass
class Context:
    """What an entry is evaluated against."""

    angle: AngleUnit = "DEG"
    variables: Mapping[str, Number] = field(default_factory=dict)
    stat: Callable[[str], Number] | None = None  # STAT-mode variables, None outside STAT
    estimate: Callable[[str, Number], Number] | None = None  # x̂, ŷ, x̂₁, x̂₂
    rnd: Callable[[Number], Number] = lambda value: value  # Rnd( at the display setting
    rng: random.Random = field(default_factory=random.Random)
    relations: bool = False  # VERIFY mode
    # + and − read a following a% as a change by that share (the EL-531); off, % is just ÷100
    # (the fx-82 and SX-II: 250+15% is 250.15, decision 0041)
    percent_addon: bool = True


# ---- lexing ---------------------------------------------------------------------------------


@dataclass(frozen=True)
class Num:
    value: Fraction


type Lexeme = Num | Tok | Tmpl


def lex(items: list[Item]) -> list[Lexeme]:
    """Join digits and the decimal point into numbers; keep every other item as it is."""
    out: list[Lexeme] = []
    digits = ""
    for item in items:
        if isinstance(item, Tok) and item.token.kind in ("digit", "dot"):
            digits += item.token.text
            continue
        if digits:
            out.append(_number(digits))
            digits = ""
        out.append(item)
    if digits:
        out.append(_number(digits))
    return out


def _number(text: str) -> Num:
    if text.count(".") > 1 or text == ".":
        raise syntax_error()
    return Num(Fraction(text if not text.endswith(".") else text + "0"))


# ---- angles -------------------------------------------------------------------------------------


def degrees_exact(value: Number, unit: AngleUnit) -> Fraction | None:
    """The angle in degrees as a fraction, when it is exactly one (30, or π/6 in radians)."""
    if isinstance(value, Exact):
        if not value.terms:
            return Fraction(0)
        q = value.rational
        if q is not None and unit == "DEG":
            return q
        if q is not None and unit == "GRA":
            return q * Fraction(9, 10)
        if unit == "RAD" and len(value.terms) == 1 and value.terms[0][:2] == (1, 1):
            return value.terms[0][2] * 180
    return None


def to_radians(x: float, unit: AngleUnit) -> float:
    if unit == "DEG":
        return math.radians(x)
    if unit == "GRA":
        return x * math.pi / 200
    return x


def from_degrees(degrees: Fraction, unit: AngleUnit) -> Number:
    if unit == "DEG":
        return v.rational(degrees)
    if unit == "GRA":
        return v.rational(degrees * Fraction(10, 9))
    return v.mul(v.rational(degrees / 180), v.PI)


def from_radians(x: float, unit: AngleUnit) -> float:
    if unit == "DEG":
        return math.degrees(x)
    if unit == "GRA":
        return x * 200 / math.pi
    return x


def convert_angle(value: Number, source: AngleUnit, target: AngleUnit) -> Number:
    """An angle typed in `source` units (30°, 1ʳ, 50ᵍ) as a value in the current unit."""
    if source == target:
        return value
    exact = degrees_exact(value, source)
    if exact is not None:
        return from_degrees(exact, target)
    return v.check(from_radians(to_radians(float(value), source), target))


# ---- the parser -----------------------------------------------------------------------------

ATOM_KINDS = ("const", "var", "statvar", "func", "lparen", "neg")
ATOM_TEMPLATES = ("frac", "mixed", "sqrt", "root", "abs", "logab")


class Parser:
    def __init__(self, items: list[Item], context: Context) -> None:
        self.lexemes = lex(items)
        self.i = 0
        self.ctx = context

    # -- helpers --

    def peek(self) -> Lexeme | None:
        return self.lexemes[self.i] if self.i < len(self.lexemes) else None

    def take(self) -> Lexeme:
        lexeme = self.peek()
        if lexeme is None:
            raise syntax_error()
        self.i += 1
        return lexeme

    @staticmethod
    def kind(lexeme: Lexeme | None) -> str:
        if lexeme is None:
            return "end"
        if isinstance(lexeme, Num):
            return "num"
        if isinstance(lexeme, Tmpl):
            return f"tmpl:{lexeme.kind}"
        return lexeme.token.kind

    def starts_operand(self, lexeme: Lexeme | None) -> bool:
        kind = self.kind(lexeme)
        if kind == "num" or kind in ATOM_KINDS:
            return True
        return kind.startswith("tmpl:") and kind[5:] in (*ATOM_TEMPLATES, "exp10")

    # -- entry points --

    def entry(self) -> Value:
        if not self.lexemes:
            raise syntax_error()
        value = self.expression(0)
        if self.peek() is not None:
            raise syntax_error()
        return value

    def slot(self, items: list[Item]) -> Number:
        """Evaluate a template slot as a separate expression."""
        inner = Parser(items, self.ctx)
        return number(inner.entry())

    # -- Pratt loop --

    def expression(self, bp: int) -> Value:
        left = self.nud()
        while True:
            lexeme = self.peek()
            kind = self.kind(lexeme)
            if kind in ("end", "rparen", "comma"):
                return left
            if kind in ("postfix", "estimator") or kind in ("tmpl:pow", "tmpl:exp10"):
                if bp >= BP_POSTFIX:
                    return left
                left = self.postfix(left)
                continue
            if kind == "op":
                assert isinstance(lexeme, Tok)
                op_bp = {"+": BP_ADD, "−": BP_ADD, "×": BP_MUL, "÷": BP_MUL}.get(lexeme.id, BP_PERM)
                if op_bp <= bp:
                    return left
                self.take()
                right = self.expression(op_bp)
                left = binary(lexeme.id, left, right)
                continue
            if kind == "rel":
                if not self.ctx.relations:
                    raise syntax_error()
                if bp >= BP_REL:
                    return left
                assert isinstance(lexeme, Tok)
                self.take()
                right = self.expression(BP_REL)
                left = relation(lexeme.id, number(left), number(right))
                if self.kind(self.peek()) == "rel":
                    raise syntax_error()
                continue
            if self.starts_operand(lexeme):
                if bp >= BP_IMPLIED:
                    return left
                right = self.expression(BP_IMPLIED)
                left = v.mul(number(left), number(right))
                continue
            raise syntax_error()

    def nud(self) -> Value:  # noqa: PLR0911
        lexeme = self.take()
        if isinstance(lexeme, Num):
            return v.rational(lexeme.value)
        if isinstance(lexeme, Tmpl):
            if lexeme.kind == "exp10":  # ×10³ on its own is 10³
                return self.exp10(v.rational(1), lexeme)
            return self.template(lexeme)
        token = lexeme.token
        match token.kind:
            case "neg":
                return v.neg(number(self.expression(BP_NEG)))
            case "lparen":
                value = self.expression(0)
                self.close()
                return value
            case "const":
                return self.constant(lexeme.id)
            case "var":
                return self.ctx.variables.get(lexeme.id, v.ZERO)
            case "statvar":
                if self.ctx.stat is None:
                    raise syntax_error()
                return self.ctx.stat(lexeme.id)
            case "func":
                return self.function(lexeme.id[:-1])
        raise syntax_error()

    def close(self) -> None:
        kind = self.kind(self.peek())
        if kind == "rparen":
            self.take()
        elif kind != "end":
            raise syntax_error()

    def constant(self, name: str) -> Number:
        if name == "π":
            return v.PI
        if name == "e":
            return math.e
        if name == "ten":
            return v.rational(10)
        return self.ctx.rng.randrange(1000) / 1000  # Ran#: a decimal with three places

    def arguments(self) -> list[Number]:
        args = [number(self.expression(0))]
        while self.kind(self.peek()) == "comma":
            self.take()
            args.append(number(self.expression(0)))
        self.close()
        return args

    def function(self, name: str) -> Value:
        if name in ("Pol", "Rec"):
            x, y = self.exactly(2)
            return polar(x, y, self.ctx.angle) if name == "Pol" else rectangular(x, y, self.ctx)
        if name in ("GCD", "LCM", "RanInt#"):
            a, b = (whole(value) for value in self.exactly(2))
            if name == "GCD":
                return v.rational(math.gcd(a, b))
            if name == "LCM":
                return v.rational(abs(a * b) // math.gcd(a, b) if a and b else 0)
            if a >= b:
                raise v.math_error()
            return v.rational(self.ctx.rng.randint(a, b))
        (x,) = self.exactly(1)
        if name == "Rnd":
            return self.ctx.rnd(x)
        return apply(name, x, self.ctx.angle)

    def exactly(self, n: int) -> list[Number]:
        args = self.arguments()
        if len(args) != n:
            raise syntax_error()
        return args

    def template(self, tmpl: Tmpl) -> Number:
        slots = tmpl.slots
        match tmpl.kind:
            case "frac":
                return v.div(self.slot(slots[0]), self.slot(slots[1]))
            case "mixed":
                whole_part = self.slot(slots[0])
                part = v.div(self.slot(slots[1]), self.slot(slots[2]))
                return v.sub(whole_part, part) if float(whole_part) < 0 else v.add(whole_part, part)
            case "sqrt":
                return v.sqrt(self.slot(slots[0]))
            case "root":
                index = whole(self.slot(slots[0]))
                if index < 1:
                    raise v.math_error()
                return v.root(index, self.slot(slots[1]))
            case "abs":
                value = self.slot(slots[0])
                return v.neg(value) if float(value) < 0 else value
            case "logab":
                return log_base(self.slot(slots[0]), self.slot(slots[1]))
        raise syntax_error()

    def exp10(self, left: Number, tmpl: Tmpl) -> Number:
        exponent = self.slot(tmpl.slots[0])
        return v.mul(left, v.power(v.rational(10), exponent))

    def postfix(self, left: Value) -> Value:  # noqa: PLR0911, PLR0912
        lexeme = self.take()
        if isinstance(lexeme, Tmpl):
            if lexeme.kind == "exp10":
                return self.exp10(number(left), lexeme)
            return v.power(number(left), self.slot(lexeme.slots[0]))
        assert isinstance(lexeme, Tok)
        name = lexeme.id
        if lexeme.token.kind == "estimator":
            if self.ctx.estimate is None:
                raise syntax_error()
            return self.ctx.estimate(name, number(left))
        x = number(left)
        match name:
            case "²":
                return v.mul(x, x)
            case "³":
                return v.mul(v.mul(x, x), x)
            case "⁻¹":
                return v.inverse(x)
            case "!":
                n = whole(x)
                if not 0 <= n <= MAX_FACTORIAL:
                    raise v.math_error()
                return v.rational(math.factorial(n))
            case "%":
                share = v.div(x, v.rational(100))
                return Percent(share) if self.ctx.percent_addon else share
            case "dms":
                return self.dms(x)
            case "deg":
                return convert_angle(x, "DEG", self.ctx.angle)
            case "rad":
                return convert_angle(x, "RAD", self.ctx.angle)
            case "gra":
                return convert_angle(x, "GRA", self.ctx.angle)
        raise syntax_error()

    def dms(self, degrees: Number) -> Number:
        """12°34°56° is 12 degrees, 34 minutes and 56 seconds."""
        total = degrees
        for scale in (60, 3600):
            following = self.lexemes[self.i : self.i + 2]
            if (
                len(following) == 2  # noqa: PLR2004
                and isinstance(following[0], Num)
                and isinstance(following[1], Tok)
                and following[1].id == "dms"
            ):
                self.i += 2
                part = v.div(v.rational(following[0].value), v.rational(scale))
                total = v.sub(total, part) if float(total) < 0 else v.add(total, part)
            else:
                break
        return total


# ---- operations -----------------------------------------------------------------------------


def number(value: Value) -> Number:
    """A plain number; a share (a%) is its value; a pair or a truth value cannot be used."""
    if isinstance(value, Percent):
        return value.share
    if isinstance(value, (Pair, bool)):
        raise syntax_error()
    return value


def whole(value: Number) -> int:
    n = v.as_integer(value)
    if n is None or abs(n) >= MAX_INTEGER:
        raise v.math_error()
    return n


def binary(op: str, left: Value, right: Value) -> Number:  # noqa: PLR0911
    a = number(left)
    if isinstance(right, Percent):
        share = right.share
        if op == "+":
            return v.add(a, v.mul(a, share))
        if op == "−":
            return v.sub(a, v.mul(a, share))
    b = number(right)
    match op:
        case "+":
            return v.add(a, b)
        case "−":
            return v.sub(a, b)
        case "×":
            return v.mul(a, b)
        case "÷":
            return v.div(a, b)
    n, r = whole(a), whole(b)
    if n < 0 or r < 0 or r > n:
        raise v.math_error()
    return v.rational(math.perm(n, r) if op == "nPr" else math.comb(n, r))


def relation(op: str, a: Number, b: Number) -> bool:
    qa, qb = v.as_rational(a), v.as_rational(b)
    if qa is not None and qb is not None:
        diff = float(qa - qb)
    else:
        x, y = float(a), float(b)
        diff = 0.0 if math.isclose(x, y, rel_tol=1e-10, abs_tol=1e-12) else x - y
    return {
        "=": diff == 0,
        "≠": diff != 0,
        ">": diff > 0,
        "≥": diff >= 0,
        "<": diff < 0,
        "≤": diff <= 0,
    }[op]


def apply(name: str, x: Number, unit: AngleUnit) -> Number:  # noqa: PLR0911, PLR0912
    """A one-argument function key."""
    if name in ("sin", "cos", "tan"):
        degrees = degrees_exact(x, unit)
        if degrees is not None:
            exact = v.exact_trig(name, degrees)
            if exact is not None:
                return exact
        radians = to_radians(float(x), unit)
        if name == "tan" and abs(math.cos(radians)) < 1e-15:  # noqa: PLR2004
            raise v.math_error()
        return v.check({"sin": math.sin, "cos": math.cos, "tan": math.tan}[name](radians))
    if name in ("sin⁻¹", "cos⁻¹", "tan⁻¹"):
        key = {"sin⁻¹": "asin", "cos⁻¹": "acos", "tan⁻¹": "atan"}[name]
        f = float(x)
        if key != "atan" and abs(f) > 1:
            raise v.math_error()
        exact_degrees = v.exact_inverse_trig(key, x)
        if exact_degrees is not None:
            return from_degrees(Fraction(exact_degrees), unit)
        radians = {"asin": math.asin, "acos": math.acos, "atan": math.atan}[key](f)
        return v.check(from_radians(radians, unit))
    f = float(x)
    match name:
        case "sinh":
            return v.check(math.sinh(f)) if abs(f) < 230 else _overflow()  # noqa: PLR2004
        case "cosh":
            return v.check(math.cosh(f)) if abs(f) < 230 else _overflow()  # noqa: PLR2004
        case "tanh":
            return v.check(math.tanh(f))
        case "sinh⁻¹":
            return v.check(math.asinh(f))
        case "cosh⁻¹":
            if f < 1:
                raise v.math_error()
            return v.check(math.acosh(f))
        case "tanh⁻¹":
            if abs(f) >= 1:
                raise v.math_error()
            return v.check(math.atanh(f))
        case "log":
            return log_base(v.rational(10), x)
        case "ln":
            if f <= 0:
                raise v.math_error()
            return v.check(math.log(f)) if f != 1 else v.ZERO
    raise syntax_error()


def _overflow() -> Number:
    raise v.math_error()


def log_base(base: Number, x: Number) -> Number:
    b, f = float(base), float(x)
    if b <= 0 or b == 1 or f <= 0:
        raise v.math_error()
    qb, qx = v.as_rational(base), v.as_rational(x)
    estimate = math.log(f) / math.log(b)
    if qb is not None and qx is not None:
        k = round(estimate)
        if abs(estimate - k) < 1e-9 and abs(k) <= 400 and Fraction(qb) ** k == qx:  # noqa: PLR2004
            return v.rational(k)
    return v.check(estimate)


def polar(x: Number, y: Number, unit: AngleUnit) -> Pair:
    r = v.sqrt(v.add(v.mul(x, x), v.mul(y, y)))
    fx, fy = float(x), float(y)
    if fx == 0 and fy == 0:
        raise v.math_error()
    radians = math.atan2(fy, fx)
    degrees = math.degrees(radians)
    nearest = round(degrees / 15) * 15
    if abs(degrees - nearest) < 1e-9 and (nearest % 30 == 0 or nearest % 45 == 0):  # noqa: PLR2004
        theta = from_degrees(Fraction(nearest), unit)
    else:
        theta = v.check(from_radians(radians, unit))
    return Pair("r", r, "θ", theta)


def rectangular(r: Number, theta: Number, context: Context) -> Pair:
    x = v.mul(r, number(apply("cos", theta, context.angle)))
    y = v.mul(r, number(apply("sin", theta, context.angle)))
    return Pair("X", x, "Y", y)


def evaluate(items: list[Item], context: Context) -> Value:
    """Evaluate an entry. Raises `CalcError` (Syntax ERROR, Math ERROR) as the device would."""
    try:
        return Parser(items, context).entry()
    except CalcError:
        raise
    except OverflowError, ZeroDivisionError, ValueError:
        raise v.math_error() from None
    except RecursionError:
        raise CalcError("Stack") from None
