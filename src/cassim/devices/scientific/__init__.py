"""CASSim fx scientific calculator device."""

from __future__ import annotations

from cassim.device.profile import Profile
from cassim.devices import Device
from cassim.doc.document import PageType, PageTypes


def new_calc(_: object) -> dict[str, str]:
    return {"expression": "", "result": "0"}


PROFILE = Profile(
    name="CASSim fx",
    handheld={},
    computer={},
    modifiers=("shift", "alpha"),
    keypad=(),
    status=lambda _settings: "Natural Display",
    menus={},
)

PAGES = PageTypes(
    "scientific",
    (PageType("calculator", "Calculation", new=new_calc),),
)

DEVICE = Device(
    id="scientific",
    title="CASSim fx",
    profile=PROFILE,
    pages=PAGES,
    engine=None,
    ui="cassim.devices.scientific.ui",
    storage="fx.",
)
