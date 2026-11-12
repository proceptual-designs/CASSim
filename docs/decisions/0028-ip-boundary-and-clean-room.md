# 0028: IP boundary and clean-room rule

Status: accepted 2026-11-12. Requirements: NFR-LEG-001, NFR-LEG-002, NFR-LEG-005, NFR-LEG-006, NFR-LEG-008, NFR-LEG-009, FR-DEV-005, FR-CPD-004, FR-DOC-006. This is not legal advice; Simon may get a lawyer's review before public release.

## Principle

**Copy behaviour, structure and vocabulary; never copy expression or code.**

CASSim exists so that students can practise on something that transfers to the real handheld: the same key positions, menu names and numbering, page types, command names and syntax. That is the method of operating the calculator, and it is what CASSim reproduces. The artwork, the prose and the software that TI wrote are expression, and CASSim reproduces none of them.

## Background

- *Data Access Corp v Powerflex Services Pty Ltd* [1999] HCA 49 (High Court of Australia). Copyright did not subsist in the individual command words of a computer language that Powerflex reused to build a compatible product. Powerflex was still liable for copying an embedded data table (the Huffman compression table). So command names are free to reuse, but tables or other data taken out of TI software are protected.
- *Lotus Development Corp v Borland International* (1st Cir. 1995, US). A menu command hierarchy is a "method of operation" and not copyrightable. Persuasive only; not binding in Australia.
- Visual material (icons, keypad and device artwork, screen chrome, fonts), help and error text, the Reference Guide's prose, and firmware are protected expression.
- "TI-Nspire" is a trademark. Saying what CASSim is compatible with (nominative use) is fine; implying TI's endorsement is not, under trademark law and under section 18 of the Australian Consumer Law (misleading or deceptive conduct). NFR-LEG-002's disclaimer covers this.
- Precedent: Woxi (<https://github.com/ad-si/Woxi>, AGPL-3.0) reimplements a subset of the Wolfram Language. Woxi Studio reads and writes `.nb` files and uses Mathematica-style cell names, but calls itself only "Mathematica-like" and does not copy Mathematica's artwork.

## Allowed (method of operation and interoperability)

- Command and function names, TI syntax and the Unicode symbol set (C-4).
- Menu structure, menu item names, menu numbering and keyboard shortcuts.
- Page types and key positions, including the secondary ctrl and shift labels.
- Document settings and their names.
- Output behaviour, observed through black-box use (the corpus).

## Not allowed

- TI logos, icons, keypad or device artwork, screen chrome, or fonts.
- Pixel tracing of reference screenshots.
- ROM, OS or firmware content, or any data tables extracted from TI software.
- Verbatim prose from TI: help text, catalog descriptions, error-message wording beyond short functional labels, or passages from the Reference Guide. CASSim writes its own.
- Anything implying TI endorsement.

## Clean-room rule (NFR-LEG-008)

Behaviour is learned only by observing the TI-Nspire CX CAS software and handheld in normal use: typing inputs and recording the outputs and screenshots, as the corpus already does (`docs/testing/TESTING.md`). It is never learned by decompiling, disassembling, debugging, unpacking or patching TI binaries, or by inspecting their memory or network traffic.

`references/` (including both Reference Guides and the shortcuts sheet) is for consultation only. What CASSim takes from it is facts (names, syntax, argument order, which menu an item is in), written up in CASSim's own words. Its text is never pasted into `src/`, the build or the in-app help (NFR-LEG-009). A short attributed note in a code comment that says what the guide specifies (for example "the guide allows ▶ only at the end of an entry line") is a citation, not copied help text.

## Screenshots and artwork

The screenshot policy is unchanged: reference screenshots live in `docs/design/reference/` and never in the build (NFR-LEG-001). Skin, keypad and icon work is drawn from scratch to match *positions and layout*, not traced from a screenshot or photograph (FR-DEV-005, FR-CPD-004).

## Short labels (NFR-LEG-009)

Menu labels and error names that are a few words long and functional ("Solve", "Domain error", "Non-real calculation") may match the device, so that students recognise them on the real handheld. Anything longer (a help paragraph, a catalog description, an explanation in a dialog) must be original.

## `.tns` files (FR-DOC-006)

Open and Save only read and write the native `.cassim.json` format. `.tns` stays Won't for now. If it is ever built, it lives under File > Import… and File > Export…, and the format is worked out only from public documentation or from black-box comparison of `.tns` files that Simon made with TI software he is licensed to use, never by decompiling TI software.

## Corpus capture (NFR-LEG-006)

The corpus was captured from the TI-Nspire CX CAS Premium Teacher Software, so NFR-LEG-006 is now a Must for TI. Its licence terms are recorded in decision 0029 (SRS Q42).

## Casio and HP (NFR-LEG-005)

The same boundary applies to the Casio ClassPad and HP Prime profiles (M8, M9): their command names, menu structure, key positions and settings may be matched; their logos, artwork, fonts, help text, ROM, firmware and emulator software may not. Behaviour is learned from their emulators and handhelds by observation only, after recording each emulator's licence terms (NFR-LEG-006, Q17, Q18).

## Consequences

- SRS: NFR-LEG-008 and NFR-LEG-009 added (Must); NFR-LEG-006 is Must for TI; FR-DEV-005, FR-CPD-004 and FR-DOC-006 reworded; C-2 and the scope say what is reproduced.
- PLAN.md: principle 5, the storage paragraph and the decisions list carry the rule; a pre-release audit of in-app strings against the Reference Guide sits in the release gates of PLAN.md section 11.
- Code: `device/serialize.py` names the native suffix (`SUFFIX`, `OPEN_EXTENSIONS`); tests check that Open and Save use only `.cassim.json` and that the File menu has no `.tns` entry.
- A first audit (2026-11-12) compared every 8-word run in `src/` with the text of both Reference Guides. The only matches are function signatures (`tvmFV(N,I,PV,Pmt,[PpY],[CpY],[PmtAt])` and the like, which are syntax) and one attributed comment in `core/ast.py`. No user-facing string longer than 12 words was copied.
