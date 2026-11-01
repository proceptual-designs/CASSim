"""Replay the golden corpus against the engine.

`python -m tools.replay` runs every case, whatever its status, and prints a summary. Only the
pytest module `tests/corpus/test_replay.py` enforces results.
"""

import io
import sys
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from cassim.core.session import Result, Session, same_value
from cassim.core.settings import PRESETS, Settings, updated

SEED = Path(__file__).parents[1] / "corpus" / "seed"
# Eight displayed digits, so a correct value can differ by half a unit in the last place.
DEFAULT_TOLERANCE = 1.0e-7
_NOT_COMPARED = {"ignore"}
_UNSUPPORTED_COMPARE = {"family"}

type Case = dict[str, Any]
type Step = dict[str, Any]


@dataclass(frozen=True, slots=True)
class Outcome:
    case_id: str
    passed: bool
    reason: str = ""
    crashed: bool = False


def load_cases() -> Iterator[Case]:
    for path in sorted(SEED.glob("*.yaml")):
        yield from yaml.safe_load(path.read_text(encoding="utf-8"))["cases"]


def case_settings(case: Case) -> Settings:
    return updated(PRESETS[case.get("course", "none")], case.get("settings", {}))


def _error_failure(step: Step, result: Result) -> str | None:
    if result.error is None:
        return f"{step['in']}: expected an error, got {result.text}"
    wanted = step.get("error_contains", "")
    return None if wanted in result.error else f"{step['in']}: wrong error: {result.error}"


def _result_failure(step: Step, result: Result, settings: Settings) -> str | None:
    if result.error is not None:
        return f"{step['in']}: {result.error}"
    compare = step.get("compare", "canonical")
    if compare in _NOT_COMPARED:
        return None
    if compare in _UNSUPPORTED_COMPARE:
        return f"{step['in']}: compare mode {compare} is not implemented"
    if compare == "text":
        wanted_text = str(step["out"])
        return None if result.text == wanted_text else f"{step['in']}: got {result.text}"
    return _value_failure(step, result, settings, compare)


def _value_failure(step: Step, result: Result, settings: Settings, compare: str) -> str | None:
    expected = str(step["out"])
    # Expected text is read with CAS on and Auto, so it means what it shows.
    reader = Session(Settings(angle=settings.angle))
    wanted = reader.eval(expected)
    if wanted.value is None or result.value is None:
        return f"{step['in']}: cannot read expected {expected}: {wanted.error}"
    tolerance = step.get("tol", DEFAULT_TOLERANCE) if compare == "numeric" else None
    if same_value(result.value, wanted.value, tolerance):
        return None
    return f"{step['in']}: got {result.text}, expected {expected}"


def _run_step(session: Session, step: Step) -> str | None:
    if step.get("new_problem"):
        session.new_problem()
    elif "set" in step:
        session.set(**step["set"])
    elif "in" in step:
        result = session.eval(step["in"])
        if step.get("error"):
            return _error_failure(step, result)
        return _result_failure(step, result, session.settings)
    return None


def run_case(case: Case) -> Outcome:
    session = Session(case_settings(case))
    try:
        for step in case["steps"]:
            if failure := _run_step(session, step):
                return Outcome(case["id"], passed=False, reason=failure)
    except Exception as error:  # a crash is a finding, reported with the rest
        return Outcome(case["id"], False, f"{type(error).__name__}: {error}", crashed=True)
    return Outcome(case["id"], passed=True)


def main() -> None:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    verbose = "-v" in sys.argv
    outcomes = [run_case(case) for case in load_cases()]
    for outcome in outcomes:
        if verbose or outcome.crashed:
            state = "pass" if outcome.passed else "FAIL"
            print(f"{state} {outcome.case_id} {outcome.reason}"[:170])
    tally = Counter("pass" if o.passed else "crash" if o.crashed else "fail" for o in outcomes)
    print(f"{len(outcomes)} cases: {dict(tally)}")


if __name__ == "__main__":
    main()
