"""The Nspire's app: its state joined to its views, inside the shell (decision 0032 item 5).

Everything that belongs to the browser (storage, files, the clipboard, links, notices, install
and full screen, the engine worker) is reached through the `Shell` it is mounted with.
"""

from __future__ import annotations

import asyncio
import os
import time

import flet as ft

from cassim.app.shell import BrowserOffers, Shell
from cassim.core.settings import Settings, next_choice
from cassim.device.engine import LocalEngine, local_session
from cassim.device.keys import Binding, keypad_units
from cassim.device.menu import MenuItem
from cassim.device.wizard import Wizard
from cassim.devices.nspire.document import loads
from cassim.devices.nspire.pages import PAGES
from cassim.devices.nspire.pages.calculator import Calculator, calculator_of
from cassim.devices.nspire.runner import Runner, Status
from cassim.devices.nspire.ui.layout import (
    GAP,
    MARGIN,
    NARROW,
    PHONE_MARGIN,
    SCREEN_H,
    SCREEN_W,
    SPLITTER,
    STATUS_H,
    HandheldPlan,
    Sizing,
    clamp_share,
    computer_screen_height,
    handheld_plan,
    keypad_size,
    starting_mode,
)
from cassim.devices.nspire.ui.state import AppState, Mode, System
from cassim.devices.nspire.ui.views import (
    SYMBOL_FONT,
    SYMBOL_FONT_FILE,
    CalculatorView,
    Keypad,
    Sidebar,
    chip,
    settings_dialog,
    sorter_dialog,
    system_settings_dialog,
    wizard_dialog,
)
from cassim.doc.document import Document
from cassim.doc.serialize import (
    OPEN_EXTENSIONS,
    DocumentFileError,
    dumps,
    file_name,
    parse,
)
from cassim.doc.share import LinkTooLongError, encode, unpack

# TODO(M2b): a first visit should pick Handheld below about 700 px (decision 0013 item 3).
# Flet fires no resize event at start-up, so this needs a different hook.


# The keys of the two texts kept in browser storage, after the device's prefix (`cassim.`).
AUTOSAVE_KEY = "autosave"
SYSTEM_KEY = "system"
# The document is saved this long after the last change, not on every key (decision 0031): saving
# writes the whole document, and with sheet data that is too slow to do per key.
AUTOSAVE_DELAY = 0.5  # seconds


def browser_doc_items(*, handheld: bool, offers: BrowserOffers) -> tuple[MenuItem, ...]:
    """The Doc menu's last three items, always in this order so the keys never move (muscle
    memory): the view switch, Fullscreen and Install. One the browser cannot do is greyed,
    Fullscreen reads Exit Fullscreen while the page is fullscreen, and Install reads Uninstall in
    the installed app. Both views are offered on a phone too."""
    install = (
        MenuItem("Uninstall CASSim", "dialog", "uninstall", hint="CASSim")
        if offers.installed
        else MenuItem(
            "Install CASSim", "dialog", "install", hint="CASSim", enabled=offers.installable
        )
    )
    return (
        MenuItem(
            f"{'Computer' if handheld else 'Handheld'} view", "dialog", "switch_view", hint="CASSim"
        ),
        MenuItem(
            "Exit Fullscreen" if offers.in_fullscreen else "Fullscreen",
            "dialog",
            "fullscreen",
            hint="CASSim",
            enabled=offers.can_fullscreen and (offers.in_fullscreen or not offers.standalone),
        ),
        install,
    )


