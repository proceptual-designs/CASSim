"""Context menus on the marks of a Data & Statistics plot (FR-STAT-001, FR-STAT-003).

From stats4 R5-G2 (a right-click, a long press or ctrl+menu): a box plot, a histogram bar, and a
regression line or its equation label, with the Zoom and Color submenus. Numbers and grey items
are as recorded; actions CASSim has not built (Zoom In and Out, colours, Variable Bin Width,
Shade Under Function, Graph Trace) stay grey so the numbering matches the device.
"""

from __future__ import annotations

from cassim.device.menu import MenuItem
from cassim.devices.nspire.pages.statistics import Statistics
from cassim.stats.plots import PlotType

TARGETS = frozenset({"box", "histogram", "regression"})


def _item(label: str, arg: str, key: str, *, enabled: bool = True) -> MenuItem:
    return MenuItem(label, "statistics", arg, key=key, enabled=enabled)


def _grey(label: str, key: str = "") -> MenuItem:
    return MenuItem(label, key=key, enabled=False)


def zoom(key: str) -> MenuItem:
    return MenuItem(
        "Zoom",
        key=key,
        items=(
            MenuItem("Window settings…", "statistics", "wizard:window", key="1"),
            _item("Zoom - data", "zoom-data", "2"),
            _grey("Zoom - in", "3"),
            _grey("Zoom - out", "4"),
        ),
    )


def color(key: str) -> MenuItem:
    """Line, Fill and Text Color: the device enables one of them for each mark; CASSim has no
    colour choice yet, so all three are grey."""
    return MenuItem(
        "Color",
        key=key,
        items=(_grey("Line color", "1"), _grey("Fill color", "2"), _grey("Text color", "3")),
    )


def _plot(plot: PlotType, key: str) -> MenuItem:
    return _item(plot.value, f"plot:{plot.value}", key)


def context_menu(statistics: Statistics, target: str) -> MenuItem | None:
    if target == "box":
        return MenuItem(
            "Box plot",
            items=(
                _plot(PlotType.DOT, "1"),
                _plot(PlotType.HISTOGRAM, "2"),
                _plot(PlotType.NORMAL_PROBABILITY, "3"),
                _item(
                    "Show Box Plot Outliers"
                    if statistics.extend_whiskers
                    else "Extend Box Plot Whiskers",
                    "toggle-whiskers",
                    "4",
                ),
                zoom("5"),
                color("6"),
            ),
        )
    if target == "histogram":
        scales = tuple(
            scale
            for scale in ("Frequency", "Percent", "Density")
            if scale != statistics.histogram_scale
        )
        return MenuItem(
            "Histogram",
            items=(
                _plot(PlotType.DOT, "1"),
                _plot(PlotType.BOX, "2"),
                _plot(PlotType.NORMAL_PROBABILITY, "3"),
                MenuItem(
                    "Scale",
                    key="4",
                    items=tuple(
                        _item(scale, f"histogram-scale:{scale}", str(number))
                        for number, scale in enumerate(scales, start=1)
                    ),
                ),
                MenuItem(
                    "Bin settings",
                    key="5",
                    items=(
                        _item("Equal bin width", "wizard:bin-width", "1"),
                        _grey("Variable bin width", "2"),
                    ),
                ),
                zoom("6"),
                color("7"),
            ),
        )
    if target == "regression":
        return MenuItem(
            "Regression",
            items=(
                _item("Remove regression", "regression:none", "1"),
                _grey("Shade under function", "2"),
                _item(
                    "Hide Residual Squares"
                    if statistics.residual_squares
                    else "Show Residual Squares",
                    "toggle-residual-squares",
                    "3",
                ),
                _item(
                    "Hide Residual Plot" if statistics.residual_plot else "Show Residual Plot",
                    "toggle-residual-plot",
                    "4",
                ),
                _grey("Graph trace", "5"),
                color("6"),
            ),
        )
    return None
