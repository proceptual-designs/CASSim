"""Open, Save and Save As for any device: documents kept by name in the app's own storage.

The convention every CASSim app follows (decision 0033, FR-DOC-010): Open and Save work on
documents kept by name in storage the app looks after (IndexedDB in the browser, the app's
preferences on the desktop), under the device's own prefix. Files on disk are Import and Export
only. A device gives this class its text (`dump`) and a way to take a saved text back (`load`),
and puts `open`, `save` and `save_as` in its Doc menu beside its own Import and Export.

Every app uses it, the Nspire included (SDD-15 section 9.3). An app whose documents load
asynchronously (the Nspire recalculates one through its engine) gives a coroutine as `load`, and
an app with its own idea of "changed" (the Nspire ignores which page is showing) gives `mark`.
"""

from __future__ import annotations

import functools
import hashlib
import inspect
from collections.abc import Awaitable, Callable
from datetime import datetime

import flet as ft

from cassim.app.shell import Shell
from cassim.doc.library import CURRENT_KEY, MAX_NAME, UNTITLED, Current, Store, clean_name


class SavedDocuments:
    """One device's saved documents and the three dialogs that use them."""

    def __init__(  # noqa: PLR0913  (one keyword for each thing a device supplies)
        self,
        page: ft.Page,
        shell: Shell,
        *,
        dump: Callable[[str], str],
        load: Callable[[str, str], Awaitable[None] | None],
        changed: Callable[[], None] | None = None,
        said: Callable[[str], None] | None = None,
        noun: str = "document",
        menu: str = "Doc",
        mark: Callable[[], str] | None = None,
        on_dialog: Callable[[ft.AlertDialog | None], None] | None = None,
        suggest: Callable[[], str] | None = None,
        open_title: str = "Open",
    ) -> None:
        """`dump(name)` is the open document as text, to save under `name`; `load(text, name)`
        replaces the open document with a saved one (a coroutine if that takes time) and raises
        ValueError if it cannot. `changed` is called after the open document or its name
        changes, and `said` with a short note such as "Saved" for the device to show. `noun` is
        what the device calls a document ("calculation", "program"), and `menu` the path to its
        Save and Export ("Doc", or the Nspire's "Doc ▸ File"). `mark` decides whether the
        document has changed (by default, its dumped text). `on_dialog` hears the Save as dialog
        open (with the dialog) and close (with None), so a device can send keys to its name box;
        `suggest` is the name it offers; `open_title` names the Open dialog as its menu item."""
        self.page = page
        self.shell = shell
        self.dump = dump
        self.load = load
        self.changed = changed or (lambda: None)
        self.said = said or (lambda _: None)
        self.noun = noun
        self.menu = menu
        self._mark = mark
        self.on_dialog = on_dialog or (lambda _: None)
        self.suggest = suggest
        self.open_title = open_title
        self.current = Current()

    @functools.cached_property
    def store(self) -> Store:
        """The device's library, under its storage prefix (made on first use)."""
        return Store(self.shell.read, self.shell.write, self.shell.remove)

    # ---- state --------------------------------------------------------------------------------

    async def start(self) -> None:
        """Read the index and which saved document is open (kept through a reload)."""
        await self.store.index()
        self.current = Current.loads(await self.shell.read(CURRENT_KEY))

    @property
    def name(self) -> str:
        """The name the open document is saved under, or "Untitled"."""
        return self.current.stored or UNTITLED

    def mark(self) -> str:
        """What decides whether the open document differs from its saved copy."""
        if self._mark is not None:
            return self._mark()
        return hashlib.sha256(self.dump("").encode("utf-8")).hexdigest()

    def dirty(self) -> bool:
        return self.mark() != self.current.saved

    def remember(self, current: Current) -> None:
        self.current = current
        self.shell.write(CURRENT_KEY, current.dumps())

    def fresh(self) -> None:
        """The open document is new and has nothing to lose yet (New, Reset, a first visit)."""
        self.remember(Current(None, self.mark()))

    def unsaved(self) -> None:
        """The open document came from outside the library (an imported file, an example, a
        link): it is saved nowhere here until Save."""
        self.remember(Current(None, ""))

    # ---- Save and Save As ---------------------------------------------------------------------

    def save(self, _: object = None) -> None:
        """Save under the document's name, or ask for one if it has never been saved here."""
        if self.current.stored is None:
            self.save_as()
        else:
            self.page.run_task(self.store_as, self.current.stored)

    async def store_as(self, name: str) -> None:
        await self.store.save(name, self.dump(name))
        self.remember(Current(name, self.mark()))
        self.changed()
        self.said(f"Saved “{name}” in this app.")

    def save_as(self, _: object = None) -> None:
        """Ask for a name, then save under it (asking first before replacing another one)."""
        start = self.suggest() if self.suggest is not None else self.current.stored or ""
        field = ft.TextField(value=start, label="Name", autofocus=True, max_length=MAX_NAME)

        def close() -> None:
            self.page.pop_dialog()
            self.on_dialog(None)

        def done(_: object = None) -> None:
            name = clean_name(field.value or "")
            if not name:
                field.error = "Type a name"
                field.update()
                return
            close()
            index = self.store.cached
            other = index.spelled(name) if index is not None else None
            if other is not None and other.casefold() != (self.current.stored or "").casefold():

                async def replace() -> None:
                    await self.store_as(name)

                self.shell.confirm(
                    f"Replace saved {self.noun}?",
                    f"“{other}” is already saved here. Replace it with this {self.noun}?",
                    "Replace",
                    replace,
                )
                return
            self.page.run_task(self.store_as, name)

        field.on_submit = done
        dialog = ft.AlertDialog(
            title=ft.Text("Save as"),
            content=ft.Column(
                [
                    ft.Text(
                        f"Saved in this app, on this device. {self.menu} ▸ Export file… "
                        "saves a file you can move or share.",
                        size=13,
                    ),
                    field,
                ],
                tight=True,
                width=min(360, (self.page.width or 360) - 80),
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: close()),
                ft.TextButton("Save", on_click=done),
            ],
        )
        self.on_dialog(dialog)  # before it shows: the keys go to the name box
        self.page.show_dialog(dialog)

    # ---- Open ---------------------------------------------------------------------------------

    def open(self, _: object = None) -> None:
        """The saved documents, newest first; each can be opened or deleted."""
        index = self.store.cached
        items = index.items if index is not None else []
        if not items:
            self.shell.notice(
                f"No saved {self.noun}s",
                f"Nothing is saved here yet. {self.menu} ▸ Save keeps a {self.noun} in this app; "
                f"{self.menu} ▸ Import file… opens a file.",
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
                    await self.store.delete(name)
                    if (self.current.stored or "").casefold() == name.casefold():
                        self.unsaved()  # the open copy is now saved nowhere
                    self.changed()
                    self.open()

                self.shell.confirm(
                    f"Delete “{name}”?",
                    "It is removed from this app's storage. This cannot be undone.",
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
                title=ft.Text(self.open_title),
                content=ft.Column(
                    rows,
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                    width=min(380, (self.page.width or 380) - 80),
                ),
                actions=[ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog())],
            )
        )

    async def open_saved(self, name: str) -> None:
        text = await self.store.text(name)
        if text is None:
            self.shell.notice(f"Cannot open “{name}”", "It is no longer in this app's storage.")
            return
        try:
            loading = self.load(text, name)
            if inspect.isawaitable(loading):
                await loading
        except ValueError as error:
            self.shell.notice(f"Cannot open “{name}”", str(error))
            return
        self.remember(Current(name, self.mark()))
        self.changed()

    def ask_discard(self, then: Callable[[], object]) -> None:
        """Do `then` (which replaces the open document) at once, or after asking when the open
        document has changes that are not saved."""
        if not self.dirty():
            then()
            return

        async def discard() -> None:
            then()

        self.shell.confirm(
            "Discard changes?",
            f"This {self.noun} has changes that are not saved. {self.menu} ▸ Save keeps them.",
            "Discard",
            discard,
        )
