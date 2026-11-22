"""AST node types and pretty-printer.

Nodes are immutable. `str(node)` prints TI linear text in a canonical spelling (`≤`, `→`, `▶`,
explicit `*`) with only the parentheses that precedence needs, so that parsing the printed text
gives back an equal tree. Names keep the spelling they were typed with: case folding and
resolving constants such as `pi` and `ⅈ` are the evaluator's job.
"""

from dataclasses import dataclass
from enum import IntEnum


class Prec(IntEnum):
    """Binding strength, tightest last. Follows the guide's EOS table, levels 18 to 1."""

    STORE = 10
    CONVERT = 20  # not in the EOS table; the guide allows ▶ only at the end of an entry line
    CONSTRAINT = 30
    IFF = 40
    IMPLIES = 50
    XOR = 60
    OR = 70
    AND = 80
    NOT = 90
    COMPARE = 100
    ANGLE = 105  # not in the EOS table; r∠θ always appears as a whole term
    ADD = 110
    MUL = 120
    CONCAT = 130
    NEGATE = 140
    POWER = 150
    POST = 160
    ATOM = 170


BINARY_PREC: dict[str, Prec] = {
    "|": Prec.CONSTRAINT,
    "⇔": Prec.IFF,
    "⇒": Prec.IMPLIES,
    "xor": Prec.XOR,
    "nor": Prec.XOR,
    "nand": Prec.XOR,
    "or": Prec.OR,
    "and": Prec.AND,
    "∠": Prec.ANGLE,
    "+": Prec.ADD,
    "-": Prec.ADD,
    ".+": Prec.ADD,
    ".-": Prec.ADD,
    "*": Prec.MUL,
    "/": Prec.MUL,
    ".*": Prec.MUL,
    "./": Prec.MUL,
    "&": Prec.CONCAT,
    "^": Prec.POWER,
    ".^": Prec.POWER,
}
RIGHT_ASSOCIATIVE = frozenset({"^", ".^"})
COMPARE_OPS = frozenset({"=", "≠", "<", "≤", ">", "≥"})
POSTFIX_OPS = frozenset({"!", "%", "°", "'", "ʳ", "ᵍ", "ᵀ"})
# The operand of each prefix operator is parsed at this strength.
UNARY_OPERAND_PREC: dict[str, int] = {
    "-": Prec.NEGATE,
    "not": Prec.NOT,
    "∠": Prec.ANGLE + 1,
}
_UNARY_PREC: dict[str, Prec] = {
    "-": Prec.NEGATE,
    "not": Prec.NOT,
    "∠": Prec.ANGLE,
    "#": Prec.ATOM,
}
_WORD_OPS = frozenset({"and", "or", "xor", "nor", "nand"})


class Node:
    """Base class: everything binds as tightly as an atom unless it says otherwise."""

    __slots__ = ()

    @property
    def prec(self) -> int:
        return Prec.ATOM


@dataclass(frozen=True, slots=True)
class Number(Node):
    """A numeric literal, as typed: `1.` is approximate and `1` exact, so the text matters."""

    text: str

    def __str__(self) -> str:
        return self.text


@dataclass(frozen=True, slots=True)
class Dms(Node):
    """A degrees-minutes-seconds literal such as `60°15'45"`."""

    text: str

    def __str__(self) -> str:
        return self.text


@dataclass(frozen=True, slots=True)
class String(Node):
    value: str

    def __str__(self) -> str:
        return f'"{self.value}"'


@dataclass(frozen=True, slots=True)
class Name(Node):
    """Any identifier: a variable, `pi`, `@n1`, `stat.results`, `lib\\fn` or the unit `_m`."""

    text: str

    def __str__(self) -> str:
        return self.text


@dataclass(frozen=True, slots=True)
class Call(Node):
    """`f(a,b)`. A name followed by parentheses is always a call, never a product."""

    func: str
    args: tuple[Expr, ...]

    def __str__(self) -> str:
        return f"{self.func}({_join(self.args)})"


@dataclass(frozen=True, slots=True)
class Index(Node):
    """Subscripting, `l[1]` or `m[1,2]`."""

    base: Expr
    subscripts: tuple[Expr, ...]

    def __str__(self) -> str:
        # `2[1]` would read as the product 2*[1].
        base = f"({self.base})" if isinstance(self.base, Number) else _wrap(self.base, Prec.POST)
        return f"{base}[{_join(self.subscripts)}]"


@dataclass(frozen=True, slots=True)
class ListLit(Node):
    items: tuple[Expr, ...]

    def __str__(self) -> str:
        return f"{{{_join(self.items)}}}"


@dataclass(frozen=True, slots=True)
class Matrix(Node):
    """`[1,2;3,4]`. Rows need not be equal in length here; the evaluator rejects that."""

    rows: tuple[tuple[Expr, ...], ...]

    def __str__(self) -> str:
        return "[" + ";".join(_join(row) for row in self.rows) + "]"


