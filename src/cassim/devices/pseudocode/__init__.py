"""CASSim pseudocode Code view device."""

from cassim.device.profile import Profile
from cassim.devices import Device
from cassim.doc.document import PageType, PageTypes


def new_code(_: object) -> dict[str, str]:
    return {"source": ""}


PROFILE = Profile(
    name="Pseudocode & Python",
    handheld={},
    computer={},
    modifiers=(),
    keypad=(),
    status=lambda _settings: "Pseudocode",
    menus={},
)

PAGES = PageTypes(
    "pseudocode",
    (PageType("code", "Pseudocode", new=new_code),),
)

DEVICE = Device(
    id="pseudocode",
    title="Pseudocode & Python",
    profile=PROFILE,
    pages=PAGES,
    engine=None,
    ui="cassim.devices.pseudocode.ui",
    storage="pseudocode.",
)
