"""What a session hands back: a result row and a variable-list row.

Kept apart from `session.py` so the UI can hold these without importing the engine. In the browser
the UI's worker never loads SymPy; the engine runs in a worker of its own (decision 0027).
"""

from dataclasses import dataclass

from cassim.core.values import Value


@dataclass(frozen=True, slots=True)
class Result:
    text: str
    latex: str
    value: Value | None
    error: str | None
    full: str = ""  # the text at 14 digits: what `Ans` stands for in a history line
    warnings: tuple[str, ...] = ()  # shown by the entry's warning triangle (FR-CALC-007)


@dataclass(frozen=True, slots=True)
class VariableInfo:
    """One row of the variable list."""

    name: str
    text: str  # the value as linear text, or `f(x)` for a function
    latex: str
    is_function: bool
    items: tuple[str, ...] | None = None  # formatted list items or matrix rows/cells
    source: str = ""  # a restorable TI definition, for the Computer variable-list undo


def latex_for_markdown(latex: str) -> str:
    r"""Make LaTeX survive Flet's Markdown, which collapses a double backslash to one (0014).

    The TeX row end `\cr` means the same as a row break and passes through unchanged.
    """
    return latex.replace("\\\\", r"\cr ")
