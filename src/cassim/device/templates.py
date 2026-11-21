"""The template kinds of the 2D editor, each declared once (decision 0035, stage 2).

A `Spec` says everything the model knows about a kind: how many slots it has, whether its slots form
a grid, how Left and Right walk it, the TI text the parser reads for it, its LaTeX, and the call it
is read back from (the bridge in `editor_ast.py`). A function-like kind gives its call once and the
linear text comes from that, so writing a template and reading it back cannot drift apart.

Drawing as controls belongs to a UI (`devices/nspire/ui/entry.py`); a test checks that it draws
every kind declared here.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum


class Kind(StrEnum):
    """Template kinds; the comment lists the slots in Tab order (the device's, decision 0023)."""

    FRACTION = "fraction"  # numerator, denominator
    POWER = "power"  # exponent, attached to the term before it
    ROOT = "root"  # radicand
    MATRIX = "matrix"  # rows x columns of cells, row by row
    NTH_ROOT = "nth_root"  # index, radicand
    LOG = "log"  # base, argument
    ABS = "abs"  # argument
    PIECEWISE = "piecewise"  # rows of (value, condition)
    SYSTEM = "system"  # rows of one equation
    DERIVATIVE = "derivative"  # variable, expression
    DERIVATIVE2 = "derivative2"  # variable, expression
    DERIVATIVE_N = "derivative_n"  # order, variable, expression
    DMS = "dms"  # degrees, minutes, seconds
    INTEGRAL = "integral"  # lower, upper, integrand, variable
    ANTIDERIVATIVE = "antiderivative"  # integrand, variable
    SUM = "sum"  # variable, lower, upper, expression
    PRODUCT = "product"  # variable, lower, upper, expression
    LIMIT = "limit"  # variable, point, direction (+ or -, may be empty), expression
    LIST = "list"  # the elements of {a, b, c}; typing a comma starts the next one


type Writer = Callable[[list[str], int], str]  # slots' text (Tab order) and a grid's columns
# A call's arguments in order: a slot number, or literal text the argument must be (`2` for d²/dx²)
type Arguments = tuple[int | str, ...]


@dataclass(frozen=True, slots=True)
class Call:
    """The TI function a template is written as, and which slot each argument comes from."""

    name: str
    arguments: Arguments

    def write(self, slots: list[str], _cols: int = 0) -> str:
        args = (slots[a] if isinstance(a, int) else a for a in self.arguments)
        return f"{self.name}({','.join(args)})"


@dataclass(frozen=True, slots=True)
class Spec:
    slots: int  # slots in a template of this kind; 0 for a grid, whose size is chosen when made
    latex: Writer
    linear: Writer
    call: Call | None = None  # the call the bridge reads back as this template
    grid: int | None = None  # a grid's fixed number of columns (0: chosen when made); None: not one
    walked: bool = False  # Left and Right go through the slots in Tab order before leaving
    joins: bool = True  # after a term the linear text needs a `*` (`x` then |□| is not `xabs(`)


def _called(
    name: str, arguments: Arguments, slots: int, latex: Writer, *, walked: bool = False
) -> Spec:
    call = Call(name, arguments)
    return Spec(slots, latex, call.write, call, walked=walked)


def _rows(slots: list[str], cols: int, joint: str) -> str:
    return r" \\ ".join(joint.join(slots[i : i + cols]) for i in range(0, len(slots), cols))


def _matrix_text(slots: list[str], cols: int) -> str:
    rows = [",".join(slots[i : i + cols]) for i in range(0, len(slots), cols)]
    return "[" + ";".join(rows) + "]"


def _matrix_latex(slots: list[str], cols: int) -> str:
    body = r" \\ ".join(" & ".join(slots[i : i + cols]) for i in range(0, len(slots), cols))
    return rf"\left[\begin{{matrix}}{body}\end{{matrix}}\right]"


_DEFINITE = Call("∫", (2, 3, 0, 1))
_INDEFINITE = Call("∫", (2, 3))  # the same slots without bounds: read back as an antiderivative


def _integral(s: list[str], _cols: int) -> str:
    """The definite-integral template; with both limits left empty it is the indefinite one."""
    return (_INDEFINITE if not s[0].strip() and not s[1].strip() else _DEFINITE).write(s)


def _limit(s: list[str], _cols: int) -> str:
    """`limit`'s fourth argument is the direction slot: + is from the right (1), - the left."""
    text = s[2].strip().replace("−", "-")
    direction = "," + {"+": "1", "-": "-1"}.get(text, text) if text else ""
    return f"limit({s[3]},{s[0]},{s[1]}{direction})"


SPECS: dict[Kind, Spec] = {
    Kind.FRACTION: Spec(
        2, lambda s, _: rf"\frac{{{s[0]}}}{{{s[1]}}}", lambda s, _: f"(({s[0]})/({s[1]}))"
    ),
    # `{}` keeps a power at the start of a row valid LaTeX
    Kind.POWER: Spec(1, lambda s, _: rf"{{}}^{{{s[0]}}}", lambda s, _: f"^({s[0]})", joins=False),
    Kind.ROOT: Spec(
        1, lambda s, _: rf"\sqrt{{{s[0]}}}", Call("√", (0,)).write, Call("√", (0,)), joins=False
    ),
    Kind.MATRIX: Spec(0, _matrix_latex, _matrix_text, grid=0),
    Kind.NTH_ROOT: _called("root", (1, 0), 2, lambda s, _: rf"\sqrt[{s[0]}]{{{s[1]}}}"),
    Kind.LOG: _called("log", (1, 0), 2, lambda s, _: rf"\log_{{{s[0]}}}\left({s[1]}\right)"),
    Kind.ABS: _called("abs", (0,), 1, lambda s, _: rf"\left|{s[0]}\right|"),
    Kind.PIECEWISE: Spec(
        0,
        lambda s, c: rf"\begin{{cases}}{_rows(s, c, ', & ')}\end{{cases}}",
        lambda s, _: "piecewise(" + ",".join(s) + ")",
        grid=2,
    ),
    Kind.SYSTEM: Spec(
        0,
        lambda s, c: rf"\begin{{cases}}{_rows(s, c, '')}\end{{cases}}",
        lambda s, _: "{" + ",".join(s) + "}",
        grid=1,
    ),
    # d²/dx² before dⁿ/dxⁿ, so `derivative(f,x,2)` reads back as the second derivative
    Kind.DERIVATIVE2: _called(
        "derivative",
        (1, 0, "2"),
        2,
        lambda s, _: rf"\frac{{d^{{2}}}}{{d{s[0]}^{{2}}}}\left({s[1]}\right)",
        walked=True,
    ),
    Kind.DERIVATIVE: _called(
        "derivative",
        (1, 0),
        2,
        lambda s, _: rf"\frac{{d}}{{d{s[0]}}}\left({s[1]}\right)",
        walked=True,
    ),
    Kind.DERIVATIVE_N: _called(
        "derivative",
        (2, 1, 0),
        3,
        lambda s, _: rf"\frac{{d^{{{s[0]}}}}}{{d{s[1]}^{{{s[0]}}}}}\left({s[2]}\right)",
        walked=True,
    ),
    Kind.DMS: Spec(
        3, lambda s, _: rf"{s[0]}^\circ {s[1]}' {s[2]}''", lambda s, _: f"({s[0]}°{s[1]}'{s[2]}\")"
    ),
    Kind.INTEGRAL: Spec(
        4,
        lambda s, _: rf"\int_{{{s[0]}}}^{{{s[1]}}}{s[2]}\,d{s[3]}",
        _integral,
        _DEFINITE,
        walked=True,
    ),
    Kind.ANTIDERIVATIVE: _called(
        "∫", (0, 1), 2, lambda s, _: rf"\int {s[0]}\,d{s[1]}", walked=True
    ),
    Kind.SUM: _called(
        "Σ", (3, 0, 1, 2), 4, lambda s, _: rf"\sum_{{{s[0]}={s[1]}}}^{{{s[2]}}}{s[3]}", walked=True
    ),
    Kind.PRODUCT: _called(
        "Π", (3, 0, 1, 2), 4, lambda s, _: rf"\prod_{{{s[0]}={s[1]}}}^{{{s[2]}}}{s[3]}", walked=True
    ),
    Kind.LIMIT: Spec(
        4,
        lambda s, _: rf"\lim_{{{s[0]}\to {s[1]}^{{{s[2]}}}}}{s[3]}",
        _limit,
        walked=True,
    ),
    Kind.LIST: Spec(
        0,
        lambda s, _: r"\left\{" + r",\,".join(s) + r"\right\}",
        lambda s, _: "{" + ",".join(s) + "}",
        grid=0,
    ),
}

# Templates whose slots form a grid: Up and Down move between rows, Backspace steps back a cell.
# The number is the fixed width (0: chosen when the template is made).
GRIDS = {kind: spec.grid for kind, spec in SPECS.items() if spec.grid is not None}
# Templates whose slots Left and Right walk through in Tab order before leaving (an integral:
# lower, upper, integrand, variable). Right leaves any other slot (a fraction's, a power's) at once.
WALKED = frozenset(kind for kind, spec in SPECS.items() if spec.walked)
