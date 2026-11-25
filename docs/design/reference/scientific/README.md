# Scientific calculator layout reference (design input)

No screenshots are kept here yet. The four keypad layouts of CASSim Scientific (Casio fx-82 series, Abacus SX-II series, Sharp EL-531 series, HP 10s series; SDD-14 section 4.2) were laid out from the keypad pictures and key sequences in the makers' manuals, which are in `references/` (not in the repository):

| Manual | Layout |
|---|---|
| `fx-82AU_PLUS_II_EN.pdf`, `How-Do-I...fx82-and-fx-100AU.pdf` | Casio fx-82 series (and the deferred fx-100 series, FR-FX-UI-006) |
| `ABACUS SX-II MATRIXn manual.pdf` | Abacus SX-II series |
| `Sharp EL-531TH operation guide.pdf` | Sharp EL-531 series |
| `HP 10s+ user guide (EN).pdf` | HP 10s series |

If a layout screenshot of a maker's emulator or a photograph of a calculator is taken as design input, it goes in this folder, named `layout-<maker>-<what it shows>.png`, and gets a row in a table here, as in `../nspire/README.md`. Images in this folder are kept locally only (`.gitignore`) and never go in the build. Reference only: no maker's logos, artwork or keypad graphics are shipped; CASSim's keys are its own drawing (SDD-14 section 2).

Not kept here:

- Evidence of what the emulators show (the fx-82AU PLUS II and SX-II check): `docs/testing/emulator-scientific-results.md`, with the screenshots in `docs/testing/scientific-shots/`, once the run in `docs/testing/emulator-scientific-capture.md` is done.
- CASSim's own first sketch of the calculator: `docs/design/mockups/cassim_fx_interactive_mockup.html`.
