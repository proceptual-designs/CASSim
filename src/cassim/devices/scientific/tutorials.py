"""The interactive tutorials (FR-FX-TUT-001 to -006).

The lessons follow docs/design/tutorials-catalog-fx.md.

A lesson is a list of steps; a step is one or more keypad keys with an instruction and the reason
for it. The student presses every key (Guide Me), watches it played (Show Me), or is given a new
problem and checked on the answer (Test Me). What the screen should show after each step is not
written by hand: `expected_screens` runs the lesson on a headless calculator, so it always matches
what the calculator really does. The lesson answers are checked the same way in the tests.

Pure Python: no Flet. Progress is kept by the view in browser storage; nothing leaves the device.
"""

from __future__ import annotations

import dataclasses
import math
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

from cassim.devices.scientific import keys as k
from cassim.devices.scientific import layouts
from cassim.devices.scientific import values as v
from cassim.devices.scientific.state import ScientificState

TutorialMode = Literal["guide", "show", "test"]
SPEEDS = (0.5, 1.0, 1.5, 2.0)


@dataclass(frozen=True)
class Step:
    keys: tuple[str, ...]
    instruction: str
    why: str = ""


@dataclass(frozen=True)
class Challenge:
    """Test Me: a new problem, and how to tell the student's calculator has the answer."""

    prompt: str
    check: Callable[[ScientificState], bool]
    answer: str  # shown after a wrong check: what the calculator should end with, not the keys
    start: tuple[str, ...] | None = None  # keys pressed (unseen) after a reset; None: the lesson's


@dataclass(frozen=True)
class Lesson:
    id: str
    title: str
    category: str
    problem: str
    steps: tuple[Step, ...]
    answer: str  # the answer line after the last step, as `Display.text` shows it
    challenge: Challenge
    start: tuple[str, ...] = ()  # keys pressed (unseen) after a reset, before step 1
    needs_mode: str = ""  # a mode beyond COMP and STAT that the lesson uses
    dialect: layouts.Dialect = "casio"  # whose key sequences the steps are (layouts.Dialect)

    @property
    def key(self) -> str:
        """Its name in the list of finished lessons: the same lesson on another calculator's
        keys is a different lesson."""
        return self.id if self.dialect in ("casio", "sx2") else f"{self.dialect}.{self.id}"

    @property
    def key_count(self) -> int:
        return sum(len(step.keys) for step in self.steps)

    def prepare(self, state: ScientificState, *, test: bool = False) -> None:
        """Reset the calculator and set it up for step 1 (or for the Test me problem)."""
        state.reset()
        start = self.challenge.start if test and self.challenge.start is not None else self.start
        for key in start:
            state.press(key)


def _ans_close(target: float, rel: float = 1e-6) -> Callable[[ScientificState], bool]:
    def check(state: ScientificState) -> bool:
        if state.result is None or isinstance(state.result, (bool,)):
            return False
        try:
            value = float(v.check(state.variables["Ans"]))
        except v.CalcError:
            return False
        return math.isclose(value, target, rel_tol=rel, abs_tol=1e-9)

    return check


def _answer_is(text: str) -> Callable[[ScientificState], bool]:
    def check(state: ScientificState) -> bool:
        return state.screen == "calc" and state.answer_text() == text

    return check


def _is_number(value: object, target: float) -> bool:
    return isinstance(value, (v.Exact, float, int)) and math.isclose(float(value), target)


def _value_is(target: float) -> Callable[[ScientificState], bool]:
    """The last answer has this value, whatever form the display shows it in (a natural display
    shows 1/2 where a linear one shows 0.5)."""
    return _ans_close(target, rel=1e-9)


def _settings_reset_memories_kept(state: ScientificState) -> bool:
    """Judged on the calculator, not the keys: SETUP is back to this calculator's defaults (a
    linear-display calculator's default is LineIO), the mode is COMP, and A and M still hold the
    values stored before the test."""
    return (
        state.setup == state.default_setup()
        and state.mode == "COMP"
        and float(state.variables["A"]) == 5  # noqa: PLR2004
        and float(state.variables["M"]) == 7  # noqa: PLR2004
    )


# Test me for "reset": a different mess (degrees, Fix 2, A = 5, M = 7, STAT data) and a different
# clear (the setup only), so it is like the lesson but not the same.
MESSY = (
    *(k.SHIFT, k.MODE, "3"),  # Deg
    *(k.SHIFT, k.MODE, "6", "2"),  # Fix 2
    *("5", k.SHIFT, k.RCL, k.NEG),  # 5 → A
    *("7", k.SHIFT, k.RCL, k.MPLUS),  # 7 → M
    *(k.MODE, "2", "1", "4", k.EQ, k.AC),  # STAT data
)


