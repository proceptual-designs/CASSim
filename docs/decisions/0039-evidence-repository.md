# 0039: Evidence is kept in a separate repository

Status: accepted 2026-11-25 (Simon). Requirements: NFR-LEG-001, NFR-LEG-005, NFR-LEG-006. Replaces decision 0029, which moved to the evidence repository with the material it describes.

## Decision

This repository holds the code, the corpus cases and the written results: what was typed, what the device showed, and what CASSim does. The files those results were transcribed from are kept in a second repository, `CASSim-evidence`:

| Kept in `CASSim-evidence` | Path there |
|---|---|
| Simulator screenshots for corpus cases | `corpus/shots/` |
| Simulator screenshots for the emulator checks | `docs/testing/*-shots/` (not `app-shots/`, which shows CASSim and stays here) |
| Capture briefs, run plans and the list of items still to check | `docs/testing/emulator-*-capture.md`, `*-brief.md`, `*-plan.md`, `*-remaining.md`, `simulator-todo.md` |
| Makers' keypad and layout screenshots used as design input | `docs/design/reference/<device>/` |
| Reference material (guides, teacher resource books, libraries) | `references/` |
| The record of the software licence terms read before capture (NFR-LEG-006) | `docs/decisions/0029-ti-teacher-software-licence.md` |

The evidence repository uses the same relative paths as this one. A path such as `evidence: shots/methods.solve.quadratic.jpg` in a corpus case, or `docs/testing/pages-shots-6/B-A1-2-space-3.png` in a results file, names a file at that path in the evidence repository.

## How the tools find it

`tools/evidence.py` looks for the folder named by the `CASSIM_EVIDENCE` environment variable, and otherwise for `CASSim-evidence` beside the working copy. It is never linked into a worktree.

Nothing needs it to build, run or test CASSim. The corpus replays from the YAML alone. Checks that read evidence (`corpus/validate.py --check-evidence`, `tools/ref_matrix.py`, `tests/unit/test_tns_container.py`) skip or report when it is absent, as it is on CI.

## Rules

- A new capture stores its screenshots at the usual path in the evidence repository and its transcription here. `.gitignore` here refuses the evidence paths.
- Evidence is never in an app build (NFR-LEG-001).
- Before capturing from another maker's software, its licence terms are recorded beside the evidence (NFR-LEG-006), and the decision here that starts the capture says that this was done.
