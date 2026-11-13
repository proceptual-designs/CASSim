"""How a spreadsheet page reaches the sheets in its Problem's engine (slice 3b, decision 0031).

The page sends `sheet` ops and later takes the replies for its page id, the same way whether the
maths runs here (`LocalLink`, the desktop) or in the engine worker (`RemoteLink`, the browser:
the ops wait in the `RemoteSession`'s outbox for the app's Runner, and its replies arrive with
`RemoteSession.accept`).

One link per Problem session. It numbers the Problem's sheet pages and knows which are alive, so
a deleted page's sheet is dropped from the engine (freeing its lists) and an undone delete brings
it back.

Nothing here loads SymPy: `LocalLink` imports the engine side only when it is made.
"""

from __future__ import annotations

import weakref
from typing import TYPE_CHECKING, Protocol

from cassim.device.engine import RemoteSession

if TYPE_CHECKING:
    from collections.abc import Sequence

    from cassim.core.session import Session
    from cassim.device.engine import SheetOp, SheetReply
    from cassim.device.sheets import ProblemSheets


class SheetPage(Protocol):
    """What a link needs of a page model: its id, and the op that rebuilds it in an engine."""

    id: int

    def restore_op(self) -> SheetOp: ...


class SheetLink:
    """The part shared by both links: page ids and which pages are alive."""

    deferred = False  # replies come later, through the Runner

    def __init__(self) -> None:
        self._next = 1
        self._alive: set[int] = set()

    def new_id(self) -> int:
        self._next += 1
        return self._next - 1

    def send(self, op: SheetOp) -> None:
        raise NotImplementedError

    def take(self, page: int) -> list[SheetReply]:
        """The replies for `page` that have arrived since it last looked."""
        raise NotImplementedError

    def retain(self, pages: Sequence[SheetPage]) -> None:
        """The sheet pages the Problem holds now: a page that went away (deleted) is dropped
        from the engine, and one that came back (an undone delete, a load) is rebuilt there."""
        live = {page.id: page for page in pages}
        for gone in sorted(self._alive - live.keys()):
            self.send({"op": "sheet", "page": gone, "action": "drop", "args": {}})
        for back in sorted(live.keys() - self._alive):
            self.send(live[back].restore_op())
        self._alive = set(live)

    def alive(self, page: int) -> None:
        """A page made on this link (new, not loaded) counts as alive from the start."""
        self._alive.add(page)


class RemoteLink(SheetLink):
    deferred = True

    def __init__(self, session: RemoteSession) -> None:
        super().__init__()
        self._session = session

    def send(self, op: SheetOp) -> None:
        self._session.outbox.append(op)

    def take(self, page: int) -> list[SheetReply]:
        return self._session.sheet_inbox.pop(page, [])


class LocalLink(SheetLink):
    """The sheets run in this process, beside the Problem's `Session`: an op is done at once."""

    def __init__(self, session: Session) -> None:
        super().__init__()
        from cassim.device.sheets import ProblemSheets  # noqa: PLC0415 (loads SymPy)

        self.sheets: ProblemSheets = ProblemSheets(session)
        self._inbox: dict[int, list[SheetReply]] = {}

    def _keep(self, replies: dict[int, SheetReply]) -> None:
        for page, reply in replies.items():
            self._inbox.setdefault(page, []).append(reply)

    def send(self, op: SheetOp) -> None:
        replies: dict[int, SheetReply] = {}
        self.sheets.run(op, replies)
        self.sheets.settle(replies)
        self._keep(replies)

    def take(self, page: int) -> list[SheetReply]:
        # A Calculator entry here changes the Session directly, with no reply: catch up first.
        replies: dict[int, SheetReply] = {}
        self.sheets.settle(replies)
        self._keep(replies)
        return self._inbox.pop(page, [])


_LINKS: weakref.WeakKeyDictionary[object, SheetLink] = weakref.WeakKeyDictionary()


def link_for(session: Session | RemoteSession) -> SheetLink:
    """The one link of a Problem's session."""
    link = _LINKS.get(session)
    if link is None:
        link = RemoteLink(session) if isinstance(session, RemoteSession) else LocalLink(session)
        _LINKS[session] = link
    return link