def _entries(*numbers: str) -> tuple[Step, ...]:
    """One step per data value: type it, then =."""
    return tuple(
        Step(
            (*tuple(number), k.EQ),
            f"Type {number} and press {{EQ}}.",
            "= stores the value and moves down a row.",
        )
        for number in numbers
    )


def _keys(text: str) -> tuple[str, ...]:
    """Digits and a decimal point as keys."""
    return tuple(k.DOT if ch == "." else ch for ch in text)


def _stat_steps(
    menu: str, item: str, what: str, why: str = "", *, two: bool = False
) -> tuple[Step, ...]:
    names = {"3": "Sum", "4": "Var", "5": "Reg" if two else "MinMax", "6": "MinMax"}
    return (
        Step((k.SHIFT, "1"), "Press {SHIFT 1} to open the STAT menu.", why),
        Step((menu,), f"Press {menu} for {names[menu]}."),
        Step((item, k.EQ), f"Press {item} for {what}, then {{EQ}} to calculate it."),
    )


OPEN_1VAR = (
    Step((k.MODE,), "Press {MODE} to see the calculation modes."),
    Step(("2",), "Press 2 for STAT.", "STAT mode works with lists of data."),
    Step(("1",), "Press 1 for 1-VAR.", "One variable: a single list of numbers."),
)
FREQ_ON = (k.SHIFT, k.MODE, k.DOWN, "3", "1")

