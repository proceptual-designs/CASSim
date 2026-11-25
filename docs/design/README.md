# Design documents

What is kept in `docs/design/`, and where each kind of file goes. The requirements are in `docs/SRS.md` only; a design document names the requirement IDs it designs for and does not restate them. Decisions and spike results are in `docs/decisions/`.

## Design documents (SDD)

`SDD-nn-<topic>.md`, numbered as in SRS appendix A, which lists the full set and what stands in for the ones not yet written.

| File | Covers | Device |
|---|---|---|
| `SDD-02-worker-and-cancel.md` | Engine worker, Cancel and restore | shared (used by the Nspire) |
| `SDD-04-device-model.md` | Keys, menus, wizards, the 2D editor, documents | shared framework and Nspire data |
| `SDD-05-ui-flet.md` | The shell, the Nspire UI, the pseudocode workspace | shell, Nspire, Pseudocode & Python |
| `SDD-07-data-pages.md` | Lists & Spreadsheet, Data & Statistics, Finance | Nspire |
| `SDD-10-pwa-and-build.md` | Build, bundles, offline site, CI and deploy | all |
| `SDD-14-scientific-calculator-fx.md` | CASSim Scientific | Scientific |

## Supporting notes

A note that belongs to one design document or feature, named `<topic>.md`, with `-<device>` at the end when the topic exists for more than one device.

| File | What it is | Belongs to |
|---|---|---|
| `shortcuts.md` | The Nspire keyboard shortcuts CASSim supports (FR-CALC-004) | Nspire, SDD-04 |
| `complete-square.md` | What `completeSquare` accepts and the form it returns | Nspire engine |
| `tutorials-catalog-fx.md` | The planned and built tutorial lessons | Scientific, SDD-14 section 7 |

## Mock-ups: `mockups/`

CASSim's own design sketches, committed. One so far: `cassim_fx_interactive_mockup.html`, the first interactive sketch of CASSim Scientific (2026-11-22, when it was called CASSim fx). The built app has moved on from it; SDD-14 is the current design.

## Reference screenshots: `reference/<device>/`

Screenshots of a maker's own software or calculator, used as design input for layout. They are the makers' work, so the images are kept on Simon's computer only (`.gitignore`) and never go in the build; each folder's `README.md` is committed and lists them.

| Folder | Holds |
|---|---|
| `reference/nspire/` | Four layout screenshots of the TI-Nspire CX CAS Teacher Software |
| `reference/scientific/` | No screenshots yet; the layouts came from the manuals in `references/` |

A new device gets its own folder here (`reference/classpad/`, `reference/prime/`).

## What is not kept here

| Kind of file | Where |
|---|---|
| Evidence of what a simulator or emulator showed (screenshots and results) | `docs/testing/emulator-<topic>-results.md` with the screenshots in `docs/testing/<topic>-shots/`; a corpus case's screenshot is in `corpus/shots/` |
| Screenshots of CASSim itself | `docs/testing/app-shots/` |
| Manuals and books (the makers' PDFs, VCE resource books) | `references/`, not in the repository |
| Pseudocode dialect, syntax file and trace tables | `docs/pseudocode/` |
| Help pages for users | `docs/wiki/` |
