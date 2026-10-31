"""TI error codes and messages.

Codes and wording come from the Error Codes appendix of the TI-Nspire CAS Reference Guide.
"""

SYNTAX = 910
MISSING_OPEN_PAREN = 680
MISSING_CLOSE_PAREN = 690
MISSING_QUOTE = 700
MISSING_CLOSE_BRACKET = 710
MISSING_CLOSE_BRACE = 720

_MESSAGES = {
    SYNTAX: "Syntax error",
    MISSING_OPEN_PAREN: "Missing (",
    MISSING_CLOSE_PAREN: "Missing )",
    MISSING_QUOTE: 'Missing "',
    MISSING_CLOSE_BRACKET: "Missing ]",
    MISSING_CLOSE_BRACE: "Missing }",
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