LESSONS: tuple[Lesson, ...] = (
    Lesson(
        id="reset",
        title="Resetting the calculator",
        category="Getting started",
        problem="Clear every setting and memory before a test.",
        start=(k.SHIFT, k.MODE, "4", "7", k.MPLUS, k.MODE, "2", "1"),
        steps=(
            Step((k.SHIFT, "9"), "Press {SHIFT 9} to open CLR."),
            Step(("3",), "Press 3 for All.", "All resets the settings and clears every memory."),
            Step((k.EQ,), "Press {EQ} to confirm.", "{AC} would cancel instead."),
            Step((k.AC,), "Press {AC} to go back to the calculation screen."),
        ),
        answer="",
        challenge=Challenge(
            "Someone has changed the settings and left 5 in A and 7 in M. Put the settings back "
            "to their defaults but keep the memories.",
            _settings_reset_memories_kept,
            "the settings reset (COMP mode, default SETUP) with A = 5 and M = 7 kept",
            start=MESSY,
        ),
    ),
    Lesson(
        id="freq",
        title="Turning on the frequency column",
        category="Getting started",
        problem="Switch on the FREQ column for frequency tables.",
        steps=(
            Step((k.SHIFT, k.MODE), "Press {SHIFT MODE} to open SETUP."),
            Step((k.DOWN,), "Press ▼ to see the second page of settings."),
            Step(("3",), "Press 3 for STAT."),
            Step(("1",), "Press 1 for ON.", "Each data row now has a frequency."),
        ),
        answer="",
        challenge=Challenge(
            "The frequency column is on. Turn it off.",
            lambda state: not state.setup.frequency,
            "STAT's frequency setting OFF",
            start=FREQ_ON,
        ),
        start=(),
    ),
    Lesson(
        id="stddev",
        title="Mean and standard deviation (sx and σx)",
        category="Statistics",
        problem="Find the mean and the sample standard deviation of 12, 15, 18, 22, 25.",
        steps=(
            *OPEN_1VAR,
            *_entries("12", "15", "18", "22", "25"),
            Step(
                (k.AC,),
                "Press {AC} to leave the table.",
                "The data stays in memory: STAT stays lit.",
            ),
            *_stat_steps("4", "2", "x̄ (the mean)"),
            *_stat_steps(
                "4",
                "4",
                "sx (the sample standard deviation)",
                "sx divides by n−1; σx, item 3, divides by n.",
            ),
        ),
        answer="5.224940191",
        challenge=Challenge(
            "Find sx for the scores 3, 8, 10, 15.",
            _ans_close(4.966554809),
            "4.966554809",
        ),
    ),
    Lesson(
        id="fivenum",
        title="Five-number summary",
        category="Statistics",
        problem="Find min, Q1, median, Q3 and max of 4, 7, 9, 12, 14, 18, 21, 25.",
        steps=(
            *OPEN_1VAR,
            *_entries("4", "7", "9", "12", "14", "18", "21", "25"),
            Step((k.AC,), "Press {AC} to leave the table."),
            *_stat_steps("5", "1", "minX"),
            *_stat_steps("5", "3", "Q1", "Q1 is the median of the lower half."),
            *_stat_steps("5", "4", "med (the median)"),
            *_stat_steps("5", "5", "Q3", "Q3 is the median of the upper half."),
            *_stat_steps("5", "2", "maxX"),
        ),
        answer="25",
        challenge=Challenge(
            "Find Q1 of 2, 5, 6, 9, 11, 14, 20. (The median is left out of both halves.)",
            _ans_close(5.0),
            "5",
        ),
    ),
    Lesson(
        id="freqtable",
        title="Statistics from a frequency table",
        category="Statistics",
        problem="Scores 1, 2, 3, 4 occur 5, 12, 8 and 3 times. Find n and the mean.",
        start=FREQ_ON,
        steps=(
            *OPEN_1VAR,
            *_entries("1", "2", "3", "4"),
            Step((k.UP,) * 4, "Press ▲ four times to go back to the first row."),
            Step((k.RIGHT,), "Press ▶ to move to the FREQ column."),
            *_entries("5", "12", "8", "3"),
            Step((k.AC,), "Press {AC} to leave the table."),
            *_stat_steps("4", "1", "n, the number of scores"),
            *_stat_steps("4", "2", "x̄, the mean"),
        ),
        answer="2.321428571",
        challenge=Challenge(
            "Scores 0, 1, 2 occur 4, 10 and 6 times. Find the mean.",
            _ans_close(1.1),
            "1.1",
        ),
    ),
    Lesson(
        id="linreg",
        title="Correlation and the regression line",
        category="Bivariate data",
        problem=(
            "Fit y = A + Bx to (2, 5), (4, 9), (6, 12), (8, 17), (10, 20); find r and ŷ at x = 7."
        ),
        steps=(
            Step((k.MODE, "2"), "Press {MODE} then 2 for STAT."),
            Step(("2",), "Press 2 for A+BX, the straight line.", "Two columns: X and Y."),
            *_entries("2", "4", "6", "8", "10"),
            Step((k.UP,) * 5, "Press ▲ five times to go back to the first row."),
            Step((k.RIGHT,), "Press ▶ to move to the Y column."),
            *_entries("5", "9", "12", "17", "20"),
            Step((k.AC,), "Press {AC} to leave the table."),
            *_stat_steps(
                "5",
                "3",
                "r, the correlation coefficient",
                "Reg appears for two-variable data.",
                two=True,
            ),
            *_stat_steps("5", "1", "A, the intercept", two=True),
            *_stat_steps("5", "2", "B, the slope", two=True),
            Step(("7",), "Type 7, the x value to predict from."),
            *_stat_steps("5", "5", "ŷ, the predicted y", two=True),
        ),
        answer="14.5",
        challenge=Challenge(
            "For (1, 3), (2, 5), (3, 8), (4, 9), find the slope B.",
            _ans_close(2.1),
            "2.1",
        ),
    ),
    Lesson(
        id="fractions",
        title="Fractions and S⇔D",
        category="Number",
        problem="Work out 2/3 + 3/4 as a fraction, a decimal and a mixed number.",
        steps=(
            Step(
                (k.FRAC,), "Press {FRAC}, the fraction key.", "The cursor goes into the numerator."
            ),
            Step(("2",), "Type 2."),
            Step((k.DOWN,), "Press ▼ to move to the denominator."),
            Step(("3",), "Type 3."),
            Step((k.RIGHT,), "Press ▶ to leave the fraction."),
            Step((k.ADD,), "Press {ADD}."),
            Step((k.FRAC, "3", k.DOWN, "4"), "Enter 3/4 the same way: fraction, 3, ▼, 4."),
            Step((k.EQ,), "Press {EQ}.", "The answer is a fraction."),
            Step((k.SD,), "Press {SD} to see it as a decimal."),
            Step((k.SHIFT, k.SD), "Press {SHIFT SD} for a mixed number."),
        ),
        answer="1 5⌟12",
        challenge=Challenge("Work out 5/6 − 1/4 as a fraction.", _answer_is("7⌟12"), "7/12"),
    ),
    Lesson(
        id="trig",
        title="Exact trigonometry",
        category="Trigonometry",
        problem="Find sin 30° exactly, then the angle whose sine is 0.5.",
        steps=(
            Step((k.SIN, "3", "0", k.RPAREN), "Press {SIN}, type 30 and close the bracket."),
            Step((k.EQ,), "Press {EQ}.", "The exact value is 1/2."),
            Step((k.SHIFT, k.SIN), "Press {SHIFT SIN} for sin⁻¹."),
            Step(("0", k.DOT, "5", k.RPAREN), "Type 0.5 and close the bracket."),
            Step((k.EQ,), "Press {EQ}.", "The angle is in degrees."),
        ),
        answer="30",
        challenge=Challenge("Find cos 60°.", _value_is(0.5), "1/2"),
    ),
    Lesson(
        id="percent",
        title="Percentage increase",
        category="Number",
        problem="Increase $250 by 15%.",
        steps=(
            Step(("2", "5", "0", k.ADD, "1", "5"), "Type 250 + 15."),
            Step((k.SHIFT, k.LPAREN), "Press {SHIFT LPAREN} for %.", "+ 15% adds 15% of 250."),
            Step((k.EQ,), "Press {EQ}.", "The exact answer is 575/2."),
            Step((k.SD,), "Press {SD} to see it as a decimal: $287.50."),
        ),
        answer="287.5",
        challenge=Challenge("Decrease $80 by 25%.", _ans_close(60.0), "60"),
    ),
    Lesson(
        id="memory",
        title="Storing a value in a variable",
        category="Memory",
        problem="Store 12 × 3 in A, then work out 2A.",
        steps=(
            Step(("1", "2", k.MUL, "3", k.EQ), "Work out 12 × 3."),
            Step((k.SHIFT, k.RCL), "Press {SHIFT RCL} for STO.", "STO lights up."),
            Step((k.NEG,), "Press {NEG}, which has A above it.", "36 is now in A."),
            Step(("2", k.ALPHA, k.NEG), "Type 2, then {ALPHA NEG} to type A."),
            Step((k.EQ,), "Press {EQ}."),
        ),
        answer="72",
        challenge=Challenge("Store 7 in B, then work out B².", _ans_close(49.0), "49"),
    ),
    Lesson(
        id="prime",
        title="Prime factorisation (FACT)",
        category="Number",
        problem="Write 1050 as a product of primes.",
        steps=(
            Step(("1", "0", "5", "0", k.EQ), "Type 1050 and press {EQ}."),
            Step((k.SHIFT, k.DMS), "Press {SHIFT DMS} for FACT."),
        ),
        answer="2×3×5²×7",
        challenge=Challenge("Factorise 360.", _answer_is("2³×3²×5"), "2³×3²×5"),
    ),
    Lesson(
        id="table",
        needs_mode="TABLE",
        title="A table of values",
        category="Functions",
        problem="Tabulate f(x) = x² − 3 for x = 1 to 5.",
        steps=(
            Step((k.MODE, "3"), "Press {MODE} then 3 for TABLE."),
            Step((k.ALPHA, k.RPAREN), "Press {ALPHA RPAREN} to type X."),
            Step((k.X2, k.SUB, "3"), "Press {X2}, then {SUB} 3."),
            Step((k.EQ,), "Press {EQ}. The calculator asks for the start."),
            Step(("1", k.EQ), "Type 1 and press {EQ} (start)."),
            Step(("5", k.EQ), "Type 5 and press {EQ} (end)."),
            Step(("1", k.EQ), "Type 1 and press {EQ} (step)."),
            Step((k.DOWN, k.DOWN, k.DOWN), "Press ▼ to scroll down the table."),
        ),
        answer="",
        challenge=Challenge(
            "Make a table of 2X + 1 from 0 to 4 and stop on X = 4.",
            lambda state: (
                state.screen == "table"
                and bool(state.table_rows)
                and float(state.table_rows[state.table_cursor[0]][0]) == 4  # noqa: PLR2004
                and _is_number(state.table_rows[state.table_cursor[0]][1], 9)
            ),
            "the table of 2X + 1 (start 0, end 4, step 1) with the row X = 4 selected",
        ),
    ),
)

