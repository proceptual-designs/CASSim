"""Devices: each calculator is a plug-in package here (decision 0032, PLAN.md section 15).

A device package exposes one `Device` as `DEVICE`. It depends on the shared layers (`core`,
`device`, `doc`, `runtime`) and never on another device (FR-PROF-008), and it must import without
Flet, because the engine worker, the CLI and the headless tests load it. Its Flet views are named
by `Device.ui` and imported only by the shell.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cassim.device.profile import Profile
    from cassim.doc.document import PageTypes


@dataclass(frozen=True)
class Engine:
    """What a device's worker runs: the module that handles its ops, and the Pyodide packages
    unpacked beside it."""

    module: str
    packages: tuple[str, ...] = ()


@dataclass(frozen=True)
class Device:
    id: str  # the name in code, files and share links
    title: str  # what the switcher and the title bar call it
    profile: Profile  # keymaps, keypad layouts, menus, wizards and the status line
    pages: PageTypes  # its page types; the first is a new document's page
    engine: Engine | None = None  # None for a device with no worker
    ui: str = ""  # the dotted name of its Flet UI module; "" until it has one
    storage: str = ""  # the prefix of its keys in browser storage
    help: str = ""  # its section of the help site


@dataclass(frozen=True)
class Site:
    """Where a device is published alone (PLAN.md section 15.1)."""

    bundle: str  # the short name: the bundle and the Cloudflare Pages project `cassim-<bundle>`
    product: str
    url: str


# Every device, built or not. The shell names the right site for a document whose device is not
# in its bundle (FR-PROF-009), so this table cannot live in the device packages.
SITES = {
    "nspire": Site("tin", "CASSim-TIN", "https://cassim-tin.pages.dev/"),
    "pseudocode": Site("pseudo", "CASSim-pseudo", "https://cassim-pseudo.pages.dev/"),
    "classpad": Site("cp", "CASSim-CP", "https://cassim-cp.pages.dev/"),
    "prime": Site("prime", "CASSim-Prime", "https://cassim-prime.pages.dev/"),
}


def load(device_id: str) -> Device:
    """The device with this id. Its package is imported here, by name, and nowhere else in the
    shell, so a bundle holds only the devices it lists (`cassim.bundle`)."""
    if device_id not in SITES:
        msg = f"{device_id!r} is not a device"
        raise ValueError(msg)
    return import_module(f"cassim.devices.{device_id}").DEVICE
