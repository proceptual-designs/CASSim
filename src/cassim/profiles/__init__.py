"""Device profiles: the data that makes the framework in `cassim.device` a particular device."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from cassim.core.settings import Settings
from cassim.device.keys import Keymap, Keypad
from cassim.device.menu import MenuItem


@dataclass(frozen=True)
class Profile:
    name: str
    handheld: Keymap
    computer: Keymap
    modifiers: tuple[str, ...]
    keypad: Keypad
    status: Callable[[Settings], str]  # the title-bar settings text
    menus: Mapping[str, MenuItem]  # by the action that opens them: `doc`, `menu`