LESSONS_BY_ID: dict[str, Lesson] = {lesson.id: lesson for lesson in LESSONS}

# ---- the HP 10s (fx-82MS family) and the Sharp EL-531: the same problems in their own keys ----

DT = "DATA"  # M+ in SD and REG mode (DT), and in STAT mode on the EL-531 (DATA)


def _ms_clear_stats() -> Step:
    return Step(
        (k.SHIFT, k.MODE, "1", k.EQ),
        "Press {SHIFT MODE} (CLR), 1 (Scl) and {EQ} to clear old data.",
        "Always clear the statistics memory before typing new data.",
    )


def _data(*values: str, how: str = "") -> tuple[Step, ...]:
    """One step per value (or x,f or x,y pair, written with the key between): type it, then DT."""
    steps = []
    for value in values:
        typed: list[str] = []
        for part in value.split(" "):
            typed.extend(SEPARATORS.get(part, _keys(part)))
        shown = value.replace("STOXY", "(x,y)").replace("TOK:;", ";").replace("COMMA", ",")
        steps.append(
            Step(
                (*typed, DT),
                f"Type {shown} and press {{{DT}}}.",
                how or "The value is stored; the screen counts the data so far.",
            )
        )
    return tuple(steps)


SEPARATORS: dict[str, tuple[str, ...]] = {
    "STOXY": ("STOXY",),
    "TOK:;": ("TOK:;",),
    "COMMA": (k.SHIFT, k.RPAREN),
}


