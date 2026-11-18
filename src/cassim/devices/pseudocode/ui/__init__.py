"""Pseudocode Code view Flet UI."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cassim.app.shell import Shell
    from cassim.devices.pseudocode.ui.app import CodeApp


def mount(shell: Shell) -> CodeApp:
    from cassim.devices.pseudocode.ui import app  # noqa: PLC0415

    return app.mount(shell)
