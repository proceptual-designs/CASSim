"""Typed Value union: Expr, Str, Bool, List, Matrix, Void and Unevaluated.

Numbers, symbolic expressions and relations are all `Expr`, which holds a SymPy object that only
`compat/sympy_adapter.py` may look inside. Unit values arrive with the catalog (M1d).
"""

from dataclasses import dataclass
from typing import Any

type Raw = Any


@dataclass(frozen=True, slots=True)
class Expr:
    raw: Raw


@dataclass(frozen=True, slots=True)
class Str:
    value: str


@dataclass(frozen=True, slots=True)
class Bool:
    value: bool


@dataclass(frozen=True, slots=True)
class Unevaluated:
    """A call to a name that is not a function, kept as typed because an argument is a list,
    matrix or string. Calls with plain arguments are symbolic expressions instead."""

    name: str
    args: tuple[Value, ...]


@dataclass(frozen=True, slots=True)
class Void:
    """What a statement with nothing to show returns; the calculator prints `Done`."""


@dataclass(frozen=True, slots=True)
class ListValue:
    items: tuple[Value, ...]


@dataclass(frozen=True, slots=True)
class MatrixValue:
    rows: tuple[tuple[Expr, ...], ...]


type Value = Expr | Str | Bool | ListValue | MatrixValue | Void | Unevaluated
