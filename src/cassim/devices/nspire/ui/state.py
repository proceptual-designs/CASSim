"""The app's state without Flet: a document, the display mode and the two keyboards."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass, field, replace
from enum import StrEnum
from typing import TYPE_CHECKING

from cassim.app.keyboard import key_name
from cassim.app.theme import THEMES, valid_theme_overrides
from cassim.core.settings import Settings
from cassim.device.editor import MARK
from cassim.device.engine import RemoteSession, local_session
from cassim.device.keys import Binding, Keyboard, Keypad
from cassim.device.menu import MenuItem, MenuState
from cassim.device.profile import Profile
from cassim.device.sheet_link import link_for
from cassim.device.wizard import Wizard
from cassim.devices.nspire import keymap as nspire
from cassim.devices.nspire.document import Document as NspireDocument
from cassim.devices.nspire.document import PageKind
from cassim.devices.nspire.pages.calculator import calculator_of
from cassim.devices.nspire.pages.spreadsheet import (
    NAME_ROW,
    SHEET_ACTIONS,
    Spreadsheet,
    spreadsheet_of,
)
from cassim.devices.nspire.screen import Screen, render
from cassim.doc.document import Document

if TYPE_CHECKING:
    from cassim.core.session import Session

_MENU_ONLY = frozenset({"menu_pick", "menu_back", "menu_page", "select"})
# Keys the page sorter passes on: they act on the document or open a menu, never on a page.
_SORTER_PASSES = frozenset(
    {
        "add_page",
        "add_problem",
        "move_page",
        "move_problem",
        "undo_pages",
        "redo_pages",
        "delete_page",
        "new_document",
        "dialog",
    }
)
SORTER = "page_sorter"  # the sorter's name as a `dialog` action (ctrl+up, Doc > View)


class Mode(StrEnum):
    HANDHELD = "handheld"
    COMPUTER = "computer"


@dataclass
class System:
    """System Settings: how the app looks, apart from the document (FR-DOC-002)."""

    start_mode: Mode = Mode.COMPUTER
    math_size: int = 20  # LaTeX size in the entry and history
    computer_keypad: bool = False  # Computer mode shows the keypad beside the screen
    keypad_share: float = 0.0  # Handheld: the keypad's share of the room (splitter); 0 is auto
    zoom: float = 1.0  # everything larger or smaller than the fitted size
    letters: str = ""  # keypad letter layout, a name in `Profile.keypads` ("" is the default)
    theme_name: str = "Dark"
    theme_overrides: dict[str, dict[str, str]] = field(default_factory=dict)
    theme_error: str = field(default="", compare=False, repr=False)

    def dumps(self) -> str:
        data = asdict(self)
        del data["theme_error"]
        return json.dumps(data)

    @classmethod
    def loads(cls, text: str) -> System:
        """Saved settings; anything unreadable or out of range falls back to the default."""
        system = cls()
        try:
            data = json.loads(text)
            system.start_mode = Mode(data["start_mode"])
            size = data["math_size"]
            system.math_size = size if size in MATH_SIZES.values() else system.math_size
            system.computer_keypad = data.get("computer_keypad") is True
            for name, low, high in (("keypad_share", 0.0, 0.8), ("zoom", 0.5, 2.0)):
                value = data.get(name)
                ok = isinstance(value, int | float) and not isinstance(value, bool)
                if ok and low <= value <= high:
                    setattr(system, name, float(value))
            letters = data.get("letters", "")
            system.letters = letters if isinstance(letters, str) else ""
            name = data.get("theme_name", "Dark")
            overrides = data.get("theme_overrides", {})
            if (
                isinstance(name, str)
                and name in THEMES
                and isinstance(overrides, dict)
                and all(k in THEMES and valid_theme_overrides(v) for k, v in overrides.items())
            ):
                system.theme_name = name
                system.theme_overrides = overrides
            else:
                system.theme_error = "Saved theme settings are invalid; Dark defaults are in use."
        except ValueError, KeyError, TypeError:
            return cls()
        return system


MATH_SIZES = {"Small": 16, "Normal": 20, "Large": 26}


class AppState:
    """Everything the views draw. A profile supplies the keymaps and keypad (FR-DEV-007)."""

    def __init__(
        self,
        document: Document | None = None,
        *,
        mode: Mode = Mode.COMPUTER,
        profile: Profile = nspire.PROFILE,
        sessions: Callable[[Settings], Session | RemoteSession] = local_session,
    ) -> None:
        self.sessions = sessions  # RemoteSessions when the maths runs in another worker
        self.document = document if document is not None else NspireDocument(sessions=sessions)
        self.mode = mode
        self.profile = profile
        self.keypad_keys = Keyboard(profile.handheld, profile.modifiers)
        self.computer_keys = Keyboard(profile.computer)
        # set by the GUI: reads the system clipboard and pastes it (keypad paste, which has no text)
        self.request_paste: Callable[[], None] | None = None
        self.clipboard_out: Callable[[str], None] | None = None  # set by the GUI: system clipboard
        self.show_dialog: Callable[[str], None] | None = None  # set by the GUI: named dialogs
        self.show_wizard: Callable[[Wizard], None] | None = None  # set by the GUI: field dialogs
        self.menu: MenuState | None = None
        # The page sorter is open on the screen (ctrl+up). The page it highlights is the current
        # page, so moving the highlight goes to that page and Enter only closes the sorter.
        self.sorting = False
        # set by the GUI: extra Doc menu items for what the browser offers (install, fullscreen)
        self.doc_extras: Callable[[], tuple[MenuItem, ...]] | None = None
        # Caps lock, set by the Caps Lock key or the keypad's ctrl+shift. Flet's key events do not
        # say whether the lock is on, so it is tracked here from its own key presses.
        self.caps = False
        self.system = System(mode)
        # The document's name as the title bar shows it, with `*` for unsaved changes (set by the
        # GUI, which knows the saved copies)
        self.doc_title = ""
        # Set by the GUI: runs the given step at once, or after asking, when it would throw away
        # unsaved changes (a new document)
        self.ask_discard: Callable[[Callable[[], None]], None] | None = None
        self.on_new_document: Callable[[], None] | None = None  # set by the GUI
        self.pad_scale = 1.0  # the keypad's own scale: the screen's times the splitter's ratio
        self.scale = 1.0  # Handheld mode draws everything this many times larger (FR-DEV-004)

    @property
    def math_size(self) -> float:
        """The LaTeX size in the entry and history, at the current Handheld scale."""
        return self.system.math_size * self.scale

    def px(self, size: float) -> float:
        """A length in the handheld's pixels, drawn at the current scale."""
        return size * self.scale

    def kpx(self, size: float) -> float:
        """A length on the keypad, drawn at the keypad's scale."""
        return size * self.pad_scale

    @property
    def keypad(self) -> Keypad:
        """The keypad in the chosen letter layout; an unknown choice gives the profile's own."""
        return self.profile.keypads.get(self.system.letters, self.profile.keypad)

    @property
    def pending(self) -> str:
        """The keypad modifier waiting for the next key ("ctrl", "shift" or "")."""
        return self.keypad_keys.pending

    def clear_pending(self) -> None:
        """Drop a keypad modifier that has done its job (a shift used for a tap in the entry)."""
        self.keypad_keys.pending = ""

    def replace_document(self, document: Document) -> None:
        """Open another document (a new one, a file or the autosave) and close any menu."""
        self.document = document
        self.menu = None
        self.sorting = False
        self.keypad_keys.pending = ""

    @property
    def sheet(self) -> Spreadsheet | None:
        """The current page's spreadsheet, if it is a Lists & Spreadsheet page."""
        return spreadsheet_of(self.document.current)

    def prepare(self) -> None:
        """Before drawing: the current sheet takes the engine's replies and asks for the cells
        it shows; a dialog it wants opened is opened."""
        sheet = self.sheet
        if sheet is not None:
            sheet.update()
            self._open_sheet_wizard(sheet)

    def retain_sheets(self) -> None:
        """After pages are added, deleted, moved or brought back: each Problem's engine keeps
        exactly the sheets of its pages (a deleted sheet frees the lists it linked)."""
        for problem in self.document.problems:
            sheets = [page.model for page in problem.pages if isinstance(page.model, Spreadsheet)]
            link_for(problem.session).retain(sheets)

    def _open_sheet_wizard(self, sheet: Spreadsheet) -> None:
        if sheet.wizard is not None and self.show_wizard is not None:
            wizard, sheet.wizard = sheet.wizard, None
            self.show_wizard(wizard)

    def new_document(self) -> None:
        """A blank document with the current Document Settings, once any unsaved changes have
        been let go (the GUI asks)."""
        if self.ask_discard is not None:
            self.ask_discard(self._new_document)
        else:
            self._new_document()

    def _new_document(self) -> None:
        self.replace_document(
            NspireDocument(settings=self.document.settings, sessions=self.sessions)
        )
        if self.on_new_document is not None:
            self.on_new_document()

    def screen(self) -> Screen:
        view = self.menu.view() if self.menu is not None and self.menu.open else None
        status = self.profile.status(self.document.settings)
        status = f"{status} CAPS" if self.caps else status
        return render(self.document, status, view, self.profile.pages, sorter=self.sorting)

    def page_name(self, kind: str) -> str:
        """The device's name for a page type ("Lists & Spreadsheet")."""
        return self.profile.pages.get(str(kind), str(kind))

    def press_keypad(self, name: str) -> None:
        self._perform(self.keypad_keys, name)

    def key_event(
        self,
        key: str,
        *,
        shift: bool = False,
        ctrl: bool = False,
        alt: bool = False,
        meta: bool = False,
    ) -> bool:
        """Handle a physical key. False means it is not ours: let the browser have it."""
        binding = self.binding_for(key, shift=shift, ctrl=ctrl, alt=alt, meta=meta)
        if binding is None:
            return False
        self.run(binding)
        return True

    def binding_for(
        self,
        key: str,
        *,
        shift: bool = False,
        ctrl: bool = False,
        alt: bool = False,
        meta: bool = False,
    ) -> Binding | None:
        """What a physical key does, without doing it (the GUI fetches the system clipboard
        before a paste)."""
        name = key_name(key, shift=shift, ctrl=ctrl, alt=alt, meta=meta)
        return None if name is None else self._cased(self.computer_keys.press(name))

    def _cased(self, binding: Binding | None) -> Binding | None:
        """With caps lock on, a typed letter swaps case (so Shift still gives a small letter)."""
        letter = binding is not None and binding.action == "insert" and binding.arg.isalpha()
        if self.caps and binding is not None and letter and len(binding.arg) == 1:
            return Binding("insert", binding.arg.swapcase())
        return binding

    def run_action(self, action: str, arg: str = "") -> None:
        """Do an action by name, for GUI buttons and menus."""
        self.run(Binding(action, arg))

    def paste_text(self, text: str) -> None:
        """Paste text from the system clipboard (the calculator's own nodes if it matches)."""
        self.run(Binding("paste", text))

    def run(self, binding: Binding) -> None:
        """Do a binding: document actions here, everything else on the current page."""
        if self._shell_action(binding) or self._document_action(binding):
            return
        sheet = self.sheet
        if sheet is not None:
            self._sheet_key(sheet, binding)
            return
        if binding.action in SHEET_ACTIONS:
            return  # a sheet's key on another page does nothing
        calculator = calculator_of(self.document.current)
        if binding.action in ("undo", "redo") and self._page_undo(binding.action):
            return
        if calculator is None:
            return
        calculator.perform(binding)
        if binding.action in ("copy", "cut") and self.clipboard_out is not None:
            self.clipboard_out(self.document.clipboard.text)

    def _sheet_key(self, sheet: Spreadsheet, binding: Binding) -> None:
        if binding.action == "context_menu":
            self._open_menu(sheet.context_menu())
            return
        undo = binding.action in ("undo", "redo") and not sheet.dialogs and sheet.mode is None
        if undo and sheet.editing is None:
            can = sheet.can_undo if binding.action == "undo" else sheet.can_redo
            if not can:  # nothing left on the page: the document's own undo (as the Calculator)
                (self.document.undo if binding.action == "undo" else self.document.redo)()
                self.retain_sheets()
                return
        sheet.perform(binding)
        if binding.action in ("copy", "cut") and self.clipboard_out is not None:
            self.clipboard_out(self.document.clipboard.text)
        self._open_sheet_wizard(sheet)

    def _page_undo(self, action: str) -> bool:
        """Undo or redo with nothing left to step in the entry line falls through to the document
        (emulator run S7 f: ctrl+Z on a fresh page undoes the page insert, ctrl+Y brings it back).
        True if the document took the key."""
        calculator = calculator_of(self.document.current)
        if calculator is not None and (
            calculator.error is not None or calculator.pending is not None
        ):
            return False  # the key belongs to the dialog or the run
        if action == "redo":
            if calculator is not None and calculator.can_redo:
                return False
            return self.document.redo()
        if calculator is not None and calculator.can_undo:
            return False
        return self.document.undo()

    def _shell_action(self, binding: Binding) -> bool:
        """Caps lock, menus and dialogs, which belong to the shell and not to a page."""
        if binding.action == "caps":
            self.caps = not self.caps
        elif self.menu is not None and self.menu.open:
            self._menu_key(binding)
        elif self.sorting:
            self._sorter_key(binding)
        elif binding == Binding("dialog", SORTER):
            self.sorting = True
        elif binding.action == "open_menu":
            name = binding.arg
            if name == "menu" and self.sheet is not None:
                name = "menu_sheet"
            elif name == "menu" and calculator_of(self.document.current) is None:
                name = "menu_stub"  # a stub has only About, Help
            self._open_menu(name)
        elif binding.action == "wizard":
            self._open_wizard(binding.arg)
        else:
            return binding.action in _MENU_ONLY  # a menu click with no menu open does nothing
        return True

    def _sorter_key(self, binding: Binding) -> None:
        """While the page sorter is open it takes every key. The arrows move the highlight (left
        and right through the pages in order, up and down between Problems), Enter, the centre
        key, Esc and ctrl+up close it, and Delete or del removes the highlighted page. A tap on a
        tile highlights it, and a tap on the highlighted tile opens it."""
        document = self.document
        action = binding.action
        if action in ("enter", "select", "escape") or binding == Binding("dialog", SORTER):
            self.sorting = False
        elif action == "sorter_go":
            self._sorter_tap(binding.arg)
        elif action == "open_menu":
            if binding.arg == "doc":  # a page's own Menu has nothing to do in the sorter
                self._open_menu(binding.arg)
        elif action in _SORTER_PASSES:
            self._document_action(binding)
        else:
            keys: dict[str, Callable[[], object]] = {
                "left": lambda: document.next_page(-1),
                "right": document.next_page,
                "up": lambda: self._sorter_problem(-1),
                "down": lambda: self._sorter_problem(1),
                "delete": document.delete_page,
                "backspace": document.delete_page,
                "undo": document.undo,
                "redo": document.redo,
            }
            key = keys.get(action)
            if key is not None:  # anything else (typing, the page's own keys) does nothing
                key()

    def _sorter_problem(self, step: int) -> None:
        """Up or down in the sorter: the same page number in the Problem above or below, or its
        last page when it has fewer."""
        document = self.document
        problem = document.problem + step
        if 0 <= problem < len(document.problems):
            document.go(problem, min(document.page, len(document.problems[problem].pages) - 1))

    def _sorter_tap(self, where: str) -> None:
        """A tap on tile `problem.page` (from 0) highlights it; a tap on the highlighted one opens
        it."""
        document = self.document
        problem, page = (int(part) for part in where.split("."))
        if (problem, page) == (document.problem, document.page):
            self.sorting = False
        else:
            document.go(problem, page)

    def _open_menu(self, name: str) -> None:
        root = self._variables_menu() if name == "variables" else self.profile.menus.get(name)
        if root is not None and name == "doc" and self.doc_extras is not None:
            extras = self.doc_extras()
            if extras:
                root = replace(root, items=(*root.items, *extras))
        if root is not None:
            self.menu = MenuState(root)

    def _variables_menu(self) -> MenuItem | None:
        """The var key: the current Problem's variables, each typed by choosing it. On a sheet's
        name cell it links the column instead (check 6, E7)."""
        sheet = self.sheet
        calculator = calculator_of(self.document.current)
        session = sheet.session if sheet is not None else calculator.session if calculator else None
        if session is None:
            return None
        rows = sorted(session.variables(), key=lambda row: row.name.casefold())
        if sheet is not None and sheet.cursor[1] == NAME_ROW:
            lists = tuple(
                MenuItem(row.name, "sheet", f"link:{row.name}", hint=row.text)
                for row in rows
                if row.text.startswith("{")
            )
            return MenuItem(
                "var",
                items=(
                    MenuItem("Store Var", "sheet", "store_var", key="1"),
                    MenuItem("Unlink", "sheet", "unlink", key="2"),
                    MenuItem(
                        "Link To:",
                        key="3",
                        jump=True,
                        items=lists or (MenuItem("(none)", "escape"),),
                    ),
                ),
            )
        items = tuple(
            MenuItem(row.text, "insert", f"{row.name}(", hint="function")
            if row.is_function
            else MenuItem(row.name, "insert", row.name, hint=f"{row.name} = {row.text}")
            for row in rows
        )
        return MenuItem("Variables", jump=True, items=items or (MenuItem("(none)", "escape"),))

    def _open_wizard(self, name: str) -> None:
        wizard = self.profile.wizards.get(name)
        if wizard is not None and self.show_wizard is not None:
            self.show_wizard(wizard)

    def finish_wizard(self, wizard: Wizard, values: dict[str, str]) -> list[str]:
        """Paste what a dialog built. Returns the problems instead if a field will not do."""
        problems = wizard.problems(values)
        if not problems:
            bindings = wizard.bindings(values)
            if self.sheet is not None and wizard.steps is None:
                # On a sheet a command's dialog (Distributions) puts `=its formula` in the
                # selected cell's entry line, to be entered with Return (run 4, S10)
                text = "".join(b.arg for b in bindings if b.action in ("insert", "insert_linear"))
                text = text.replace(MARK, "")
                bindings = [Binding("sheet", f"edit:={text}")] if text else []
            for binding in bindings:
                self.run(binding)
        return problems

    def store_wizard(self, wizard: Wizard, values: dict[str, str]) -> None:
        """Leave a live dialog's results in variables (the Finance Solver's `tvm.` set)."""
        calculator = calculator_of(self.document.current)
        if wizard.store is not None and calculator is not None:
            calculator.session.store_numbers(wizard.store(values))

    def _menu_key(self, binding: Binding) -> None:
        """While a menu is open it takes every key; a chosen leaf runs once the menu has closed."""
        assert self.menu is not None
        chosen = self.menu.press(binding.action, binding.arg)
        if not self.menu.open:
            self.menu = None
        if chosen is not None:
            self.run(chosen)

    def _document_action(self, binding: Binding) -> bool:
        document = self.document
        kind = (
            PageKind(binding.arg or PageKind.CALCULATOR)
            if binding.action.startswith("add")
            else None
        )
        steps = int(binding.arg or 1) if binding.action.startswith("move") else 0
        actions: dict[str, Callable[[], object]] = {
            "add_page": lambda: (
                document.can_add_page() and document.add_page(kind or PageKind.CALCULATOR)
            ),
            "add_problem": lambda: document.add_problem(kind or PageKind.CALCULATOR),
            "delete_page": document.delete_page,
            "next_page": document.next_page,
            "prev_page": lambda: document.next_page(-1),
            "move_page": lambda: document.move_page(document.page + steps),
            "move_problem": lambda: document.move_problem(document.problem + steps),
            "undo_pages": document.undo,
            "redo_pages": document.redo,
            "dialog": lambda: self.show_dialog and self.show_dialog(binding.arg),
            "new_document": self.new_document,
        }
        if binding.action in ("add_page", "add_problem") and not binding.arg:
            # ctrl+I, ctrl+doc, Doc > Insert > Page or Problem: choose the application first
            self._open_menu(binding.action)
            return True
        action = actions.get(binding.action)
        if action is None:
            return False
        action()
        self.retain_sheets()
        return True

    def _perform(self, keyboard: Keyboard, name: str) -> bool:
        binding = keyboard.press(name)
        if binding is None:
            return False
        cased = self._cased(binding) if keyboard is self.keypad_keys else binding
        assert cased is not None
        if cased.action == "paste" and not cased.arg and self.request_paste is not None:
            self.request_paste()  # the GUI fetches the system clipboard, then pastes
            return True
        self.run(cased)
        return True
