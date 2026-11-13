"""Document > Problem > Variables. A Problem's variables and user functions share one namespace.

Every store or delete raises the scope's revision and records it against the name, so the engine
can send only what changed since its last reply (decision 0031, FR-DOC-008).
"""

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
    """The variables of one Problem. Names arrive already folded (see `variable_key`)."""

    def __init__(self) -> None:
        self._items: dict[str, Variable] = {}
        self.revision = 0  # raised by every change
        self._changed: dict[str, int] = {}  # each name's revision when last stored or deleted
        # Names a spreadsheet holds (check run 2, G): a linked list must stay a list, and a
        # formula column's variable takes no store from an entry. Entries check these; the
        # sheet itself stores past them.
        self.lists: set[str] = set()
        self.read_only: set[str] = set()

    def _touch(self, name: str) -> None:
        self.revision += 1
        self._changed[name] = self.revision

    def get(self, name: str) -> Variable | None:
        return self._items.get(name)

    def define(self, name: str, item: Variable) -> None:
        self._items[name] = item
        self._touch(name)

    def delete(self, name: str) -> None:
        if self._items.pop(name, None) is not None:
            self._touch(name)

    def clear_az(self) -> None:
        """Delete every single-letter name from a to z, as ClearAZ does."""
        for name in [n for n in self._items if len(n) == 1 and "a" <= n <= "z"]:
            del self._items[name]
            self._touch(name)

    def fold_names(self) -> None:
        """Merge names that differ only in case, as when case sensitivity is turned off."""
        before = set(self._items)
        items = {name.casefold(): item for name, item in self._items.items()}
        self._items.clear()
        self._items.update(items)
        for name in sorted(before | set(items)):
            self._touch(name)

    def clear(self) -> None:
        for name in sorted(self._items):
            self._touch(name)
        self._items.clear()

    def names(self) -> frozenset[str]:
        return frozenset(self._items)

    def revision_of(self, name: str) -> int:
        """When `name` last changed; 0 if it never has."""
        return self._changed.get(name, 0)

    def changed_since(self, revision: int) -> frozenset[str]:
        """The names stored or deleted after `revision`."""
        return frozenset(name for name, when in self._changed.items() if when > revision)
