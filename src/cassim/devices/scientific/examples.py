"""Doc ▸ Examples: ready-made problems (SDD-14 section 5.1).

Each example is the keys a student would press, so it is loaded by pressing them on a fresh
calculator: whatever it shows is what the calculator really does. Pure data: no Flet.
"""

from __future__ import annotations

from cassim.devices.scientific import keys as k
from cassim.devices.scientific.layouts import Layout, offers_table
from cassim.devices.scientific.state import ScientificState


def _number_keys(text: str) -> tuple[str, ...]:
    return tuple(k.DOT if ch == "." else ch for ch in text)


def _column(*numbers: str) -> tuple[str, ...]:
    out: list[str] = []
    for number in numbers:
        out.extend((*_number_keys(number), k.EQ))
    return tuple(out)


EXAMPLES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Standard deviation: 12, 15, 18, 22, 25",
        (k.MODE, "2", "1", *_column("12", "15", "18", "22", "25")),
    ),
    (
        "Five-number summary: 4, 7, 9, 12, 14, 18, 21, 25",
        (k.MODE, "2", "1", *_column("4", "7", "9", "12", "14", "18", "21", "25")),
    ),
    (
        "Linear regression: (2, 5) (4, 9) (6, 12) (8, 17) (10, 20)",
        (
            k.MODE,
            "2",
            "2",
            *_column("2", "4", "6", "8", "10"),
            *(k.UP,) * 5,
            k.RIGHT,
            *_column("5", "9", "12", "17", "20"),
        ),
    ),
    (
        "Table of values: f(X) = 2X² − 3X + 1, X = 1 to 5",
        (k.MODE, "4", "2", k.ALPHA, k.RPAREN, k.X2, k.SUB, "3", k.ALPHA, k.RPAREN, k.ADD, "1"),
    ),
    (
        "Mixed numbers: 2⅓ + 5/6",
        (k.SHIFT, k.FRAC, "2", k.RIGHT, "1", k.DOWN, "3", k.RIGHT, k.ADD, k.FRAC, "5", k.DOWN, "6"),
    ),
    ("Trigonometry: sin 60°", (k.SIN, "6", "0", k.RPAREN)),
    (
        "Degrees, minutes and seconds: 12°34'56\"",
        ("1", "2", k.DMS, "3", "4", k.DMS, "5", "6", k.DMS),
    ),
    ("Prime factorisation: 1050", ("1", "0", "5", "0", k.EQ, k.SHIFT, k.DMS)),
)


def missing(index: int, layout: Layout, modes: tuple[str, ...] | None = None) -> str:
    """Why the calculator behind these keys cannot show the example ("" when it can). `modes`
    are the modes switched on (the layout's own, and TABLE when that extra is on)."""
    title = EXAMPLES[index][0]
    if title.startswith("Table") and "TABLE" not in (layout.modes if modes is None else modes):
        if offers_table(layout):
            return "TABLE is an extra mode: switch it on in CASSim ▸ Settings first."
        return f"The {layout.title} has no TABLE mode."
    linear = layout.dialect in ("ms", "sharp")
    if linear and title.startswith("Five-number"):
        return f"The {layout.title} has no quartiles."
    if linear and title.startswith("Prime"):
        return f"The {layout.title} has no prime factorisation."
    return ""


def load_example(state: ScientificState, index: int) -> None:
    """Reset the calculator and press the example's keys. They are the fx-82's keys, so they are
    pressed on its menus and the calculator then goes back to its own (STAT data typed into the
    fx-82's table stays, for a calculator that enters it with DT or DATA)."""
    _, presses = EXAMPLES[index]
    dialect = state.dialect
    state.reset()
    state.dialect = "casio"
    try:
        for key in presses:
            state.press(key)
    finally:
        state.dialect = dialect
    if dialect in ("ms", "sharp") and state.screen == "stat_editor":
        state.screen = "calc"
