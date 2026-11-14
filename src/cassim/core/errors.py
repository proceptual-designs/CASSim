"""TI error codes and messages.

Codes and wording come from the Error Codes appendix of the TI-Nspire CAS Reference Guide.
"""

import logging

_log = logging.getLogger(__name__)

SYNTAX = 910
MISSING_OPEN_PAREN = 680
MISSING_CLOSE_PAREN = 690
MISSING_QUOTE = 700
MISSING_CLOSE_BRACKET = 710
MISSING_CLOSE_BRACE = 720
DATA_TYPE = 210
DIMENSION = 230  # an index past the end of a list (emulator check 6, G7)
DIMENSION_MISMATCH = 240
DOMAIN = 260
INVALID_LIST_OR_MATRIX = 510
TOO_FEW_ARGUMENTS = 930
TOO_MANY_ARGUMENTS = 940
# Not in the guide (3.2 predates the setting); the simulator's number was not captured.
CAS_RESTRICTED = -1
# Ours, for language that a later milestone will implement.
NOT_IMPLEMENTED = -2
# Ours: the simulator shows no number for these. The wording of RESERVED_NAME, RECURSION and
# NOT_A_FUNCTION is the simulator's (emulator check 6, part B); the rest are not captured.
RESERVED_NAME = -3
RECURSION = -4
MEMORY = -5
SINGULAR = -6
VARIABLE_NAME_NEEDED = -7
USE_DERIVATIVE_AT_POINT = -8
NO_SOLUTION = -9
# A store to a list that a spreadsheet column is linked to, or to a formula column's variable
# (emulator check run 2, G4, G9, G14).
VARIABLE_IN_USE = -10
INVALID_INPUT = -11
NOT_A_FUNCTION = -12
# Ours: a Python exception that no TI error covers, a bug in CASSim (see `internal`).
INTERNAL = -13
NON_REAL = 800  # TI's number for a non-real result in Real mode

_MESSAGES = {
    SYNTAX: "Syntax error",
    MISSING_OPEN_PAREN: "Missing (",
    MISSING_CLOSE_PAREN: "Missing )",
    MISSING_QUOTE: 'Missing "',
    MISSING_CLOSE_BRACKET: "Missing ]",
    MISSING_CLOSE_BRACE: "Missing }",
    DATA_TYPE: "Data type",
    DIMENSION: "Dimension error",
    DIMENSION_MISMATCH: "Dimension mismatch",
    DOMAIN: "Domain error",
    INVALID_LIST_OR_MATRIX: "Invalid list or matrix",
    TOO_FEW_ARGUMENTS: "Too few arguments",
    TOO_MANY_ARGUMENTS: "Too many arguments",
    CAS_RESTRICTED: "CAS computations are restricted in CAS Off and Exact Arithmetic modes.",
    RESERVED_NAME: "Invalid variable or function name",
    RECURSION: "Recursion too deep",
    NOT_A_FUNCTION: "Name is not a function",
    MEMORY: "Memory",
    SINGULAR: "Singular matrix",
    VARIABLE_NAME_NEEDED: "Argument must be a variable name",
    USE_DERIVATIVE_AT_POINT: "Use Derivative at a Point",
    NO_SOLUTION: "No solution found",
    VARIABLE_IN_USE: (
        "Cannot accept change, variable in use: Cannot change to requested variable type."
    ),
    INVALID_INPUT: "Cannot accept change: Invalid input.",
    NON_REAL: "Non-real result",
}


# Warnings: the entry succeeds, and its history row gets a triangle that shows the text
# (FR-CALC-007, decision 0026).
NON_REAL_CALCULATION = "Non-real calculation"


class TIError(Exception):
    """An error the calculator would report to the user."""

    def __init__(self, code: int, message: str | None = None) -> None:
        self.code = code
        self.message = message if message is not None else _MESSAGES[code]
        super().__init__(self.message)


_MOST_SHOWN = 300  # characters of an internal error's message, which can quote a long formula


def internal(error: Exception) -> TIError:
    """A TIError for an unexpected exception, such as one SymPy raises that we did not foresee.

    The entry shows the exception's type and message, so a user can report it; the traceback goes
    to the log (the browser console), not the screen.
    """
    _log.error("unexpected error during evaluation", exc_info=error)
    detail = str(error)
    if len(detail) > _MOST_SHOWN:
        detail = detail[: _MOST_SHOWN - 1] + "…"
    name = type(error).__name__
    return TIError(
        INTERNAL, f"Internal error: {name}: {detail}" if detail else f"Internal error: {name}"
    )


class TISyntaxError(TIError):
    """The entry line could not be read. `pos` is a character offset into it."""

    def __init__(self, code: int, pos: int, message: str | None = None) -> None:
        super().__init__(code, message)
        self.pos = pos
