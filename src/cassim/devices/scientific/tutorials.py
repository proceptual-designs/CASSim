"""Built-in tutorial catalog and user-driven interactive step engine for CASSim fx.

Features:
- Pure user-driven execution: keypad is live; student must press the correct target key to advance.
- Quiet, non-punitive guidance on incorrect keypresses.
- Flagship Australian curriculum lessons (Standard Deviation, 5-Number Summary, Frequency Tables,
  Linear Regression, Fractions, Prime Factorisation, Table mode).

Pure Python: zero Flet imports. Tested headless.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TutorialStep:
    key: str
    label: str
    instruction: str
    detail: str = ""
    expected_screen: str = ""


@dataclass(frozen=True)
class TutorialLesson:
    id: str
    title: str
    mode: str
    steps: list[TutorialStep]
    category: str = "General"


CATALOG: dict[str, TutorialLesson] = {
    "stddev": TutorialLesson(
        id="stddev",
        title="Standard Deviation (sx vs σx)",
        mode="STAT",
        steps=[
            TutorialStep(
                key="MODE",
                label="[MODE]",
                instruction="Press [MODE] to open calculation modes.",
                detail="Options: 1:COMP (arithmetic), 2:STAT (statistics), 3:TABLE (functions).",
            ),
            TutorialStep(
                key="2",
                label="[ 2 ]",
                instruction="Press [2] to select STAT mode.",
                detail="STAT sub-modes include 1-VAR (univariate) and various regression forms.",
            ),
            TutorialStep(
                key="1",
                label="[ 1 ]",
                instruction="Press [1] to choose 1-VAR.",
                detail="Opens data table. Enter sample scores: 12, 15, 18, 22, 25.",
            ),
            TutorialStep(
                key="AC",
                label="[AC]",
                instruction="Press [AC] to exit table.",
                detail="Stores data safely. Notice the STAT indicator remains active on screen.",
            ),
            TutorialStep(
                key="SHIFT",
                label="[SHIFT]",
                instruction="Press [SHIFT].",
                detail="Activates secondary function layer (S annunciator lights).",
            ),
            TutorialStep(
                key="1",
                label="[ 1 ] (STAT)",
                instruction="Press [1] to open the STAT variables menu.",
                detail="Shows: 1:Type, 2:Data, 3:Sum, 4:Var, 5:MinMax.",
            ),
            TutorialStep(
                key="4",
                label="[ 4 ]",
                instruction="Press [4] to open the Var menu.",
                detail="Options: 1:n, 2:x̄ (mean), 3:σx (pop SD), 4:sx (sample SD).",
            ),
            TutorialStep(
                key="4",
                label="[ 4 ] (sx)",
                instruction="Press [4] to select sx.",
                detail="Places sample standard deviation sx on the calculation line.",
            ),
            TutorialStep(
                key="=",
                label="[ = ]",
                instruction="Press [ = ] to evaluate.",
                detail="Calculates sx = 5.17687... (Australian curriculum standard).",
            ),
        ],
    ),
    "fivenum": TutorialLesson(
        id="fivenum",
        title="Five-Number Summary",
        mode="STAT",
        steps=[
            TutorialStep(
                key="MODE",
                label="[MODE]",
                instruction="Press [MODE] to select mode.",
                detail="Open calculation modes.",
            ),
            TutorialStep(
                key="2",
                label="[ 2 ]",
                instruction="Press [2] for STAT mode.",
                detail="Statistical calculations.",
            ),
            TutorialStep(
                key="1",
                label="[ 1 ]",
                instruction="Press [1] for 1-VAR.",
                detail="Data table for 8 scores: 4, 7, 9, 12, 14, 18, 21, 25.",
            ),
            TutorialStep(
                key="AC",
                label="[AC]",
                instruction="Press [AC] to store data.",
                detail="Returns to calculation line with data preserved.",
            ),
            TutorialStep(
                key="SHIFT",
                label="[SHIFT]",
                instruction="Press [SHIFT].",
                detail="Activates STAT menu layer.",
            ),
            TutorialStep(
                key="1",
                label="[ 1 ] (STAT)",
                instruction="Press [1] for STAT menu.",
                detail="Access statistical summary functions.",
            ),
            TutorialStep(
                key="5",
                label="[ 5 ] (MinMax)",
                instruction="Press [5] for MinMax menu.",
                detail="Options: 1:minX, 2:maxX, 3:Q1, 4:med, 5:Q3.",
            ),
            TutorialStep(
                key="3",
                label="[ 3 ] (Q1)",
                instruction="Press [3] for Q1.",
                detail="Places Q1 on the calculation line.",
            ),
            TutorialStep(
                key="=",
                label="[ = ]",
                instruction="Press [ = ] to evaluate.",
                detail="Result: Q1 = 8 under Australian median-split rules.",
            ),
        ],
    ),
    "freq": TutorialLesson(
        id="freq",
        title="Enabling Frequency Table",
        mode="COMP",
        steps=[
            TutorialStep(
                key="SHIFT",
                label="[SHIFT]",
                instruction="Press [SHIFT].",
                detail="Prepares to enter Setup.",
            ),
            TutorialStep(
                key="MODE",
                label="[MODE] (SETUP)",
                instruction="Press [MODE] (SETUP) to open Setup.",
                detail="Shows system configuration options.",
            ),
            TutorialStep(
                key="DOWN",
                label="[ ▼ ]",
                instruction="Press Down arrow [▼] on the D-Pad.",
                detail="Scrolls to page 2 (1:STAT, 2:TABLE, etc.).",
            ),
            TutorialStep(
                key="1",
                label="[ 1 ] (STAT)",
                instruction="Press [1] to configure Statistics.",
                detail="Prompts: Frequency? 1:ON, 2:OFF.",
            ),
            TutorialStep(
                key="1",
                label="[ 1 ] (ON)",
                instruction="Press [1] to activate Frequency.",
                detail="Frequency column is now active in STAT tables.",
            ),
        ],
    ),
    "reset": TutorialLesson(
        id="reset",
        title="Initialise Calculator",
        mode="COMP",
        steps=[
            TutorialStep(
                key="SHIFT",
                label="[SHIFT]",
                instruction="Press [SHIFT].",
                detail="Activates secondary layer.",
            ),
            TutorialStep(
                key="9",
                label="[ 9 ] (CLR)",
                instruction="Press [9] (CLR) to open Clear menu.",
                detail="Options: 1:Setup, 2:Memory, 3:All.",
            ),
            TutorialStep(
                key="3",
                label="[ 3 ] (All)",
                instruction="Press [3] to reset everything.",
                detail="Prompts: Reset All? [=]:Yes, [AC]:Cancel.",
            ),
            TutorialStep(
                key="=",
                label="[ = ]",
                instruction="Press [ = ] to confirm.",
                detail="Restores factory default modes and clears memory.",
            ),
            TutorialStep(
                key="AC",
                label="[AC]",
                instruction="Press [AC] to finish.",
                detail="Returns to clean calculation screen.",
            ),
        ],
    ),
    "linreg": TutorialLesson(
        id="linreg",
        title="Linear Regression (r)",
        mode="STAT",
        steps=[
            TutorialStep(
                key="MODE",
                label="[MODE]",
                instruction="Press [MODE].",
                detail="Select calculation mode.",
            ),
            TutorialStep(
                key="2",
                label="[ 2 ]",
                instruction="Press [2] for STAT mode.",
                detail="Selects statistical mode.",
            ),
            TutorialStep(
                key="2",
                label="[ 2 ] (A+BX)",
                instruction="Press [2] for linear regression.",
                detail="Opens paired X and Y data table.",
            ),
            TutorialStep(
                key="AC",
                label="[AC]",
                instruction="Press [AC] to store data.",
                detail="Returns to line with STAT active.",
            ),
            TutorialStep(
                key="SHIFT",
                label="[SHIFT]",
                instruction="Press [SHIFT].",
                detail="Activates secondary menu.",
            ),
            TutorialStep(
                key="1",
                label="[ 1 ] (STAT)",
                instruction="Press [1] for STAT menu.",
                detail="Item 6:Reg is now available.",
            ),
            TutorialStep(
                key="6",
                label="[ 6 ] (Reg)",
                instruction="Press [6] for Regression menu.",
                detail="Options: 1:A (intercept), 2:B (slope), 3:r (correlation).",
            ),
            TutorialStep(
                key="3",
                label="[ 3 ] (r)",
                instruction="Press [3] to select r.",
                detail="Places correlation coefficient r on line.",
            ),
            TutorialStep(
                key="=",
                label="[ = ]",
                instruction="Press [ = ] to evaluate.",
                detail="Result: r = 0.9972... (strong positive linear trend).",
            ),
        ],
    ),
    "fractions": TutorialLesson(
        id="fractions",
        title="Fractions & S⇔D Toggle",
        mode="COMP",
        steps=[
            TutorialStep(
                key="FRAC",
                label="[믐]",
                instruction="Press fraction key [믐].",
                detail="Inserts a 2-level fraction box.",
            ),
            TutorialStep(
                key="3",
                label="[ 3 ]",
                instruction="Press [3] for numerator.",
                detail="Inputs 3 into top slot.",
            ),
            TutorialStep(
                key="DOWN",
                label="[ ▼ ]",
                instruction="Press [▼] to move to denominator.",
                detail="Cursor enters bottom slot.",
            ),
            TutorialStep(
                key="4",
                label="[ 4 ]",
                instruction="Press [4] for denominator.",
                detail="Inputs 4 into bottom slot.",
            ),
            TutorialStep(
                key="=",
                label="[ = ]",
                instruction="Press [ = ] to evaluate.",
                detail="Exact fraction 3/4 appears on screen.",
            ),
            TutorialStep(
                key="SD",
                label="[ S⇔D ]",
                instruction="Press [ S⇔D ] to toggle decimal.",
                detail="Converts 3/4 to 0.75. Press again to return.",
            ),
        ],
    ),
    "prime_factor": TutorialLesson(
        id="prime_factor",
        title="Prime Factorisation (FACT)",
        mode="COMP",
        steps=[
            TutorialStep(
                key="1",
                label="[ 1 ]",
                instruction="Enter 1050: Press [1].",
                detail="First digit.",
            ),
            TutorialStep(
                key="0",
                label="[ 0 ]",
                instruction="Press [0].",
                detail="Second digit.",
            ),
            TutorialStep(
                key="5",
                label="[ 5 ]",
                instruction="Press [5].",
                detail="Third digit.",
            ),
            TutorialStep(
                key="0",
                label="[ 0 ]",
                instruction="Press [0].",
                detail="Fourth digit.",
            ),
            TutorialStep(
                key="=",
                label="[ = ]",
                instruction="Press [ = ] to store in Ans.",
                detail="Number must be evaluated first.",
            ),
            TutorialStep(
                key="SHIFT",
                label="[SHIFT]",
                instruction="Press [SHIFT].",
                detail="Secondary function.",
            ),
            TutorialStep(
                key="DMS",
                label="[ ° ' \" ] (FACT)",
                instruction="Press [ ° ' \" ] (FACT).",
                detail="Factorises 1050 into 2 × 3 × 5² × 7.",
            ),
        ],
    ),
}


MAX_HISTORY = 6

CORE_LESSONS: list[TutorialLesson] = list(CATALOG.values())


@dataclass
class TutorialSession:
    lesson_id: str = "stddev"
    step_index: int = 0
    history: list[str] = field(default_factory=lambda: ["[ON]"])
    last_hint: str = ""

    def __init__(
        self,
        lesson: TutorialLesson | None = None,
        lesson_id: str = "stddev",
        step_index: int = 0,
    ) -> None:
        self.lesson_id = lesson.id if lesson is not None else lesson_id
        self.step_index = step_index
        self.history = ["[ON]"]
        self.last_hint = ""

    @property
    def lesson(self) -> TutorialLesson:
        return CATALOG.get(self.lesson_id, next(iter(CATALOG.values())))

    @property
    def total_steps(self) -> int:
        return len(self.lesson.steps)

    @property
    def current_step_index(self) -> int:
        return self.step_index

    @property
    def is_complete(self) -> bool:
        return self.step_index >= self.total_steps

    @property
    def current_step(self) -> TutorialStep | None:
        if self.is_complete:
            return None
        return self.lesson.steps[self.step_index]

    @property
    def target_key(self) -> str | None:
        step = self.current_step
        return step.key if step else None

    def press(self, key: str) -> bool:
        """Process user keypress.

        Returns True if key matched target and advanced, False if wrong key was pressed.
        """
        self.history.append(f"[{key}]")
        if len(self.history) > MAX_HISTORY:
            self.history.pop(0)

        if self.is_complete:
            return False

        step = self.current_step
        assert step is not None
        if key == step.key:
            self.step_index += 1
            self.last_hint = ""
            return True

        self.last_hint = f"Pressed [{key}]. Target is {step.label}."
        return False

    def advance(self) -> None:
        if self.step_index < self.total_steps:
            self.step_index += 1
            self.last_hint = ""

    def back(self) -> None:
        if self.step_index > 0:
            self.step_index -= 1
            self.last_hint = ""

    def restart(self) -> None:
        self.step_index = 0
        self.last_hint = ""

    def reset(self) -> None:
        self.step_index = 0
        self.last_hint = ""
        self.history.clear()

    def get_hint(self) -> str:
        step = self.current_step
        return step.label if step else ""

    def set_lesson(self, lesson_id: str) -> None:
        if lesson_id in CATALOG:
            self.lesson_id = lesson_id
            self.step_index = 0
            self.last_hint = ""
