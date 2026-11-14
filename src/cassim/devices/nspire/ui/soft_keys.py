"""The on-screen keyboard in Computer view on a phone or tablet.

A browser shows its on-screen keyboard only for a focused text box, and the calculator draws its
entry line itself. So a hidden text box takes the focus when the user taps where typing goes (the
entry line, a sheet cell), and what is typed into it is turned into calculator keys. The box
always holds one invisible character, so Backspace on an otherwise empty box still changes it.
"""

from __future__ import annotations

from cassim.device.keys import Binding

SENTINEL = "\u200b"  # a zero-width space: what the box holds between keys

# Actions after which typing is expected: a tap in the entry line or on a cell
TYPING_ACTIONS = frozenset({"place", "extend", "sheet_tap"})


def keys_for(value: str) -> list[Binding]:
    """The calculator keys for what the box holds now (it held only SENTINEL before). A removed
    sentinel is a Backspace; every other character is typed."""
    keys: list[Binding] = []
    if SENTINEL not in value:
        keys.append(Binding("backspace"))
    for char in value.replace(SENTINEL, ""):
        keys.append(Binding("enter") if char == "\n" else Binding("insert", char))
    return keys