def _ms_var(*pages_then_item: str, what: str, why: str = "") -> tuple[Step, ...]:
    """SHIFT S-VAR (or S-SUM), ▶ to the right page, the item, then =."""
    *rights, item = pages_then_item
    menu = "1" if rights and rights[0] == "sum" else "2"
    rights = [r for r in rights if r != "sum"]
    name = "S-SUM" if menu == "1" else "S-VAR"
    steps = [Step((k.SHIFT, menu), f"Press {{SHIFT {menu}}} for {name}.", why)]
    if rights:
        steps.append(
            Step((k.RIGHT,) * len(rights), f"Press ▶ {len(rights)} times for the next page.")
        )
    steps.append(Step((item, k.EQ), f"Press {item} for {what}, then {{EQ}}."))
    return tuple(steps)


def _sharp_recall(token: str, what: str, why: str = "") -> Step:
    return Step(
        (k.RCL, f"TOK:{token}"),
        f"Press {{RCL TOK:{token}}} for {what}.",
        why or "RCL and a statistics key show its value straight away.",
    )


def _same(lesson_id: str, dialect: layouts.Dialect, **changes: object) -> Lesson:
    return dataclasses.replace(LESSONS_BY_ID[lesson_id], dialect=dialect, **changes)


FRACTIONS_LINEAR = (
    Step(("2", k.FRAC, "3"), "Type 2, press {FRAC}, then 3.", "a b/c marks a fraction: 2⌟3."),
    Step((k.ADD, "3", k.FRAC, "4"), "Press {ADD}, then 3 {FRAC} 4."),
    Step((k.EQ,), "Press {EQ}.", "1⌟5⌟12 is the mixed number 1 5/12."),
    Step((k.FRAC,), "Press {FRAC} to see it as a decimal.", "Press it again to go back."),
    Step((k.SHIFT, k.SD), "Press {SHIFT SD} (d/c) for an improper fraction."),
)
TRIG_LINEAR = (
    Step(
        (k.SIN, "3", "0", k.EQ), "Press {SIN}, type 30 and press {EQ}.", "The angle is in degrees."
    ),
    Step((k.SHIFT, k.SIN), "Press {SHIFT SIN} for sin⁻¹."),
    Step(("0", k.DOT, "5", k.EQ), "Type 0.5 and press {EQ}.", "The angle whose sine is 0.5."),
)
MS_MESSY = (
    *(k.MODE, k.MODE, "2"),  # Rad
    *(k.MODE, k.MODE, k.MODE, "1", "2"),  # Fix 2
    *("5", k.SHIFT, k.RCL, k.NEG),  # 5 → A
    *("7", k.SHIFT, k.RCL, k.MPLUS),  # 7 → M
    *(k.MODE, "2", "4", DT),  # SD with data
)
SHARP_MESSY = (
    *(k.SHIFT, k.MODE, "0", "0"),  # FIX
    *("5", "STOXY", k.NEG),  # 5 → A
    *("7", "STOXY", k.MPLUS),  # 7 → M
)


def _memories_cleared_fix_kept(state: ScientificState) -> bool:
    return state.setup.disp == "Fix" and all(
        float(state.variables[name]) == 0 for name in ("A", "M")
    )


