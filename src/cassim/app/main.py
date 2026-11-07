"""Entry point: `uv run flet run src/cassim/app/main.py` (or `python -m cassim.app.main`)."""

from __future__ import annotations

import flet as ft

from cassim.app.state import AppState, Mode
from cassim.app.theme import DARK
from cassim.app.ui import (
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    CalculatorView,
    Keypad,
    Sidebar,
    chip,
    settings_dialog,
    sorter_dialog,
    system_settings_dialog,
)
from cassim.device.keys import Binding
from cassim.device.serialize import DocumentFileError, dumps, loads

# TODO(M2b): a first visit should pick Handheld below about 700 px (decision 0013 item 3).
# Flet fires no resize event at start-up, so this needs a different hook.


AUTOSAVE_KEY = "cassim.autosave"


def connect_clipboard(page: ft.Page, state: AppState) -> ft.Clipboard:
    """Copy and cut also fill the system clipboard; paste reads it (see `Clipboard`)."""
    clipboard = ft.Clipboard()
    page.services.append(clipboard)

    def copy_out(text: str) -> None:
        page.run_task(clipboard.set, text)

    state.clipboard_out = copy_out
    return clipboard


class App:
    """Wires the state to the views: the top bar, the screen, the keypad and the sidebar."""

    def __init__(self, page: ft.Page, state: AppState) -> None:
        self.page = page
        self.state = state
        self.theme = DARK
        self.view = CalculatorView(state, self.theme, self.act)
        self.keypad = Keypad(state, self.press, self.theme)
        self.sidebar = Sidebar(state, self.refresh, self.theme)
        self.toolbar = ft.Row(spacing=6, wrap=True)
        self.layout = ft.Container(expand=True)
        self.clipboard = connect_clipboard(page, state)
        state.show_dialog = self.show_dialog
        self.files = ft.FilePicker()
        page.services.append(self.files)
        self.prefs = ft.SharedPreferences()
        page.services.append(self.prefs)
        self.saved = ""  # the last text autosaved, so an idle refresh writes nothing

    async def start(self) -> None:
        page = self.page
        page.title = "CASSim"
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = self.theme.background
        page.padding = 12
        page.on_keyboard_event = self.on_key
        self.arrange()
        page.add(ft.Column([self.toolbar, self.layout], expand=True))
        await self.recover()
        self.refresh()
        print("CASSIM: READY", flush=True)

    def autosave(self) -> None:
        """Keep the document in browser storage so a reload or crash loses nothing (FR-DOC-003)."""
        text = dumps(self.state.document)
        if text != self.saved:
            self.saved = text
            self.page.run_task(self.prefs.set, AUTOSAVE_KEY, text)

    async def recover(self) -> None:
        """Reopen the autosaved document, if there is a readable one."""
        text = await self.prefs.get(AUTOSAVE_KEY)
        if not isinstance(text, str):
            return
        try:
            self.state.replace_document(loads(text))
            self.saved = text
        except DocumentFileError:
            return  # a damaged autosave is ignored, and overwritten by the next change

    def refresh(self) -> None:
        self.autosave()
        self.view.refresh()
        self.keypad.refresh()
        self.sidebar.refresh()
        self.toolbar.controls = self.toolbar_controls()
        self.page.update()

    def press(self, name: str) -> None:
        self.state.press_keypad(name)
        self.refresh()

    async def on_key(self, e: ft.KeyboardEvent) -> None:
        state = self.state
        binding = state.binding_for(e.key, shift=e.shift, ctrl=e.ctrl, alt=e.alt, meta=e.meta)
        if binding is None:
            return
        if binding.action == "paste":  # the system clipboard may hold text from elsewhere
            binding = Binding("paste", await self.clipboard.get() or "")
        state.run(binding)
        self.refresh()

    def act(self, action: str, arg: str = "") -> None:
        self.state.run_action(action, arg)
        self.refresh()

    def set_mode(self, mode: Mode) -> None:
        self.state.mode = mode
        self.arrange()
        self.refresh()

    def toolbar_controls(self) -> list[ft.Control]:
        theme, mode = self.theme, self.state.mode
        return [
            chip("Handheld", lambda: self.set_mode(Mode.HANDHELD), theme, on=mode is Mode.HANDHELD),
            chip("Computer", lambda: self.set_mode(Mode.COMPUTER), theme, on=mode is Mode.COMPUTER),
            chip("◀ page", lambda: self.act("prev_page"), theme),
            chip("page ▶", lambda: self.act("next_page"), theme),
            chip("+ page", lambda: self.act("add_page"), theme),
            chip("+ problem", lambda: self.act("add_problem"), theme),
            chip("delete page", lambda: self.act("delete_page"), theme),
            chip("Doc", lambda: self.act("open_menu", "doc"), theme),
            chip("Menu", lambda: self.act("open_menu", "menu"), theme),
            chip("Sorter", lambda: self.show_dialog("page_sorter"), theme),
            chip("settings", self.open_settings, theme),
        ]

    def show_dialog(self, name: str) -> None:
        if name == "save_file":
            self.page.run_task(self.save_file)
        elif name == "open_file":
            self.page.run_task(self.open_file)
        elif name == "document_settings":
            self.open_settings()
        elif name == "system_settings":
            system_settings_dialog(self.page, self.state, self.on_system_change, self.theme)
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
            self.state.replace_document(loads(picked[0].bytes.decode("utf-8")))
        except (DocumentFileError, UnicodeDecodeError) as error:
            self.notice("Cannot open that file", str(error))
        self.refresh()

    def notice(self, title: str, message: str) -> None:
        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text(title),
                content=ft.Text(message),
                actions=[ft.TextButton("OK", on_click=lambda _: self.page.pop_dialog())],
            )
        )

    def on_system_change(self) -> None:
        self.refresh()

    def open_settings(self) -> None:
        settings_dialog(self.page, self.state, self.refresh, self.theme)

    def arrange(self) -> None:
        view = self.view.control
        if self.state.mode is Mode.HANDHELD:
            view.width, view.height = SCREEN_WIDTH, SCREEN_HEIGHT
            view.expand = False
            self.layout.content = ft.Column(
                [view, self.keypad.control],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            )
        else:
            view.width = view.height = None
            view.expand = True
            self.layout.content = ft.Row(
                [ft.Container(self.sidebar.control, width=170, padding=8), view],
                expand=True,
                spacing=12,
            )


async def main(page: ft.Page) -> None:
    await App(page, AppState()).start()


if __name__ == "__main__":
    ft.run(main)
