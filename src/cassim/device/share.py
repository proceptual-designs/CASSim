"""Share a document as a link (FR-DOC-007): compressed JSON in the URL fragment, so nothing
reaches a server. A link that would be too long is refused, and the caller offers a file instead.
"""

from __future__ import annotations

import base64
import zlib

from cassim.device.document import Document
from cassim.device.serialize import DocumentFileError, dumps, loads

PREFIX = "doc="
MAX_FRAGMENT = 2000  # characters, as in the SRS; longer links break in chat apps and e-mail
MAX_JSON = 2_000_000  # a bound on what a crafted fragment can expand to


class LinkTooLongError(ValueError):
    """The document does not fit in a link; export a file instead."""


def encode(document: Document) -> str:
    """The URL fragment (without `#`) for `document`."""
    packed = zlib.compress(dumps(document).encode("utf-8"), 9)
    fragment = PREFIX + base64.urlsafe_b64encode(packed).decode("ascii").rstrip("=")
    if len(fragment) > MAX_FRAGMENT:
        msg = f"the link would be {len(fragment)} characters (the limit is {MAX_FRAGMENT})"
        raise LinkTooLongError(msg)
    return fragment


def unpack(fragment: str) -> str | None:
    """The document text in a fragment, or None when the fragment is not a share link. Nothing is
    run: loading replays entries through the engine but never runs Python or programs
    (NFR-SEC-001)."""
    fragment = fragment.lstrip("#")
    if not fragment.startswith(PREFIX):
        return None
    body = fragment[len(PREFIX) :]
    try:
        packed = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
        expander = zlib.decompressobj()
        raw = expander.decompress(packed, MAX_JSON)
        if expander.unconsumed_tail:
            msg = "the link holds too much data"
            raise DocumentFileError(msg)
        return raw.decode("utf-8")
    except (ValueError, zlib.error) as error:
        if isinstance(error, DocumentFileError):
            raise
        msg = f"the link is damaged: {error}"
        raise DocumentFileError(msg) from error


def decode(fragment: str) -> Document | None:
    """The document in a fragment, loaded in this process, or None for a non-link."""
    text = unpack(fragment)
    return None if text is None else loads(text)
