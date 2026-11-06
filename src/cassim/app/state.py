"""The app's state without Flet: a document, the display mode and the two keyboards."""

from __future__ import annotations

from collections.abc import Callable
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

    @property
    def pending(self) -> str:
        """The keypad modifier waiting for the next key ("ctrl", "shift" or "")."""
        return self.keypad_keys.pending

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
        match binding.action:
            case "add_page":
                if document.can_add_page():
                    document.add_page(PageKind(binding.arg or PageKind.CALCULATOR))
            case "add_problem":
                document.add_problem(PageKind(binding.arg or PageKind.CALCULATOR))
            case "delete_page":
                document.delete_page()
            case "next_page":
                document.next_page()
            case "prev_page":
                document.next_page(-1)
            case "dialog":
                if self.show_dialog is not None:
                    self.show_dialog(binding.arg)
            case _:
                return False
        return True

    def _perform(self, keyboard: Keyboard, name: str) -> bool:
        binding = keyboard.press(name)
        if binding is None:
            return False
        self.run(binding)
        return True
