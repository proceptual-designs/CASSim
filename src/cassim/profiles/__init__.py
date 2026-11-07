"""Device profiles: the data that makes the framework in `cassim.device` a particular device."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

from cassim.core.settings import Settings
from cassim.device.keys import Keymap, Keypad
from cassim.device.menu import MenuItem
from cassim.device.wizard import Wizard


@dataclass(frozen=True)
class Profile:
    name: str
    handheld: Keymap
    computer: Keymap
    modifiers: tuple[str, ...]
    keypad: Keypad
    status: Callable[[Settings], str]  # the title-bar settings text
    menus: Mapping[str, MenuItem]  # by the action that opens them: `doc`, `menu`
    wizards: Mapping[str, Wizard] = field(default_factory=dict)  # dialogs, by name
    # Other keypads the user may choose (System Settings), by name; the first is the default.
    keypads: Mapping[str, Keypad] = field(default_factory=dict)
