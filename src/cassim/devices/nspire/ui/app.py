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
from dataclasses import replace
from datetime import datetime

import flet as ft

from cassim.app.shell import BrowserOffers, Shell
from cassim.app.theme import themed
from cassim.core.settings import Settings, next_choice
from cassim.device.engine import LocalEngine, local_session
from cassim.device.keys import Binding, keypad_units
from cassim.device.menu import MenuItem
from cassim.device.pointer import Pointer
from cassim.device.wizard import Wizard
from cassim.devices.nspire.document import loads
from cassim.devices.nspire.pages import PAGES
from cassim.devices.nspire.pages.calculator import Calculator, calculator_of
from cassim.devices.nspire.runner import Runner, Status
from cassim.devices.nspire.ui.keypad import STICK_KEY, Keypad
from cassim.devices.nspire.ui.layout import (
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
    computer_screen_height,
    full_screen_height,
    handheld_plan,
    keypad_size,
    starting_mode,
)
from cassim.devices.nspire.ui.soft_keys import SENTINEL, TYPING_ACTIONS, keys_for
from cassim.devices.nspire.ui.state import SORTER, AppState, Mode, System
from cassim.devices.nspire.ui.theme_settings import theme_settings_dialog
from cassim.devices.nspire.ui.views import (
    POINTER_TICK,
    SYMBOL_FONT,
    SYMBOL_FONT_FILE,
    CalculatorView,
    Sidebar,
    chip,
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

# TODO(M2b): a first visit should pick Handheld below about 700 px (decision 0013 item 3).
# Flet fires no resize event at start-up, so this needs a different hook.


SIDEBAR_W = 170  # the Computer view's sidebar
TITLE_H = 20  # the screen's title bar, in the handheld's pixels

# The keys of the two texts kept in browser storage, after the device's prefix (`cassim.`).
AUTOSAVE_KEY = "autosave"
SYSTEM_KEY = "system"
# The document is saved this long after the last change, not on every key (decision 0031): saving
# writes the whole document, and with sheet data that is too slow to do per key.
AUTOSAVE_DELAY = 0.5  # seconds
FLASH_SECONDS = 2.0  # how long a note such as "Saved" stays in the status line


def browser_doc_items(
    *, handheld: bool, offers: BrowserOffers, phone: bool = False, use_cutout: bool = True
) -> tuple[MenuItem, ...]:
    """The Doc menu's last three items, always in this order so the keys never move (muscle
    memory): the view switch, Fullscreen and Install. One the browser cannot do is greyed,
    Fullscreen reads Exit Fullscreen while the page is fullscreen; on an installed phone it
    toggles the cutout instead. Install reads Uninstall in the installed app. A phone has only
    Handheld view, so the view switch is greyed there."""
    cutout_toggle = phone and handheld and offers.installed
    install = (
        MenuItem("Uninstall CASSim", "dialog", "uninstall", hint="CASSim")
        if offers.installed
        else MenuItem(
            "Install CASSim", "dialog", "install", hint="CASSim", enabled=offers.installable
        )
    )
    return (
        MenuItem(
            f"{'Computer' if handheld else 'Handheld'} view",
            "dialog",
            "switch_view",
            hint="CASSim",
            enabled=not phone,
        ),
        MenuItem(
            ("Avoid cutout" if use_cutout else "Use cutout")
            if cutout_toggle
            else ("Exit Fullscreen" if offers.in_fullscreen else "Fullscreen"),
            "dialog",
            "fullscreen",
            hint="CASSim",
            enabled=cutout_toggle
            or (offers.can_fullscreen and (offers.in_fullscreen or not offers.standalone)),
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
        self.sheet_line = ""  # the debug SHEET line last printed
        self.plan: HandheldPlan | None = None  # the last Handheld arrangement
        self.shape: tuple[Mode, bool, bool, bool, bool, bool] | None = (
            None  # what the layout is built from
        )
        self.holder: ft.Container | None = None  # the splitter's box in a portrait layout
        self.resizing = False  # a splitter redraw is queued: further drag steps only add up
        self.first_visit = False  # nothing saved yet: the window size picks the mode
        self.use_cutout = True
        self.starting = False  # loading the autosave through a remote engine
        self.theme = shell.theme
        self.shift = False  # Flet sends no modifiers with a click, so remember the key
        self.view = CalculatorView(
            state, self.theme, self.act, lambda: self.shift, self.cycle_setting
        )
        self.view.body_size = self.body_size
        self.pointer = Pointer()  # steered by the keypad's centre key
        self.ticking = False  # the pointer's timer is running
        self.keypad = Keypad(state, self.press, self.theme, on_stick=self.on_stick)
        self.sidebar = Sidebar(
            state, self.refresh, self.theme, lambda: self.act("open_menu", "menu")
        )
        self.toolbar = ft.Row(spacing=6, wrap=True)
        self.layout = ft.Container(expand=True)
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
        state.clipboard_out = shell.copy  # copy and cut also fill the system clipboard
        state.show_dialog = self.show_dialog
        state.doc_extras = self.doc_extras
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
        state.ask_discard = self.ask_discard
        state.on_new_document = self.on_new_document

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
        width = (self.page.width or 1000) - 2 * MARGIN - SIDEBAR_W - 12
        if state.system.computer_keypad:
            width -= keypad_size(*keypad_units(state.keypad))[0] * state.pad_scale
        height = self.view.control.height or computer_screen_height(self.page.height)
        return max(width, 200.0), max(height - title, 120.0)

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

    def act(self, action: str, arg: str = "") -> None:
        if self.busy:
            return
        self.state.run_action(action, arg)
        self.refresh()
        self.offer_keyboard(action)

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
        """The page reported what the browser offers: the Install row may appear or go."""
        self.arrange()
        self.refresh()

    def doc_extras(self) -> tuple[MenuItem, ...]:
        """The Doc menu's last three items (see `browser_doc_items`)."""
        handheld = self.state.mode is Mode.HANDHELD
        return browser_doc_items(
            handheld=handheld,
            offers=self.shell.offers,
            phone=self.phone,
            use_cutout=self.use_cutout,
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
            chip("Sorter", lambda: self.act("dialog", SORTER), theme),
            chip("settings", self.open_settings, theme),
            chip("Help", lambda: self.show_dialog("help"), theme),
            chip("About", lambda: self.show_dialog("about"), theme),
            *([chip("Install", self.install, theme)] if self.installable else []),
        ]

    def show_dialog(self, name: str) -> None:
        dialogs: dict[str, Callable[[], object]] = {
            "fullscreen": self.go_fullscreen,
            "install": self.install,
            "uninstall": self.shell.uninstall,
            "switch_view": lambda: self.set_mode(
                Mode.COMPUTER if self.state.mode is Mode.HANDHELD else Mode.HANDHELD
            ),
            "save": self.save,
            "save_as": self.save_as,
            "open_document": self.open_document,
            "export_file": lambda: self.page.run_task(self.export_file),
            "import_file": lambda: self.ask_discard(lambda: self.page.run_task(self.import_file)),
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
                [ft.Text("Saved in this browser. Doc > File > Export File… saves a file."), field],
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
        self.keypad = Keypad(self.state, self.press, theme, on_stick=self.on_stick)
        self.sidebar = Sidebar(
            self.state, self.refresh, theme, lambda: self.act("open_menu", "menu")
        )
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
        view = self.view.control
        state = self.state
        system = state.system
        phone = self.phone
        offer = self.installable and state.mode is Mode.HANDHELD
        self.keypad.install = (
            self.install if offer else None
        )  # Install takes the empty top-right cell
        # Full screen, or the installed app: the Handheld screen takes the spare height, up to
        # the top edge (and under a camera cutout: `viewport-fit=cover` in tools/publish.py)
        full = state.mode is Mode.HANDHELD and self.shell.offers.standalone and system.zoom <= 1
        self.full = full
        self.toolbar.visible = not full
        if state.mode is Mode.HANDHELD:
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
            sizing = replace(sizing, bar=0) if full else sizing  # the screen may use that band
            self.plan = plan
            state.scale, state.pad_scale = plan.scale, plan.pad_scale
            view.width = state.px(SCREEN_W)
            view.height = (
                full_screen_height(plan, height, units[1], sizing) if full else state.px(SCREEN_H)
            )
            view.expand = False
            shape = (Mode.HANDHELD, plan.side_by_side, phone, system.zoom > 1, offer, full)
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
                ft.Container(self.sidebar.control, width=SIDEBAR_W, padding=8),
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
