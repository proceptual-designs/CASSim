"""Validate and compile the restricted Python math expressions used by graph sampling."""

from __future__ import annotations

import ast
import math
from collections.abc import Callable
from typing import cast

_MATH_NAMES = frozenset(
    {
        "sin",
        "cos",
        "tan",
        "asin",
        "acos",
        "atan",
        "sinh",
        "cosh",
        "tanh",
        "asinh",
        "acosh",
        "atanh",
        "exp",
        "log",
        "fabs",
        "floor",
        "ceil",
        "copysign",
        "min",
        "max",
        "pi",
        "e",
        "inf",
        "nan",
    }
)
_ALLOWED_AST_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Call,
    ast.Compare,
    ast.BoolOp,
    ast.IfExp,
    ast.Constant,
    ast.Name,
    ast.Attribute,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
    ast.UAdd,
    ast.USub,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.And,
    ast.Or,
    ast.Not,
    ast.Load,
)


def check_math_source(source: str) -> None:
    """Reject syntax, names and calls outside the small graph-worker expression grammar."""
    tree = ast.parse(source, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_AST_NODES):
            msg = f"unsupported syntax in graph expression: {type(node).__name__}"
            raise ValueError(msg)
        if isinstance(node, ast.Name) and node.id not in {"x", "math", "min", "max"}:
            msg = f"unsupported name in graph expression: {node.id}"
            raise ValueError(msg)
        if isinstance(node, ast.Attribute) and (
            not isinstance(node.value, ast.Name)
            or node.value.id != "math"
            or node.attr not in _MATH_NAMES
        ):
            msg = f"unsupported attribute in graph expression: {node.attr}"
            raise ValueError(msg)
        if isinstance(node, ast.Call):
            function = node.func
            valid_math_call = (
                isinstance(function, ast.Attribute)
                and isinstance(function.value, ast.Name)
                and function.value.id == "math"
                and function.attr in _MATH_NAMES
            )
            valid_builtin_call = isinstance(function, ast.Name) and function.id in {"min", "max"}
            if not (valid_math_call or valid_builtin_call) or node.keywords:
                msg = "unsupported function call in graph expression"
                raise ValueError(msg)
        if isinstance(node, ast.Constant) and not isinstance(node.value, int | float | bool):
            msg = "only numeric and boolean constants are allowed in graph expressions"
            raise ValueError(msg)


def compile_math_source(source: str) -> Callable[[float], float]:
    """Compile a checked math expression with no builtins or ambient globals."""
    check_math_source(source)
    tree = ast.parse(f"lambda x: ({source})", mode="eval")
    code = compile(tree, "<cassim-graph>", "eval")
    compiled = eval(code, {"__builtins__": {}, "math": math, "min": min, "max": max}, {})
    return cast(Callable[[float], float], compiled)