MS_LESSONS: tuple[Lesson, ...] = (
    Lesson(
        id="reset",
        title="Resetting the calculator",
        category="Getting started",
        problem="Clear every mode, setting and memory before a test.",
        dialect="ms",
        start=(k.MODE, k.MODE, "2", "7", DT, k.MODE, "2"),
        steps=(
            Step((k.SHIFT, k.MODE), "Press {SHIFT MODE} to open CLR."),
            Step(
                ("3",),
                "Press 3 for All.",
                "All resets the modes and settings and clears every memory.",
            ),
            Step((k.EQ,), "Press {EQ} to confirm.", "{AC} would cancel instead."),
        ),
        answer="",
        challenge=Challenge(
            "Someone has changed the modes and left 5 in A and 7 in M. Put the modes and "
            "settings back but keep the memories.",
            _settings_reset_memories_kept,
            "the modes reset (COMP, default settings) with A = 5 and M = 7 kept",
            start=MS_MESSY,
        ),
    ),
    Lesson(
        id="stddev",
        title="Mean and standard deviation (xσn-1 and xσn)",
        category="Statistics",
        problem="Find the mean and the sample standard deviation of 12, 15, 18, 22, 25.",
        dialect="ms",
        steps=(
            Step((k.MODE,), "Press {MODE} to see the calculation modes."),
            Step(("2",), "Press 2 for SD.", "SD mode works with a list of data."),
            _ms_clear_stats(),
            *_data("12", "15", "18", "22", "25"),
            *_ms_var("1", what="x̄ (the mean)"),
            *_ms_var(
                "3",
                what="xσn-1 (the sample standard deviation, sx)",
                why="xσn-1 divides by n−1; xσn, item 2, divides by n.",
            ),
        ),
        answer="5.224940191",
        challenge=LESSONS_BY_ID["stddev"].challenge,
    ),
    Lesson(
        id="freqtable",
        title="Statistics from a frequency table",
        category="Statistics",
        problem="Scores 1, 2, 3, 4 occur 5, 12, 8 and 3 times. Find n and the mean.",
        dialect="ms",
        steps=(
            Step((k.MODE, "2"), "Press {MODE} then 2 for SD."),
            _ms_clear_stats(),
            *_data(
                "1 TOK:; 5",
                "2 TOK:; 12",
                "3 TOK:; 8",
                "4 TOK:; 3",
                how="{TOK:;} (;) gives the score how many times it occurs.",
            ),
            *_ms_var("sum", "3", what="n, the number of scores"),
            *_ms_var("1", what="x̄, the mean"),
        ),
        answer="2.321428571",
        challenge=LESSONS_BY_ID["freqtable"].challenge,
    ),
    Lesson(
        id="linreg",
        title="Correlation and the regression line",
        category="Bivariate data",
        problem=LESSONS_BY_ID["linreg"].problem,
        dialect="ms",
        steps=(
            Step((k.MODE, "3"), "Press {MODE} then 3 for REG."),
            Step(("1",), "Press 1 for Lin, the straight line y = A + Bx."),
            _ms_clear_stats(),
            *_data(
                "2 COMMA 5",
                "4 COMMA 9",
                "6 COMMA 12",
                "8 COMMA 17",
                "10 COMMA 20",
                how="x , y then DT stores the pair.",
            ),
            *_ms_var(">", ">", "3", what="r, the correlation coefficient"),
            *_ms_var(">", ">", "1", what="A, the intercept"),
            *_ms_var(">", ">", "2", what="B, the slope"),
            Step(("7",), "Type 7, the x value to predict from."),
            *_ms_var(">", ">", ">", "2", what="ŷ, the predicted y"),
        ),
        answer="14.5",
        challenge=LESSONS_BY_ID["linreg"].challenge,
    ),
    Lesson(
        id="fractions",
        title="Fractions and a b/c",
        category="Number",
        problem=LESSONS_BY_ID["fractions"].problem,
        dialect="ms",
        steps=FRACTIONS_LINEAR,
        answer="17⌟12",
        challenge=LESSONS_BY_ID["fractions"].challenge,
    ),
    Lesson(
        id="trig",
        title="Trigonometry in degrees",
        category="Trigonometry",
        problem="Find sin 30°, then the angle whose sine is 0.5.",
        dialect="ms",
        steps=TRIG_LINEAR,
        answer="30",
        challenge=LESSONS_BY_ID["trig"].challenge,
    ),
    Lesson(
        id="percent",
        title="Percentage increase",
        category="Number",
        problem="Increase $250 by 15%.",
        dialect="ms",
        steps=(
            Step(("2", "5", "0", k.MUL, "1", "5"), "Type 250 × 15."),
            Step(
                (k.SHIFT, k.LPAREN, k.EQ), "Press {SHIFT LPAREN EQ} for %.", "15% of 250 is 37.5."
            ),
            Step((k.ADD,), "Press {ADD} to add it on.", "250 + 37.5 = 287.5."),
        ),
        answer="287.5",
        challenge=LESSONS_BY_ID["percent"].challenge,
    ),
    _same("memory", "ms"),
)

