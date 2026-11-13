"""Entry point: `uv run flet run src/cassim/app/main.py` (or `python -m cassim.app.main`).

The shell (decision 0032 item 5). It reads which devices this build holds from `cassim.bundle`,
makes a `Shell` for the first of them and mounts that device's UI. With one device there is no
switcher (FR-PROF-003); the switcher comes with the second device.
"""

from __future__ import annotations

from importlib import import_module
from pathlib import Path

import flet as ft

from cassim import bundle, devices
from cassim.app.shell import Shell

ASSETS = Path(__file__).parent / "assets"


async def main(page: ft.Page, **options: object) -> None:
    """Open the app on `page`. `options` go to the device's UI (`view` and `settings` for the
    Nspire, from the command line)."""
    device = devices.load(bundle.DEVICES[0])
    ui = import_module(device.ui)
    await ui.mount(Shell(page, device)).start(**options)


def run(*, web: bool = False, **options: object) -> None:
    """Start the app in its own window, or in the default browser with `web` (`cassim --web`).
    `view` and `settings` come from `--view`, `--course` and `--set`."""

    async def start(page: ft.Page) -> None:
        await main(page, **options)

    ft.run(
        start,
        view=ft.AppView.WEB_BROWSER if web else ft.AppView.FLET_APP,
        route_url_strategy=ft.RouteUrlStrategy.HASH,
        assets_dir=str(ASSETS),
    )


if __name__ == "__main__":
    run()
