"""Where the evidence files are: simulator screenshots, capture briefs and reference material.

They are kept in a separate repository, `CASSim-evidence`, laid out with the same relative
paths this repository uses (`corpus/shots/`, `docs/testing/*-shots/`, `references/`). It is
found through the `CASSIM_EVIDENCE` environment variable, or else as a folder beside the
main working copy. Nothing in the build or the test suite needs it: checks that read
evidence skip when it is absent.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = "CASSIM_EVIDENCE"
DEFAULT_NAME = "CASSim-evidence"


def evidence_root() -> Path | None:
    """The evidence folder, or None when this machine does not have it."""
    named = os.environ.get(ENV)
    root = Path(named) if named else ROOT.parent / DEFAULT_NAME
    return root if root.is_dir() else None


def evidence_path(relative: str | Path) -> Path:
    """The path of an evidence file given its path relative to the repository root.

    Falls back to the same path inside this working copy (for example an ignored local
    `references/` folder), so the result may not exist: callers check before reading.
    """
    root = evidence_root()
    if root is not None and (root / relative).exists():
        return root / relative
    return ROOT / relative
