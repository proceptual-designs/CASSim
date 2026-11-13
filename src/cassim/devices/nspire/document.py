"""Nspire documents: the shared document model with the Nspire's page types filled in."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cassim.device.engine import RemoteSession, local_session
from cassim.devices.nspire.pages import PAGES, PageKind
from cassim.doc import document, serialize, share

if TYPE_CHECKING:
    from collections.abc import Callable

    from cassim.core.session import Session
    from cassim.core.settings import Settings

__all__ = ["Document", "PageKind", "decode", "loads"]


class Document(document.Document):
    """A document whose pages are the Nspire's."""

    def __init__(
        self,
        name: str = "Untitled",
        settings: Settings | None = None,
        sessions: Callable[[Settings], Session | RemoteSession] = local_session,
    ) -> None:
        super().__init__(PAGES, name, settings, sessions)


def loads(text: str) -> document.Document:
    """The Nspire document in a file's text, loaded in this process."""
    return serialize.loads(text, PAGES)


def decode(fragment: str) -> document.Document | None:
    """The Nspire document in a share link's fragment, or None for a non-link."""
    return share.decode(fragment, PAGES)
