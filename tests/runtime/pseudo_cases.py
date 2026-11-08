"""The pseudocode golden corpus as the tests load it: `seed.yaml` plus any `batch*.yaml` beside it.

Cases in a batch file carry `review` (approved or unreviewed) and `requires` (dialect features
the case needs). They are replayed like seed cases; the ones that need an unimplemented feature are
listed in `NOT_YET` and run as strict expected failures.
"""

from pathlib import Path
from typing import Any

import pytest
import yaml

DIR = Path(__file__).parents[2] / "corpus" / "pseudocode"

# Seeded simulations with 10^5 to 10^6 passes: exact against CPython, but 20 to 100 s each.
SLOW = {
    "book.u1.dice.d6-tally",
    "book.u1.dice.best-of-two-average",
    "proposed.simulation.monte-carlo-pi",
}
# Needs a feature that is not built yet (the reason shows as the xfail reason).
NOT_YET = {"proposed.tuple-return.box-volume": "tuples and tuple return (FR-PSE-008, Could)"}

# Batch-3 cases whose `trace.horizontal_eligible` the interpreter disagrees with (2026-11-07).
# To settle when the trace tables are worked on (M7): either the rule in
# docs/pseudocode/trace-tables.md (exactly one loop, none nested) or the case's flag is wrong.
# Output is correct for all of them.
HORIZONTAL_LATER = {
    "proposed.list.mean-max-min",
    "book.u2.derivative.forward-vs-central",
    "book.u1.lcg.turbo-pascal",
    "proposed.simpson.4-(x-1)^2",
    "proposed.simpson.4-(x-1)^2.fn",
    "proposed.heun.x-t",
    "book.u2.sine-range-reduction",
    "author.stats.four-means",
    "author.list.all-max-positions",
    "author.random.randint-from-rand",
    "book.u1.dice.best-of-two-average",
    "proposed.simulation.monte-carlo-pi",
}


def load() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for path in [DIR / "seed.yaml", *sorted(DIR.glob("batch*.yaml"))]:
        cases += yaml.safe_load(path.read_text(encoding="utf-8"))["cases"]
    return cases


CASES = load()


def params(*, run: bool) -> list[Any]:
    """pytest params for every case. With `run`, slow cases are marked and unbuilt ones xfail."""
    out = []
    for case in CASES:
        marks = []
        if run and case["id"] in SLOW:
            marks.append(pytest.mark.slow)
        if run and case["id"] in NOT_YET:
            marks.append(pytest.mark.xfail(reason=NOT_YET[case["id"]], strict=True))
        out.append(pytest.param(case, id=case["id"], marks=marks))
    return out
