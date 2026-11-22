"""Errors produced by the Python/pseudocode translators."""


class TranslationError(ValueError):
    """A construct cannot be represented safely in the destination language."""

    def __init__(
        self, line: int, construct: str, detail: str = "", *, language: str = "Python"
    ) -> None:
        self.line = line
        self.construct = construct
        self.detail = detail
        self.language = language
        text = f"line {line}: unsupported {language} construct {construct}"
        if detail:
            text += f": {detail}"
        super().__init__(text)
