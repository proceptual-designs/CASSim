"""The Nspire's app: its state joined to its views, inside the shell (decision 0032 item 5).

Everything that belongs to the browser (storage, files, the clipboard, links, notices, install
and full screen, the engine worker) is reached through the `Shell` it is mounted with.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import time
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime

import flet as ft

from cassim.app import about
from cassim.app.shell import BrowserOffers, Shell
from cassim.app.theme import themed
from cassim.core.results import VariableInfo
from cassim.core.settings import Settings, next_choice
from cassim.device.editor import Editor
from cassim.device.engine import LocalEngine, RemoteSession, local_session
from cassim.device.keys import Action, Binding, keypad_units
from cassim.device.menu import MenuItem
from cassim.device.pointer import Pointer
from cassim.device.wizard import Wizard
from cassim.devices.nspire.document import loads
from cassim.devices.nspire.pages import PAGES
from cassim.devices.nspire.pages.calculator import Calculator, Pending, calculator_of
from cassim.devices.nspire.runner import Runner, Status
from cassim.devices.nspire.ui.keypad import STICK_KEY, Keypad
from cassim.devices.nspire.ui.layout import (
    COMPUTER_SPLITTER,
    FULL_RESERVE,
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
    computer_columns,
    computer_screen_height,
    full_screen_height,
    handheld_plan,
    keypad_size,
    starting_mode,
)
from cassim.devices.nspire.ui.sidebar import Sidebar
from cassim.devices.nspire.ui.soft_keys import SENTINEL, TYPING_ACTIONS, keys_for
from cassim.devices.nspire.ui.state import (
    COMPUTER_MAX_SIDEBAR,
    COMPUTER_MIN_SIDEBAR,
    SORTER,
    AppState,
    Mode,
    System,
)
from cassim.devices.nspire.ui.theme_settings import theme_settings_dialog
from cassim.devices.nspire.ui.views import (
    POINTER_TICK,
    SYMBOL_FONT,
    SYMBOL_FONT_FILE,
    CalculatorView,
    label_text,
    settings_dialog,
    system_settings_dialog,
    wizard_dialog,
)
from cassim.doc.document import Document
from cassim.doc.library import (
    CURRENT_KEY,
    UNTITLED,
    Current,
    Store,
    clean_name,
    document_fingerprint,
    fingerprint,
    title,
)
from cassim.doc.serialize import (
    OPEN_EXTENSIONS,
    DocumentFileError,
    dumps,
    file_name,
    parse,
    to_dict,
)
from cassim.doc.share import LinkTooLongError, encode, unpack
from cassim.sheet.fileio import read_csv, read_xlsx, write_csv, write_xlsx

# TODO(M2b): a first visit should pick Handheld below about 700 px (decision 0013 item 3).
# Flet fires no resize event at start-up, so this needs a different hook.


TITLE_H = 20  # the screen's title bar, in the handheld's pixels
COMPUTER_PANEL_NAMES = {
    "sidebar": "Controls and pages",
    "workspace": "Calculation",
    "keypad": "Keypad",
}

# The keys of the two texts kept in browser storage, after the device's prefix (`cassim.`).
AUTOSAVE_KEY = "autosave"
SYSTEM_KEY = "system"
# The document is saved this long after the last change, not on every key (decision 0031): saving
# writes the whole document, and with sheet data that is too slow to do per key.
AUTOSAVE_DELAY = 0.5  # seconds
FLASH_SECONDS = 2.0  # how long a note such as "Saved" stays in the status line


@dataclass(frozen=True)
class VariableDeletion:
    calculator: Calculator
    sources: tuple[str, ...]
    names: tuple[str, ...]


def browser_menu_items(
    *, handheld: bool, offers: BrowserOffers, phone: bool = False, use_cutout: bool = True
) -> tuple[MenuItem, ...]:
    """The CASSim menu's browser items, always in this order so the keys never move (muscle
    memory): the view switch, Fullscreen, Install and Check for Updates. One the browser cannot
    do is greyed, Fullscreen reads Exit Fullscreen while the page is fullscreen; on an installed
    phone it toggles the cutout instead. Install reads Uninstall in the installed app. A phone
    has only Handheld view, so the view switch is greyed there."""
    cutout_toggle = phone and handheld and offers.installed
    product = about.product_name()
    install = (
        MenuItem(f"Uninstall {product}", "dialog", "uninstall")
        if offers.installed
        else MenuItem(f"Install {product}", "dialog", "install", enabled=offers.installable)
    )
    return (
        MenuItem(
            f"{'Computer' if handheld else 'Handheld'} view",
            "dialog",
            "switch_view",
            hint="Alt+Shift+C" if handheld else "Alt+Shift+H",
            enabled=not phone,
        ),
        MenuItem(
            ("Avoid cutout" if use_cutout else "Use cutout")
            if cutout_toggle
            else ("Exit Fullscreen" if offers.in_fullscreen else "Fullscreen"),
            "dialog",
            "fullscreen",
            enabled=cutout_toggle
            or (offers.can_fullscreen and (offers.in_fullscreen or not offers.standalone)),
        ),
        install,
        MenuItem("Check for Updates…", "dialog", "check_updates"),
    )


def cassim_items(
    *, handheld: bool, offers: BrowserOffers, phone: bool = False, use_cutout: bool = True
) -> tuple[MenuItem, ...]:
    """App actions and browser status, shared by both CASSim menu entry points."""
    status = {
        "checking": "Offline: Preparing",
        "ready": "Offline: Ready",
        "unavailable": "Offline: Unavailable",
        "update_failed": "Update failed",
        "unsupported": "Offline: Unknown",
    }.get(offers.offline_state, "Offline: Unknown")
    return (
        *browser_menu_items(handheld=handheld, offers=offers, phone=phone, use_cutout=use_cutout),
        MenuItem(status, "dialog", "offline_status", hint=offers.offline_message),
        *(
            (MenuItem("Retry offline / update", "dialog", "retry_offline"),)
            if offers.offline_retry
            else ()
        ),
        *((MenuItem("Reload update…", "dialog", "reload_update"),) if offers.update_ready else ()),
        MenuItem("Help (wiki)…", "dialog", "help", hint="F1"),
        MenuItem(f"About {about.product_name()}…", "dialog", "about"),
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
        self.sheet_line = ""  # the debug SHEET line last printed
        self.plan: HandheldPlan | None = None  # the last Handheld arrangement
        self.shape: tuple[Mode, bool, bool, bool, bool] | None = (
            None  # what the layout is built from
        )
        self.holder: ft.Container | None = None  # the splitter's box in a portrait layout
        self.resizing = False  # a splitter redraw is queued: further drag steps only add up
        self.first_visit = False  # nothing saved yet: the window size picks the mode
        self.use_cutout = True
        self.starting = False  # loading the autosave through a remote engine
        self.sheet_file_busy = False
        self.theme = shell.theme
        self.shift = False  # Flet sends no modifiers with a click, so remember the key
        self.view = CalculatorView(
            state, self.theme, self.act, lambda: self.shift, self.cycle_setting
        )
        self.view.body_size = self.body_size
        self.pointer = Pointer()  # steered by the keypad's centre key
        self.ticking = False  # the pointer's timer is running
        self.keypad = Keypad(
            state, self.press, self.theme, on_cassim=self.press_cassim, on_stick=self.on_stick
        )
        self.sidebar = Sidebar(
            state,
            self.refresh,
            self.theme,
            on_delete=self.delete_variables,
        )
        self.toolbar = ft.Column(spacing=4)
        self.layout = ft.Container(expand=True)
        self.computer_panels: dict[str, ft.Container] = {}
        self.computer_row: ft.Row | None = None
        self.dragged_boundary: tuple[str, str] | None = None
        # Computer view on a phone or tablet: a hidden text box in the toolbar row takes the
        # focus when typing is expected, so the on-screen keyboard opens (see soft_keys)
        self.sink = ft.TextField(
            value=SENTINEL,
            autocorrect=False,
            enable_suggestions=False,
            on_change=self.on_sink,
            on_submit=self.on_sink_submit,
            on_focus=lambda _: setattr(self, "sink_focused", True),
            on_blur=lambda _: setattr(self, "sink_focused", False),
        )
        self.sink_focused = False
        self.sink_box = ft.Container(self.sink, width=1, height=1, opacity=0)
        self.frame = ft.Column([self.toolbar, self.layout], expand=True)
        # Handheld in full screen or the installed app: the screen fills the height, there is no
        # toolbar row, and a status message (Calculating..., Saved) shows in the title bar
        self.full = False
        # The margin round everything. Not `page.padding`: a change to that after start-up does
        # not reach the page, and a phone needs a thinner margin than a computer.
        self.outer = ft.Container(self.frame, padding=MARGIN, expand=True)
        self._wire_state(shell, state)
        self.variable_undo: list[VariableDeletion] = []
        self.variable_redo: list[VariableDeletion] = []
        state.ask_discard = self.ask_discard
        state.on_new_document = self.on_new_document

    def _wire_state(self, shell: Shell, state: AppState) -> None:
        state.clipboard_out = shell.copy  # copy and cut also fill the system clipboard
        state.show_dialog = self.show_dialog
        state.cassim_menu = self.cassim_menu
        state.show_wizard = self.show_wizard
        state.request_paste = self.request_paste
        self.typing_dialog: ft.AlertDialog | None = None  # its text boxes take the keyboard
        self.saved = ""  # the last text autosaved, so an idle refresh writes nothing
        self.save_at = 0.0  # when the waiting autosave runs (time.monotonic)
        self.save_waiting = False  # a save task is waiting for that time
        # Documents saved by name in this browser (FR-DOC-010), and the open one's link to them
        self.library = Store(shell.read, shell.write, shell.remove)
        self.current = Current(None, document_fingerprint(state.document))
        self.dirty = False  # the document differs from its saved copy (or has none)

    async def start(self, view: Mode | None = None, settings: Settings | None = None) -> None:
        """Open the app. `view` and `settings` (from the command line) override the saved view and
        the settings of the recovered document."""
        page = self.page
        page.title = about.product_name()
        page.fonts = {SYMBOL_FONT: SYMBOL_FONT_FILE}
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = self.theme.background
        page.padding = 0
        page.on_keyboard_event = self.on_key
        page.on_resize = self.on_resize
        page.on_app_lifecycle_state_change = self.on_lifecycle
        # Pick the view before the first draw, so the page never shows one view and then swaps
        await self.recover_system()
        self.apply_theme()
        if view is not None:
            self.state.mode = view
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
        if self.state.system.theme_error:
            self.notice("Appearance settings", self.state.system.theme_error)
        print("CASSIM: UI", flush=True)  # the first screen is on its way (tools/loadtime.py)
        if self.runner is not None:
            self.starting = True
            self.status.value = "Starting the calculator engine..."
        try:
            await self.recover()
        finally:
            self.starting = False
            self.status.value = ""
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
        """Autosave the document at once, if it changed since the last autosave, and update the
        unsaved-changes marker. This is the working state only: the named copy changes only on
        Save (FR-DOC-010)."""
        data = to_dict(self.state.document)
        text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        if text != self.saved:
            self.saved = text
            self.shell.write(AUTOSAVE_KEY, text)
        self.mark(fingerprint(data))

    def mark(self, printed: str) -> None:
        """Show whether the document (with fingerprint `printed`) has unsaved changes."""
        dirty = printed != self.current.saved
        if dirty != self.dirty:
            self.dirty = dirty
            self.state.doc_title = self.doc_title()
            self.view.set_doc_title(self.state.doc_title)
            self.page.update()

    def doc_title(self) -> str:
        """The title bar's middle: the document's name, or in full screen (no toolbar row) a
        status message while there is one."""
        if self.full and self.status.value:
            return str(self.status.value)
        return title(self.state.document.name, dirty=self.dirty)

    def remember(self, current: Current) -> None:
        """Link the open document to its saved copy (or to none) and keep that with the
        autosave, so the name and the marker survive a reload."""
        self.current = current
        self.shell.write(CURRENT_KEY, current.dumps())
        self.dirty = document_fingerprint(self.state.document) != current.saved
        self.state.doc_title = self.doc_title()

    async def recover_system(self) -> None:
        """Reopen the saved System Settings, if any, and pick the view to start in. A phone is
        always in Handheld, whatever start view was saved; with nothing saved, the window's size
        picks the view (and keeps picking it as the window changes, until a view is chosen)."""
        saved = await self.shell.read(SYSTEM_KEY)
        if saved is not None:
            self.state.system = System.loads(saved)
            self.state.mode = Mode.HANDHELD if self.phone else self.state.system.start_mode
        else:
            self.first_visit = True
            self.state.mode = starting_mode(self.page.width, self.page.height)

    async def recover(self) -> None:
        """Reopen the autosaved document, if it is readable."""
        await self.library.index()  # read once now, so the dialogs can check names at once
        self.state.doc_title = self.doc_title()
        text = await self.shell.read(AUTOSAVE_KEY)
        if text is None:
            return
        try:
            self.replace(await self.read(text))
            self.saved = text
            link = await self.shell.read(CURRENT_KEY)
            current = Current.loads(link)
            if link is None:  # an autosave from before named documents: count it as saved
                current.saved = document_fingerprint(self.state.document)
            self.current = current
            self.dirty = document_fingerprint(self.state.document) != current.saved
            self.state.doc_title = self.doc_title()
            if self.debug:  # the end-to-end tests check what came back
                count = sum(len(problem.pages) for problem in self.state.document.problems)
                print(f"CASSIM: RECOVERED {count} pages", flush=True)
        except DocumentFileError:
            return  # a damaged autosave is ignored, and overwritten by the next change

    def body_size(self) -> tuple[float, float]:
        """The screen's room under its title bar, for a page that draws to size (the sheet)."""
        state = self.state
        title = state.px(TITLE_H)
        if state.mode is Mode.HANDHELD:
            return state.px(SCREEN_W), (self.view.control.height or state.px(SCREEN_H)) - title
        widths, _ = computer_columns(
            self.page.width,
            state.system.computer_sidebar_width,
            state.system.computer_keypad_width,
            keypad_visible=state.system.computer_keypad,
        )
        height = self.view.control.height or computer_screen_height(self.page.height)
        return max(widths["workspace"], 200.0), max(height - title, 120.0)

    def refresh(self) -> None:
        start = time.perf_counter()
        self.state.prepare()  # a sheet takes the engine's replies first
        self.state.doc_title = self.doc_title()
        self.autosave()
        self.view.refresh()
        self.view.show_pointer(self.pointer)
        self.keypad.refresh()
        if self.state.mode is Mode.COMPUTER:  # the sidebar is not shown in Handheld
            self.sidebar.refresh()
        self.place_status()
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
            self.print_sheet()
        self.kick()

    def place_status(self) -> None:
        """The status line goes in the toolbar row, or in full screen (which has no toolbar row)
        in the middle of the screen's title bar, in place of the name while it has something to
        say."""
        if self.full:
            self.toolbar.controls = []
        else:
            self.toolbar.controls = [*self.toolbar_controls(), self.status, self.sink_box]
        self.state.doc_title = self.doc_title()
        self.view.set_doc_title(self.state.doc_title)

    def print_sheet(self) -> None:
        """`CASSIM: SHEET A2 16`: the cursor's cell and what it shows, when that changes. The
        end-to-end tests read the sheet this way; its canvas has nothing to read."""
        sheet = self.state.sheet
        if sheet is None:
            return
        screen = sheet.screen()
        line = f"{screen.address} {screen.cells.get(sheet.cursor, ('', False))[0]}".strip()
        if line != self.sheet_line:
            self.sheet_line = line
            print(f"CASSIM: SHEET {line}", flush=True)

    # ---- the engine -------------------------------------------------------------------------

    @property
    def busy(self) -> bool:
        return (
            self.starting
            or self.sheet_file_busy
            or (self.runner is not None and not self.runner.idle)
        )

    @property
    def running(self) -> bool:
        """An entry is being calculated, so Esc can cancel it."""
        return self.runner is not None and self.runner.status is Status.BUSY

    async def read(self, text: str) -> Document:
        """A document from its text, replayed by whichever engine this app uses."""
        return loads(text) if self.runner is None else await self.runner.load(text, PAGES)

    def replace(self, document: Document) -> None:
        self.variable_undo.clear()
        self.variable_redo.clear()
        self.state.replace_document(document)
        if self.runner is not None:
            self.runner.retain(document)

    def kick(self) -> None:
        """Start whatever the engine owes the screen: a queued entry, or queued settings."""
        runner = self.runner
        if self.sheet_file_busy or runner is None or not runner.idle:
            return
        calculator = calculator_of(self.state.document.current)
        if calculator is not None and calculator.pending is not None:
            self.page.run_task(self.run_pending, calculator)
        elif runner.dirty(self.state.document):
            self.page.run_task(self.run_sync)

    async def run_pending(self, calculator: Calculator) -> None:
        assert self.runner is not None
        self.say("Calculating... press Esc to cancel")
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
        self.say("Cancelling... restarting the calculator")
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
        self.pointer.hide()  # a key press puts the pointer away
        self.state.press_keypad(name)
        self.refresh()

    def press_cassim(self) -> None:
        if self.busy:
            return
        ctrl = self.state.pending == "ctrl"
        self.state.clear_pending()
        if ctrl:
            if self.installable:
                self.install()
            else:
                self.shell.notice(
                    f"Install {about.product_name()}",
                    "Install is not available in this browser.",
                )
        else:
            self.state.run_action("open_menu", "cassim")
        self.refresh()

    # ---- the pointer that the keypad's centre key steers -----------------------------------

    def on_stick(self, event: str, dx: float, dy: float) -> None:
        """The centre key as a joystick (see `Keypad.on_stick`). A tap with the pointer showing
        clicks where it is; with it hidden, the key does its usual `select`."""
        pointer = self.pointer
        if event == "tap":
            place = pointer.click()
            if place is None:
                self.press(STICK_KEY)
            elif not self.busy:
                if not self.view.click_at(*place):
                    # no hit test on this page, or its sizes not in yet: select as before
                    self.state.press_keypad(STICK_KEY)
                self.refresh()
            return
        if event == "start":
            pointer.resize(*self.body_size())
            pointer.press()
            if self.view.measuring:
                self.show_pointer()
            else:  # redraw once with the history reporting its sizes, for clicks
                self.view.measuring = True
                self.refresh()
            if not self.ticking:
                self.page.run_task(self.steer)
        elif event == "move":
            pointer.drag(dx, dy)
        else:
            pointer.release()

    def show_pointer(self) -> None:
        """Send only the arrow: a whole refresh per step would be far too slow on a phone."""
        self.view.show_pointer(self.pointer)
        with contextlib.suppress(RuntimeError):  # not on a page (the tests' stand-in page)
            self.view.pointer.update()

    async def steer(self) -> None:
        """Move the pointer while it shows; the loop ends when it hides."""
        self.ticking = True
        try:
            last = time.monotonic()
            while self.pointer.visible:
                await asyncio.sleep(POINTER_TICK)
                now = time.monotonic()
                if self.pointer.step(now - last):
                    self.show_pointer()
                last = now
            self.show_pointer()  # hidden by a key press between steps
        finally:
            self.ticking = False
            self.view.measuring = False  # the next refresh stops the size reports

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
        if self.sink_focused and binding.action in ("insert", "backspace", "enter"):
            return  # typed into the hidden box: on_sink turns it into keys
        if binding.action == "paste":  # the system clipboard may hold text from elsewhere
            binding = Binding("paste", await self.shell.pasted())
        if binding.action in ("undo", "redo") and self.variable_history_action(binding.action):
            self.refresh()
            return
        self.pointer.hide()
        state.run(binding)
        self.refresh()

    # ---- the on-screen keyboard (Computer view on a phone or tablet) --------------------------

    @property
    def soft_keyboard(self) -> bool:
        return self.state.mode is Mode.COMPUTER and self.shell.offers.touch

    def on_sink(self, _: object = None) -> None:
        """Keys typed on the on-screen keyboard reach the calculator."""
        keys = keys_for(self.sink.value or "")
        self.sink.value = SENTINEL
        if self.busy:
            return
        for binding in keys:
            if binding.action in ("undo", "redo") and self.variable_history_action(binding.action):
                continue
            self.state.run(binding)
        self.refresh()

    def on_sink_submit(self, _: object = None) -> None:
        self.on_sink()
        if not self.busy:
            self.state.run(Binding("enter"))
            self.refresh()
        self.page.run_task(self.sink.focus)  # Enter would otherwise close the keyboard

    def offer_keyboard(self, action: str) -> None:
        """After a tap where typing goes, open the on-screen keyboard."""
        if self.debug and action in TYPING_ACTIONS:
            print(f"CASSIM: KEYBOARD {action} touch={self.soft_keyboard}", flush=True)
        if action in TYPING_ACTIONS and self.soft_keyboard:
            self.page.run_task(self.sink.focus)

    def request_paste(self) -> None:
        self.page.run_task(self.paste_from_clipboard)

    async def paste_from_clipboard(self) -> None:
        """Paste the system clipboard into the entry line (the keypad's ctrl+v)."""
        self.state.paste_text(await self.shell.pasted())
        self.refresh()

    def act(self, action: Action, arg: str = "") -> None:
        if self.busy:
            return
        if action == "statistics_eval":
            self.page.run_task(self.run_statistics_eval, arg)
            return
        self.state.run_action(action, arg)
        self.refresh()
        self.offer_keyboard(action)

    async def run_statistics_eval(self, expression: str) -> None:
        statistics = self.state.statistics
        if statistics is None:
            return
        self.say("Updating data...")
        if isinstance(statistics.session, RemoteSession):
            if self.runner is None:
                msg = "a remote Data & Statistics session requires the Runner"
                raise RuntimeError(msg)
            calculator = Calculator(statistics.session)
            calculator.pending = Pending(expression, False)
            finished = await self.runner.evaluate(calculator)
            if not finished:
                statistics.message = "Update cancelled."
            elif calculator.history:
                statistics.message = calculator.history[-1].result.error or ""
            else:
                msg = "the engine accepted no point update result"
                raise RuntimeError(msg)
        else:
            result = statistics.session.eval(expression, approximate=False)
            statistics.message = result.error or ""
        self.status.value = ""
        self.refresh()

    def cycle_setting(self, name: str) -> None:
        """A click on Rad/Deg, Auto/Approx or Real/Rect/Polar in the title bar."""
        if self.busy:
            return
        self.state.document.set(**{name: next_choice(self.state.document.settings, name)})
        self.refresh()

    def on_resize(self, e: ft.PageResizeEvent) -> None:
        """Keep the layout fitted to the window; a first visit follows its size until chosen, and
        a window that shrinks to phone size goes to Handheld."""
        if self.first_visit:
            self.state.mode = starting_mode(e.width, e.height)
        elif starting_mode(e.width, e.height) is Mode.HANDHELD:  # phone-sized now
            self.state.mode = Mode.HANDHELD
        self.arrange()
        self.refresh()

    @property
    def phone(self) -> bool:
        """A phone-sized window (its short side is narrow): only Handheld view is offered, with no
        splitter and a thinner margin."""
        sides = [side for side in (self.page.width, self.page.height) if side]
        return bool(sides) and min(sides) < NARROW

    @property
    def installable(self) -> bool:
        """The browser has offered to install CASSim and it is not installed yet."""
        return self.shell.offers.installable

    def install(self) -> None:
        self.shell.install()

    def go_fullscreen(self) -> None:
        """Toggle the cutout on an installed phone, or the browser's fullscreen elsewhere."""
        if self.phone and self.state.mode is Mode.HANDHELD and self.shell.offers.installed:
            self.use_cutout = not self.use_cutout
            self.arrange()
            self.refresh()
        else:
            self.shell.toggle_fullscreen()

    def on_bridge(self) -> None:
        """The page reported a change in browser capabilities or offline/update status."""
        if self.state.menu is not None and self.state.menu.root.label == about.product_name():
            root = self.cassim_menu()
            if self.state.menu.root != root:
                self.state._open_menu("cassim")
        self.arrange()
        self.refresh()

    def cassim_menu(self) -> MenuItem:
        handheld = self.state.mode is Mode.HANDHELD
        return MenuItem(
            about.product_name(),
            items=cassim_items(
                handheld=handheld,
                offers=self.shell.offers,
                phone=self.phone,
                use_cutout=self.use_cutout,
            ),
        )

    def toggle_keypad(self) -> None:
        """Show or hide the keypad beside the screen in Computer mode (kept with the settings)."""
        system = self.state.system
        system.computer_keypad = not system.computer_keypad
        self.arrange()
        self.on_system_change()

    def set_mode(self, mode: Mode) -> None:
        if mode is Mode.COMPUTER and self.phone:
            return  # no room on a phone for Computer view and the on-screen keyboard
        self.first_visit = False
        self.state.mode = mode
        self.arrange()
        self.refresh()

    def toolbar_controls(self) -> list[ft.Control]:
        theme, mode = self.theme, self.state.mode
        if mode is Mode.HANDHELD:
            return []  # the keypad has the Doc, Menu and CASSim keys

        def button(text: str, action: Callable[[], None], fill: str, colour: str) -> ft.Container:
            return ft.Container(
                label_text(text, size=13, color=colour, no_wrap=True),
                expand=True,
                height=36,
                alignment=ft.Alignment.CENTER,
                bgcolor=fill,
                border_radius=6,
                ink=True,
                on_click=lambda _: action(),
            )

        mode_control = ft.SegmentedButton(
            segments=[
                ft.Segment(value=Mode.HANDHELD.value, label="Handheld"),
                ft.Segment(value=Mode.COMPUTER.value, label="Computer"),
            ],
            selected=[mode.value],
            show_selected_icon=False,
            expand=True,
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.SELECTED: theme.accent,
                    ft.ControlState.DEFAULT: theme.key,
                },
                color={
                    ft.ControlState.SELECTED: theme.accent_text,
                    ft.ControlState.DEFAULT: theme.key_text,
                },
                padding=ft.Padding.symmetric(horizontal=4, vertical=5),
                text_style=ft.TextStyle(size=12),
            ),
            on_change=lambda e: self.set_mode(Mode(e.control.selected[0])),
        )
        keypad = button(
            "Keypad",
            self.toggle_keypad,
            theme.accent if self.state.system.computer_keypad else theme.key,
            theme.accent_text if self.state.system.computer_keypad else theme.key_text,
        )
        keypad.expand = False
        keypad.width = 76
        cassim = button(
            about.product_name(),
            lambda: self.act("open_menu", "cassim"),
            theme.accent,
            theme.accent_text,
        )
        cassim.tooltip = (
            "CASSim menu: attention required"
            if self.shell.offers.needs_attention
            else "CASSim menu"
        )
        if self.shell.offers.needs_attention:
            cassim.content = ft.Row(
                [
                    label_text(about.product_name(), size=13, color=theme.accent_text),
                    ft.Icon(ft.Icons.CIRCLE, size=8, color="#e53935"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=4,
            )
        doc_fill, doc_text = theme.key_colours("nav")
        undo = ft.IconButton(
            icon=ft.Icons.UNDO,
            tooltip="Undo (Ctrl+Z)",
            on_click=lambda _: self.undo_action(),
            icon_color=theme.key_text,
            bgcolor=theme.key,
            icon_size=15,
            width=42,
            height=36,
            padding=4,
        )
        redo = ft.IconButton(
            icon=ft.Icons.REDO,
            tooltip="Redo (Ctrl+Y)",
            on_click=lambda _: self.redo_action(),
            icon_color=theme.key_text,
            bgcolor=theme.key,
            icon_size=15,
            width=42,
            height=36,
            padding=4,
        )
        return [
            ft.Row([mode_control, keypad], spacing=4),
            ft.Row(
                [
                    cassim,
                    button("Doc", lambda: self.act("open_menu", "doc"), doc_fill, doc_text),
                    button("Settings", self.open_settings, theme.key, theme.key_text),
                ],
                spacing=4,
            ),
            ft.Row(
                [
                    undo,
                    redo,
                    button(
                        "Menu",
                        lambda: self.act("open_menu", "menu"),
                        theme.accent,
                        theme.accent_text,
                    ),
                ],
                spacing=4,
            ),
            ft.Row(
                [
                    button(
                        "Page manager",
                        lambda: self.act("dialog", SORTER),
                        theme.key,
                        theme.key_text,
                    ),
                    button("+ Page", lambda: self.act("add_page"), theme.key, theme.key_text),
                    button("+ Problem", lambda: self.act("add_problem"), theme.key, theme.key_text),
                ],
                spacing=4,
            ),
        ]

    def delete_variables(self, variables: tuple[VariableInfo, ...]) -> None:
        if not variables or self.busy:
            return
        problem = self.state.document.problems[self.state.document.problem]
        calculator = next(
            (
                model
                for page in problem.pages
                if (model := calculator_of(page)) is not None
                and model.pending is None
                and model.error is None
            ),
            None,
        )
        if calculator is None:
            self.notice(
                "Delete variables",
                "Add a Calculator page to this Problem before deleting variables.",
            )
            return
        sources = tuple(variable.source for variable in variables)
        if any(not source for source in sources):
            self.notice("Delete variables", "One or more variables cannot be restored.")
            return
        names = tuple(variable.name for variable in variables)
        self.page.run_task(self._delete_variables, calculator, names, sources)

    async def _delete_variables(
        self, calculator: Calculator, names: tuple[str, ...], sources: tuple[str, ...]
    ) -> None:
        if await self._calculator_command(calculator, f"DelVar {','.join(names)}"):
            self.variable_undo.append(VariableDeletion(calculator, sources, names))
            self.variable_redo.clear()
            self.flash(f"Deleted {', '.join(names)}. Ctrl+Z to restore.")
        self.refresh()

    async def _calculator_command(self, calculator: Calculator, command: str) -> bool:
        saved_editor = calculator.editor
        calculator.editor = Editor()
        calculator.editor.insert_text(command)
        try:
            calculator.perform(Binding("enter"))
            if calculator.pending is not None:
                if self.runner is None:
                    msg = "a local calculator left a command pending"
                    raise RuntimeError(msg)
                await self.runner.evaluate(calculator)
        finally:
            calculator.editor = saved_editor
        if not calculator.history or calculator.history[-1].result.error is not None:
            error = calculator.history[-1].result.error if calculator.history else "No result"
            self.notice("Variable change failed", str(error))
            return False
        return True

    def variable_history_action(self, action: str) -> bool:
        history = self.variable_undo if action == "undo" else self.variable_redo
        if not history or self.busy:
            return False
        self.page.run_task(self._apply_variable_history, action)
        return True

    async def _apply_variable_history(self, action: str) -> None:
        source = self.variable_undo if action == "undo" else self.variable_redo
        target = self.variable_redo if action == "undo" else self.variable_undo
        change = source[-1]
        commands = change.sources if action == "undo" else (f"DelVar {','.join(change.names)}",)
        for command in commands:
            if not await self._calculator_command(change.calculator, command):
                self.refresh()
                return
        source.pop()
        target.append(change)
        self.flash("Restored variables" if action == "undo" else "Deleted variables")
        self.refresh()

    def undo_action(self) -> None:
        if not self.variable_history_action("undo"):
            self.state.run_action("undo_pages")
            self.refresh()

    def redo_action(self) -> None:
        if not self.variable_history_action("redo"):
            self.state.run_action("redo_pages")
            self.refresh()

    def show_dialog(self, name: str) -> None:
        dialogs: dict[str, Callable[[], object]] = {
            "fullscreen": self.go_fullscreen,
            "install": self.install,
            "uninstall": self.shell.uninstall,
            "check_updates": self.shell.check_for_updates,
            "offline_status": lambda: self.shell.notice(
                "Offline status", self.shell.offers.offline_message
            ),
            "retry_offline": self.shell.retry_offline,
            "reload_update": self.reload_update,
            "switch_view": lambda: self.set_mode(
                Mode.COMPUTER if self.state.mode is Mode.HANDHELD else Mode.HANDHELD
            ),
            "save": self.save,
            "save_as": self.save_as,
            "open_document": self.open_document,
            "export_file": lambda: self.page.run_task(self.export_file),
            "import_file": lambda: self.ask_discard(lambda: self.page.run_task(self.import_file)),
            "sheet_import_csv": lambda: self._start_sheet_file_action("csv", importing=True),
            "sheet_export_csv": lambda: self._start_sheet_file_action("csv", importing=False),
            "sheet_import_xlsx": lambda: self._start_sheet_file_action("xlsx", importing=True),
            "sheet_export_xlsx": lambda: self._start_sheet_file_action("xlsx", importing=False),
            "share_link": self.share_link,
            "document_settings": self.open_settings,
            "system_settings": lambda: system_settings_dialog(
                self.page, self.state, self.on_system_change, self.theme, self.open_appearance
            ),
            "help": self.shell.help,
            "about": self.shell.about,
        }
        dialog = dialogs.get(name)
        if dialog is not None:
            dialog()

    def reload_update(self) -> None:
        if document_fingerprint(self.state.document) == self.current.saved:
            self.shell.reload_update()
            return

        async def reload() -> None:
            self.shell.reload_update()

        self.shell.confirm(
            "Reload CASSim?",
            "This document has unsaved changes. Reloading may interrupt recent changes.",
            "Reload",
            reload,
        )

    # ---- documents saved by name in this browser (FR-DOC-010) --------------------------------

    def save(self) -> None:
        """Save: under the document's name, or ask for one if it has never been saved here."""
        if self.current.stored is None:
            self.save_as()
        else:
            self.page.run_task(self.store_as, self.current.stored)

    async def store_as(self, name: str) -> None:
        document = self.state.document
        document.name = name
        data = to_dict(document)
        await self.library.save(name, json.dumps(data, ensure_ascii=False, separators=(",", ":")))
        self.remember(Current(name, fingerprint(data)))
        self.refresh()
        self.flash(f"Saved “{name}”")
        if self.debug:
            print(f"CASSIM: SAVED {name}", flush=True)

    def say(self, text: str) -> None:
        """Show `text` in the status line now, without redrawing the rest."""
        self.status.value = text
        self.place_status()
        self.page.update()

    def flash(self, text: str) -> None:
        """Show `text` in the status line for a moment."""
        self.say(text)

        async def clear() -> None:
            await asyncio.sleep(FLASH_SECONDS)
            if self.status.value == text:
                self.say("")

        self.page.run_task(clear)

    def save_as(self) -> None:
        """Ask for a name, then save under it (asking first before replacing another one)."""
        library = self.library
        start = "" if self.state.document.name == UNTITLED else self.state.document.name
        field = ft.TextField(value=start, label="Name", autofocus=True, max_length=60)

        def done(_: object = None) -> None:
            name = clean_name(field.value or "")
            if not name:
                field.error = "Type a name"
                field.update()
                return
            self.page.pop_dialog()
            self.typing_dialog = None
            index = library.cached
            other = index.spelled(name) if index is not None else None
            if other is not None and other.casefold() != (self.current.stored or "").casefold():

                async def replace() -> None:
                    await self.store_as(name)

                self.shell.confirm(
                    "Replace saved document?",
                    f"“{other}” is already saved in this browser. Replace it with this document?",
                    "Replace",
                    replace,
                )
                return
            self.page.run_task(self.store_as, name)

        def cancel(_: object) -> None:
            self.page.pop_dialog()
            self.typing_dialog = None

        field.on_submit = done
        dialog = ft.AlertDialog(
            title=ft.Text("Save As"),
            content=ft.Column(
                [
                    ft.Text("Saved in this browser.\nDoc > File > Export File… saves a file."),
                    field,
                ],
                tight=True,
                width=360,
            ),
            actions=[
                ft.TextButton("Save", on_click=done),
                ft.TextButton("Cancel", on_click=cancel),
            ],
        )
        self.typing_dialog = dialog  # the keys go to the name box, not the calculator
        self.page.show_dialog(dialog)

    def open_document(self) -> None:
        """Open: the documents saved in this browser, newest first; each can be deleted."""
        index = self.library.cached
        items = index.items if index is not None else []
        if not items:
            self.notice(
                "No saved documents",
                "Nothing is saved in this browser yet. Doc > File > Save keeps a document here; "
                "Import File… opens a .cassim.json file.",
            )
            return

        def opened(name: str) -> Callable[[object], None]:
            def go(_: object) -> None:
                self.page.pop_dialog()
                self.ask_discard(lambda: self.page.run_task(self.open_saved, name))

            return go

        def deleted(name: str) -> Callable[[object], None]:
            def go(_: object) -> None:
                self.page.pop_dialog()

                async def gone() -> None:
                    await self.library.delete(name)
                    if self.current.stored == name:  # the open copy is now saved nowhere
                        self.remember(Current(None, ""))
                    self.refresh()
                    self.open_document()

                self.shell.confirm(
                    f"Delete “{name}”?",
                    "It is removed from this browser. This cannot be undone.",
                    "Delete",
                    gone,
                )

            return go

        rows: list[ft.Control] = [
            ft.ListTile(
                title=ft.Text(item.name),
                subtitle=ft.Text(datetime.fromtimestamp(item.when).strftime("%d %b %Y, %H:%M")),
                on_click=opened(item.name),
                trailing=ft.IconButton(
                    ft.Icons.DELETE_OUTLINE, tooltip="Delete", on_click=deleted(item.name)
                ),
            )
            for item in items
        ]
        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Open Document"),
                content=ft.Column(rows, tight=True, scroll=ft.ScrollMode.AUTO, width=380),
                actions=[ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog())],
            )
        )

    async def open_saved(self, name: str) -> None:
        text = await self.library.text(name)
        try:
            if text is None:
                msg = "it is no longer in this browser's storage"
                raise DocumentFileError(msg)
            self.replace(await self.read(text))
            self.state.document.name = name
            self.remember(Current(name, document_fingerprint(self.state.document)))
        except DocumentFileError as error:
            self.notice(f"Cannot open “{name}”", str(error))
        self.refresh()

    def ask_discard(self, then: Callable[[], object]) -> None:
        """Do `then` (which replaces the document) at once, or after asking when the open
        document has changes that are not saved."""
        if document_fingerprint(self.state.document) == self.current.saved:
            then()
            return

        async def discard() -> None:
            then()
            self.refresh()

        self.shell.confirm(
            "Discard changes?",
            f"“{self.state.document.name}” has changes that are not saved. "
            "Doc > File > Save keeps them.",
            "Discard",
            discard,
        )

    def on_new_document(self) -> None:
        """A new document is saved nowhere, and has nothing to lose yet."""
        self.variable_undo.clear()
        self.variable_redo.clear()
        self.remember(Current(None, document_fingerprint(self.state.document)))

    # ---- files on disk: Import and Export (FR-DOC-004, FR-DOC-006) ----------------------------

    async def export_file(self) -> None:
        """Download the document as `.cassim.json`."""
        document = self.state.document
        await self.shell.save_file(file_name(document), dumps(document), "Export document")

    async def import_file(self) -> None:
        """Open a `.cassim.json` file. It is not in the browser's library until it is saved,
        so it shows as unsaved."""
        try:
            text = await self.shell.pick_file(OPEN_EXTENSIONS, "Import document")
            if text is None:
                return
            self.replace(await self.read(text))
            self.remember(Current(None, ""))
        except (DocumentFileError, UnicodeDecodeError) as error:
            self.notice("Cannot open that file", str(error))
        self.refresh()

    def _start_sheet_file_action(self, kind: str, *, importing: bool) -> None:
        if self.sheet_file_busy:
            return
        self.sheet_file_busy = True
        self.page.run_task(self._sheet_file_action, kind, importing)

    async def _sheet_file_action(self, kind: str, importing: bool) -> None:
        try:
            sheet = self.state.sheet
            if sheet is None:
                return
            if importing:
                data = await self.shell.pick_file_bytes((kind,), f"Import {kind.upper()} data")
                if data is None:
                    return
                rows = read_csv(data) if kind == "csv" else read_xlsx(data)
                sheet.import_rows(rows)
                if self.runner is not None:
                    await self.runner.sync(self.state.document)
                sheet.update()
            else:
                if self.runner is not None:
                    await self.runner.sync(self.state.document)
                sheet.update()
                sheet.request_export_view()
                if self.runner is not None:
                    await self.runner.sync(self.state.document)
                sheet.update()
                rows = sheet.export_rows(formulas=kind == "xlsx")
                if kind == "csv":
                    data = write_csv([[cell.text for cell in row] for row in rows])
                else:
                    data = write_xlsx(rows)
                await self.shell.save_bytes_file(
                    f"spreadsheet.{kind}", data, f"Export {kind.upper()} data"
                )
        except (OSError, ValueError) as error:
            operation = "import" if importing else "export"
            self.notice(f"Cannot {operation} {kind.upper()} data", str(error))
        finally:
            self.sheet_file_busy = False
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
                self.remember(Current(None, ""))  # not saved in this browser yet
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
        self.apply_theme()
        self.arrange()  # the letter layout changes the keypad's size
        self.refresh()

    def open_appearance(self) -> None:
        self.typing_dialog = theme_settings_dialog(
            self.page, self.state.system, self.on_system_change
        )

    def apply_theme(self) -> None:
        system = self.state.system
        theme = themed(system.theme_name, system.theme_overrides.get(system.theme_name, {}))
        self.page.theme_mode = (
            ft.ThemeMode.LIGHT if system.theme_name == "Light" else ft.ThemeMode.DARK
        )
        self.page.bgcolor = theme.background
        self.status.color = theme.status_text
        if theme == self.theme:
            return
        self.theme = self.shell.theme = theme
        self.view = CalculatorView(
            self.state, theme, self.act, lambda: self.shift, self.cycle_setting
        )
        self.view.body_size = self.body_size
        self.keypad = Keypad(
            self.state, self.press, theme, on_cassim=self.press_cassim, on_stick=self.on_stick
        )
        self.sidebar.theme = theme
        self.shape = None

    def open_settings(self) -> None:
        settings_dialog(self.page, self.state, self.refresh, self.theme)

    def handheld_room(
        self, *, phone: bool, full: bool, margin: int
    ) -> tuple[float | None, float | None]:
        """Set the outer padding and return the viewport inside the selected safe area."""
        top, right, bottom, left = (
            self.shell.offers.safe_area
            if phone and self.shell.offers.installed and not self.use_cutout
            else (0, 0, 0, 0)
        )
        self.outer.padding = ft.Padding.only(
            top=top + (0 if full else margin),
            right=right + margin,
            bottom=bottom + margin,
            left=left + margin,
        )
        width = max(1, self.page.width - left - right) if self.page.width else None
        height = max(1, self.page.height - top - bottom) if self.page.height else None
        return width, height

    def arrange(self) -> None:
        state = self.state
        system = state.system
        self.keypad.installable = self.installable
        self.keypad.needs_attention = self.shell.offers.needs_attention
        full = state.mode is Mode.HANDHELD and self.shell.offers.standalone and system.zoom <= 1
        self.full = full
        self.toolbar.visible = not full
        if state.mode is Mode.HANDHELD:
            self._arrange_handheld(full=full, phone=self.phone)
        else:
            self._arrange_computer()

    def _arrange_handheld(self, *, full: bool, phone: bool) -> None:
        view = self.view.control
        state = self.state
        system = state.system
        self.frame.controls = [self.toolbar, self.layout]
        share = system.keypad_share or None  # 0 is auto; a phone always uses it
        margin = PHONE_MARGIN if phone else MARGIN
        width, height = self.handheld_room(phone=phone, full=full, margin=margin)
        self.frame.spacing = 0  # the toolbar holds only the status line
        units = keypad_units(state.keypad)
        sizing = Sizing(
            None if phone else share,
            system.zoom,
            FULL_RESERVE if full else STATUS_H,
            margin,
            not phone,
        )
        plan = handheld_plan(width, height, units[0], units[1], sizing)
        sizing = replace(sizing, bar=0) if full else sizing
        self.plan = plan
        state.scale, state.pad_scale = plan.scale, plan.pad_scale
        view.width = state.px(SCREEN_W)
        view.height = (
            full_screen_height(plan, height, units[1], sizing) if full else state.px(SCREEN_H)
        )
        view.expand = False
        shape = (Mode.HANDHELD, plan.side_by_side, phone, system.zoom > 1, full)
        if shape == self.shape:
            self.size_splitter(plan)
            return
        self.shape = shape
        parts: list[ft.Control] = [view, self.keypad.control]
        if not phone:
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
        if system.zoom > 1:
            self.layout.content = ft.Column(
                [ft.Row([self.layout.content], scroll=ft.ScrollMode.AUTO)],
                scroll=ft.ScrollMode.AUTO,
            )

    def _arrange_computer(self) -> None:
        state = self.state
        system = state.system
        view = self.view.control
        self.shape = None
        self.outer.padding = MARGIN
        self.frame.spacing = 0
        self.frame.controls = [self.layout]
        state.scale = state.pad_scale = system.zoom
        self.layout.alignment = None
        view.width = None
        view.expand = True
        height = computer_screen_height(self.page.height, toolbar_height=28)
        self.sidebar.height = max(180, height - 160)
        widths, _ = computer_columns(
            self.page.width,
            system.computer_sidebar_width,
            system.computer_keypad_width,
            keypad_visible=system.computer_keypad,
        )
        visible = [
            name
            for name in system.computer_column_order
            if name != "keypad" or system.computer_keypad
        ]
        children: list[ft.Control] = []
        self.computer_panels = {}
        for index, name in enumerate(visible):
            panel = self._computer_panel(name, widths[name], height)
            self.computer_panels[name] = panel
            children.append(
                ft.DragTarget(
                    panel,
                    group="computer-columns",
                    on_accept=lambda _, target=name: self._drop_column(target),
                )
            )
            if index + 1 < len(visible):
                children.append(self._computer_splitter(name, visible[index + 1], height))
        self.computer_row = ft.Row(
            children,
            width=max((self.page.width or 1000) - 2 * MARGIN, 1),
            height=height,
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
        self.layout.content = self.computer_row

    def _computer_panel(self, name: str, width: float, height: float) -> ft.Container:
        controls: list[ft.Control] = []
        if self.state.system.computer_column_controls:
            title = COMPUTER_PANEL_NAMES[name]
            controls.append(
                ft.Row(
                    [
                        label_text(title, size=12, color=self.theme.panel_text, expand=True),
                        ft.IconButton(
                            icon=ft.Semantics(
                                label=f"Move {title.lower()} left",
                                content=ft.Icon(ft.Icons.ARROW_LEFT),
                            ),
                            tooltip=f"Move {title.lower()} left",
                            on_click=lambda _, column=name: self._move_column(column, -1),
                            icon_color=self.theme.key_text,
                            icon_size=12,
                            width=24,
                            height=24,
                            padding=2,
                        ),
                        ft.IconButton(
                            icon=ft.Semantics(
                                label=f"Move {title.lower()} right",
                                content=ft.Icon(ft.Icons.ARROW_RIGHT),
                            ),
                            tooltip=f"Move {title.lower()} right",
                            on_click=lambda _, column=name: self._move_column(column, 1),
                            icon_color=self.theme.key_text,
                            icon_size=12,
                            width=24,
                            height=24,
                            padding=2,
                        ),
                    ],
                    spacing=3,
                )
            )
        if name == "sidebar":
            content: ft.Control = ft.Column(
                [self.toolbar, self.sidebar.control], spacing=6, expand=True
            )
        elif name == "workspace":
            self.view.control.height = max(
                height - (38 if self.state.system.computer_column_controls else 8), 300
            )
            content = self.view.control
        else:
            content = ft.Column(
                [ft.Row([self.keypad.control], scroll=ft.ScrollMode.AUTO)],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )
        controls.append(content)
        return ft.Container(
            ft.Column(controls, spacing=6, expand=True),
            width=width,
            height=height,
            padding=4,
        )

    def _computer_splitter(self, first: str, second: str, height: float) -> ft.Control:
        def resize(delta: float) -> None:
            self._resize_boundary(first, second, delta)

        def step(delta: float) -> None:
            resize(delta)
            self.shell.write(SYSTEM_KEY, self.state.system.dumps())

        divider = ft.GestureDetector(
            ft.Container(
                ft.Container(
                    width=2,
                    height=max(
                        height - 28 - (48 if self.state.system.computer_column_controls else 0), 1
                    ),
                    bgcolor=self.theme.key_label,
                ),
                expand=True,
                alignment=ft.Alignment.CENTER,
                bgcolor=ft.Colors.TRANSPARENT,
                tooltip="Drag to resize adjacent columns",
            ),
            expand=True,
            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
            drag_interval=24,
            on_horizontal_drag_update=lambda event: (
                resize(event.global_delta.x) if event.global_delta is not None else None
            ),
            on_horizontal_drag_end=lambda _: self.shell.write(
                SYSTEM_KEY, self.state.system.dumps()
            ),
        )
        controls: list[ft.Control] = [
            ft.Draggable(
                ft.Container(
                    ft.Icon(ft.Icons.DRAG_INDICATOR, size=16, color=self.theme.key_label),
                    width=COMPUTER_SPLITTER,
                    height=28,
                    alignment=ft.Alignment.CENTER,
                    tooltip="Drag left or right to move columns",
                ),
                group="computer-columns",
                on_drag_start=lambda _: setattr(self, "dragged_boundary", (first, second)),
            ),
        ]
        if self.state.system.computer_column_controls:
            controls.extend(
                [
                    ft.IconButton(
                        icon=ft.Semantics(
                            label="Narrow the column on the left",
                            content=ft.Icon(ft.Icons.ARROW_LEFT),
                        ),
                        tooltip="Narrow the column on the left",
                        on_click=lambda _: step(-16),
                        icon_color=self.theme.key_text,
                        icon_size=10,
                        width=16,
                        height=24,
                        padding=0,
                    ),
                    ft.IconButton(
                        icon=ft.Semantics(
                            label="Widen the column on the left",
                            content=ft.Icon(ft.Icons.ARROW_RIGHT),
                        ),
                        tooltip="Widen the column on the left",
                        on_click=lambda _: step(16),
                        icon_color=self.theme.key_text,
                        icon_size=10,
                        width=16,
                        height=24,
                        padding=0,
                    ),
                ]
            )
        controls.append(divider)
        return ft.Container(
            ft.Column(
                controls, spacing=0, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            width=COMPUTER_SPLITTER,
            height=height,
            alignment=ft.Alignment.TOP_CENTER,
        )

    def _resize_boundary(self, first: str, second: str, delta: float) -> None:
        system = self.state.system
        if first == "sidebar" and second == "workspace":
            system.computer_sidebar_width += delta
        elif first == "workspace" and second == "sidebar":
            system.computer_sidebar_width -= delta
        elif first == "workspace" and second == "keypad":
            system.computer_keypad_width -= delta
        elif first == "keypad" and second == "workspace":
            system.computer_keypad_width += delta
        elif first == "sidebar" and second == "keypad":
            system.computer_sidebar_width += delta / 2
            system.computer_keypad_width -= delta / 2
        elif first == "keypad" and second == "sidebar":
            system.computer_sidebar_width -= delta / 2
            system.computer_keypad_width += delta / 2
        system.computer_sidebar_width = max(
            COMPUTER_MIN_SIDEBAR, min(COMPUTER_MAX_SIDEBAR, system.computer_sidebar_width)
        )
        system.computer_keypad_width = max(240.0, min(500.0, system.computer_keypad_width))
        self._size_computer_panels()

    def _size_computer_panels(self) -> None:
        if self.computer_row is None:
            return
        system = self.state.system
        widths, _ = computer_columns(
            self.page.width,
            system.computer_sidebar_width,
            system.computer_keypad_width,
            keypad_visible=system.computer_keypad,
        )
        for name, panel in self.computer_panels.items():
            panel.width = widths[name]
        self.page.update()

    def _move_column(self, name: str, step: int) -> None:
        order = self.state.system.computer_column_order
        visible = [
            column for column in order if column != "keypad" or self.state.system.computer_keypad
        ]
        index = visible.index(name)
        target = max(0, min(len(visible) - 1, index + step))
        first, second = order.index(name), order.index(visible[target])
        order[first], order[second] = order[second], order[first]
        self.on_system_change()

    def _drop_column(self, target: str) -> None:
        boundary = self.dragged_boundary
        self.dragged_boundary = None
        if boundary is None:
            return
        order = self.state.system.computer_column_order
        left, right = boundary
        source = right if order.index(target) <= order.index(left) else left
        first, second = order.index(source), order.index(target)
        order[first], order[second] = order[second], order[first]
        self.on_system_change()

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
