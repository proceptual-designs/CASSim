# 0001. Tooling

Date: 2026-10-31. Status: accepted.

- Python 3.14 (matches Pyodide 314.0.7), uv 0.8.22, Ruff 0.17.3, Ty 0.0.95, pytest 9.2, Hypothesis, Playwright (drives the installed Edge; no browser download needed).
- The virtualenv lives outside OneDrive: `UV_PROJECT_ENVIRONMENT=C:\dev\venvs\emcas` (user environment variable; also set in `.mcp.json`). Build output goes to `C:\dev\builds\`.
- **Ty:** runs cleanly on the skeleton with its default rules. Stability on SymPy-heavy code is still unverified; revisit when `sympy_adapter.py` lands. Fallback: pyright.
- **Core must not import Flet:** enforced by `src/emcas/core/ruff.toml` (banned-api). It extends the root config.
- `spikes/` is excluded from Ruff; it holds throwaway code.
- Flet MCP (`flet-mcp`, in the `web` dependency group) is registered in `.mcp.json` as `uv run --group web flet mcp`.
- Dependency groups: `dev`, `test` (default); `web` (Flet, SciPy, `flet-mcp`) is opt-in, so core CI stays light.
