# 0012. VCAA question text in the pseudocode corpus and examples

Date: 2026-11-02. Status: accepted for development (owner decision), with a condition before anything is made public.
Files: `corpus/pseudocode/seed.yaml` (cases marked `third_party: true`), `docs/pseudocode/`.

## Context

The pseudocode corpus and the examples contain algorithm questions transcribed from VCAA exams and from the VCAA pseudocode support page (the simple loops, the intersect and bisection questions, the dice questions, and so on). Each such case is marked `third_party: true` and names its source.

## What VCAA's published terms say

Checked on 2026-11-02 at <https://vcaa.vic.edu.au/footer/copyright> (summarised here, not legal advice; the page does not mention exam questions by name):

- An "up front" licence lets registered schools and educational institutions in Australia copy and communicate VCAA works, in whole or in part, through secure learning-management or intranet systems, for non-commercial educational purposes.
- "Separate copyright permission from the VCAA is required for any publication on a website."
- Commercial use, or use beyond the allowances in the Copyright Act 1968 (Cth), needs permission through the VCAA request form, and a fee may apply.
- The licence does not extend to third-party content inside VCAA works.
- Attribution is required: (c) Victorian Curriculum and Assessment Authority.

## Decision

The owner's position is that the algorithm questions are generic enough not to be protectable as individual questions, and that VCAA's licence allows non-commercial educational use without asking. On that basis the cases stay in the **private** repository for development, each with `third_party: true` and its `source` attribution.

## Condition before anything goes public

The licence above covers schools using material internally. It does not cover publishing on a website, and CASSim is to be released under the Unlicense, which would let anyone reuse the repository contents commercially. So before the repository is made public or the corpus is distributed, do one of:

1. get VCAA's permission for the cases;
2. replace each `third_party: true` case with an original program that exercises the same construct (the author's own examples already cover every construct); or
3. leave those cases out of the public tree.

The application build never contains the corpus (as with `references/`), so the shipped app is unaffected. The author's own materials are his to license as he chooses.

## Update 2026-11-02 (14:57)

The owner confirmed the VCAA questions are fine to use and asked for a note of which paper each came from. Each case's `source` field names it, and `docs/pseudocode/sources.md` lists them all (cases still needing the exact paper confirmed are flagged). The condition above (permission, replacement or removal before any public release) stands.
