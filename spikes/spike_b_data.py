"""Spike B (decision 0031): what large lists cost in the engine.

Times, for lists of 100, 500 and 2,500 elements, the operations a spreadsheet makes on every
edit: building the list, one element store, a column formula, a sort, One-Variable Statistics,
the variable snapshot the engine sends after every op, a JSON round trip of a typed payload, and
rebuilding a Problem by replaying its journal against restoring it from the variables' text.

Run natively (`python spikes/spike_b_data.py`) and inside Pyodide by `spikes/run_web_spike_b.py`.
"""

from __future__ import annotations

import json
import time

from cassim.core.format import to_latex, to_text
from cassim.core.session import Session
from cassim.core.values import ListValue

SIZES = (100, 500, 2500)


def say(msg: str) -> None:
    print(f"SPIKE: {msg}", flush=True)


def timed(fn) -> tuple[float, object]:
    start = time.perf_counter()
    out = fn()
    return (time.perf_counter() - start) * 1000, out


def ok(session: Session, line: str) -> float:
    ms, result = timed(lambda: session.eval(line))
    if result.error:
        raise RuntimeError(f"{line[:40]}: {result.error}")
    return ms


def literal(n: int, kind: str) -> str:
    if kind == "int":
        items = [str((i * 37) % 1000) for i in range(n)]
    elif kind == "dec":
        items = [f"{((i * 37) % 1000) / 7:.4f}" for i in range(n)]
    else:  # exact fractions
        items = [f"{(i * 37) % 1000}/7" for i in range(n)]
    return "{" + ",".join(items) + "}"


def run(n: int, kind: str) -> None:
    session = Session()
    row: dict[str, float] = {}
    row["define"] = ok(session, f"xs:={literal(n, kind)}")
    row["index"] = ok(session, "xs[2]")  # `xs[2]:=20` is not implemented yet (needed by 3a)
    row["xs^2"] = ok(session, "sq:=xs^2")
    row["2xs+1"] = ok(session, "lin:=2*xs+1")
    row["sum"] = ok(session, "sum(xs)")
    row["mean"] = ok(session, "mean(xs)")
    row["OneVar"] = ok(session, "OneVar xs")
    row["SortA"] = ok(session, "SortA xs")
    row["LinRegMx"] = ok(session, "LinRegMx xs,lin")

    # What EngineCore.apply does after every op today: format every variable.
    row["snapshot"], _ = timed(session.variables)

    # One list as the delta reply would send it: element display text, and floats for plotting.
    value = session.scope.get("xs")
    assert isinstance(value, ListValue)
    settings = session.settings
    row["cells_text"], cells = timed(lambda: [to_text(item, settings) for item in value.items])
    row["cells_latex"], _ = timed(lambda: [to_latex(item) for item in value.items])
    row["whole_text"], _ = timed(lambda: to_text(value, settings))
    payload = {"name": "xs", "rev": 3, "cells": cells}
    row["json"], _ = timed(lambda: json.loads(json.dumps(payload)))

    # Rebuild after a Cancel: replay the journal, or restore each variable from its text.
    journal = [f"xs:={literal(n, kind)}", "sq:=xs^2", "lin:=2*xs+1", "SortA xs"]

    def replay() -> None:
        fresh = Session()
        for line in journal:
            fresh.eval(line)

    row["replay"], _ = timed(replay)
    texts = {
        name: to_text(session.scope.get(name), settings)  # type: ignore[arg-type]
        for name in ("xs", "sq", "lin")
    }

    def restore() -> Session:
        fresh = Session()
        for name, text in texts.items():
            fresh.eval(f"{name}:={text}")
        return fresh

    row["restore"], restored = timed(restore)
    same = all(
        to_text(restored.scope.get(name), settings) == text  # type: ignore[union-attr,arg-type]
        for name, text in texts.items()
    )
    say(
        f"RESULT n={n} kind={kind} "
        + " ".join(f"{key}={ms:.0f}" for key, ms in row.items())
        + f" restore_same={same} json_bytes={len(json.dumps(payload))}"
    )


def main() -> None:
    say("START")
    warm = Session()
    warm.eval("OneVar {1,2,3}")
    warm.eval("LinRegMx {1,2,3},{2,4,7}")
    for kind in ("int", "dec", "frac"):
        for n in SIZES:
            try:
                run(n, kind)
            except Exception as error:  # a spike reports and carries on
                say(f"ERROR n={n} kind={kind} {error!r}")
    say("DONE")


if __name__ == "__main__":
    main()
