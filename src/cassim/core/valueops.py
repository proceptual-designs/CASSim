"""Helpers shared by the evaluator and the catalog for taking values apart and putting them back."""

from collections.abc import Callable

from cassim.core import errors
from cassim.core.compat import sympy_adapter as cas
from cassim.core.errors import TIError
from cassim.core.values import (
    Bool,
    Cell,
    Expr,
    ListValue,
    MatrixValue,
    Raw,
    Shown,
    Str,
    Value,
)


def as_expr(value: Value) -> Expr:
    if isinstance(value, Expr):
        return value
    if isinstance(value, Shown):
        return as_expr(value.value)
    if isinstance(value, Bool):
        return Expr(cas.boolean(value.value))
    raise TIError(errors.DATA_TYPE)


def raw_of(value: Value) -> Raw:
    return as_expr(value).raw


def cell_of(value: Value) -> Cell:
    """A value as a matrix cell: a string stays a string, anything else must be a number."""
    return value if isinstance(value, Str) else as_expr(value)


def map_value(function: Callable[[Value], Value], value: Value) -> Value:
    """Apply `function` to a value, or to each element of a list or matrix."""
    if isinstance(value, ListValue):
        return ListValue(tuple(map_value(function, item) for item in value.items))
    if isinstance(value, MatrixValue):
        return MatrixValue(
            tuple(tuple(cell_of(function(cell)) for cell in row) for row in value.rows)
        )
    return function(value)


def raw_list(value: Value) -> list[Raw]:
    """The elements of a list, which must all be numbers or expressions."""
    if not isinstance(value, ListValue):
        raise TIError(errors.DATA_TYPE)
    return [raw_of(item) for item in value.items]


def list_of(raws: list[Raw]) -> ListValue:
    return ListValue(tuple(Expr(raw) for raw in raws))


def raw_rows(value: Value) -> list[list[Raw]]:
    if not isinstance(value, MatrixValue):
        raise TIError(errors.DATA_TYPE)
    return [[raw_of(cell) for cell in row] for row in value.rows]


def matrix_of(rows: list[list[Raw]]) -> MatrixValue:
    return MatrixValue(tuple(tuple(Expr(cell) for cell in row) for row in rows))


def vector_parts(value: Value) -> list[Raw]:
    """A vector given as a list or as a one-row or one-column matrix, flattened."""
    if isinstance(value, ListValue):
        return raw_list(value)
    rows = raw_rows(value)
    if len(rows) == 1:
        return rows[0]
    if all(len(row) == 1 for row in rows):
        return [row[0] for row in rows]
    raise TIError(errors.DIMENSION_MISMATCH)


def vector_like(template: Value, parts: list[Raw]) -> Value:
    """Put `parts` back in the shape of `template`."""
    if isinstance(template, ListValue):
        return list_of(parts)
    assert isinstance(template, MatrixValue)
    if len(template.rows) == 1:
        return matrix_of([parts])
    return matrix_of([[part] for part in parts])
