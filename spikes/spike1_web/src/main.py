import sys
import time

import flet as ft

T0 = time.perf_counter()


async def main(page: ft.Page) -> None:
    page.title = "spike1"
    out = ft.Text("starting", key="result", selectable=True)
    ticker = ft.Text("tick 0", key="ticker")
    page.add(ft.Text(f"python {sys.version.split()[0]} on {sys.platform}"), ticker, out)
    lines: list[str] = []

    def log(msg: str) -> None:
        lines.append(msg)
        print(f"SPIKE: {msg}", flush=True)
        out.value = "\n".join(lines)
        page.update()

    def timed(label: str, fn):
        t = time.perf_counter()
        try:
            r = fn()
            log(f"{label}: {time.perf_counter() - t:.3f}s -> {r}")
        except Exception as e:
            log(f"{label}: ERROR {e!r}")

    log(f"main() reached {time.perf_counter() - T0:.3f}s after module import")
    t = time.perf_counter()
    try:
        import micropip

        await micropip.install(["sympy", "numpy", "scipy"])
        log(f"micropip install sympy/numpy/scipy: {time.perf_counter() - t:.3f}s")
    except Exception as e:
        log(f"micropip ERROR {e!r}")
        return
    timed("import sympy", lambda: __import__("sympy").__version__)
    import sympy as sp

    x = sp.symbols("x")
    timed("solve x^2-4", lambda: sp.solve(x**2 - 4, x))
    timed("integrate", lambda: sp.integrate(sp.sin(x) ** 2, x))
    timed("factor", lambda: sp.factor(x**6 - 1))
    timed("import numpy", lambda: __import__("numpy").__version__)
    timed("import scipy.stats", lambda: __import__("scipy.stats").__version__)

    def normcdf():
        from scipy.stats import norm

        return norm.cdf(1.96)

    timed("norm.cdf(1.96)", normcdf)

    def busy() -> None:
        t = time.perf_counter()
        while time.perf_counter() - t < 3:
            pass

    def on_busy(_e: ft.ControlEvent) -> None:
        # Does the ticker keep updating while Python is busy? (worker test)
        busy()
        log("busy 3s done")

    n = {"i": 0}

    def on_tick(_e: ft.ControlEvent) -> None:
        n["i"] += 1
        ticker.value = f"tick {n['i']}"
        page.update()

    page.add(
        ft.Button("busy 3s", key="busy", on_click=on_busy),
        ft.Button("tick", key="tick", on_click=on_tick),
    )
    log("DONE")


ft.run(main)
