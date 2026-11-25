"""CASSim Scientific: a natural-display scientific calculator for Australian schools (SDD-14).

`engine` (statistics), `values`, `parser`, `display`, `editor` and `state` are the calculator and
import without Flet; `tutorials` holds the lessons; `keys` names every key and the computer
keyboard map. Only `ui/` imports Flet.
"""

from __future__ import annotations

from cassim.device.profile import Profile
from cassim.devices import Device
from cassim.devices.scientific.keys import COMMANDS
from cassim.doc.document import PageType, PageTypes

HELP_PAGE = "Scientific-calculator.html"


def new_calc(_: object) -> dict[str, str]:
    return {}


PROFILE = Profile(
    name="CASSim Scientific",
    handheld={},
    computer=COMMANDS,  # the shortcuts the published page keeps from the browser
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
    title="CASSim Scientific",
    profile=PROFILE,
    pages=PAGES,
    engine=None,
    ui="cassim.devices.scientific.ui",
    storage="scientific.",
    help=HELP_PAGE,
)
