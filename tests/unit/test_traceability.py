# Requirements traced here: NFR-MAINT-006
"""The traceability tool: IDs come from the SRS, citations from tests (NFR-MAINT-006)."""

from pathlib import Path

from tools.traceability import SRS, Requirement, citations, problems, render, requirements

SAMPLE = """
## 4. Things
### 4.1 Parts
| ID | Requirement | Pri | Ver |
|---|---|---|---|
| FR-AAA-001 | A table row. | M | T |
| FR-AAA-002 | **Bold** row, with a pipe \| in it. | S | D |

- NFR-BBB-001 (M) A bullet.
- **FID-1** (S, T) A bold bullet.
"""


def test_ids_priorities_and_sections_are_read_from_the_srs() -> None:
    found = {r.id: r for r in requirements(SAMPLE)}
    assert found["FR-AAA-001"] == Requirement("FR-AAA-001", "M", "4.1")
    assert found["FR-AAA-002"].priority == "S"
    assert found["NFR-BBB-001"].priority == "M"
    assert found["FID-1"].priority == "S"


def test_the_real_srs_has_requirements_in_every_priority() -> None:
    reqs = requirements(SRS.read_text(encoding="utf-8"))
    assert len(reqs) > 150
    assert {r.priority for r in reqs} == {"M", "S", "C", "W"}


def test_citations_are_found_in_a_folder(tmp_path: Path) -> None:
    (tmp_path / "test_a.py").write_text('"""FR-AAA-001 and NFR-BBB-001."""', encoding="utf-8")
    (tmp_path / "note.txt").write_text("FR-AAA-002", encoding="utf-8")  # not a searched suffix
    cited = citations((tmp_path,), tmp_path)
    assert set(cited) == {"FR-AAA-001", "NFR-BBB-001"}


def test_a_gap_needs_a_reason_and_a_stale_reason_is_reported() -> None:
    reqs = requirements(SAMPLE)
    cited = {"FR-AAA-001": {"tests/x.py"}}
    reasons = {"FR-AAA-001": "stale", "GONE-1": "unknown"}
    found = problems(reqs, cited, reasons)
    assert any(p.startswith("FR-AAA-002") for p in found)
    assert any("FR-AAA-001" in p and "delete the reason" in p for p in found)
    assert any(p.startswith("GONE-1") for p in found)
    assert "**none recorded**" in render(reqs, cited, {})
