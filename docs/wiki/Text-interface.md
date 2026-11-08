# Text interface

If you have the CASSim source and `uv` installed, a text version of the Calculator page runs in a terminal. It is handy for checking an answer or running a file of entries.

```
uv run cassim --text
uv run cassim --text --course methods
uv run cassim -c "solve(x^2=2,x)"
uv run cassim run lesson.tib
```

`uv run cassim` on its own opens the graphical app. `--view handheld` or `--view computer` chooses its view, and `--course` and `--set` set the Document Settings.

## Plain keyboard spellings

| Symbol | Type |
|---|---|
| π | `pi` |
| ∞ | `infinity` |
| ⅇ (Euler's constant) | `@e` |
| ⅈ (imaginary unit) | `@i` |
| ᴇ (exponent marker) | `@E` |

Full details are in [docs/user/repl.md](https://github.com/simonjtyler/CASSim/blob/main/docs/user/repl.md).
