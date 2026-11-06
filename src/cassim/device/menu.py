"""Menus as data (FR-DEV-001, FR-DEV-007): a tree of items and the state of walking through it.

A profile supplies the trees. Items are chosen with Up/Down and Enter, or by the item's key (1 to 9,
then A to Z, as on the handheld). Right opens a submenu, Left or Escape goes back.
"""

from __future__ import annotations

import string
from dataclasses import dataclass, field

from cassim.device.keys import Binding

KEYS = string.digits[1:] + string.ascii_uppercase  # 1 to 9, then A to Z


@dataclass(frozen=True)
class MenuItem:
    """A leaf does `action`; an item with `items` opens a submenu. `key` overrides the position."""

    label: str
    action: str = ""
    arg: str = ""
    items: tuple[MenuItem, ...] = ()
    key: str = ""


@dataclass(frozen=True)
class Row:
    """One drawn row of the open menu."""

    key: str
    label: str
    submenu: bool
    selected: bool


@dataclass(frozen=True)
class MenuView:
    title: str  # the path so far, "Insert"
    rows: tuple[Row, ...]


@dataclass
class _Level:
    item: MenuItem
    index: int = 0


@dataclass
class MenuState:
    """An open menu. `press` returns the binding of a chosen leaf, which closes the menu."""

    root: MenuItem
    levels: list[_Level] = field(default_factory=list)
    open: bool = True

    def __post_init__(self) -> None:
        self.levels = [_Level(self.root)]

    @property
    def level(self) -> _Level:
        return self.levels[-1]

    def keys(self) -> list[str]:
        """The key of each item of the current level."""
        used = {item.key for item in self.level.item.items if item.key}
        spare = (key for key in KEYS if key not in used)
        return [item.key or next(spare) for item in self.level.item.items]

    def view(self) -> MenuView:
        level = self.level
        title = " > ".join(entry.item.label for entry in self.levels)
        rows = tuple(
            Row(key, item.label, bool(item.items), index == level.index)
            for index, (key, item) in enumerate(zip(self.keys(), level.item.items, strict=True))
        )
        return MenuView(title, rows)

    def press(self, action: str, arg: str = "") -> Binding | None:
        """Handle a navigation action (`up`, `down`, `left`, `right`, `enter`, `escape`) or an
        `insert` of an item key. Returns the binding to run when a leaf is chosen."""
        level = self.level
        count = len(level.item.items)
        match action:
            case "up":
                level.index = (level.index - 1) % count
            case "down":
                level.index = (level.index + 1) % count
            case "left" | "backspace":
                self._back()
            case "escape":
                self.open = False
            case "right" | "enter":
                return self._choose(level.index, only_submenu=action == "right")
            case "insert":
                keys = self.keys()
                if arg.upper() in keys:
                    return self._choose(keys.index(arg.upper()), only_submenu=False)
        return None

    def _back(self) -> None:
        if len(self.levels) > 1:
            self.levels.pop()
        else:
            self.open = False

    def _choose(self, index: int, *, only_submenu: bool) -> Binding | None:
        item = self.level.item.items[index]
        self.level.index = index
        if item.items:
            self.levels.append(_Level(item))
            return None
        if only_submenu:
            return None
        self.open = False
        return Binding(item.action, item.arg)
