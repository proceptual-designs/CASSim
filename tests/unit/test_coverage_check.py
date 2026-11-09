# Requirements traced here: NFR-MAINT-004
"""The per-package coverage check (NFR-MAINT-004)."""

from tools import coverage_check


def report(core: tuple[int, int], app: tuple[int, int]) -> dict[str, object]:
    def entry(covered: int, total: int) -> dict[str, dict[str, int]]:
        return {"summary": {"covered_lines": covered, "num_statements": total}}

    return {
        "files": {
            r"src\cassim\core\a.py": entry(*core),
            "src/cassim/app/b.py": entry(*app),
            "src/cassim/__init__.py": entry(1, 1),
        }
    }


def test_packages_are_summed_from_the_report() -> None:
    found = coverage_check.by_package(report((90, 100), (1, 10)))
    assert found["core"] == 90.0
    assert found["app"] == 10.0
    assert "__init__.py" not in found


def test_a_package_below_its_floor_is_reported(monkeypatch) -> None:
    monkeypatch.setattr(coverage_check, "floors", lambda: {"core": 95.0, "device": 80.0})
    problems = coverage_check.check(report((90, 100), (1, 10)))
    assert any("core: 90.0%" in p for p in problems)
    assert any(p.startswith("device") for p in problems)  # a floor for a missing package
    assert coverage_check.check(report((96, 100), (1, 10))) == [
        "device: not in the coverage report"
    ]
