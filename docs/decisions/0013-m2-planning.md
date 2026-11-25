# 0013. M2 planning decisions

Date: 2026-11-02. Status: accepted (owner decisions), with two spikes to run first.
Since changed (note added 2026-11-25): this was the plan before the M2 spikes, and most items have been settled by later decisions. Item 1: results are drawn from LaTeX by `ft.Markdown` (0014, 0035). Item 2: CASSim has its own template editor; MathLive and MathQuill are not used (0015, 0017). Item 6: the data pages and Graphs are no longer stubs (0031). Item 8 and spike D: 0016. Item 9: the presets built are Dark, Light and High contrast (SDD-05). Item 10: the site is on Cloudflare Pages, not GitHub Pages (PLAN.md section 14). Items 3, 4, 5 and 7 stand.

## Decisions

1. **2D result rendering: spike first.** Compare LaTeX through a web renderer (KaTeX or MathJax) with our own layout drawn on the Flet canvas. The layout tree in `core/pretty.py` is terminal-only and is not the GUI's renderer.
2. **Maths input editor (2d): spike first.** Embed MathLive (fallback MathQuill) in the Flet web build and check focus, keyboard, mobile and offline behaviour. The linear editor ships first; 2d can follow.
3. **Display mode on a cold boot.** The chosen mode is stored in the settings. On a first visit, or when nothing is stored, pick it with a media query (or the Flet equivalent) from the viewport: phones and narrow screens start in Handheld, larger screens in Computer.
4. **Keypad and skin.** The same basic layout as the handheld, for familiarity, generated from the reference images and drawn as our own artwork. Fonts, corner rounding, colours and the like are ours. The skin is driven by a config file (extends FR-THEME-002 from colours to the whole look), so it can be changed without code.
5. **Keyboard capture.** When focus is in the calculator area (not the top menu or other chrome), the app captures keys: Ctrl+Enter, the TI key layers and so on. Outside it, browser shortcuts work as normal. A visible focus state shows which one is active. The browser-reserved combinations (Ctrl+W, Ctrl+T and similar) need a list of what cannot be captured and an alternative for each.
6. **Pages at the end of M2:** the Calculator page works; Graphs, Lists & Spreadsheet, Data & Statistics and Notes are registered stubs.
7. **Settings dialogs.** `case` goes in Document Settings. A new **`ascii`** setting (also a Document Setting) spells results with keyboard characters so they can be copied; it is in the engine now (`Settings.ascii`, `:set ascii=on`). `pretty` stays a REPL option.
8. **Cancel and state.** Test it: cancel terminates the engine worker, and a fresh worker is restored from the document model. How often to checkpoint is decided by measurement.
9. **Themes (Dark, Light, Outline).** Decide palettes while building the skin config (item 4) and see how they look.
10. **Hosting.** GitHub Pages is a static host, so a Flet static build (`flet publish`) can be served from it. Points to handle: the project site lives under `/<repo>/`, so publish with the matching base URL; `.mjs` and `.wasm` need the right MIME types (GitHub Pages serves them correctly, but check, since local servers often do not: decision 0002); the `index.html` patch and vendored packages from decision 0002 run in the publish step; the service worker scope follows the base URL. Check the build size against the Pages limits (1 GB site, 100 MB per file; decision 0002 measured 73 MB plus 22 MB). Pages cannot set response headers, so anything needing `COOP`/`COEP` (such as `SharedArrayBuffer`) is not available; spike 4 found workers do not need it.

## Spikes to run before the matching work

| Spike | Question | Feeds |
|---|---|---|
| A | Render a result as maths: KaTeX/MathJax in Flet versus a canvas layout of the engine's AST. Measure fidelity, speed, offline and size. | 2b |
| B | MathLive in the Flet web build: focus and keyboard capture, copy and paste, touch, offline, getting text out as TI syntax. | 2d |
| C | Publish the current shell to GitHub Pages from a project path and load it offline after first use. | 2e |
| D | Cancel and restore: terminate the engine worker mid-calculation and rebuild state from the document model. | 2c |
