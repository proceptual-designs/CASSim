"""What a run records: one `Step` per executed line, enough to step forwards and backwards."""

from dataclasses import dataclass, field

from cassim.runtime.pseudocode.tree import Diagnostic


@dataclass(frozen=True, slots=True)
class Change:
    name: str
    old: object  # None when the variable did not exist
    new: object
    existed: bool = True


@dataclass(frozen=True, slots=True)
class Step:
    """One executed line.

    `kind` is assign, condition, print, input, call, return, loop (a loop pass starting) or halt.
    `cond` holds the condition with values substituted and its result. `loop` is the innermost
    enclosing loop as (line of the loop, pass number from 1), which feeds the horizontal layout.
    """

    index: int
    line: int
    kind: str
    depth: int
    changes: tuple[Change, ...] = ()
    cond: tuple[str, bool] | None = None
    calc: str = ""
    output: str | None = None
    loop: tuple[int, int] | None = None
    function: str = ""  # the function whose body this line is in ("" at top level)


@dataclass(slots=True)
class RunResult:
    output: list[str]
    steps: list[Step]
    warnings: list[Diagnostic]
    halt: str  # finished | error | step_limit | event_cap
    error: str | None = None
    error_line: int = 0
    variables: dict[str, object] = field(default_factory=dict)
    loop_entries: int = 0  # how many times a loop was started, over the whole run
    max_loop_depth: int = 0
    loop_body_runs: int = 0  # passes through a loop body, over all loops
    constants: tuple[str, ...] = ()
    functions: dict[str, str] = field(default_factory=dict)

    @property
    def horizontal_eligible(self) -> bool:
        """Exactly one loop, run once, with no loop inside another (trace-tables.md section 3)."""
        return self.loop_entries == 1 and self.max_loop_depth == 1
