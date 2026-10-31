"""Corpus progress summary, shown after the replay run."""

from typing import Any

from tools.replay import load_cases


def pytest_terminal_summary(terminalreporter: Any) -> None:
    counts: dict[tuple[str, int, str], int] = {}
    for case in load_cases():
        key = (case["course"], case["tier"], case.get("status", "pending"))
        counts[key] = counts.get(key, 0) + 1
    terminalreporter.section("corpus status (course, tier, status: cases)")
    for (course, tier, status), n in sorted(counts.items()):
        terminalreporter.line(f"{course:<11} tier {tier}  {status:<8} {n}")
