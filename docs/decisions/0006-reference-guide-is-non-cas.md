# 0006. The Reference Guide in `references/` is the non-CAS edition

Date: 2026-11-01. Status: **open, needs a CAS command source.**

`references/TI-Nspire_ReferenceGuide_EN_4.5.pdf` is the guide for the numeric TI-Nspire. It has no entries for `solve`, `cSolve`, `zeros`, `limit`, `taylor`, `deSolve`, `expand`, `completeSquare`, `cFactor` or `comDenom`, and `factor()` appears only in its numeric form. The draft index (`docs/reference_index_draft.txt`) was therefore not missing `solve` through an extraction bug: the guide does not document it.

The draft did miss real guide entries, because it matched only headings tagged `Catalog >`. Key-driven entries use a `<key> key` tag instead: `sin()`, `cos()`, `tan()`, their inverses and reciprocals, `ln()`, `log()`, `exp()`, plus `Ans`, `nand`, `nor` and others. `tools/ref_matrix.py` finds headings from the PDF structure (name line followed by its syntax line) and produces `docs/command_matrix.csv` and `.md`.

## Consequence
The matrix covers the 281 numeric-guide headings. The CAS-only commands, which are the core of M1 tier 1, have no authoritative list. The corpus currently uses 25 names that are not in the guide (`docs/command_matrix.md`).

## Options (pick one)
1. Add TI's **CAS** Reference Guide PDF to `references/` (free from education.ti.com), and point the tool at it. Best: it also gives syntax, argument order and examples.
2. Capture the emulator's Catalog listing (Catalog > A to Z) on the teacher-software machine, as a text list.
3. Build the CAS list from the corpus plus the VCE teacher resource books only. Cheapest, but will be incomplete.
