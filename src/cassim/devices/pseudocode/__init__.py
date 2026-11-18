"""The standalone Pseudocode device and its placeholder UI."""

from cassim.device.profile import Profile
from cassim.devices import Device
from cassim.doc.document import PageType, PageTypes

PAGES = PageTypes("pseudocode", (PageType("code", "Pseudocode"),))
PROFILE = Profile(
    name="Pseudocode & Python",
    handheld={},
    computer={},
    modifiers=(),
    keypad=(),
    status=lambda _settings: "Pseudocode",
    menus={},
)

DEVICE = Device(
    id="pseudocode",
    title="Pseudocode & Python",
    profile=PROFILE,
    pages=PAGES,
    ui="cassim.devices.pseudocode.ui",
    storage="pseudocode.",
)
