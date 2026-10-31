"""TI error codes and messages.

Codes and wording come from the Error Codes appendix of the TI-Nspire CAS Reference Guide.
"""

SYNTAX = 910
MISSING_OPEN_PAREN = 680
MISSING_CLOSE_PAREN = 690
MISSING_QUOTE = 700
MISSING_CLOSE_BRACKET = 710
MISSING_CLOSE_BRACE = 720
DATA_TYPE = 210
DIMENSION_MISMATCH = 240
DOMAIN = 260
INVALID_LIST_OR_MATRIX = 510
TOO_FEW_ARGUMENTS = 930
TOO_MANY_ARGUMENTS = 940
# Not in the guide (3.2 predates the setting); the emulator's number was not captured.
CAS_RESTRICTED = -1
# Ours, for language that a later milestone will implement.
NOT_IMPLEMENTED = -2

_MESSAGES = {
    SYNTAX: "Syntax error",
    MISSING_OPEN_PAREN: "Missing (",
    MISSING_CLOSE_PAREN: "Missing )",
    MISSING_QUOTE: 'Missing "',
    MISSING_CLOSE_BRACKET: "Missing ]",
    MISSING_CLOSE_BRACE: "Missing }",
    DATA_TYPE: "Data type",
    DIMENSION_MISMATCH: "Dimension mismatch",
    DOMAIN: "Domain error",
    INVALID_LIST_OR_MATRIX: "Invalid list or matrix",
    TOO_FEW_ARGUMENTS: "Too few arguments",
    TOO_MANY_ARGUMENTS: "Too many arguments",
    CAS_RESTRICTED: "CAS computations are restricted in CAS Off and Exact Arithmetic modes.",
}


class TIError(Exception):
    """An error the calculator would report to the user."""

    def __init__(self, code: int, message: str | None = None) -> None:
        self.code = code
        self.message = message if message is not None else _MESSAGES[code]
        super().__init__(self.message)


class TISyntaxError(TIError):
    """The entry line could not be read. `pos` is a character offset into it."""

    def __init__(self, code: int, pos: int, message: str | None = None) -> None:
        super().__init__(code, message)
        self.pos = pos
