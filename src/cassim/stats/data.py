"""Read numeric and categorical values from the calculator's formatted list items."""

from __future__ import annotations

import ast
import math
from collections.abc import Mapping
from fractions import Fraction

type DataValue = float | str | None
type Number = Fraction | float
MIN_QUOTED_ITEM = 2


class NumericExpression:
    def __init__(
        self,
        names: dict[str, Number] | None = None,
        lists: Mapping[str, tuple[Number, ...]] | None = None,
    ) -> None:
        self.names = names or {}
        self.lists = lists or {}

    def evaluate(self, expression: str) -> Number:
        normalized = self._normalize(expression)
        return self._node(ast.parse(normalized, mode="eval").body)

    def validate(self, expression: str) -> None:
        normalized = self._normalize(expression)
        self._validate(ast.parse(normalized, mode="eval").body)

    @staticmethod
    def _normalize(expression: str) -> str:
        return (
            expression.replace("ᴇ", "e")
            .replace("ⅇ", "_euler")
            .replace("π", "pi")
            .replace("√(", "sqrt(")
            .replace("·", "*")
            .replace("^", "**")
        )

    def _validate(self, node: ast.expr) -> None:
        match node:
            case ast.Constant(value=value) if isinstance(value, int | float):
                return
            case ast.Name(id="pi" | "_euler"):
                return
            case ast.Name(id=name) if name in self.names:
                return
            case ast.UnaryOp(op=ast.UAdd() | ast.USub(), operand=operand):
                self._validate(operand)
            case ast.BinOp(op=ast.Add() | ast.Sub() | ast.Mult() | ast.Div() | ast.Pow()):
                self._validate(node.left)
                self._validate(node.right)
            case ast.Call(
                func=ast.Name(id="mean"),
                args=[ast.Name(id=name)],
                keywords=[],
            ) if name in self.lists:
                return
            case ast.Call(
                func=ast.Name(id=name),
                args=[argument],
                keywords=[],
            ) if name in {"abs", "cos", "exp", "ln", "log", "sin", "sqrt", "tan"}:
                self._validate(argument)
            case _:
                raise ValueError("not a supported numeric expression")

    def _node(self, node: ast.expr) -> Number:
        result: Number | None = None
        match node:
            case ast.Constant(value=value) if isinstance(value, int | float):
                result = Fraction(str(value))
            case ast.Name(id="pi"):
                result = math.pi
            case ast.Name(id="_euler"):
                result = math.e
            case ast.Name(id=name) if name in self.names:
                result = self.names[name]
            case ast.UnaryOp(op=ast.UAdd(), operand=operand):
                result = self._node(operand)
            case ast.UnaryOp(op=ast.USub(), operand=operand):
                result = -self._node(operand)
            case ast.BinOp():
                result = self._binary(node)
            case ast.Call(
                func=ast.Name(id="mean"),
                args=[ast.Name(id=name)],
                keywords=[],
            ) if values := self.lists.get(name):
                result = sum(values, Fraction(0)) / len(values)
            case ast.Call(func=ast.Name(id=name), args=[argument], keywords=[]):
                result = self._call(name, argument)
        if result is None:
            raise ValueError(f"not a numeric value: {ast.dump(node)}")
        return result

    def _binary(self, node: ast.BinOp) -> Number:
        left, right = self._node(node.left), self._node(node.right)
        match node.op:
            case ast.Add():
                return left + right
            case ast.Sub():
                return left - right
            case ast.Mult():
                return left * right
            case ast.Div():
                return left / right
            case ast.Pow():
                return left**right
        raise ValueError(f"not a numeric operation: {ast.dump(node.op)}")

    def _call(self, name: str, argument: ast.expr) -> Number:
        value = float(self._node(argument))
        functions = {
            "abs": abs,
            "cos": math.cos,
            "exp": math.exp,
            "ln": math.log,
            "log": math.log10,
            "sin": math.sin,
            "sqrt": math.sqrt,
            "tan": math.tan,
        }
        try:
            return functions[name](value)
        except KeyError:
            raise ValueError(f"not a numeric function: {name}") from None


def parse_item(text: str) -> DataValue:
    """Return a finite number or an unquoted string; void and non-real values are omitted."""
    value = text.strip()
    if not value or value == "_":
        return None
    if len(value) >= MIN_QUOTED_ITEM and value[0] == value[-1] == '"':
        return value[1:-1].replace('""', '"')
    try:
        result = float(NumericExpression().evaluate(value))
    except SyntaxError, ValueError, ZeroDivisionError, OverflowError:
        return None
    return result if math.isfinite(result) else None


def parse_items(items: tuple[str, ...] | None) -> tuple[DataValue, ...]:
    return () if items is None else tuple(parse_item(item) for item in items)


def as_numbers(values: tuple[DataValue, ...]) -> tuple[float | None, ...]:
    return tuple(value if isinstance(value, float) else None for value in values)


def as_categories(values: tuple[DataValue, ...]) -> tuple[str | None, ...]:
    return tuple(str(value) if value is not None else None for value in values)
