"""The TI-Nspire CX CAS device (FR-PROF-002)."""

from cassim.devices import Device, Engine
from cassim.devices.nspire.keymap import PROFILE
from cassim.devices.nspire.pages import DEVICE as ID
from cassim.devices.nspire.pages import PAGES

DEVICE = Device(
    id=ID,
    title=PROFILE.name,
    profile=PROFILE,
    pages=PAGES,
    # The CAS engine is `core/` as it stands (decision 0032 item 7); SymPy needs mpmath.
    engine=Engine("cassim.device.engine", ("sympy", "mpmath")),
    ui="cassim.devices.nspire.ui",
    storage="cassim.",  # today's keys (`cassim.autosave`), so saved documents are kept
)
