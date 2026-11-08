"""Key bindings and the modifier state (FR-DEV-001, FR-DEV-007).

A profile supplies keymaps as data: a map from a key name to a `Binding` (an action name and an
argument). A key name is `key` or `modifier+key`, for example `ctrl+Enter` on a computer keyboard or
`ctrl+div` on a keypad. Nothing here knows which device the keys belong to.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class Binding:
    """What a key does: an action the page understands, with one optional argument."""

    action: str
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
    the theme gives colours to (`digit`, `alpha`, `nav`...). A key with no name is a gap."""

    name: str
    label: str
    shift: str = ""
    ctrl: str = ""
    width: float = 1.0
    height: float = 1.0
    style: str = ""


def gap(width: float = 1.0) -> Key:
    """Empty space in a keypad row."""
    return Key("", "", width=width)


type Keypad = tuple[tuple[Key, ...], ...]


def keypad_units(keypad: Keypad) -> tuple[float, float]:
    """The keypad's size in key units: its widest row, and the sum of the row heights."""
    width = max(sum(key.width for key in row) for row in keypad)
    height = sum(max(key.height for key in row) for row in keypad)
    return width, height
