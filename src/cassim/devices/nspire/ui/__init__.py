"""The Nspire's Flet views. The shell imports this module by the name in `Device.ui` and calls
`mount`; nothing else in the device package imports Flet."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cassim.app.shell import Shell
    from cassim.devices.nspire.ui.app import App


def mount(shell: Shell) -> App:
    """The Nspire's app in `shell`; `await app.start()` opens it."""
    from cassim.devices.nspire.ui import app  # noqa: PLC0415  (Flet loads only when mounted)

    return app.mount(shell)
