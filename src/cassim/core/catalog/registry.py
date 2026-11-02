"""The table of built-in functions and commands, filled by the modules beside this one.

A function is *eager* (its arguments are evaluated first and arrive as values) or *lazy* (it gets
the syntax tree, for `seq`, `when` and others that decide what to evaluate). A command is a
statement written without parentheses, such as `SortA l`.
"""

from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Protocol

from cassim.core import ast
from cassim.core.scope import Scope
from cassim.core.settings import Settings
from cassim.core.values import Value


class Host(Protocol):
    """What a catalog entry may ask of the evaluator running it."""

    @property
    def settings(self) -> Settings: ...

    @property
    def scope(self) -> Scope: ...

    def expr(self, node: ast.Expr) -> Value: ...

    def bound(self, bindings: dict[str, Value]) -> AbstractContextManager[None]: ...


type Eager = Callable[[Host, list[Value]], Value]
type Lazy = Callable[[Host, tuple[ast.Expr, ...]], Value]
type CommandRun = Callable[[Host, tuple[ast.Expr, ...]], Value]


@dataclass(frozen=True, slots=True)
class EagerEntry:
    name: str
    run: Eager
    low: int
    high: int | None  # None means any number of arguments from `low`
    cas: bool


@dataclass(frozen=True, slots=True)
class LazyEntry:
    name: str
    run: Lazy
    low: int
    high: int | None
    cas: bool


type Entry = EagerEntry | LazyEntry


_FUNCTIONS: dict[str, Entry] = {}
_COMMANDS: dict[str, CommandRun] = {}


def eager[F: Callable[..., Value]](
    name: str, low: int, high: int | None = -1, *, cas: bool = False
) -> Callable[[F], F]:
    """Register a function whose arguments are evaluated first. `high` defaults to `low`.

    `cas=True` marks a function that CAS Off and Exact Arithmetic refuse outright.
    """
    return _register(name, low, low if high == -1 else high, False, cas)


def lazy[F: Callable[..., Value]](
    name: str, low: int, high: int | None = -1, *, cas: bool = False
) -> Callable[[F], F]:
    """Register a function that receives its arguments unevaluated."""
    return _register(name, low, low if high == -1 else high, True, cas)


def _register[F: Callable[..., Value]](
    name: str, low: int, high: int | None, is_lazy: bool, cas: bool
) -> Callable[[F], F]:
    def decorate(function: F) -> F:
        kind = LazyEntry if is_lazy else EagerEntry
        _FUNCTIONS[name.casefold()] = kind(name, function, low, high, cas)
        return function

    return decorate


def command(name: str) -> Callable[[CommandRun], CommandRun]:
    """Register a statement such as `SortA`. `name` is the spelling the parser knows."""

    def decorate(function: CommandRun) -> CommandRun:
        _COMMANDS[name.casefold()] = function
        return function

    return decorate


def lookup(name: str) -> Entry | None:
    return _FUNCTIONS.get(name.casefold())


def lookup_command(name: str) -> CommandRun | None:
    return _COMMANDS.get(name.casefold())


def is_builtin(name: str) -> bool:
    return name.casefold() in _FUNCTIONS
