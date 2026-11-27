# 0040: Run runs at once, without a prompt, because the runner is sandboxed

Status: accepted 2026-11-27 (Simon, asked 2026-11-26 and confirmed 2026-11-27). Requirements: FR-PY-002, FR-RUN-004, FR-EDT-004, NFR-SEC-002, C-7. Changes the "trust prompt" rule in AGENTS.md, PLAN.md (section 4 item 4, 5a, risk 8) and the SRS. Recorded in SDD-15 section 9.5.

## Decision

Pseudocode and Python programs run as soon as the person presses Run. There is no permission or trust prompt. Code that arrives from Open, Import, an example or a share link still never runs by itself: it is opened and waits for Run (C-7, FR-EDT-004).

## Why this is safe now

The prompt was the control while the sandbox was unproven: Pyodide is CPython with a `js` bridge to the page, so user Python run in it could reach the network, the page and IndexedDB (PLAN.md risk 8). A check of the code on 2026-11-27 found:

- **Run never executes user code as Python.** A Pseudocode program goes to CASSim's own interpreter (`runtime/pseudocode/interp.py`). A Python program is first translated to pseudocode (`python_to_pseudocode`), which refuses `import`, attribute access and calls of anything but a plain name; the interpreter then resolves names only to the program's own variables and functions and to a fixed table of maths, list and random built-ins. There is no route to Python's `eval`, `exec`, `open`, `__import__`, `js` or the network. Runs are bounded (1,000 passes per loop, 20,000 trace steps, recursion depth 100) and Stop cancels between steps.
- **The Python Console was the exception, and is closed.** It ran each line with Python's `exec` and full built-ins in the app's process: in the browser that reached the page's JavaScript (and so the network and saved documents), and on the desktop the whole computer. It now sends each line through the same translator and interpreter as Run (`CodeApp.submit_python_console`; tests in `tests/app/test_pseudocode_view.py`, `test_python_console_is_sandboxed`).
- The only other `eval` in the code, `core/compat/math_source.py`, compiles graph expressions after checking them against a whitelist of syntax, names (`x`, `math`, `min`, `max`), `math` functions and numeric constants, with no built-ins.

## Limits

- The sandbox holds because no user code reaches a real Python. If a real Python runtime is added (FR-RUN-003 names the standard library), the 5a spike on keeping that code off the network and the host page must pass first, and this decision is reviewed then.
- A single large calculation (a huge exact power, say) runs to completion before Stop is seen, because Stop is checked between steps. It can slow the tab; it cannot reach anything outside the interpreter.
- What the Console accepts is what a program accepts: Python that the translator does not support (string repetition such as `50 * 'hi'`, for example) gives an error in both.