@dataclass(frozen=True, slots=True)
class Unary(Node):
    """A prefix operator: `-`, `not`, `∠` or the indirection `#`."""

    op: str
    operand: Expr

    @property
    def prec(self) -> int:
        return _UNARY_PREC[self.op]

    def __str__(self) -> str:
        if self.op == "#":
            return f"#{_wrap(self.operand, Prec.ATOM)}"
        operand = _wrap(self.operand, UNARY_OPERAND_PREC[self.op])
        return f"not {operand}" if self.op == "not" else f"{self.op}{operand}"


@dataclass(frozen=True, slots=True)
class Postfix(Node):
    """A post operator: `!`, `%`, `°`, `'`, `ʳ`, `ᵍ` or the transpose `ᵀ`."""

    op: str
    operand: Expr

    @property
    def prec(self) -> int:
        return Prec.POST

    def __str__(self) -> str:
        return f"{_wrap(self.operand, Prec.POST)}{self.op}"


@dataclass(frozen=True, slots=True)
class Binary(Node):
    """A binary operator, including the constraint `|` and the polar `∠`."""

    op: str
    left: Expr
    right: Expr

    @property
    def prec(self) -> int:
        return BINARY_PREC[self.op]

    def __str__(self) -> str:
        prec = self.prec
        right_assoc = self.op in RIGHT_ASSOCIATIVE
        left = _wrap(self.left, prec + 1 if right_assoc else prec)
        negated = right_assoc and isinstance(self.right, Unary) and self.right.op == "-"
        right = str(self.right) if negated else _wrap(self.right, prec if right_assoc else prec + 1)
        if negated and self.left == Name("ⅇ"):
            right = f"({right})"  # TI writes ⅇ^(-a) (emulator check 6, K4 and K7)
        if self.op in _WORD_OPS or self.op == "|":
            return f"{left} {self.op} {right}"
        # `1.+x` would read as the number `1.` plus x.
        gap = " " if self.op[0] == "." and left[-1].isdigit() else ""
        return f"{left}{gap}{self.op}{right}"


@dataclass(frozen=True, slots=True)
class Compare(Node):
    """A relation, possibly chained, so `0≤x≤2*π` keeps its shape."""

    first: Expr
    rest: tuple[tuple[str, Expr], ...]

    @property
    def prec(self) -> int:
        return Prec.COMPARE

    def __str__(self) -> str:
        parts = [_wrap(self.first, Prec.COMPARE + 1)]
        parts += [f"{op}{_wrap(term, Prec.COMPARE + 1)}" for op, term in self.rest]
        return "".join(parts)


@dataclass(frozen=True, slots=True)
class Convert(Node):
    """A conversion such as `x▶Polar` or `0.3▶approxFraction(0.001)`."""

    value: Expr
    target: Name | Call

    @property
    def prec(self) -> int:
        return Prec.CONVERT

    def __str__(self) -> str:
        return f"{_wrap(self.value, Prec.CONVERT)}▶{self.target}"


type Expr = (
    Number
    | Dms
    | String
    | Name
    | Call
    | Index
    | ListLit
    | Matrix
    | Unary
    | Postfix
    | Binary
    | Compare
    | Convert
)


@dataclass(frozen=True, slots=True)
class Assign(Node):
    """`target:=value`."""

    target: Expr
    value: Expr

    def __str__(self) -> str:
        return f"{self.target}:={self.value}"


@dataclass(frozen=True, slots=True)
class Store(Node):
    """`value→target`."""

    value: Expr
    target: Expr

    def __str__(self) -> str:
        return f"{self.value}→{self.target}"


@dataclass(frozen=True, slots=True)
class Define(Node):
    """`Define f(x)=body`, optionally `LibPub` or `LibPriv`."""

    target: Expr
    body: Expr
    visibility: str | None = None

    def __str__(self) -> str:
        keyword = f"Define {self.visibility}" if self.visibility else "Define"
        return f"{keyword} {self.target}={self.body}"


@dataclass(frozen=True, slots=True)
class Command(Node):
    """A statement written without parentheses, `SortA l` or `LinRegMx x,y,1`."""

    name: str
    args: tuple[Expr, ...]

    def __str__(self) -> str:
        return f"{self.name} {_join(self.args)}" if self.args else self.name


type Stmt = Expr | Assign | Store | Define | Command


@dataclass(frozen=True, slots=True)
class Line(Node):
    """One entry line: statements separated by `:`."""

    statements: tuple[Stmt, ...]

    def __str__(self) -> str:
        return ":".join(str(s) for s in self.statements)


def _wrap(node: Expr, minimum: int) -> str:
    return f"({node})" if node.prec < minimum else str(node)


def _join(items: tuple[Expr, ...]) -> str:
    return ",".join(str(item) for item in items)
