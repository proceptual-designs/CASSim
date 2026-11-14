# Requirements traced here: FR-DOC-010
"""Documents saved by name in the browser: Save, Save As, Open, and the unsaved marker."""

import asyncio
import json
from typing import Any

import pytest
from tests.app.test_splitter_drag import handheld_app

from cassim.device.keys import Binding
from cassim.devices.nspire.document import Document
from cassim.devices.nspire.ui import app as nspire_app
from cassim.doc.library import (
    CURRENT_KEY,
    INDEX_KEY,
    Current,
    Library,
    Store,
    clean_name,
    document_fingerprint,
    title,
)


@pytest.fixture(autouse=True)
def quick_notes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(nspire_app, "FLASH_SECONDS", 0.0)


class Memory:
    """Browser storage as a dict."""

    def __init__(self) -> None:
        self.texts: dict[str, str] = {}

    async def read(self, key: str) -> str | None:
        return self.texts.get(key)

    def write(self, key: str, text: str) -> None:
        self.texts[key] = text

    def remove(self, key: str) -> None:
        self.texts.pop(key, None)

    def store(self) -> Store:
        return Store(self.read, self.write, self.remove)


def test_names_are_tidied_and_matched_without_case() -> None:
    assert clean_name("  Week 3   revision.cassim.json ") == "Week 3 revision"
    assert clean_name("   ") == ""
    assert len(clean_name("x" * 200)) == 60
    library = Library()
    library.touch("Methods", 1.0)
    library.touch("Spec", 2.0)
    assert library.names() == ["Spec", "Methods"]  # newest first
    assert library.has("METHODS")
    assert library.spelled("methods") == "Methods"
    library.touch("methods", 3.0)
    assert library.names() == ["methods", "Spec"]


def test_a_damaged_index_keeps_what_it_can() -> None:
    text = json.dumps([["Good", 1.5], ["", 2], [3, 4], "x", ["Good", 9], ["Also", 2]])
    assert Library.loads(text).names() == ["Good", "Also"]
    assert Library.loads("not json").names() == []
    assert Library.loads('{"a": 1}').names() == []
    assert Current.loads("[]") == Current()
    assert Current.loads(Current("A", "f").dumps()) == Current("A", "f")


def test_the_title_marks_unsaved_changes() -> None:
    assert title("Methods", dirty=False) == "Methods"
    assert title("Methods", dirty=True) == "*Methods"
    assert title("", dirty=False) == "Untitled"


def test_the_fingerprint_ignores_which_page_is_showing() -> None:
    document = Document()
    before = document_fingerprint(document)
    document.add_page()
    added = document_fingerprint(document)
    assert added != before
    document.next_page(-1)
    assert document_fingerprint(document) == added


def test_the_store_saves_lists_and_deletes() -> None:
    memory = Memory()
    store = memory.store()

    async def run() -> None:
        await store.save("Methods", "one")
        await store.save("Spec", "two")
        await store.save("methods", "three")  # the same name with other capitals
        assert (await store.index()).names() == ["methods", "Spec"]
        assert await store.text("methods") == "three"
        assert "doc:Methods" not in memory.texts
        await store.delete("Spec")
        assert (await store.index()).names() == ["methods"]
        assert "doc:Spec" not in memory.texts
        assert Library.loads(memory.texts[INDEX_KEY]).names() == ["methods"]

    asyncio.run(run())


def library_app() -> tuple[Any, Any, Memory]:
    app, page = handheld_app()
    memory = Memory()
    app.library = memory.store()
    shell: Any = app.shell
    shell.write = memory.write
    shell.read = memory.read
    page.dialogs = []
    page.show_dialog = page.dialogs.append
    page.pop_dialog = lambda: page.dialogs.pop() if page.dialogs else None
    asyncio.run(app.library.index())
    return app, page, memory


def test_typing_marks_the_document_unsaved_and_save_clears_it() -> None:
    app, page, memory = library_app()
    app.save_now()
    assert not app.dirty
    app.state.run(Binding("insert", "1"))
    app.save_now()
    assert app.dirty
    assert app.doc_title() == "*Untitled"
    asyncio.run(app.store_as("Week 1"))
    page.run_queued()
    assert not app.dirty
    assert app.state.doc_title == "Week 1"
    assert app.state.document.name == "Week 1"
    assert Current.loads(memory.texts[CURRENT_KEY]).stored == "Week 1"
    assert "doc:Week 1" in memory.texts
    app.state.run(Binding("insert", "2"))
    app.save_now()
    assert app.state.doc_title == "*Week 1"  # the autosave does not write the named copy
    assert '"entry":"1"' in memory.texts["doc:Week 1"]


def test_save_asks_for_a_name_only_the_first_time() -> None:
    app, page, _ = library_app()
    app.show_dialog("save")
    assert page.dialogs  # Save As, since it was never saved here
    assert app.typing_dialog is page.dialogs[-1]
    page.dialogs.clear()
    app.current = Current("Week 1", "")
    app.show_dialog("save")
    assert not page.dialogs
    page.run_queued()
    assert not app.dirty


def test_a_new_document_asks_before_dropping_unsaved_changes() -> None:
    app, page, _ = library_app()
    app.state.run(Binding("insert", "1"))
    app.state.run_action("new_document")
    assert len(page.dialogs) == 1  # Discard changes?
    assert app.state.document.current.model.editor.linear() == "1"
    page.dialogs.clear()
    asyncio.run(app.store_as("Kept"))
    page.run_queued()
    app.state.run_action("new_document")  # saved: no question
    assert not page.dialogs
    assert app.state.document.current.model.editor.linear() == ""
    assert app.current == Current(None, document_fingerprint(app.state.document))
    assert app.state.doc_title == "Untitled"


def test_open_shows_the_saved_documents_and_opens_one() -> None:
    app, page, _ = library_app()
    app.state.run(Binding("insert", "7"))
    asyncio.run(app.store_as("Seven"))
    page.run_queued()
    app.state.run_action("new_document")
    app.show_dialog("open_document")
    assert len(page.dialogs) == 1
    asyncio.run(app.open_saved("Seven"))
    assert app.state.document.current.model.editor.linear() == "7"
    assert app.state.doc_title == "Seven"
    assert not app.dirty


def test_open_with_nothing_saved_says_so(monkeypatch: pytest.MonkeyPatch) -> None:
    app, _, _ = library_app()
    told: list[str] = []
    monkeypatch.setattr(app, "notice", lambda heading, _: told.append(heading))
    app.show_dialog("open_document")
    assert told == ["No saved documents"]


def test_the_name_and_the_marker_survive_a_reload() -> None:
    app, page, memory = library_app()
    app.state.run(Binding("insert", "1"))
    asyncio.run(app.store_as("Week 1"))
    page.run_queued()
    app.state.run(Binding("insert", "2"))
    app.save_now()
    page.run_queued()
    again, _, _ = library_app()
    again.shell.read = memory.read
    again.library = memory.store()
    again.first_visit = False
    asyncio.run(again.recover())
    assert again.state.doc_title == "*Week 1"
    assert again.current.stored == "Week 1"
