"""The pseudocode program tree. Pure data: the parser builds it and the interpreter walks it."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Num:
    """A numeric literal. `text` is kept so Exact mode can read a decimal as a fraction."""

    text: str
    line: int = 0


@dataclass(frozen=True, slots=True)
class Str:
    value: str
    line: int = 0


@dataclass(frozen=True, slots=True)
class Name:
    name: str
    line: int = 0


@dataclass(frozen=True, slots=True)
class Unary:
    op: str  # "-", "not", "abs", "sqrt"
    operand: Expr
    line: int = 0


@dataclass(frozen=True, slots=True)
class Binary:
    op: str  # + - * / ÷ div mod ^ and or  ("*" also stands for implicit multiplication)
    left: Expr
    right: Expr
    line: int = 0
    implicit: bool = False


@dataclass(frozen=True, slots=True)
class Compare:
    """A (possibly chained) comparison: `a < b ≤ c`."""

    first: Expr
    ops: tuple[str, ...]  # = ≠ < > ≤ ≥
    rest: tuple[Expr, ...]
    line: int = 0


@dataclass(frozen=True, slots=True)
class Paren:
    inner: Expr
    line: int = 0


@dataclass(frozen=True, slots=True)
class Call:
    """`f(a, b)`. Whether this is a call or a product `x(a+b)` is decided when it runs."""

    name: str
    args: tuple[Expr, ...]
    line: int = 0


@dataclass(frozen=True, slots=True)
class Index:
    target: Expr
    index: Expr
    line: int = 0


@dataclass(frozen=True, slots=True)
class ListLit:
    items: tuple[Expr, ...]
    line: int = 0


type Expr = Num | Str | Name | Unary | Binary | Compare | Paren | Call | Index | ListLit


@dataclass(frozen=True, slots=True)
class Param:
    """A parameter. `sig` is the variable list of a function parameter written `f(x)`."""

    name: str
    sig: tuple[str, ...] | None = None
    default: Expr | None = None


@dataclass(slots=True)
class Assign:
    target: Name | Index
    value: Expr
    line: int


@dataclass(slots=True)
class FuncAssign:
    """`P(x) ← expression`: defines a local function (book `newton3`)."""

    name: str
    params: tuple[str, ...]
    body: Expr
    line: int


@dataclass(slots=True)
class Input:
    target: Name | Index
    line: int


@dataclass(slots=True)
class Print:
    items: list[Expr]
    line: int


@dataclass(slots=True)
class Append:
    value: Expr
    target: Expr
    line: int


@dataclass(slots=True)
class ExprStmt:
    expr: Expr
    line: int


@dataclass(slots=True)
class Return:
    value: Expr | None
    line: int


@dataclass(slots=True)
class Break:
    line: int


@dataclass(slots=True)
class If:
    branches: list[tuple[Expr, list[Stmt], int]]  # condition, body, line of the keyword
    orelse: list[Stmt] | None
    line: int
    else_line: int = 0


@dataclass(slots=True)
class While:
    cond: Expr
    body: list[Stmt]
    line: int


@dataclass(slots=True)
class For:
    var: str
    start: Expr
    stop: Expr
    step: Expr | None
    body: list[Stmt]
    line: int


@dataclass(slots=True)
class ForEach:
    var: str
    iterable: Expr
    body: list[Stmt]
    line: int


@dataclass(slots=True)
class RepeatTimes:
    count: Expr
    body: list[Stmt]
    line: int


@dataclass(slots=True)
class RepeatUntil:
    body: list[Stmt]
    cond: Expr
    line: int
    until_line: int = 0


@dataclass(slots=True)
class Define:
    name: str
    params: tuple[Param, ...]
    body: list[Stmt]
    line: int


type Stmt = (
    Assign
    | FuncAssign
    | Input
    | Print
    | Append
    | ExprStmt
    | Return
    | Break
    | If
    | While
    | For
    | ForEach
    | RepeatTimes
    | RepeatUntil
    | Define
)


@dataclass(frozen=True, slots=True)
class Diagnostic:
    line: int
    message: str
    severity: str = "warning"  # warning | error


@dataclass(slots=True)
class Program:
    body: list[Stmt]
    lines: list[str]
    warnings: list[Diagnostic] = field(default_factory=list)
    split_names: bool = False  # `ax` is a×x when undefined (syntax file: names.split_products)
