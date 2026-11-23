"""CASSim fx scientific calculator Flet UI."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cassim.app.shell import Shell
    from cassim.devices.scientific.ui.app import ScientificApp


def mount(shell: Shell) -> ScientificApp:
    from cassim.devices.scientific.ui import app  # noqa: PLC0415

    return app.mount(shell)
