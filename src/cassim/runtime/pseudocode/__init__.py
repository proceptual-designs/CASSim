"""CASSim pseudocode: tokenizer, parser, tree interpreter and run trace (M7b)."""

from collections.abc import Iterable

from cassim.runtime.pseudocode.errors import PseudocodeError, PseudocodeSyntaxError
from cassim.runtime.pseudocode.interp import Interpreter
from cassim.runtime.pseudocode.parser import parse
from cassim.runtime.pseudocode.settings import Settings
from cassim.runtime.pseudocode.steps import RunResult, Step
from cassim.runtime.pseudocode.tree import Diagnostic, Program

__all__ = [
    "Diagnostic", "Interpreter", "Program", "PseudocodeError", "PseudocodeSyntaxError", "RunResult",
    "Settings", "Step", "parse", "run",
]  # fmt: skip


def run(
    source: str,
    settings: Settings | None = None,
    inputs: Iterable[str] = (),
    *,
    trace: bool = True,
) -> RunResult:
    """Parse and run `source`. A syntax error is returned as a result with halt == "error"."""
    try:
        program = parse(source)
    except PseudocodeSyntaxError as e:
        step = Step(0, e.line, "halt", 0, calc=e.message)
        return RunResult([], [step], [], "error", e.message, e.line)
    return Interpreter(program, settings, inputs, trace=trace).run()
