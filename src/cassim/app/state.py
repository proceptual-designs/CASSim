"""The app's state without Flet: a document, the display mode and the two keyboards."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from cassim.app.keyboard import key_name
from cassim.device.document import Document, PageKind
from cassim.device.keys import Binding, Keyboard
from cassim.device.menu import MenuState
from cassim.device.screen import Screen, render
from cassim.profiles import Profile, nspire


class Mode(StrEnum):
    HANDHELD = "handheld"
    COMPUTER = "computer"


@dataclass
class System:
    """System Settings: how the app looks, apart from the document (FR-DOC-002)."""

    start_mode: Mode = Mode.COMPUTER
    math_size: int = 20  # LaTeX size in the entry and history


MATH_SIZES = {"Small": 16, "Normal": 20, "Large": 26}


class AppState:
    """Everything the views draw. A profile supplies the keymaps and keypad (FR-DEV-007)."""

    def __init__(
        self,
        document: Document | None = None,
        *,
        mode: Mode = Mode.COMPUTER,
        profile: Profile = nspire.PROFILE,
    ) -> None:
        self.document = document if document is not None else Document()
        self.mode = mode
        self.profile = profile
        self.keypad_keys = Keyboard(profile.handheld, profile.modifiers)
        self.computer_keys = Keyboard(profile.computer)
        self.clipboard_out: Callable[[str], None] | None = None  # set by the GUI: system clipboard
        self.show_dialog: Callable[[str], None] | None = None  # set by the GUI: named dialogs
        self.menu: MenuState | None = None
        self.system = System(mode)

    @property
    def pending(self) -> str:
        """The keypad modifier waiting for the next key ("ctrl", "shift" or "")."""
        return self.keypad_keys.pending

    def replace_document(self, document: Document) -> None:
        """Open another document (a new one, a file or the autosave) and close any menu."""
        self.document = document
        self.menu = None
        self.keypad_keys.pending = ""

    def new_document(self) -> None:
        """A blank document with the current Document Settings."""
        self.replace_document(Document(settings=self.document.settings))

    def screen(self) -> Screen:
        view = self.menu.view() if self.menu is not None and self.menu.open else None
        return render(self.document, self.profile.status(self.document.settings), view)

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
        return None if name is None else self.computer_keys.press(name)

    def run_action(self, action: str, arg: str = "") -> None:
        """Do an action by name, for GUI buttons and menus."""
        self.run(Binding(action, arg))

    def paste_text(self, text: str) -> None:
        """Paste text from the system clipboard (the calculator's own nodes if it matches)."""
        self.run(Binding("paste", text))

    def run(self, binding: Binding) -> None:
        """Do a binding: document actions here, everything else on the current page."""
        if self.menu is not None and self.menu.open:
            self._menu_key(binding)
            return
        if binding.action == "open_menu":
            self._open_menu(binding.arg)
            return
        if self._document_action(binding):
            return
        calculator = self.document.current.calculator
        if calculator is None:
            return
        calculator.perform(binding)
        if binding.action in ("copy", "cut") and self.clipboard_out is not None:
            self.clipboard_out(self.document.clipboard.text)

    def _open_menu(self, name: str) -> None:
        root = self.profile.menus.get(name)
        if root is not None:
            self.menu = MenuState(root)

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
        action = actions.get(binding.action)
        if action is None:
            return False
        action()
        return True

    def _perform(self, keyboard: Keyboard, name: str) -> bool:
        binding = keyboard.press(name)
        if binding is None:
            return False
        self.run(binding)
        return True
