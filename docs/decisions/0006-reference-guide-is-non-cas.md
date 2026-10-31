# 0006. Reference sources for the command matrix

Date: 2026-11-01. Status: accepted.

## Finding
`references/TI-Nspire_ReferenceGuide_EN_4.5.pdf` is the **non-CAS** guide. It has no entries for `solve`, `cSolve`, `zeros`, `limit`, `taylor`, `deSolve`, `expand`, `completeSquare`, `cFactor` or `comDenom`, and `factor()` appears only in its numeric form. The draft index (`docs/reference_index_draft.txt`) was therefore not missing `solve` through an extraction bug: the guide does not document it. The draft also missed key-driven entries (`sin()`, `ln()`, `exp()`, `Ans`, `nand`, ...) because it matched only the `Catalog >` tag.

## Decision
1. **Primary source: the TI-Nspire CAS Reference Guide.** The newest copy found is software **3.2** (2012), kept as `references/TI-NspireCAS_ReferenceGuide_EN_3.2.pdf` (git-ignored with the rest of `references/`). The installed Teacher Software ships no reference guide. A newer CAS guide, if found, replaces it.
2. **Every entry must be verified against the emulator Catalog**, because 3.2 predates the emulator. The matrix has an empty `emulator_verified` column for this. Commands the corpus uses that neither guide lists are reported separately.
3. The numeric guide 4.5 supplements the CAS guide for newer numeric commands.
4. **Not everything needs implementing first.** Priority comes from usage: **core** = used by a corpus case; **likely** = not in the corpus but mentioned 5+ times in the VCE teacher resource books; **later** = the rest. Multi-step corpus cases are listed to show which commands are combined.

`tools/ref_matrix.py` generates `docs/command_matrix.csv` and `.md`. It supersedes the draft index.

## Limits
- Book mention counts come from running text only; worked examples shown as screenshots are not searchable, so counts are lower bounds. Words like `For` and `If` count program text in the books.
- Multi-step tests are taken from the corpus only. Extracting multi-step worked problems from the books is not done.