SHARP_LESSONS: tuple[Lesson, ...] = (
    Lesson(
        id="reset",
        title="Clearing the memories and settings",
        category="Getting started",
        problem="Clear every memory and setting before a test.",
        dialect="sharp",
        start=(k.SHIFT, k.MODE, "0", "0", "7", "STOXY", k.MPLUS),
        steps=(
            Step(
                ("MCLR",), "Press {MCLR} (M-CLR).", "It offers 0 (the memories) or 1 (everything)."
            ),
            Step(("1",), "Press 1 for RESET."),
            Step((k.EQ,), "Press {EQ} to confirm.", "{AC} would cancel instead."),
        ),
        answer="",
        challenge=Challenge(
            "FIX is on and 5 is in A and 7 in M. Clear the memories but keep FIX.",
            _memories_cleared_fix_kept,
            "A = 0 and M = 0, with FIX still on",
            start=SHARP_MESSY,
        ),
    ),
    Lesson(
        id="stddev",
        title="Mean and standard deviation (sx and σx)",
        category="Statistics",
        problem="Find the mean and the sample standard deviation of 12, 15, 18, 22, 25.",
        dialect="sharp",
        steps=(
            Step((k.MODE,), "Press {MODE}.", "0 is NORMAL and 1 is STAT."),
            Step(("1", "0"), "Press 1 for STAT, then 0 for SD.", "SD works with a list of data."),
            *_data("12", "15", "18", "22", "25"),
            _sharp_recall("x̄", "x̄, the mean"),
            _sharp_recall("sx", "sx, the sample standard deviation", "σx divides by n; sx by n−1."),
        ),
        answer="5.224940191",
        challenge=LESSONS_BY_ID["stddev"].challenge,
    ),
    Lesson(
        id="freqtable",
        title="Statistics from a frequency table",
        category="Statistics",
        problem="Scores 1, 2, 3, 4 occur 5, 12, 8 and 3 times. Find n and the mean.",
        dialect="sharp",
        steps=(
            Step((k.MODE, "1", "0"), "Press {MODE}, 1 (STAT), 0 (SD)."),
            *_data(
                "1 STOXY 5",
                "2 STOXY 12",
                "3 STOXY 8",
                "4 STOXY 3",
                how="In STAT mode {STOXY} is (x,y): the score, then how many times it occurs.",
            ),
            _sharp_recall("n", "n, the number of scores"),
            _sharp_recall("x̄", "x̄, the mean"),
        ),
        answer="2.321428571",
        challenge=LESSONS_BY_ID["freqtable"].challenge,
    ),
    Lesson(
        id="linreg",
        title="Correlation and the regression line",
        category="Bivariate data",
        problem=LESSONS_BY_ID["linreg"].problem,
        dialect="sharp",
        steps=(
            Step((k.MODE, "1", "1"), "Press {MODE}, 1 (STAT), 1 (LINE).", "LINE is y = a + bx."),
            *_data(
                "2 STOXY 5",
                "4 STOXY 9",
                "6 STOXY 12",
                "8 STOXY 17",
                "10 STOXY 20",
                how="x, then {STOXY} (x,y), then y.",
            ),
            _sharp_recall("r", "r, the correlation coefficient"),
            _sharp_recall("regA", "a, the intercept"),
            _sharp_recall("regB", "b, the slope"),
            Step(
                ("7", "TOK:ŷ", k.EQ),
                "Type 7, press {TOK:ŷ} (y′), then {EQ}.",  # noqa: RUF001
                "y′ is ŷ, the predicted y.",  # noqa: RUF001
            ),
        ),
        answer="14.5",
        challenge=LESSONS_BY_ID["linreg"].challenge,
    ),
    Lesson(
        id="fractions",
        title="Fractions and a b/c",
        category="Number",
        problem=LESSONS_BY_ID["fractions"].problem,
        dialect="sharp",
        steps=FRACTIONS_LINEAR,
        answer="17⌟12",
        challenge=LESSONS_BY_ID["fractions"].challenge,
    ),
    Lesson(
        id="trig",
        title="Trigonometry in degrees",
        category="Trigonometry",
        problem="Find sin 30°, then the angle whose sine is 0.5.",
        dialect="sharp",
        steps=TRIG_LINEAR,
        answer="30",
        challenge=LESSONS_BY_ID["trig"].challenge,
    ),
    Lesson(
        id="percent",
        title="Percentage increase",
        category="Number",
        problem="Increase $250 by 15%.",
        dialect="sharp",
        steps=(
            Step(("2", "5", "0", k.ADD, "1", "5"), "Type 250 + 15."),
            Step(
                (k.SHIFT, k.LPAREN, k.EQ),
                "Press {SHIFT LPAREN EQ} for %.",
                "+ 15% adds 15% of 250.",
            ),
        ),
        answer="287.5",
        challenge=LESSONS_BY_ID["percent"].challenge,
    ),
    Lesson(
        id="memory",
        title="Storing a value in a variable",
        category="Memory",
        problem="Store 12 × 3 in A, then work out 2A.",
        dialect="sharp",
        steps=(
            Step(("1", "2", k.MUL, "3", k.EQ), "Work out 12 × 3."),
            Step(
                ("STOXY", k.NEG),
                "Press {STOXY NEG}: STO, then the key with A above it.",
                "36 is now in A.",
            ),
            Step(("2", k.ALPHA, k.NEG), "Type 2, then {ALPHA NEG} to type A."),
            Step((k.EQ,), "Press {EQ}."),
        ),
        answer="72",
        challenge=LESSONS_BY_ID["memory"].challenge,
    ),
)


