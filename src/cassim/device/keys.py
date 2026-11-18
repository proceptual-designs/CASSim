"""Key bindings and the modifier state (FR-DEV-001, FR-DEV-007).

A profile supplies keymaps as data: a map from a key name to a `Binding` (an action name and an
argument). A key name is `key` or `modifier+key`, for example `ctrl+Enter` on a computer keyboard or
`ctrl+div` on a keypad. Nothing here knows which device the keys belong to.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

type Action = Literal[
    "accent", "add_page", "add_problem", "approximate", "backspace", "caps", "clear",
    "context_menu", "copy", "cut", "delete", "delete_page", "dialog", "down", "end", "enter",
    "escape", "extend", "first_line", "goto", "home", "home_key", "insert", "insert_linear",
    "last_line", "left", "menu_back", "menu_page", "menu_pick", "move_page", "move_problem",
    "new_document", "next_page", "open_menu", "page_down", "page_up", "paste", "place", "power",
    "prev_page", "recall_at", "recall_extend", "recall_place", "recalculate", "redo", "redo_pages",
    "right", "select", "select_all", "select_cells", "select_left", "select_right",
    "select_to_end", "select_to_start", "select_word_left", "select_word_right", "sheet",
    "sheet_bar", "sheet_cancel", "sheet_choose", "sheet_drag", "sheet_goto", "sheet_ok", "sheet_op",
    "sheet_ref_fixed", "sheet_ref_mode", "sheet_tap", "shift_tab", "sorter_go",
    "statistics", "graphs_submit", "graphs_toggle", "graphs_zoom", "graphs_gesture",
    "graphs_standard", "statistics_eval", "statistics_point", "tab", "template",
    "undo", "undo_pages", "up",
    "wizard", "word_left", "word_right",
]  # fmt: skip


@dataclass(frozen=True)
class Binding:
    """What a key does: an action the page understands, with one optional argument."""

    action: Action
    arg: str = ""


type Keymap = Mapping[str, Binding]


class Keyboard:
    """Turns key presses into bindings.

    A modifier key (the on-screen ctrl and shift of a keypad) applies to the next key only, and
    pressing it again cancels it, unless the pair is bound (ctrl then shift). A computer keyboard
    sends `ctrl+Enter` as one name, so it never uses the modifier state. A printable character
    with no binding of its own is typed.
    """

    def __init__(self, keymap: Keymap, modifiers: tuple[str, ...] = ()) -> None:
        self.keymap = keymap
        self.modifiers = modifiers
        self.pending = ""

    def press(self, key: str) -> Binding | None:
        # a modifier pressed after another can be a key of its own (ctrl then shift is caps lock)
        combo = f"{self.pending}+{key}"
        if key in self.modifiers and not (self.pending and combo in self.keymap):
            self.pending = "" if self.pending == key else key
            return None
        name = f"{self.pending}+{key}" if self.pending else key
        typed = not self.pending
        self.pending = ""
        binding = self.keymap.get(name)
        if binding is None and len(key) == 1:
            if typed:
                return Binding("insert", key)
            if name == f"shift+{key}" and key.isalpha():
                return Binding("insert", key.upper())  # shift then a letter types a capital
        return binding


@dataclass(frozen=True)
class Key:
    """A key as drawn on a keypad: its name for `Keyboard.press`, its label, and the labels of the
    other layers (empty when the layer does nothing).

    `width` and `height` are in key units (a row is as tall as its tallest key); `style` is a name
    the theme gives colours to (`digit`, `alpha`, `nav`...). A key with no name is a gap.

    `join` makes one key of two pieces in rows next to each other, as a computer keyboard's
    return key is an L: the upper piece says `down` and the lower one, with the same name and no
    label, says `up`. The pieces line up at their right edges and are drawn with no gap between
    them. `outline` draws a ring round the key, to make it stand out."""

    name: str
    label: str
    shift: str = ""
    ctrl: str = ""
    width: float = 1.0
    height: float = 1.0
    style: str = ""
    join: str = ""  # "", "down" or "up"
    outline: bool = False


def gap(width: float = 1.0, height: float = 1.0) -> Key:
    """Empty space in a keypad row. Give it the row's key height: a taller gap makes the row
    taller and pushes its keys down."""
    return Key("", "", width=width, height=height)


type Keypad = tuple[tuple[Key, ...], ...]


def keypad_units(keypad: Keypad) -> tuple[float, float]:
    """The keypad's size in key units: its widest row, and the sum of the row heights."""
    width = max(sum(key.width for key in row) for row in keypad)
    height = sum(max(key.height for key in row) for row in keypad)
    return width, height
