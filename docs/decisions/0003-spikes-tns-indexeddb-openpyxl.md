# 0003. Spikes 2, 4, 5: `.tns`, IndexedDB, openpyxl

Date: 2026-10-31. Tests: `tests/unit/test_tns_container.py`, `tests/e2e/test_spike_storage_xlsx.py`.
Same environment as 0002 (Flet 1.0.5, Pyodide 314.0.7, Edge headless).

## Spike 2: `.tns` decodability: **NO-GO for M0** (stays an optional M6 stretch)

- All 21 reference `.tns` files (`mm_`, `sm_`, `gm_` libraries) share the magic `*TIMLP0601` and are not plain zips.
- Payloads have about 7.97 bits/byte entropy, no zlib/deflate stream at any header offset, and every entry's data starts with the same 8 bytes `0F CE D8 D2 81 06 86 5B`.
- [Hackspire's TNS File Format page](https://www.hackspire.org/TNS_File_Format) describes the same signature and TI's private compression method 13, and states there is "currently no known way to get data from it".
- Consequence: no dependency on `.tns`. Libraries are ported by behaviour (PLAN.md 5.5): read the UDF guides, then verify each function against the simulator. Revisit only if a decoder appears.
- The unit test pins the header and signature, so a differing file fails loudly.

## Spike 4: IndexedDB from Pyodide: **GO**

- Works through `from js import indexedDB` in the Python worker, with `create_proxy` callbacks bridged to an `asyncio` future.
- Data persisted across two page visits in the same browser context (counter 1, then 2). A 2 MB value round-tripped in about 33 ms.
- Gotcha: an IndexedDB transaction auto-commits when control returns to the event loop with no pending request. Use **one transaction per operation**, never one held across `await`s (first attempt failed with `TransactionInactiveError`).
- Not tested: storage quota and eviction behaviour, Safari/iOS, and persistence after a service-worker update.

## Spike 5: `openpyxl` in Pyodide: **GO**

- `micropip.install("openpyxl")` gives 3.1.5 (pure Python, with `et_xmlfile`) in about 0.3 s online.
- A workbook with values and a formula saved to bytes and reloaded intact (`B6=25`, `C2==A2+B2`).
- Offline needs the wheels vendored, same as flet (see 0002).

## Test integration

- `tools/webharness.py` publishes a Flet app, serves it on a free port (with correct `.mjs`/`.wasm` MIME types) and drives it with Playwright, collecting console `SPIKE:` markers. Edge is used if installed, so no browser download is needed.
- e2e tests are marked `e2e` and deselected by default (`addopts = -m "not e2e"`). Run them with `uv run pytest -m e2e` (about 90 s: each spike app is built once per session).
