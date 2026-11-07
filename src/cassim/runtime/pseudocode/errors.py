"""Errors reported in pseudocode terms: a line, never a Python traceback."""


class PseudocodeError(Exception):
    """A problem in the program text (syntax) or in running it (runtime)."""

    def __init__(self, message: str, line: int = 0, col: int = 0) -> None:
        super().__init__(message)
        self.message = message
        self.line = line
        self.col = col

    def __str__(self) -> str:
        return f"line {self.line}: {self.message}" if self.line else self.message


class PseudocodeSyntaxError(PseudocodeError):
    pass


class PseudocodeRuntimeError(PseudocodeError):
    pass


class RunLimitError(PseudocodeRuntimeError):
    """The loop-iteration, recursion or recorded-step limit was reached (FR-SET-009)."""

    def __init__(self, message: str, line: int, limit: str) -> None:
        super().__init__(message, line)
        self.limit = limit
