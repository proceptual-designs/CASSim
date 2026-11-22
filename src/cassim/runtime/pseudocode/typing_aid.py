"""Undo-safe typing-aid replacements for the pseudocode editor (FR-SYN-013)."""

from dataclasses import dataclass

_DIRECT = (
    ("<=", "≤"),
    (">=", "≥"),
    ("!=", "≠"),
    ("<-", "←"),
)
# LaTeX spellings the typing aid turns into symbols the pseudocode lexer accepts: Greek letters
# are ordinary names, the rest are operators or constants (not ± or ≈, which it rejects).
GREEK_LOWER = {
    r"\alpha": "α",
    r"\beta": "β",
    r"\gamma": "\u03b3",  # escaped: gamma looks like a Latin y
    r"\delta": "δ",
    r"\epsilon": "ε",  # the form students write (LaTeX's own \epsilon is ϵ)
    r"\varepsilon": "ε",
    r"\zeta": "ζ",
    r"\eta": "η",
    r"\theta": "θ",
    r"\kappa": "κ",
    r"\lambda": "λ",
    r"\mu": "μ",
    r"\nu": "\u03bd",  # escaped: nu looks like a Latin v
    r"\xi": "ξ",
    r"\pi": "π",
    r"\rho": "\u03c1",  # escaped: rho looks like a Latin p
    r"\sigma": "σ",
    r"\tau": "τ",
    r"\phi": "φ",  # the form students write (LaTeX's own \phi is ϕ)
    r"\varphi": "φ",
    r"\chi": "χ",
    r"\psi": "ψ",
    r"\omega": "ω",
}
GREEK_UPPER = {  # those that do not look like Latin capitals
    r"\Gamma": "Γ",
    r"\Delta": "Δ",
    r"\Theta": "Θ",
    r"\Lambda": "Λ",
    r"\Xi": "Ξ",
    r"\Pi": "Π",
    r"\Sigma": "Σ",
    r"\Phi": "Φ",
    r"\Psi": "Ψ",
    r"\Omega": "Ω",
}
LATEX_SYMBOLS = {
    r"\le": "≤",
    r"\leq": "≤",
    r"\ge": "≥",
    r"\geq": "≥",
    r"\ne": "≠",
    r"\neq": "≠",
    r"\times": "×",
    r"\div": "÷",
    r"\cdot": "·",
    r"\sqrt": "√",
    r"\infty": "∞",
    r"\land": "∧",
    r"\wedge": "∧",
    r"\lor": "∨",
    r"\vee": "∨",
    r"\lnot": "¬",
    r"\neg": "¬",
    r"\gets": "←",
    r"\leftarrow": "←",
}
_LATEX = GREEK_LOWER | GREEK_UPPER | LATEX_SYMBOLS
LATEX_WORDS = _LATEX  # converted once a space or line break follows the word
_TEXT_TERMINATORS = {" ", "\n"}


@dataclass(frozen=True, slots=True)
class TypingReplacement:
    text: str
    start: int
    end: int
    replacement: str


def replacement_before_cursor(text: str, cursor: int) -> TypingReplacement | None:
    """Return an unambiguous suffix replacement ending at `cursor`, if one exists."""
    if cursor < 0 or cursor > len(text):
        return None
    before = text[:cursor]
    for source, target in _DIRECT:
        if before.endswith(source):
            return TypingReplacement(text, cursor - len(source), cursor, target)
    if before and before[-1] in _TEXT_TERMINATORS:
        stem = before[:-1]
        for source, target in _LATEX.items():
            if stem.endswith(source):
                return TypingReplacement(
                    text,
                    cursor - len(source) - 1,
                    cursor,
                    f"{target}{before[-1]}",
                )
    return None
