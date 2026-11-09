"""Entry point: `uv run flet run src/cassim/app/main.py` (or `python -m cassim.app.main`)."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import flet as ft

from cassim.app import about
from cassim.app.layout import (
    GAP,
    NARROW,
    SCREEN_H,
    SCREEN_W,
    SPLITTER,
    HandheldPlan,
    Sizing,
    clamp_share,
    computer_screen_height,
    handheld_plan,
    keypad_size,
    starting_mode,
)
from cassim.app.state import AppState, Mode, System
from cassim.app.theme import DARK
from cassim.app.ui import (
    SYMBOL_FONT,
    SYMBOL_FONT_FILE,
    CalculatorView,
    Keypad,
    Sidebar,
    about_dialog,
    chip,
    settings_dialog,
    sorter_dialog,
    system_settings_dialog,
    wizard_dialog,
)
from cassim.core.session import Session
from cassim.core.settings import Settings, next_choice
from cassim.device.calculator import Calculator
from cassim.device.document import Document
from cassim.device.engine import LocalEngine
from cassim.device.keys import Binding, keypad_units
from cassim.device.menu import MenuItem
from cassim.device.runner import Runner, Status
from cassim.device.serialize import DocumentFileError, dumps, loads, parse
from cassim.device.share import LinkTooLongError, encode, unpack
from cassim.device.wizard import Wizard

# TODO(M2b): a first visit should pick Handheld below about 700 px (decision 0013 item 3).
# Flet fires no resize event at start-up, so this needs a different hook.


if TYPE_CHECKING:
    from cassim.app.web import Bridge

ASSETS = Path(__file__).parent / "assets"
AUTOSAVE_KEY = "cassim.autosave"
SYSTEM_KEY = "cassim.system"


def connect_clipboard(page: ft.Page, state: AppState) -> ft.Clipboard:
    """Copy and cut also fill the system clipboard; paste reads it (see `Clipboard`)."""
    clipboard = ft.Clipboard()
    page.services.append(clipboard)

    def copy_out(text: str) -> None:
        page.run_task(clipboard.set, text)

    state.clipboard_out = copy_out
    return clipboard


@dataclass(frozen=True)
class BrowserOffers:
    """What the page reports the browser can do."""

    installable: bool = False
    can_fullscreen: bool = False
    standalone: bool = False  # already installed, or fullscreen
    in_fullscreen: bool = False


def browser_doc_items(
    *, handheld: bool, phone: bool, offers: BrowserOffers
) -> tuple[MenuItem, ...]:
    """The Doc menu's last three items, always in this order so the keys never move (muscle
    memory): the view switch, Fullscreen and Install. One the browser or device cannot do is
    greyed, and Fullscreen reads Exit Fullscreen while the page is fullscreen."""
    return (
        MenuItem(
            f"{'Computer' if handheld else 'Handheld'} view",
            "dialog",
            "switch_view",
            hint="CASSim",
            enabled=not phone,
        ),
        MenuItem(
            "Exit Fullscreen" if offers.in_fullscreen else "Fullscreen",
            "dialog",
            "fullscreen",
            hint="CASSim",
            enabled=offers.can_fullscreen and (offers.in_fullscreen or not offers.standalone),
        ),
        MenuItem("Install CASSim", "dialog", "install", hint="CASSim", enabled=offers.installable),
    )


class App:
    """Wires the state to the views: the top bar, the screen, the keypad and the sidebar."""

    def __init__(self, page: ft.Page, state: AppState, runner: Runner | None = None) -> None:
        self.page = page
        self.state = state
        self.bridge = make_bridge(self.on_bridge)  # the page, from the browser's worker
        self.runner = runner  # None: the maths runs in this process, synchronously
        self.status = ft.Text("", size=13, color="#ffd479")
        self.debug = "debug" in (page.url or "")  # `#/debug` prints results for the e2e tests
        self.plan: HandheldPlan | None = None  # the last Handheld arrangement
        self.shape: tuple[Mode, bool, bool, bool, bool] | None = (
            None  # what the layout is built from
        )
        self.holder: ft.Container | None = None  # the splitter's box in a portrait layout
        self.first_visit = False  # nothing saved yet: the window size picks the mode
        self.starting = False  # loading the autosave through a remote engine
        self.theme = DARK
        self.shift = False  # Flet sends no modifiers with a click, so remember the key
        self.view = CalculatorView(
            state, self.theme, self.act, lambda: self.shift, self.cycle_setting
        )
        self.keypad = Keypad(state, self.press, self.theme)
        self.sidebar = Sidebar(
            state, self.refresh, self.theme, lambda: self.act("open_menu", "menu")
        )
        self.toolbar = ft.Row(spacing=6, wrap=True)
        self.layout = ft.Container(expand=True)
        self.clipboard = connect_clipboard(page, state)
        state.show_dialog = self.show_dialog
        state.doc_extras = self.doc_extras
        state.show_wizard = self.show_wizard
        state.request_paste = self.request_paste
        self.typing_dialog: ft.AlertDialog | None = None  # its text boxes take the keyboard
        self.files = ft.FilePicker()
        page.services.append(self.files)
        self.prefs = ft.SharedPreferences()
        page.services.append(self.prefs)
        self.launcher = ft.UrlLauncher()
        page.services.append(self.launcher)
        self.saved = ""  # the last text autosaved, so an idle refresh writes nothing

    async def start(self, view: Mode | None = None, settings: Settings | None = None) -> None:
        """Open the app. `view` and `settings` (from the command line) override the saved view and
        the settings of the recovered document."""
        page = self.page
        page.title = "CASSim"
        page.fonts = {SYMBOL_FONT: SYMBOL_FONT_FILE}
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = self.theme.background
        page.padding = 12
        page.on_keyboard_event = self.on_key
        page.on_resize = self.on_resize
        page.on_app_lifecycle_state_change = self.on_lifecycle
        self.arrange()
        # The page's key event never reports Shift on its own, so a listener tracks it for
        # shift+click (decision 0019).
        page.add(
            ft.KeyboardListener(
                ft.Column([self.toolbar, self.layout], expand=True),
                autofocus=True,
                expand=True,
                on_key_down=lambda e: self.track_shift(e.key, down=True),
                on_key_up=lambda e: self.track_shift(e.key, down=False),
            )
        )
        if self.runner is not None:
            self.starting = True
            self.status.value = "Starting the calculator engine..."
        try:
            await self.recover()
        finally:
            self.starting = False
            self.status.value = ""
        if view is not None:
            self.state.mode = view
            self.arrange()
        if settings is not None:
            self.state.document.use(settings)
        self.refresh()
        self.offer_shared(self.page.route)
        print("CASSIM: READY", flush=True)

    def autosave(self) -> None:
        """Keep the document in browser storage so a reload or crash loses nothing (FR-DOC-003)."""
        text = dumps(self.state.document)
        if text != self.saved:
            self.saved = text
            self.page.run_task(self.prefs.set, AUTOSAVE_KEY, text)

    async def recover(self) -> None:
        """Reopen the saved System Settings and the autosaved document, if they are readable."""
        saved = await self.prefs.get(SYSTEM_KEY)
        if isinstance(saved, str):
            self.state.system = System.loads(saved)
            self.state.mode = self.state.system.start_mode
            self.arrange()
        else:
            self.first_visit = True
            self.state.mode = starting_mode(self.page.width, self.page.height)
            self.arrange()
        text = await self.prefs.get(AUTOSAVE_KEY)
        if not isinstance(text, str):
            return
        try:
            self.replace(await self.read(text))
            self.saved = text
        except DocumentFileError:
            return  # a damaged autosave is ignored, and overwritten by the next change

    def refresh(self) -> None:
        self.autosave()
        self.view.refresh()
        self.keypad.refresh()
        if self.state.mode is Mode.COMPUTER:  # the sidebar is not shown in Handheld
            self.sidebar.refresh()
        self.toolbar.controls = [*self.toolbar_controls(), self.status]
        self.page.update()
        self.view.follow_selection()
        self.kick()

    # ---- the engine -------------------------------------------------------------------------

    @property
    def busy(self) -> bool:
        return self.starting or (self.runner is not None and not self.runner.idle)

    @property
    def running(self) -> bool:
        """An entry is being calculated, so Esc can cancel it."""
        return self.runner is not None and self.runner.status is Status.BUSY

    async def read(self, text: str) -> Document:
        """A document from its text, replayed by whichever engine this app uses."""
        return loads(text) if self.runner is None else await self.runner.load(text)

    def replace(self, document: Document) -> None:
        self.state.replace_document(document)
        if self.runner is not None:
            self.runner.retain(document)

    def kick(self) -> None:
        """Start whatever the engine owes the screen: a queued entry, or queued settings."""
        runner = self.runner
        if runner is None or not runner.idle:
            return
        calculator = self.state.document.current.calculator
        if calculator is not None and calculator.pending is not None:
            self.page.run_task(self.run_pending, calculator)
        elif runner.dirty(self.state.document):
            self.page.run_task(self.run_sync)

    async def run_pending(self, calculator: Calculator) -> None:
        assert self.runner is not None
        self.status.value = "Calculating... press Esc to cancel"
        self.status.update()
        finished = await self.runner.evaluate(calculator)
        if self.debug:  # the end-to-end tests read the canvas app through the console
            history = calculator.history
            shown = history[-1].result.text if finished and history else ""
            print("CASSIM: RESULT " + shown if finished else "CASSIM: CANCELLED", flush=True)
        self.status.value = "" if finished else "Cancelled"
        self.refresh()

    async def run_sync(self) -> None:
        assert self.runner is not None
        await self.runner.sync(self.state.document)
        self.refresh()

    async def cancel(self) -> None:
        assert self.runner is not None
        self.status.value = "Cancelling... restarting the calculator"
        self.status.update()
        await self.runner.cancel()
        self.status.value = ""
        if self.debug:
            print("CASSIM: RESTARTED", flush=True)
        self.refresh()

    def press(self, name: str) -> None:
        if self.busy:
            if name == "esc" and self.running:
                self.page.run_task(self.cancel)
            return
        self.state.press_keypad(name)
        self.refresh()

    def on_lifecycle(self, e: ft.AppLifecycleStateChangeEvent) -> None:
        """A key-up is lost when the window loses focus, so drop Shift then."""
        if e.state is not ft.AppLifecycleState.RESUME:
            self.shift = False

    def track_shift(self, key: str, *, down: bool) -> None:
        if "shift" in key.lower():
            self.shift = down

    def show_wizard(self, wizard: Wizard) -> None:
        self.typing_dialog = wizard_dialog(self.page, self.state, wizard, self.refresh)

    async def on_key(self, e: ft.KeyboardEvent) -> None:
        state = self.state
        if self.typing_dialog is not None and self.typing_dialog.open:
            return  # keys typed into a dialog's boxes are not calculator keys
        self.shift = e.shift
        binding = state.binding_for(e.key, shift=e.shift, ctrl=e.ctrl, alt=e.alt, meta=e.meta)
        if binding is None:
            return
        if self.busy:  # only Esc gets through: it cancels the run
            if binding.action == "escape" and self.running:
                await self.cancel()
            return
        if binding.action == "paste":  # the system clipboard may hold text from elsewhere
            binding = Binding("paste", await self.clipboard.get() or "")
        state.run(binding)
        self.refresh()

    def request_paste(self) -> None:
        self.page.run_task(self.paste_from_clipboard)

    async def paste_from_clipboard(self) -> None:
        """Paste the system clipboard into the entry line (the keypad's ctrl+v)."""
        self.state.paste_text(await self.clipboard.get() or "")
        self.refresh()

    def act(self, action: str, arg: str = "") -> None:
        if self.busy:
            return
        self.state.run_action(action, arg)
        self.refresh()

    def cycle_setting(self, name: str) -> None:
        """A click on Rad/Deg, Auto/Approx or Real/Rect/Polar in the title bar."""
        if self.busy:
            return
        self.state.document.set(**{name: next_choice(self.state.document.settings, name)})
        self.refresh()

    def on_resize(self, e: ft.PageResizeEvent) -> None:
        """Keep the layout fitted to the window; a first visit follows its size until chosen."""
        if self.first_visit:
            self.state.mode = starting_mode(e.width, e.height)
        self.arrange()
        self.refresh()

    @property
    def phone(self) -> bool:
        """A phone-sized window (its short side is narrow): only Handheld mode is usable there."""
        sides = [side for side in (self.page.width, self.page.height) if side]
        return bool(sides) and min(sides) < NARROW

    @property
    def installable(self) -> bool:
        """The browser has offered to install CASSim and it is not installed yet."""
        return self.bridge is not None and self.bridge.installable

    def install(self) -> None:
        if self.bridge is not None:
            self.bridge.install()

    def go_fullscreen(self) -> None:
        """Doc > Fullscreen, which reads Exit Fullscreen while the page is fullscreen."""
        if self.bridge is not None:
            if self.bridge.in_fullscreen:
                self.bridge.exit_fullscreen()
            else:
                self.bridge.fullscreen()

    def on_bridge(self) -> None:
        """The page reported what the browser offers: the Install row may appear or go."""
        self.arrange()
        self.refresh()

    def doc_extras(self) -> tuple[MenuItem, ...]:
        """The Doc menu's last three items (see `browser_doc_items`)."""
        bridge = self.bridge
        return browser_doc_items(
            handheld=self.state.mode is Mode.HANDHELD,
            phone=self.phone,
            offers=BrowserOffers(
                self.installable,
                bridge is not None and bridge.can_fullscreen,
                bridge is not None and bridge.standalone,
                bridge is not None and bridge.in_fullscreen,
            ),
        )

    def toggle_keypad(self) -> None:
        """Show or hide the keypad beside the screen in Computer mode (kept with the settings)."""
        system = self.state.system
        system.computer_keypad = not system.computer_keypad
        self.arrange()
        self.on_system_change()

    def set_mode(self, mode: Mode) -> None:
        self.first_visit = False
        self.state.mode = mode
        self.arrange()
        self.refresh()

    def toolbar_controls(self) -> list[ft.Control]:
        theme, mode = self.theme, self.state.mode
        if mode is Mode.HANDHELD:
            return []  # the keypad's Doc and Menu keys do everything (Install sits above the keys)
        return [
            chip("Handheld", lambda: self.set_mode(Mode.HANDHELD), theme, on=mode is Mode.HANDHELD),
            chip("Computer", lambda: self.set_mode(Mode.COMPUTER), theme, on=mode is Mode.COMPUTER),
            *(
                [chip("Keypad", self.toggle_keypad, theme, on=self.state.system.computer_keypad)]
                if mode is Mode.COMPUTER
                else []
            ),
            chip("◀ page", lambda: self.act("prev_page"), theme),
            chip("page ▶", lambda: self.act("next_page"), theme),
            chip("+ page", lambda: self.act("add_page"), theme),
            chip("+ problem", lambda: self.act("add_problem"), theme),
            chip("delete page", lambda: self.act("delete_page"), theme),
            chip("Doc", lambda: self.act("open_menu", "doc"), theme),
            chip("Sorter", lambda: self.show_dialog("page_sorter"), theme),
            chip("settings", self.open_settings, theme),
            chip("Help", lambda: self.show_dialog("help"), theme),
            chip("About", lambda: self.show_dialog("about"), theme),
            *([chip("Install", self.install, theme)] if self.installable else []),
        ]

    def show_dialog(self, name: str) -> None:
        if name == "fullscreen":
            self.go_fullscreen()
        elif name == "install":
            self.install()
        elif name == "switch_view":
            self.set_mode(Mode.COMPUTER if self.state.mode is Mode.HANDHELD else Mode.HANDHELD)
        elif name == "save_file":
            self.page.run_task(self.save_file)
        elif name == "open_file":
            self.page.run_task(self.open_file)
        elif name == "share_link":
            self.share_link()
        elif name == "document_settings":
            self.open_settings()
        elif name == "system_settings":
            system_settings_dialog(self.page, self.state, self.on_system_change, self.theme)
        elif name == "help":
            self.page.run_task(self.launcher.launch_url, about.WIKI_URL)
        elif name == "about":
            about_dialog(self.page)
        elif name == "page_sorter":
            sorter_dialog(self.page, self.state, self.refresh, self.theme)

    async def save_file(self) -> None:
        """Download the document as `.cassim.json` (FR-DOC-004)."""
        document = self.state.document
        await self.files.save_file(
            dialog_title="Save document",
            file_name=f"{document.name}.cassim.json",
            src_bytes=dumps(document).encode("utf-8"),
        )

    async def open_file(self) -> None:
        picked = await self.files.pick_files(
            dialog_title="Open document",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["json"],
            with_data=True,
        )
        if not picked or picked[0].bytes is None:
            return
        try:
            self.replace(await self.read(picked[0].bytes.decode("utf-8")))
        except (DocumentFileError, UnicodeDecodeError) as error:
            self.notice("Cannot open that file", str(error))
        self.refresh()

    def share_link(self) -> None:
        """Copy a link that holds the document in its fragment (FR-DOC-007)."""
        try:
            fragment = encode(self.state.document)
        except LinkTooLongError as error:
            self.notice("Too big for a link", f"{error}. Use Doc > File > Save to file instead.")
            return
        # the dev server reports a socket URL
        base = (self.page.url or "").partition("#")[0].replace("ws", "http", 1)
        self.page.run_task(self.clipboard.set, f"{base.rstrip('/')}/#/{fragment}")
        self.notice("Link copied", "Anyone with the link can open this document. Nothing is sent.")

    def offer_shared(self, fragment: str) -> None:
        """A page opened from a share link asks before replacing the document (FR-DOC-007). The
        hash URL strategy makes the fragment `/doc=...` the page's route."""
        try:
            text = unpack(fragment.lstrip("/"))
            name = "Untitled" if text is None else str(parse(text).get("name", "Untitled"))
        except DocumentFileError as error:
            self.notice("Cannot open that link", str(error))
            return
        if text is None:
            return

        async def accept() -> None:
            self.page.pop_dialog()
            try:
                self.replace(await self.read(text))
            except DocumentFileError as error:
                self.notice("Cannot open that link", str(error))
            self.refresh()

        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Open shared document?"),
                content=ft.Text(
                    f"“{name}” came from a link. It replaces what is open now; "
                    "nothing in it runs until you run it."
                ),
                actions=[
                    ft.TextButton("Open", on_click=lambda _: self.page.run_task(accept)),
                    ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog()),
                ],
            )
        )

    def notice(self, title: str, message: str) -> None:
        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text(title),
                content=ft.Text(message),
                actions=[ft.TextButton("OK", on_click=lambda _: self.page.pop_dialog())],
            )
        )

    def on_system_change(self) -> None:
        self.page.run_task(self.prefs.set, SYSTEM_KEY, self.state.system.dumps())
        self.arrange()  # the letter layout changes the keypad's size
        self.refresh()

    def open_settings(self) -> None:
        settings_dialog(self.page, self.state, self.refresh, self.theme)

    def arrange(self) -> None:
        view = self.view.control
        state = self.state
        system = state.system
        if self.phone:
            state.mode = Mode.HANDHELD  # Computer mode is not usable on a phone
        offer = self.installable and state.mode is Mode.HANDHELD
        self.keypad.install = (
            self.install if offer else None
        )  # Install takes the empty top-right cell
        if state.mode is Mode.HANDHELD:
            share = system.keypad_share or None  # 0 is auto; a phone always uses it
            plan = handheld_plan(
                self.page.width,
                self.page.height,
                keypad_units(state.keypad)[0],
                keypad_units(state.keypad)[1],
                Sizing(
                    None if self.phone else share,
                    system.zoom,
                    0,
                ),
            )
            self.plan = plan
            state.scale, state.pad_scale = plan.scale, plan.pad_scale
            view.width, view.height = state.px(SCREEN_W), state.px(SCREEN_H)
            view.expand = False
            shape = (Mode.HANDHELD, plan.side_by_side, self.phone, system.zoom > 1, offer)
            if shape == self.shape:
                # Same structure: only the sizes change. Rebuilding the splitter mid-drag would end
                # the drag, which is why it used to stop after a few pixels.
                self.size_splitter(plan)
                return
            self.shape = shape
            parts: list[ft.Control] = [view, self.keypad.control]
            if not self.phone:  # the splitter is for a tablet or a projected window
                parts.insert(1, self.splitter(plan))
            gap = GAP / 2
            self.layout.alignment = ft.Alignment.CENTER
            self.layout.content = (
                ft.Row(parts, spacing=gap, alignment=ft.MainAxisAlignment.CENTER)
                if plan.side_by_side
                else ft.Column(
                    parts,
                    spacing=gap,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
            if system.zoom > 1:  # zoomed past the window: scroll rather than clip
                self.layout.content = ft.Column(
                    [ft.Row([self.layout.content], scroll=ft.ScrollMode.AUTO)],
                    scroll=ft.ScrollMode.AUTO,
                )
        else:
            self.shape = None
            state.scale = state.pad_scale = system.zoom
            self.layout.alignment = None
            view.width = None
            view.expand = True
            # A fixed height from the window: the screen otherwise shrinks to its lines, and a
            # menu drawn on it would be clipped.
            view.height = computer_screen_height(self.page.height)
            parts: list[ft.Control] = [
                ft.Container(self.sidebar.control, width=170, padding=8),
                view,
            ]
            if state.system.computer_keypad:
                parts.append(ft.Column([self.keypad.control], scroll=ft.ScrollMode.AUTO))
            self.layout.content = ft.Row(
                parts, expand=True, spacing=12, vertical_alignment=ft.CrossAxisAlignment.START
            )

    def splitter(self, plan: HandheldPlan) -> ft.Control:
        """The bar between the screen and the keypad: drag it to give the screen or the keys more
        of the window, double-click it to go back to the default (kept with the settings)."""
        side = plan.side_by_side
        theme = self.theme
        grip = ft.Container(
            width=4 if side else 48,
            height=48 if side else 4,
            border_radius=2,
            bgcolor=theme.key_label,
        )

        def drag(e: ft.DragUpdateEvent) -> None:
            if e.global_delta is None or self.plan is None:
                return
            delta = e.global_delta.x if self.plan.side_by_side else e.global_delta.y
            # The keypad is on the right or at the bottom, so dragging towards the screen grows it.
            room = self.plan.extent * max(self.state.system.zoom, 0.01)
            current = self.state.system.keypad_share or self.plan.share
            self.state.system.keypad_share = clamp_share(current - delta / room)
            self.arrange()
            self.refresh()

        def reset(_: object) -> None:
            self.state.system.keypad_share = 0.0
            self.on_system_change()

        def done(_: object) -> None:
            self.page.run_task(self.prefs.set, SYSTEM_KEY, self.state.system.dumps())

        bar = ft.Container(
            grip,
            alignment=ft.Alignment.CENTER,
            width=SPLITTER if side else None,
            height=None if side else SPLITTER,
            tooltip="Drag to resize the keypad; double-click to reset",
        )
        detector = ft.GestureDetector(
            bar,
            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT
            if side
            else ft.MouseCursor.RESIZE_UP_DOWN,
            on_double_tap=reset,
            drag_interval=30,
            on_horizontal_drag_update=drag if side else None,
            on_horizontal_drag_end=done if side else None,
            on_vertical_drag_update=None if side else drag,
            on_vertical_drag_end=None if side else done,
        )
        if side:
            self.holder = None
            return detector
        self.holder = ft.Container(detector)  # a column would shrink the bar to its grip
        self.size_splitter(plan)
        return self.holder

    def size_splitter(self, plan: HandheldPlan) -> None:
        if self.holder is not None:
            across = keypad_size(*keypad_units(self.state.keypad))[0] * self.state.pad_scale
            self.holder.width = across


def make_bridge(changed: Callable[[], None]) -> Bridge | None:
    """The channel to the page, in the browser only."""
    if sys.platform != "emscripten":
        return None
    from cassim.app.web import Bridge  # noqa: PLC0415

    return Bridge(changed)


def make_runner() -> Runner | None:
    """The browser runs the maths in its own worker (so Cancel can end it); on the desktop it
    stays in this process unless `CASSIM_ENGINE=remote` asks for the same code path."""
    if sys.platform == "emscripten":
        from cassim.app.web import WorkerEngine  # noqa: PLC0415

        return Runner(WorkerEngine())
    if os.environ.get("CASSIM_ENGINE") == "remote":
        return Runner(LocalEngine())
    return None


async def main(page: ft.Page, view: Mode | None = None, settings: Settings | None = None) -> None:
    runner = make_runner()
    state = AppState(sessions=Session if runner is None else runner.new_session)
    await App(page, state, runner).start(view, settings)


def run(*, web: bool = False, view: Mode | None = None, settings: Settings | None = None) -> None:
    """Start the app in its own window, or in the default browser with `web` (`cassim --web`).
    `view` and `settings` come from `--view`, `--course` and `--set`."""

    async def start(page: ft.Page) -> None:
        await main(page, view, settings)

    ft.run(
        start,
        view=ft.AppView.WEB_BROWSER if web else ft.AppView.FLET_APP,
        route_url_strategy=ft.RouteUrlStrategy.HASH,
        assets_dir=str(ASSETS),
    )


if __name__ == "__main__":
    run()
