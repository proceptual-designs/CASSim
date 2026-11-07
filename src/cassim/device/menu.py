"""Menus as data (FR-DEV-001, FR-DEV-007): a tree of items and the state of walking through it.

A profile supplies the trees. Items are chosen with Up/Down and Enter, or by the item's key (1 to 9,
then A to Z, as on the handheld). Right opens a submenu, Left or Escape goes back. A click or tap
picks a row of any open level (`pick`), so the menus work by touch and mouse too.
"""

from __future__ import annotations

import string
from dataclasses import dataclass, field

from cassim.device.keys import Binding

KEYS = string.digits[1:] + string.ascii_uppercase  # 1 to 9, then A to Z


@dataclass(frozen=True)
class MenuItem:
    """A leaf does `action`; an item with `items` opens a submenu. `key` overrides the position.

    `hint` is the syntax shown beside the item (`solve(Equation, Var)`). A label ending in `…`
    opens a dialog, as on the handheld. A disabled item is a greyed placeholder: it keeps its
    place and number (so the numbering matches the device) but cannot be chosen."""

    label: str
    action: str = ""
    arg: str = ""
    items: tuple[MenuItem, ...] = ()
    key: str = ""
    hint: str = ""
    enabled: bool = True


@dataclass(frozen=True)
class Row:
    """One drawn row of an open menu."""

    key: str
    label: str
    submenu: bool
    selected: bool
    hint: str = ""
    enabled: bool = True


@dataclass(frozen=True)
class Panel:
    """One open level: its title and rows. Submenus cascade to the right of their parent."""

    title: str
    rows: tuple[Row, ...]


@dataclass(frozen=True)
class MenuView:
    title: str  # the path so far, "Menu > Algebra"
    rows: tuple[Row, ...]  # the deepest level, which takes the keys
    panels: tuple[Panel, ...] = ()  # every open level, outermost first
    hint: str = ""  # the syntax of the highlighted row


@dataclass
class _Level:
    item: MenuItem
    index: int = 0


def item_keys(item: MenuItem) -> list[str]:
    """The key of each child of `item`: its own key, else the next one not taken."""
    used = {child.key for child in item.items if child.key}
    spare = (key for key in KEYS if key not in used)
    return [child.key or next(spare) for child in item.items]


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
        return item_keys(self.level.item)

    def view(self) -> MenuView:
        panels = tuple(
            Panel(
                entry.item.label,
                tuple(
                    Row(
                        key,
                        item.label,
                        bool(item.items),
                        index == entry.index,
                        item.hint,
                        item.enabled,
                    )
                    for index, (key, item) in enumerate(
                        zip(item_keys(entry.item), entry.item.items, strict=True)
                    )
                ),
            )
            for entry in self.levels
        )
        title = " > ".join(entry.item.label for entry in self.levels)
        level = self.level
        hint = level.item.items[level.index].hint if level.item.items else ""
        return MenuView(title, panels[-1].rows, panels, hint)

    def press(self, action: str, arg: str = "") -> Binding | None:
        """Handle a navigation action (`up`, `down`, `left`, `right`, `enter`, `escape`) or an
        `insert` of an item key. Returns the binding to run when a leaf is chosen."""
        level = self.level
        count = len(level.item.items)
        match action:
            case "up" if count:
                level.index = (level.index - 1) % count
            case "down" if count:
                level.index = (level.index + 1) % count
            case "left" | "backspace":
                self._back()
            case "escape":
                self.open = False
            case "right" | "enter" | "select" if count:
                return self._choose(level.index, only_submenu=action == "right")
            case "insert":
                keys = self.keys()
                if arg.upper() in keys:
                    return self._choose(keys.index(arg.upper()), only_submenu=False)
            case "menu_pick":
                depth, _, index = arg.partition(":")
                return self.pick(int(depth), int(index))
            case "menu_back":
                self._back()
            case "menu_page" if count:  # a click on "more": move the highlight by a page
                level.index = max(0, min(count - 1, level.index + int(arg)))
        return None

    def pick(self, depth: int, index: int) -> Binding | None:
        """A click on row `index` of open level `depth`: deeper levels close, then the row is
        chosen (a submenu opens, a leaf runs). Clicking an open submenu's row closes it."""
        if not 0 <= depth < len(self.levels):
            return None
        opened = depth + 1 < len(self.levels) and self.levels[depth].index == index
        del self.levels[depth + 1 :]
        if opened or not 0 <= index < len(self.level.item.items):
            return None
        return self._choose(index, only_submenu=False)

    def _back(self) -> None:
        if len(self.levels) > 1:
            self.levels.pop()
        else:
            self.open = False

    def _choose(self, index: int, *, only_submenu: bool) -> Binding | None:
        item = self.level.item.items[index]
        self.level.index = index
        if not item.enabled:
            return None  # a placeholder: highlighted, but it does nothing and the menu stays open
        if item.items:
            self.levels.append(_Level(item))
            return None
        if only_submenu:
            return None
        self.open = False
        return Binding(item.action, item.arg)
