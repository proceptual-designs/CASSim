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
    pressing it again cancels it. A computer keyboard sends `ctrl+Enter` as one name, so it never
    uses the modifier state. A printable character with no binding of its own is typed.
    """

    def __init__(self, keymap: Keymap, modifiers: tuple[str, ...] = ()) -> None:
        self.keymap = keymap
        self.modifiers = modifiers
        self.pending = ""

    def press(self, key: str) -> Binding | None:
        if key in self.modifiers:
            self.pending = "" if self.pending == key else key
            return None
        name = f"{self.pending}+{key}" if self.pending else key
        typed = not self.pending
        self.pending = ""
        binding = self.keymap.get(name)
        if binding is None and typed and len(key) == 1:
            return Binding("insert", key)
        return binding


@dataclass(frozen=True)
class Key:
    """A key as drawn on a keypad: its name for `Keyboard.press`, its label, and the labels of the
    other layers (empty when the layer does nothing)."""

    name: str
    label: str
    shift: str = ""
    ctrl: str = ""


type Keypad = tuple[tuple[Key, ...], ...]
