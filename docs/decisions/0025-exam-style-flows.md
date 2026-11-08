# 0025 Exam-style flows (M2 exit criterion)

Date: 2026-11-08. Status: built; headless and browser runs pass.
Code: `tools/flows.py`, data `corpus/flows/exam.yaml`, tests `tests/flows/test_exam_flows.py` and
`tests/e2e/test_flows_browser.py` (marked `e2e`, run with `pytest -m e2e`, about 3 minutes).

## What

The corpus checks the maths one line at a time. A flow checks a whole session the way a student
works it: typing through the keymaps, leaving exponents with Right, Ans, recalling an old line,
undo, Ctrl+Enter for a decimal, Problems with their own variables, stacked fractions and the
on-screen keypad. Each flow is a list of steps in YAML (`tools/flows.py` documents them).

- **Headless** (`tests/flows`): the steps drive `AppState`, the same object the GUI drives, so the
  keymaps, editor, history, document and engine all take part. `python -m tools.flows` prints the
  outcome of every flow.
- **Browser** (`tests/e2e/test_flows_browser.py`): the 5 flows marked `browser: true` are typed
  into the published static site with Playwright and read back from the console (`#/debug` prints
  `CASSIM: RESULT ...`). They use only typing and keys with the Methods defaults. Shifted symbols
  are sent as Shift plus the key, because Flutter reports the key and not the character (0015).
- The `site` fixture moved from `test_pwa.py` to `tests/e2e/conftest.py` (session scope) so the
  site is built once for all the e2e tests.

## Expected values

Not simulator captures. Each expected value is either taken from a simulator-captured corpus case
(the step's `from`) or worked by hand (`hand: true` on the flow, with the working in `note`).
Results are compared as maths (`same_value`), so `x=3 or x=1` matches `x=1 or x=3`, as in the corpus.
The hand-worked ones are: the cubic analysis, Ans and recall, the stacked fractions, `2^x=7`,
`(1+i)^4`, `(2+i)(1-3i)`, and the list statistics. Simon should check them or capture them on the
simulator.

## Findings

- Typing `x^3-6*x^2+9*x` key by key leaves everything after `^` in the exponent until Right is
  pressed, as on the handheld; the flows write that as `{R}`.
- Capital letters need Shift (a bare `A` is `a`), so `Ans` is typed with Shift on the A.

## Not covered

Installing on a phone and the Safari and Chromebook runs (needs Simon's devices); flows in the
Handheld view by clicking the keypad in the browser; flows for pages other than the Calculator
(M3 onwards).