class App:
    """Wires the state to the views: the top bar, the screen, the keypad and the sidebar."""

    def __init__(self, shell: Shell, state: AppState, runner: Runner | None = None) -> None:
        page = shell.page
        self.shell = shell
        self.page = page
        self.state = state
        shell.changed = self.on_bridge  # the browser's offers changed
        self.runner = runner  # None: the maths runs in this process, synchronously
        self.status = ft.Text("", size=13, color="#ffd479")
        self.debug = "debug" in (page.url or "")  # `#/debug` prints results for the e2e tests
        self.shown: tuple[int, int] | None = None  # the page last drawn, for the debug PAGE line
        self.plan: HandheldPlan | None = None  # the last Handheld arrangement
        self.shape: tuple[Mode, bool, bool, bool, bool] | None = (
            None  # what the layout is built from
        )
        self.holder: ft.Container | None = None  # the splitter's box in a portrait layout
        self.resizing = False  # a splitter redraw is queued: further drag steps only add up
        self.first_visit = False  # nothing saved yet: the window size picks the mode
        self.starting = False  # loading the autosave through a remote engine
        self.theme = shell.theme
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
        self.frame = ft.Column([self.toolbar, self.layout], expand=True)
        # The margin round everything. Not `page.padding`: a change to that after start-up does
        # not reach the page, and a phone needs a thinner margin than a computer.
        self.outer = ft.Container(self.frame, padding=MARGIN, expand=True)
        state.clipboard_out = shell.copy  # copy and cut also fill the system clipboard
        state.show_dialog = self.show_dialog
        state.doc_extras = self.doc_extras
        state.show_wizard = self.show_wizard
        state.request_paste = self.request_paste
        self.typing_dialog: ft.AlertDialog | None = None  # its text boxes take the keyboard
        self.saved = ""  # the last text autosaved, so an idle refresh writes nothing
        self.save_at = 0.0  # when the waiting autosave runs (time.monotonic)
        self.save_waiting = False  # a save task is waiting for that time

    async def start(self, view: Mode | None = None, settings: Settings | None = None) -> None:
        """Open the app. `view` and `settings` (from the command line) override the saved view and
        the settings of the recovered document."""
        page = self.page
        page.title = "CASSim"
        page.fonts = {SYMBOL_FONT: SYMBOL_FONT_FILE}
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = self.theme.background
        page.padding = 0
        page.on_keyboard_event = self.on_key
        page.on_resize = self.on_resize
        page.on_app_lifecycle_state_change = self.on_lifecycle
        self.arrange()
        # The page's key event never reports Shift on its own, so a listener tracks it for
        # shift+click (decision 0019).
        page.add(
            ft.KeyboardListener(
                self.outer,
                autofocus=True,
                expand=True,
                on_key_down=lambda e: self.track_shift(e.key, down=True),
                on_key_up=lambda e: self.track_shift(e.key, down=False),
            )
        )
        print("CASSIM: UI", flush=True)  # the first screen is on its way (tools/loadtime.py)
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
        self.offer_shared(self.shell.route)
        print("CASSIM: READY", flush=True)

    def autosave(self) -> None:
        """Save the document AUTOSAVE_DELAY after the last change, so a reload or crash loses
        nothing (FR-DOC-003). Each change pushes the save back; one save task waits for it."""
        self.save_at = time.monotonic() + AUTOSAVE_DELAY
        if not self.save_waiting:
            self.save_waiting = True
            self.page.run_task(self.save_later)

    async def save_later(self) -> None:
        while (wait := self.save_at - time.monotonic()) > 0:
            await asyncio.sleep(wait)
        self.save_waiting = False
        self.save_now()

    def save_now(self) -> None:
        """Save the document at once, if it changed since the last save."""
        text = dumps(self.state.document)
        if text != self.saved:
            self.saved = text
            self.shell.write(AUTOSAVE_KEY, text)

    async def recover(self) -> None:
        """Reopen the saved System Settings and the autosaved document, if they are readable."""
        saved = await self.shell.read(SYSTEM_KEY)
        if saved is not None:
            self.state.system = System.loads(saved)
            # A phone opens in Handheld (Doc > Computer view switches for the session): the saved
            # start view defaults to Computer even where it was never chosen.
            self.state.mode = Mode.HANDHELD if self.phone else self.state.system.start_mode
            self.arrange()
        else:
            self.first_visit = True
            self.state.mode = starting_mode(self.page.width, self.page.height)
            self.arrange()
        text = await self.shell.read(AUTOSAVE_KEY)
        if text is None:
            return
        try:
            self.replace(await self.read(text))
            self.saved = text
            if self.debug:  # the end-to-end tests check what came back
                count = sum(len(problem.pages) for problem in self.state.document.problems)
                print(f"CASSIM: RECOVERED {count} pages", flush=True)
        except DocumentFileError:
            return  # a damaged autosave is ignored, and overwritten by the next change

    def refresh(self) -> None:
        start = time.perf_counter()
        self.state.prepare()  # a sheet takes the engine's replies first
        self.autosave()
        self.view.refresh()
        self.keypad.refresh()
        if self.state.mode is Mode.COMPUTER:  # the sidebar is not shown in Handheld
            self.sidebar.refresh()
        self.toolbar.controls = [*self.toolbar_controls(), self.status]
        built = time.perf_counter()
        self.page.update()
        self.view.follow_selection()
        if self.debug:  # tools/switchtime.py times a page change by this line (NFR-PERF-006)
            document = self.state.document
            here = (document.problem, document.page)
            if here != self.shown:
                self.shown = here
                build = (built - start) * 1000
                send = (time.perf_counter() - built) * 1000
                print(
                    f"CASSIM: PAGE {here[0] + 1}.{here[1] + 1} build={build:.0f} send={send:.0f}",
                    flush=True,
                )
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
        return loads(text) if self.runner is None else await self.runner.load(text, PAGES)

    def replace(self, document: Document) -> None:
        self.state.replace_document(document)
        if self.runner is not None:
            self.runner.retain(document)

    def kick(self) -> None:
        """Start whatever the engine owes the screen: a queued entry, or queued settings."""
        runner = self.runner
        if runner is None or not runner.idle:
            return
        calculator = calculator_of(self.state.document.current)
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
        """A key-up is lost when the window loses focus, so drop Shift then. A tab that is hidden
        may be closed without warning, so a waiting autosave is done at once."""
        if e.state is not ft.AppLifecycleState.RESUME:
            self.shift = False
        if e.state in (ft.AppLifecycleState.HIDE, ft.AppLifecycleState.PAUSE) and self.save_waiting:
            self.save_now()

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
            binding = Binding("paste", await self.shell.pasted())
        state.run(binding)
        self.refresh()

    def request_paste(self) -> None:
        self.page.run_task(self.paste_from_clipboard)

    async def paste_from_clipboard(self) -> None:
        """Paste the system clipboard into the entry line (the keypad's ctrl+v)."""
        self.state.paste_text(await self.shell.pasted())
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
        """A phone-sized window (its short side is narrow): it opens in Handheld, which has no
        splitter there and a thinner margin."""
        sides = [side for side in (self.page.width, self.page.height) if side]
        return bool(sides) and min(sides) < NARROW

    @property
    def installable(self) -> bool:
        """The browser has offered to install CASSim and it is not installed yet."""
        return self.shell.offers.installable

    def install(self) -> None:
        self.shell.install()

    def go_fullscreen(self) -> None:
        """Doc > Fullscreen, which reads Exit Fullscreen while the page is fullscreen."""
        self.shell.toggle_fullscreen()

    def on_bridge(self) -> None:
        """The page reported what the browser offers: the Install row may appear or go."""
        self.arrange()
        self.refresh()

    def doc_extras(self) -> tuple[MenuItem, ...]:
        """The Doc menu's last three items (see `browser_doc_items`)."""
        handheld = self.state.mode is Mode.HANDHELD
        return browser_doc_items(handheld=handheld, offers=self.shell.offers)

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
        elif name == "uninstall":
            self.shell.uninstall()
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
            self.shell.help()
        elif name == "about":
            self.shell.about()
        elif name == "page_sorter":
            sorter_dialog(self.page, self.state, self.refresh, self.theme)

    async def save_file(self) -> None:
        """Download the document as `.cassim.json` (FR-DOC-004, FR-DOC-006)."""
        document = self.state.document
        await self.shell.save_file(file_name(document), dumps(document))

    async def open_file(self) -> None:
        try:
            text = await self.shell.pick_file(OPEN_EXTENSIONS)
            if text is None:
                return
            self.replace(await self.read(text))
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
        self.shell.copy(self.shell.link(fragment))
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
            try:
                self.replace(await self.read(text))
            except DocumentFileError as error:
                self.notice("Cannot open that link", str(error))
            self.refresh()

        self.shell.confirm(
            "Open shared document?",
            f"“{name}” came from a link. It replaces what is open now; "
            "nothing in it runs until you run it.",
            "Open",
            accept,
        )

    def notice(self, title: str, message: str) -> None:
        self.shell.notice(title, message)

    def on_system_change(self) -> None:
        self.shell.write(SYSTEM_KEY, self.state.system.dumps())
        self.arrange()  # the letter layout changes the keypad's size
        self.refresh()

    def open_settings(self) -> None:
        settings_dialog(self.page, self.state, self.refresh, self.theme)

    def arrange(self) -> None:
        view = self.view.control
        state = self.state
        system = state.system
        phone = self.phone
        offer = self.installable and state.mode is Mode.HANDHELD
        self.keypad.install = (
            self.install if offer else None
        )  # Install takes the empty top-right cell
        if state.mode is Mode.HANDHELD:
            share = system.keypad_share or None  # 0 is auto; a phone always uses it
            margin = PHONE_MARGIN if phone else MARGIN
            self.outer.padding = margin
            self.frame.spacing = 0  # the toolbar holds only the status line
            plan = handheld_plan(
                self.page.width,
                self.page.height,
                keypad_units(state.keypad)[0],
                keypad_units(state.keypad)[1],
                Sizing(None if phone else share, system.zoom, STATUS_H, margin, not phone),
            )
            self.plan = plan
            state.scale, state.pad_scale = plan.scale, plan.pad_scale
            view.width, view.height = state.px(SCREEN_W), state.px(SCREEN_H)
            view.expand = False
            shape = (Mode.HANDHELD, plan.side_by_side, phone, system.zoom > 1, offer)
            if shape == self.shape:
                # Same structure: only the sizes change. Rebuilding the splitter mid-drag would end
                # the drag, which is why it used to stop after a few pixels.
                self.size_splitter(plan)
                return
            self.shape = shape
            parts: list[ft.Control] = [view, self.keypad.control]
            if not phone:  # the splitter is for a tablet or a projected window
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
            self.outer.padding = MARGIN
            self.frame.spacing = 10
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
            self.resize_soon()

        def reset(_: object) -> None:
            self.state.system.keypad_share = 0.0
            self.on_system_change()

        def done(_: object) -> None:
            self.shell.write(SYSTEM_KEY, self.state.system.dumps())

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

    def resize_soon(self) -> None:
        """Queue one redraw for the splitter. Drag steps arrive faster than the screen and keys
        can be rebuilt, and a redraw per step made the drag lag far behind the pointer; the steps
        that arrive while a redraw is queued or running only move the share."""
        if self.resizing:
            return
        self.resizing = True
        self.page.run_task(self.resize)

    async def resize(self) -> None:
        await asyncio.sleep(0)  # the drag steps already waiting are taken in first
        try:
            self.resize_now()
        finally:
            self.resizing = False

    def resize_now(self) -> None:
        """Redraw after a splitter step: only the part whose scale changed (often just the keys,
        since the screen is limited by the window's other side), and nothing else. The document
        has not changed, so there is no autosave, toolbar or sidebar work."""
        before = self.state.scale
        self.arrange()
        if self.state.scale != before:
            self.view.refresh()
        self.keypad.refresh()
        self.page.update()

    def size_splitter(self, plan: HandheldPlan) -> None:
        if self.holder is not None:
            across = keypad_size(*keypad_units(self.state.keypad))[0] * self.state.pad_scale
            self.holder.width = across


def mount(shell: Shell) -> App:
    """The Nspire's app in `shell`. In the browser the maths runs in the shell's engine worker (so
    Cancel can end it); on the desktop it stays in this process, unless `CASSIM_ENGINE=remote`
    asks for the same code path with a local engine."""
    engine = shell.engine()
    if engine is None and os.environ.get("CASSIM_ENGINE") == "remote":
        engine = LocalEngine()
    runner = None if engine is None else Runner(engine)
    state = AppState(sessions=local_session if runner is None else runner.new_session)
    return App(shell, state, runner)
