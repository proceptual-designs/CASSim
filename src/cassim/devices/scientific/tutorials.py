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
    answer: str  # shown after a wrong check


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

    @property
    def key_count(self) -> int:
        return sum(len(step.keys) for step in self.steps)

    def prepare(self, state: ScientificState) -> None:
        """Reset the calculator and set it up for step 1."""
        state.reset()
        for key in self.start:
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


def _is_reset(state: ScientificState) -> bool:
    fresh = ScientificState()
    return (
        state.setup == fresh.setup
        and state.mode == "COMP"
        and all(float(value) == 0 for value in state.variables.values())
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


def _stat_steps(menu: str, item: str, what: str, why: str = "") -> tuple[Step, ...]:
    names = {"3": "Sum", "4": "Var", "5": "MinMax", "6": "Reg"}
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
FREQ_ON = (k.SHIFT, k.MODE, k.DOWN, "1", "1")

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
            "Reset only the setup (not the memories), then reset everything again.",
            _is_reset,
            "SHIFT 9, 3, =, AC",
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
            Step(("1",), "Press 1 for STAT."),
            Step(("1",), "Press 1 for ON.", "Each data row now has a frequency."),
        ),
        answer="",
        challenge=Challenge(
            "Turn the frequency column off again.",
            lambda state: not state.setup.frequency,
            "SHIFT MODE, ▼, 1, 2",
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
                "6", "3", "r, the correlation coefficient", "Reg appears for two-variable data."
            ),
            *_stat_steps("6", "1", "A, the intercept"),
            *_stat_steps("6", "2", "B, the slope"),
            Step(("7",), "Type 7, the x value to predict from."),
            *_stat_steps("6", "5", "ŷ, the predicted y"),
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
        challenge=Challenge("Find cos 60° exactly.", _answer_is("1⌟2"), "1/2"),
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
            ),
            "MODE 3, 2 ALPHA ) + 1, =, 0 =, 4 =, 1 =, then ▼ to X = 4",
        ),
    ),
)

LESSONS_BY_ID: dict[str, Lesson] = {lesson.id: lesson for lesson in LESSONS}


def expected_screens(lesson: Lesson, layout: layouts.Layout = layouts.DEFAULT) -> list[str]:
    """What the screen shows after each step, found by running the lesson on that layout."""
    state = ScientificState()
    state.use_layout(layout.modes, linear=layout.linear)
    lesson.prepare(state)
    screens = []
    for step in lesson.steps:
        for key in step.keys:
            state.press(key)
        screens.append(state.display().text())
    return screens


def run_lesson(lesson: Lesson) -> ScientificState:
    """The calculator after every step of a lesson (for tests and Show Me)."""
    state = ScientificState()
    lesson.prepare(state)
    for step in lesson.steps:
        for key in step.keys:
            state.press(key)
    return state


def lesson_layout(lesson: Lesson, layout: layouts.Layout) -> layouts.Layout:
    """The layout a lesson runs on: the chosen one, unless that calculator lacks a mode or a key
    the lesson needs; then the default layout, which has them all."""
    if lesson.needs_mode and lesson.needs_mode not in layout.modes:
        return layouts.DEFAULT
    keys = [key for step in lesson.steps for key in step.keys]
    return layout if layouts.plan(layout, keys) is not None else layouts.DEFAULT


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
