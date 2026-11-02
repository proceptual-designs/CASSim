"""Matrices and vectors: determinants, powers, row reduction, dot and cross products."""

from cassim.core import errors
from cassim.core.catalog.registry import Host, eager
from cassim.core.compat import sympy_adapter as cas
from cassim.core.errors import TIError
from cassim.core.valueops import (
    list_of,
    matrix_of,
    raw_of,
    raw_rows,
    vector_like,
    vector_parts,
)
from cassim.core.values import Expr, MatrixValue, Raw, Value


def _square(value: Value) -> list[list[Raw]]:
    rows = raw_rows(value)
    if any(len(row) != len(rows) for row in rows):
        raise TIError(errors.DIMENSION_MISMATCH)
    return rows


def matrix_power(matrix: MatrixValue, exponent: Value) -> Value:
    """`m^n` for an integer `n`; a negative power is an inverse."""
    rows = _square(matrix)
    power = cas.integer_value(raw_of(exponent))
    if power is None:
        raise TIError(errors.DOMAIN)
    if power < 0 and cas.matrix_determinant(rows) == 0:
        raise TIError(errors.SINGULAR)
    return matrix_of(cas.matrix_power(rows, power))


@eager("eigVl", 1)
def eigenvalues(host: Host, args: list[Value]) -> Value:
    """Eigenvalues as a list of decimals, largest first."""
    return list_of(cas.eigenvalues(_square(args[0])))


@eager("eigVc", 1)
def eigenvectors(host: Host, args: list[Value]) -> Value:
    """Unit eigenvectors as the columns of a matrix, in the order of `eigVl`."""
    return matrix_of(cas.eigenvectors(_square(args[0])))


@eager("det", 1)
def det(host: Host, args: list[Value]) -> Value:
    return Expr(cas.matrix_determinant(_square(args[0])))


@eager("identity", 1)
def identity(host: Host, args: list[Value]) -> Value:
    size = cas.integer_value(raw_of(args[0]))
    if size is None or size < 1:
        raise TIError(errors.DOMAIN)
    return matrix_of(cas.matrix_identity(size))


@eager("rref", 1)
def rref(host: Host, args: list[Value]) -> Value:
    return matrix_of(cas.matrix_rref(raw_rows(args[0])))


@eager("simult", 2)
def simult(host: Host, args: list[Value]) -> Value:
    coefficients, constants = _square(args[0]), raw_rows(args[1])
    if len(constants) != len(coefficients):
        raise TIError(errors.DIMENSION_MISMATCH)
    if cas.matrix_determinant(coefficients) == 0:
        raise TIError(errors.SINGULAR)
    return matrix_of(cas.matrix_solve(coefficients, constants))


@eager("augment", 2)
def augment(host: Host, args: list[Value]) -> Value:
    left, right = raw_rows(args[0]), raw_rows(args[1])
    if len(left) != len(right):
        raise TIError(errors.DIMENSION_MISMATCH)
    return matrix_of([a + b for a, b in zip(left, right, strict=True)])


def _same_length(left: Value, right: Value) -> tuple[list[Raw], list[Raw]]:
    a, b = vector_parts(left), vector_parts(right)
    if len(a) != len(b):
        raise TIError(errors.DIMENSION_MISMATCH)
    return a, b


@eager("dotP", 2)
def dot_product(host: Host, args: list[Value]) -> Value:
    return Expr(cas.dot_product(*_same_length(args[0], args[1])))


@eager("crossP", 2)
def cross_product(host: Host, args: list[Value]) -> Value:
    left, right = _same_length(args[0], args[1])
    if len(left) not in (2, 3):
        raise TIError(errors.DIMENSION_MISMATCH)
    pad = [cas.integer(0)] * (3 - len(left))
    return vector_like(args[0], cas.cross_product(left + pad, right + pad))


@eager("norm", 1)
def norm(host: Host, args: list[Value]) -> Value:
    value = args[0]
    if isinstance(value, MatrixValue) and len(value.rows) > 1 and len(value.rows[0]) > 1:
        parts = [cell for row in raw_rows(value) for cell in row]
    else:
        parts = vector_parts(value)
    return Expr(cas.vector_norm(parts))


@eager("unitV", 1)
def unit_vector(host: Host, args: list[Value]) -> Value:
    parts = vector_parts(args[0])
    length = cas.vector_norm(parts)
    if length == 0:
        raise TIError(errors.DOMAIN)
    return vector_like(args[0], [part / length for part in parts])
