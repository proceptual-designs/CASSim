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


# A web app cannot remove itself: the browser or the system does it, so Uninstall says how.
UNINSTALL_STEPS = (
    "A web app cannot remove itself; your device does it. Your saved documents stay in this "
    "browser until you clear the site's data.\n\n"
    "• Android: touch and hold the CASSim icon, then Uninstall (or App info, Uninstall).\n"
    "• Chrome or Edge on a computer: in the CASSim window, open the ⋮ menu, then Uninstall "
    "CASSim.\n"
    "• Chromebook: right-click CASSim in the launcher, then Uninstall.\n"
    "• iPhone or iPad: touch and hold the CASSim icon, then Remove App."
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
            title=ft.Text("About CASSim"),
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

    def __init__(self, page: ft.Page, device: Device) -> None:
        self.page = page
        self.device = device
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

    def _offers_changed(self) -> None:
        self.changed()  # looked up when called: the device's UI sets it after the shell is made

    def run_task(self, handler: Callable[..., Coroutine[Any, Any, Any]], *args: object) -> None:
        self.page.run_task(handler, *args)

    # ---- storage: texts by key, each device under its own prefix (FR-PROF-004) ---------------

    async def read(self, key: str) -> str | None:
        """The text saved under `key`. In the browser it is in IndexedDB; a text saved by an
        earlier build is still in localStorage and is read from there until it is next written."""
        full = self.device.storage + key
        if self.texts is not None:
            found = await self.texts.get(full)
            if found is not None:
                return found
        saved = await self.prefs.get(full)
        return saved if isinstance(saved, str) else None

    def write(self, key: str, text: str) -> None:
        full = self.device.storage + key
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
        full = self.device.storage + key

        async def drop() -> None:
            if self.texts is not None:
                await self.texts.delete(full)
            await self.prefs.remove(full)

        self.page.run_task(drop)

    # ---- the system clipboard -----------------------------------------------------------------

    def copy(self, text: str) -> None:
        self.page.run_task(self.clipboard.set, text)

    async def pasted(self) -> str:
        return await self.clipboard.get() or ""

    # ---- files --------------------------------------------------------------------------------

    async def save_file(self, name: str, text: str, title: str = "Save document") -> None:
        """Download `text` as a file (FR-DOC-004)."""
        await self.files.save_file(
            dialog_title=title, file_name=name, src_bytes=text.encode("utf-8")
        )

    async def pick_file(
        self, extensions: tuple[str, ...], title: str = "Open document"
    ) -> str | None:
        """The text of a file the user picks, or None when nothing is picked. A file that is not
        text raises UnicodeDecodeError."""
        picked = await self.files.pick_files(
            dialog_title=title,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=list(extensions),
            with_data=True,
        )
        if not picked or picked[0].bytes is None:
            return None
        return picked[0].bytes.decode("utf-8")

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

    def help(self) -> None:
        self.page.run_task(self.launcher.launch_url, about.WIKI_URL)

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
            bridge.installable,
            bridge.can_fullscreen,
            bridge.standalone,
            bridge.in_fullscreen,
            bridge.installed,
            bridge.touch,
            bridge.safe_area,
        )

    def install(self) -> None:
        if self.bridge is not None:
            self.bridge.install()

    def uninstall(self) -> None:
        """Doc > Uninstall CASSim: asks first, then shows how (no web API removes the app)."""

        async def show_steps() -> None:
            self.notice("Uninstall CASSim", UNINSTALL_STEPS)

        self.confirm(
            "Uninstall CASSim?",
            "CASSim stays usable in the browser at the same address.",
            "Continue",
            show_steps,
        )

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
        spec = self.device.engine
        if spec is None or sys.platform != "emscripten":
            return None
        from cassim.app.web import WorkerEngine  # noqa: PLC0415

        return WorkerEngine(spec.module)
