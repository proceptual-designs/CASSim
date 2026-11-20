"""Entry point: shell Home and lazy device mounting (FR-PROF-010 to FR-PROF-018)."""

from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path
from typing import Protocol, runtime_checkable

import flet as ft

from cassim import bundle, devices
from cassim.app.home import Home
from cassim.app.shell import Shell
from cassim.doc.share import PREFIX, unpack

ASSETS = Path(__file__).parent / "assets"
LAST_DEVICE_KEY = "cassim.shell.last_device"
APP_ROUTE_PARTS = 2


@runtime_checkable
class MountedApp(Protocol):
    """The part of a device UI that the shell controls."""

    async def start(self, **options: object) -> None: ...

    def unmount(self) -> None: ...


def shared_device(route: str) -> str | None:
    """Read only the device id from a share link; its document is not replayed."""
    fragment = route.lstrip("/")
    if not fragment.startswith(PREFIX):
        return None
    try:
        text = unpack(fragment)
        data = json.loads(text) if text is not None else None
    except TypeError, ValueError:
        return None
    found = data.get("device") if isinstance(data, dict) else None
    return found if isinstance(found, str) else None


def startup_device(
    route: str,
    saved: str | None,
    bundle_name: str,
    available: tuple[str, ...],
    requested: str | None = None,
) -> str | None:
    """Choose the device to open, or None for the Home screen."""
    if not available:
        msg = "the build contains no devices"
        raise RuntimeError(msg)
    direct = requested or direct_device(route)
    if direct in available:
        return direct
    shared = shared_device(route)
    if shared in available:
        return shared
    if route.lstrip("/").startswith("debug"):
        return available[0]
    if bundle_name != "all":
        return available[0]
    return saved if saved in available else None


def direct_device(route: str) -> str | None:
    """Read an app route such as `/app/pseudocode` or `/pseudocode`."""
    parts = [part for part in route.lstrip("/").split("/") if part]
    if not parts:
        return None
    return parts[1] if len(parts) == APP_ROUTE_PARTS and parts[0] == "app" else parts[0]


class Application:
    """Own the page and lazily switch between Home and one bundled device."""

    def __init__(
        self,
        page: ft.Page,
        *,
        options: dict[str, object] | None = None,
        shell: Shell | None = None,
        bundle_name: str = bundle.NAME,
        available: tuple[str, ...] = bundle.DEVICES,
    ) -> None:
        self.page = page
        self.options = options or {}
        self.shell = shell or Shell(page)
        self.bundle_name = bundle_name
        self.available = available
        self.shell.available_devices = available
        self.shell.home = self.request_home if bundle_name == "all" else None
        self.shell.open_device_callback = lambda device_id: self.page.run_task(
            self.open_device, device_id
        )
        self.active: MountedApp | None = None
        self.home: Home | None = None

    async def start(self) -> None:
        saved = await self.shell.read_global(LAST_DEVICE_KEY)
        url = getattr(self.page, "url", "") or ""
        route = url.partition("#")[2] if "#" in url else self.shell.route
        requested = self.options.get("app")
        selected = startup_device(
            route,
            saved,
            self.bundle_name,
            self.available,
            requested if isinstance(requested, str) else None,
        )
        if selected is None and self.options.get("app") is None and self.options:
            selected = self.available[0]
        if selected is None:
            await self.show_home()
        else:
            await self.open_device(selected, remember=self.bundle_name == "all")

    async def open_device(self, device_id: str, *, remember: bool = True) -> None:
        if device_id not in self.available:
            return
        if self.active is not None:
            self.active.unmount()
            self.active = None
        self.home = None
        self.page.controls.clear()
        device = devices.load(device_id)
        self.shell.select(device)
        ui = import_module(device.ui)
        mounted = ui.mount(self.shell)
        if not isinstance(mounted, MountedApp):
            msg = f"{device.ui}.mount() does not expose start() and unmount()"
            raise TypeError(msg)
        self.active = mounted
        await mounted.start(**self.options)
        if remember:
            self.shell.write_global(LAST_DEVICE_KEY, device_id)

    async def show_home(self) -> None:
        if self.active is not None:
            self.active.unmount()
            self.active = None
        self.shell.device = None
        self.home = Home(self.shell, lambda item: self.page.run_task(self.open_device, item))
        await self.home.start()

    def request_home(self) -> None:
        if self.bundle_name == "all" and self.active is not None:
            self.page.run_task(self.show_home)


async def main(page: ft.Page, **options: object) -> None:
    """Open Home or the selected/remembered device on `page`."""
    await Application(page, options=options).start()


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
