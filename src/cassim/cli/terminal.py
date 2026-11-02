"""The interactive prompt, with tab completion. Needs prompt_toolkit (the `cli` extra)."""

from collections.abc import Iterable

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.input import PipeInput
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.output import Output

from cassim.cli.repl import APPROX_PREFIX, complete, completion_length
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


def _approximate_and_submit(event: KeyPressEvent) -> None:
    """Ctrl+Enter on the handheld: give the entry as a decimal."""
    buffer = event.current_buffer
    buffer.text = APPROX_PREFIX + buffer.text
    buffer.validate_and_handle()


def key_bindings() -> KeyBindings:
    """Alt-Enter always works. Ctrl-Enter works where the terminal reports it as its own key;
    many send a plain Enter, which cannot be told apart."""
    bindings = KeyBindings()
    bindings.add("escape", "enter")(_approximate_and_submit)
    bindings.add("c-j")(_approximate_and_submit)
    return bindings


def make_reader(
    session: Session, *, input: PipeInput | None = None, output: Output | None = None
) -> PromptSession[str]:
    return PromptSession(
        completer=CatalogCompleter(session),
        complete_while_typing=False,
        key_bindings=key_bindings(),
        input=input,
        output=output,
    )
