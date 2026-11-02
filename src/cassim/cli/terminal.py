"""The interactive prompt, with tab completion. Needs prompt_toolkit (the `cli` extra)."""

from collections.abc import Iterable

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document

from cassim.cli.repl import complete, completion_length
from cassim.core.session import Session


class CatalogCompleter(Completer):
    """Completes function, command, variable and conversion names from the live session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        before = document.text_before_cursor
        typed = completion_length(before)
        for name in complete(self._session, before):
            yield Completion(name, start_position=-typed)


def make_reader(session: Session) -> PromptSession[str]:
    return PromptSession(completer=CatalogCompleter(session), complete_while_typing=False)
