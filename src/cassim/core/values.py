"""Typed Value union: Number, Expr, List, Matrix, Str, Bool, Eq, Void, Unit.

Numbers, symbolic expressions and relations are all `Expr`, which holds a SymPy object that only
`compat/sympy_adapter.py` may look inside. Void and Unit values arrive with the catalog (M1d).
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
class ListValue:
    items: tuple[Value, ...]


@dataclass(frozen=True, slots=True)
class MatrixValue:
    rows: tuple[tuple[Expr, ...], ...]


type Value = Expr | Str | Bool | ListValue | MatrixValue
