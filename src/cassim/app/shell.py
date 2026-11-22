"""The shell: what belongs to the browser and the window, not to a calculator (decision 0032).

A device's UI is given one `Shell` when it is mounted and reaches the page, browser storage,
files, the clipboard, share links, notices, the About dialog, what the browser offers (install,
full screen) and its engine worker through it. The shell knows a device by its `Device` object
only; it never imports a device's package by name.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import flet as ft

from cassim import bundle
from cassim.app import about
from cassim.app.theme import DARK

if TYPE_CHECKING:
    from cassim.app.web import Bridge, TextStore
    from cassim.device.engine import Engine
    from cassim.devices import Device


@dataclass(frozen=True)
class BrowserOffers:
    """What the page reports the browser can do."""

    installable: bool = False
    can_fullscreen: bool = False
    standalone: bool = False  # already installed, or fullscreen
    in_fullscreen: bool = False
    installed: bool = False  # running as the installed app (not a fullscreen tab)
    touch: bool = False  # the main pointer is a finger: typing needs the on-screen keyboard
    safe_area: tuple[float, float, float, float] = (0, 0, 0, 0)  # top, right, bottom, left
    offline_state: str = "unsupported"
    offline_message: str = "Offline status is unavailable."
    offline_retry: bool = False
    update_ready: bool = False
    update_fetching: bool = False

    @property
    def update_label(self) -> str:
        if self.update_ready:
            return "Reload for Update"
        if self.update_fetching:
            return "Fetching Update"
        return "Check for Updates"

    @property
    def needs_attention(self) -> bool:
        return self.offline_state in ("unavailable", "update_failed") or self.update_ready


# A web app cannot remove itself: the browser or the system does it, so Uninstall says how.
UNINSTALL_STEPS = (
    "A web app cannot remove itself; your device does it. Your saved documents stay in this "
    "browser until you clear the site's data.\n\n"
    "• Android: touch and hold the {product} icon, then Uninstall (or App info, Uninstall).\n"
    "• Chrome or Edge on a computer: in the {product} window, open the ⋮ menu, then Uninstall "
    "{product}.\n"
    "• Chromebook: right-click {product} in the launcher, then Uninstall.\n"
    "• iPhone or iPad: touch and hold the {product} icon, then Remove App."
)

# CASSim > Check for Updates: what the page found, by its answer (see `checkUpdate` in
# tools/publish.py).
UPDATE_TITLE = "Check for Updates"
UPDATE_MESSAGES = {
    "downloading": (
        "A new version is downloading. Reload for Update will appear in the {product} menu."
    ),
    "ready": "A new version is ready. Choose Reload for Update in the {product} menu to use it.",
    "offline": "{product} could not reach its site. Check the connection and try again.",
    "unsupported": "This copy of {product} cannot check for updates.",
}


def update_message(result: str) -> str:
    if result == "current":
        version = dict(about.versions())["CASSim"]
        return f"{about.product_name()} {version} from {about.bundle.SOURCE} is up to date."
    return UPDATE_MESSAGES.get(result, UPDATE_MESSAGES["offline"]).format(
        product=about.product_name()
    )


def about_dialog(page: ft.Page) -> None:
    """About CASSim: disclaimer, privacy, licence, notices and versions (NFR-LEG-002, -003)."""

    def heading(text: str) -> ft.Text:
        return ft.Text(text, weight=ft.FontWeight.BOLD)

    notices = [ft.Text(f"{n.name}: {n.licence}, {n.use}", size=12) for n in about.NOTICES]
    body = ft.Column(
        [
            ft.Text(about.DISCLAIMER),
            heading("Privacy"),
            ft.Text(about.PRIVACY),
            heading("Licence"),
            ft.Text(about.LICENCE),
            ft.Text(f"Help: {about.WIKI_URL}", selectable=True),
            heading("Third-party notices"),
            *notices,
            heading("Version"),
            ft.Text(about.build_info(), selectable=True, size=12),
        ],
        tight=True,
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
        width=420,
    )
    page.show_dialog(
        ft.AlertDialog(
            title=ft.Text(f"About {about.product_name()}"),
            content=body,
            actions=[ft.TextButton("OK", on_click=lambda _: page.pop_dialog())],
        )
    )


def make_bridge(changed: Callable[[], None]) -> Bridge | None:
    """The channel to the page, in the browser only."""
    if sys.platform != "emscripten":
        return None
    from cassim.app.web import Bridge  # noqa: PLC0415

    return Bridge(changed)


def make_text_store() -> TextStore | None:
    """IndexedDB, in the browser only."""
    if sys.platform != "emscripten":
        return None
    from cassim.app.web import TextStore  # noqa: PLC0415

    return TextStore()


class Shell:
    """The browser's services for one mounted device."""

    def __init__(self, page: ft.Page, device: Device | None = None) -> None:
        self.page = page
        self.device = device
        self.available_devices: tuple[str, ...] = tuple(bundle.DEVICES)
        self.home: Callable[[], None] | None = None
        self.open_device_callback: Callable[[str], object] | None = None
        self.theme = DARK
        # Set by the device's UI: called when what the browser offers changes (Install appears).
        self.changed: Callable[[], None] = lambda: None
        self.bridge = make_bridge(self._offers_changed)
        self.clipboard = ft.Clipboard()
        self.files = ft.FilePicker()
        self.prefs = ft.SharedPreferences()
        self.launcher = ft.UrlLauncher()
        page.services.extend([self.clipboard, self.files, self.prefs, self.launcher])
        self.texts = make_text_store()  # IndexedDB in the browser; None on the desktop

    @property
    def active_device(self) -> Device:
        """The selected device; Home and shell services do not need one."""
        if self.device is None:
            msg = "no device is mounted"
            raise RuntimeError(msg)
        return self.device

    def select(self, device: Device) -> None:
        """Mount `device`'s storage namespace and engine behind this shell."""
        self.device = device

    def _offers_changed(self) -> None:
        self.changed()  # looked up when called: the device's UI sets it after the shell is made

    def run_task(self, handler: Callable[..., Coroutine[Any, Any, Any]], *args: object) -> None:
        self.page.run_task(handler, *args)

    # ---- storage: texts by key, each device under its own prefix (FR-PROF-004) ---------------

    async def read(self, key: str) -> str | None:
        """The text saved under `key`. In the browser it is in IndexedDB; a text saved by an
        earlier build is still in localStorage and is read from there until it is next written."""
        return await self.read_global(self.active_device.storage + key)

    async def read_global(self, full: str) -> str | None:
        """Read a shell-wide storage key without adding a device namespace."""
        if self.texts is not None:
            found = await self.texts.get(full)
            if found is not None:
                return found
        saved = await self.prefs.get(full)
        return saved if isinstance(saved, str) else None

    def write(self, key: str, text: str) -> None:
        self.write_global(self.active_device.storage + key, text)

    def write_global(self, full: str, text: str) -> None:
        """Write a shell-wide storage key without adding a device namespace."""
        if self.texts is None:
            self.page.run_task(self.prefs.set, full, text)
            return

        async def put() -> None:
            assert self.texts is not None
            await self.texts.put(full, text)
            await self.prefs.remove(full)  # the copy an earlier build left in localStorage

        self.page.run_task(put)

    def remove(self, key: str) -> None:
        """Forget the text saved under `key` (a deleted document)."""
        self.remove_global(self.active_device.storage + key)

    def remove_global(self, full: str) -> None:
        """Forget a shell-wide storage key."""

        async def drop() -> None:
            if self.texts is not None:
                await self.texts.delete(full)
            await self.prefs.remove(full)

        self.page.run_task(drop)

    async def remove_global_async(self, full: str) -> None:
        """Forget a shell-wide storage key and wait until it is persisted."""
        if self.texts is not None:
            await self.texts.delete(full)
        await self.prefs.remove(full)

    # ---- the system clipboard -----------------------------------------------------------------

    def copy(self, text: str) -> None:
        self.page.run_task(self.clipboard.set, text)

    async def pasted(self) -> str:
        return await self.clipboard.get() or ""

    # ---- files --------------------------------------------------------------------------------

    async def save_file(self, name: str, text: str, title: str = "Save document") -> None:
        """Download `text` as a file (FR-DOC-004)."""
        await self.save_bytes_file(name, text.encode("utf-8"), title)

    async def save_bytes_file(self, name: str, data: bytes, title: str) -> None:
        """Download a binary file through the platform's file picker."""
        await self.files.save_file(dialog_title=title, file_name=name, src_bytes=data)

    async def pick_file(
        self, extensions: tuple[str, ...], title: str = "Open document"
    ) -> str | None:
        """The text of a file the user picks, or None when nothing is picked. A file that is not
        text raises UnicodeDecodeError."""
        picked = await self.pick_file_bytes(extensions, title)
        return picked.decode("utf-8") if picked is not None else None

    async def pick_file_bytes(
        self, extensions: tuple[str, ...], title: str = "Open file"
    ) -> bytes | None:
        """The bytes of a file the user picks, or None when nothing is picked."""
        picked = await self.files.pick_files(
            dialog_title=title,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=list(extensions),
            with_data=True,
        )
        if not picked or picked[0].bytes is None:
            return None
        return picked[0].bytes

    # ---- links --------------------------------------------------------------------------------

    @property
    def route(self) -> str:
        """The page's address fragment: the hash URL strategy makes `#/doc=...` the route."""
        return self.page.route

    def link(self, fragment: str) -> str:
        """The address of this page with `fragment`, for a share link (FR-DOC-007)."""
        # the dev server reports a socket URL
        base = (self.page.url or "").partition("#")[0].replace("ws", "http", 1)
        return f"{base.rstrip('/')}/#/{fragment}"

    def help(self, page: str = "") -> None:
        """Open the help site at `page` (an app's own page, or the help home)."""
        self.page.run_task(self.launcher.launch_url, about.WIKI_URL + page)

    # ---- dialogs ------------------------------------------------------------------------------

    def notice(self, title: str, message: str) -> None:
        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text(title),
                content=ft.Text(message),
                actions=[ft.TextButton("OK", on_click=lambda _: self.page.pop_dialog())],
            )
        )

    def confirm(
        self, title: str, message: str, action: str, accept: Callable[[], Coroutine[Any, Any, None]]
    ) -> None:
        """Ask before doing `accept`; Cancel does nothing."""

        async def accepted() -> None:
            self.page.pop_dialog()
            await accept()

        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text(title),
                content=ft.Text(message),
                actions=[
                    ft.TextButton(action, on_click=lambda _: self.page.run_task(accepted)),
                    ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog()),
                ],
            )
        )

    def about(self) -> None:
        about_dialog(self.page)

    # ---- what the browser offers --------------------------------------------------------------

    @property
    def offers(self) -> BrowserOffers:
        bridge = self.bridge
        if bridge is None:
            return BrowserOffers()
        return BrowserOffers(
            installable=bridge.installable,
            can_fullscreen=bridge.can_fullscreen,
            standalone=bridge.standalone,
            in_fullscreen=bridge.in_fullscreen,
            installed=bridge.installed,
            touch=bridge.touch,
            safe_area=bridge.safe_area,
            offline_state=bridge.offline_state,
            offline_message=bridge.offline_message,
            offline_retry=bridge.offline_retry,
            update_ready=bridge.update_ready,
            update_fetching=getattr(bridge, "update_fetching", False),
        )

    @property
    def update_label(self) -> str:
        return self.offers.update_label

    def install(self) -> None:
        if self.bridge is not None:
            self.bridge.install()

    def retry_offline(self) -> None:
        if self.bridge is not None:
            self.bridge.retry_offline()

    def reload_update(self) -> None:
        if self.bridge is not None:
            self.bridge.reload_update()

    def uninstall(self) -> None:
        """CASSim > Uninstall: asks first, then shows how (no web API removes the app)."""

        async def show_steps() -> None:
            self.notice(
                f"Uninstall {about.product_name()}",
                UNINSTALL_STEPS.format(product=about.product_name()),
            )

        self.confirm(
            f"Uninstall {about.product_name()}?",
            f"{about.product_name()} stays usable in the browser at the same address.",
            "Continue",
            show_steps,
        )

    def check_for_updates(self) -> None:
        """Ask the server for a newer version and show the result."""
        bridge = self.bridge
        if bridge is None:
            self.notice(UPDATE_TITLE, update_message("unsupported"))
            return
        bridge.on_update = lambda result: self.notice(UPDATE_TITLE, update_message(result))
        bridge.check_update()

    def activate_update(self, reload: Callable[[], None] | None = None) -> None:
        """Check for an update, or run `reload` when one is already waiting."""
        if self.offers.update_ready:
            (reload or self.reload_update)()
        else:
            self.check_for_updates()

    def toggle_fullscreen(self) -> None:
        """Fullscreen, or back out of it while the page is fullscreen."""
        if self.bridge is not None:
            if self.bridge.in_fullscreen:
                self.bridge.exit_fullscreen()
            else:
                self.bridge.fullscreen()

    # ---- the engine ---------------------------------------------------------------------------

    def engine(self) -> Engine | None:
        """The device's engine in its own worker, in the browser (so Cancel can end it). None on
        the desktop, where the device runs its engine in this process."""
        spec = self.active_device.engine
        if spec is None or sys.platform != "emscripten":
            return None
        from cassim.app.web import WorkerEngine  # noqa: PLC0415

        return WorkerEngine(spec.module)
