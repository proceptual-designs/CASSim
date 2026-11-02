"""Document > Problem > Variables. A Problem's variables and user functions share one namespace."""

from dataclasses import dataclass

from cassim.core import ast
from cassim.core.values import Value


@dataclass(frozen=True, slots=True)
class Function:
    """A user function. The body stays as typed and is evaluated at each call."""

    params: tuple[str, ...]
    body: ast.Expr


type Variable = Value | Function


class Scope:
    """The variables of one Problem. Names are case-insensitive."""

    def __init__(self) -> None:
        self._items: dict[str, Variable] = {}

    def get(self, name: str) -> Variable | None:
        return self._items.get(name.casefold())

    def define(self, name: str, item: Variable) -> None:
        self._items[name.casefold()] = item

    def delete(self, name: str) -> None:
        self._items.pop(name.casefold(), None)

    def clear_az(self) -> None:
        """Delete every single-letter name from a to z, as ClearAZ does."""
        for name in [n for n in self._items if len(n) == 1 and "a" <= n <= "z"]:
            del self._items[name]

    def clear(self) -> None:
        self._items.clear()

    def names(self) -> frozenset[str]:
        return frozenset(self._items)
