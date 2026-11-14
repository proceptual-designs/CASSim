"""Documents saved by name in browser storage (FR-DOC-010): Open, Save and Save As.

The library is an index of names, each document's text stored under its own key. The autosave
is separate: it keeps the working state through a reload, but only Save writes the named copy, so
the open document can differ from its saved copy ("dirty"). Files on disk are Import and Export.

No Flet here: the app gives the library its storage as `read` and `write` callables.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from cassim.doc.document import Document
from cassim.doc.serialize import to_dict

INDEX_KEY = "library"  # the index of saved names, after the device's storage prefix
DOC_PREFIX = "doc:"  # each saved document's text is under `doc:<name>`
CURRENT_KEY = "current"  # which saved document is open, and whether it has changed since
UNTITLED = "Untitled"
MAX_NAME = 60


def fingerprint(data: dict[str, Any]) -> str:
    """What decides whether a document has changed since it was saved: its contents and
    settings, but not which page is showing."""
    kept = {key: value for key, value in data.items() if key not in ("problem", "page")}
    text = json.dumps(kept, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def document_fingerprint(document: Document) -> str:
    return fingerprint(to_dict(document))


def clean_name(text: str) -> str:
    """A name as typed, made fit to save under: spaces trimmed and runs of them joined, the
    `.cassim.json` ending dropped, at most MAX_NAME characters. Empty means not usable."""
    name = " ".join(text.split())
    for ending in (".cassim.json", ".json"):
        if name.lower().endswith(ending):
            name = name[: -len(ending)].rstrip()
    return name[:MAX_NAME]


@dataclass
class Saved:
    """One saved document in the index."""

    name: str
    when: float  # seconds since the epoch, when it was last saved


@dataclass
class Library:
    """The index of saved documents, newest first."""

    items: list[Saved] = field(default_factory=list)

    def names(self) -> list[str]:
        return [item.name for item in self.items]

    def has(self, name: str) -> bool:
        return any(item.name.casefold() == name.casefold() for item in self.items)

    def spelled(self, name: str) -> str | None:
        """The saved spelling of `name` (names are matched without regard to case)."""
        return next((i.name for i in self.items if i.name.casefold() == name.casefold()), None)

    def touch(self, name: str, when: float | None = None) -> None:
        """Record `name` as saved now, at the top of the list (replacing any other case)."""
        self.remove(name)
        self.items.insert(0, Saved(name, time.time() if when is None else when))

    def remove(self, name: str) -> None:
        self.items = [i for i in self.items if i.name.casefold() != name.casefold()]

    def dumps(self) -> str:
        return json.dumps([[i.name, i.when] for i in self.items], ensure_ascii=False)

    @classmethod
    def loads(cls, text: str | None) -> Library:
        """The index; anything unreadable is skipped rather than losing the rest."""
        library = cls()
        try:
            rows = json.loads(text) if text else []
        except ValueError:
            return library
        if not isinstance(rows, list):
            return library
        for row in rows:
            if (
                isinstance(row, list)
                and len(row) == 2  # noqa: PLR2004
                and isinstance(row[0], str)
                and isinstance(row[1], int | float)
                and row[0]
                and not library.has(row[0])
            ):
                library.items.append(Saved(row[0], float(row[1])))
        return library


@dataclass
class Current:
    """The open document's link to the library: the name it is saved under (None: never saved
    here) and the fingerprint of that saved copy. Kept with the autosave, so the name and the
    unsaved marker survive a reload."""

    stored: str | None = None
    saved: str = ""  # fingerprint of the saved copy ("" when there is none)

    def dumps(self) -> str:
        return json.dumps({"stored": self.stored, "saved": self.saved}, ensure_ascii=False)

    @classmethod
    def loads(cls, text: str | None) -> Current:
        try:
            data = json.loads(text) if text else {}
        except ValueError:
            return cls()
        if not isinstance(data, dict):
            return cls()
        stored, saved = data.get("stored"), data.get("saved")
        return cls(
            stored if isinstance(stored, str) and stored else None,
            saved if isinstance(saved, str) else "",
        )


def title(document_name: str, *, dirty: bool) -> str:
    """The name in the screen's title bar: `*` in front while there are unsaved changes."""
    return f"{'*' if dirty else ''}{document_name or UNTITLED}"


type Read = Callable[[str], Awaitable[str | None]]
type Write = Callable[[str, str], None]


class Store:
    """The library in storage: reads and writes the index and the documents' texts."""

    def __init__(self, read: Read, write: Write, remove: Callable[[str], None]) -> None:
        self._read = read
        self._write = write
        self._remove = remove
        # Read once, then kept here: writes are queued, so reading the index straight after a
        # save could miss it.
        self._library: Library | None = None
        self._written: dict[str, str] = {}  # texts saved this session, by name, for the same reason

    @property
    def cached(self) -> Library | None:
        """The index if it has been read (the app reads it at start-up)."""
        return self._library

    async def index(self) -> Library:
        if self._library is None:
            self._library = Library.loads(await self._read(INDEX_KEY))
        return self._library

    async def text(self, name: str) -> str | None:
        if name in self._written:
            return self._written[name]
        return await self._read(DOC_PREFIX + name)

    async def save(self, name: str, text: str) -> None:
        library = await self.index()
        old = library.spelled(name)
        if old is not None and old != name:
            self._remove(DOC_PREFIX + old)  # saved again with other capitals
            self._written.pop(old, None)
        self._write(DOC_PREFIX + name, text)
        self._written[name] = text
        library.touch(name)
        self._write(INDEX_KEY, library.dumps())

    async def delete(self, name: str) -> None:
        library = await self.index()
        library.remove(name)
        self._remove(DOC_PREFIX + name)
        self._written.pop(name, None)
        self._write(INDEX_KEY, library.dumps())