def lessons_for(layout: layouts.Layout) -> tuple[Lesson, ...]:
    """The lessons for a calculator, in its own keys. A lesson for something it does not have
    (TABLE, quartiles, FACT, the FREQ setting) is not offered."""
    match layout.dialect:
        case "ms":
            return MS_LESSONS
        case "sharp":
            return SHARP_LESSONS
    return tuple(
        lesson for lesson in LESSONS if not lesson.needs_mode or lesson.needs_mode in layout.modes
    )


def layout_state(layout: layouts.Layout) -> ScientificState:
    """A fresh calculator behind this layout's keys."""
    state = ScientificState()
    state.use_layout(layout.modes, linear=layout.linear, dialect=layout.dialect)
    state.reset()
    return state


def expected_screens(lesson: Lesson, layout: layouts.Layout = layouts.DEFAULT) -> list[str]:
    """What the screen shows after each step, found by running the lesson on that layout."""
    state = layout_state(layout)
    lesson.prepare(state)
    screens = []
    for step in lesson.steps:
        for key in step.keys:
            state.press(key)
        screens.append(state.display().text())
    return screens


def run_lesson(lesson: Lesson, layout: layouts.Layout = layouts.DEFAULT) -> ScientificState:
    """The calculator after every step of a lesson (for tests and Show Me)."""
    state = layout_state(layout)
    lesson.prepare(state)
    for step in lesson.steps:
        for key in step.keys:
            state.press(key)
    return state


_PLACEHOLDER = re.compile(r"\{([^{}]+)\}")


def wording(text: str, layout: layouts.Layout) -> str:
    """Lesson text with each {KEY KEY...} named by that layout's keys ('{SHIFT 9}' is 'SHIFT then
    9' on one calculator and '2nd then 9' on another)."""
    return _PLACEHOLDER.sub(lambda m: layouts.describe(layout, m.group(1).split()), text)


def key_label(key: str) -> str:
    spec = k.KEYS_BY_ID.get(key)
    return spec.label if spec is not None else key


@dataclass
class TutorialSession:
    """Where a student is in a lesson."""

    lesson: Lesson
    mode: TutorialMode = "guide"
    step_index: int = 0
    key_index: int = 0
    history: list[str] = field(default_factory=list)
    wrong: int = 0
    _screens: list[str] | None = None

    @property
    def is_complete(self) -> bool:
        return self.step_index >= len(self.lesson.steps)

    @property
    def current_step(self) -> Step | None:
        return None if self.is_complete else self.lesson.steps[self.step_index]

    @property
    def target_key(self) -> str | None:
        """The key to press next (the one that glows)."""
        step = self.current_step
        return None if step is None else step.keys[self.key_index]

    def expected_screen(self) -> str:
        if self._screens is None:
            self._screens = expected_screens(self.lesson)
        if self.is_complete:
            return self._screens[-1] if self._screens else ""
        return self._screens[self.step_index]

    def press(self, key: str) -> bool:
        """A key the student pressed. True when it was the one asked for (and the lesson moves
        on); False otherwise, and the lesson waits (FR-FX-TUT-003)."""
        target = self.target_key
        if target is None:
            return False
        if key != target:
            self.wrong += 1
            return False
        self.history.append(key_label(key))
        self.wrong = 0
        self.key_index += 1
        step = self.current_step
        assert step is not None
        if self.key_index >= len(step.keys):
            self.step_index += 1
            self.key_index = 0
        return True

    def hint(self) -> str:
        target = self.target_key
        if target is None:
            return ""
        spec = k.KEYS_BY_ID.get(target)
        label = key_label(target)
        spoken = spec.spoken if spec is not None else label
        where = f" ({spoken})" if spoken.lower() != label.lower() else ""
        if self.wrong > 1 and target == k.SHIFT:
            return f"Press SHIFT{where} first: the labels above the keys are its functions."
        return f"Not that one. Press [{label}]{where} to continue, or use Show me."

    def keys_done(self) -> list[str]:
        """Every key the lesson has pressed so far (to rebuild the calculator after Back)."""
        done = [key for step in self.lesson.steps[: self.step_index] for key in step.keys]
        step = self.current_step
        if step is not None:
            done.extend(step.keys[: self.key_index])
        return done

    def remaining_keys(self) -> list[str]:
        step = self.current_step
        if step is None:
            return []
        rest = list(step.keys[self.key_index :])
        rest.extend(key for later in self.lesson.steps[self.step_index + 1 :] for key in later.keys)
        return rest

    def back(self) -> None:
        """Go back to the start of this step, or of the step before if this one has not begun."""
        if self.key_index > 0:
            self.key_index = 0
        elif self.step_index > 0:
            self.step_index -= 1
        self.history = [key_label(key) for key in self.keys_done()]

    def restart(self) -> None:
        self.step_index = 0
        self.key_index = 0
        self.history = []
        self.wrong = 0
