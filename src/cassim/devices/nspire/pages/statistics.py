"""The Data & Statistics page model (FR-STAT-001, FR-STAT-003, FR-STAT-005)."""

from __future__ import annotations

import math
import re
import statistics as py_statistics
from collections.abc import Callable
from fractions import Fraction
from typing import TYPE_CHECKING, Any

from cassim.core.compat.statistics import Fit, fit_regression
from cassim.core.results import VariableInfo
from cassim.device.wizard import Field, Wizard
from cassim.stats.data import DataValue, NumericExpression, as_numbers, parse_items
from cassim.stats.plots import (
    PlotData,
    PlottedPoint,
    PlotType,
    dot_data_at,
    dot_points,
    plot_scene,
    scatter_data_at,
    scatter_points,
)

if TYPE_CHECKING:
    from cassim.core.session import Session
    from cassim.device.engine import RemoteSession
    from cassim.doc.document import Page, Problem
    from cassim.graph.scene import Scene

type PlotPoint = tuple[float, float]
MIN_NORMAL_SAMPLE = 2
WINDOW_FIELDS = 4

REGRESSIONS = (
    ("LinRegMx", "Linear (mx+b)"),
    ("LinRegBx", "Linear (a+bx)"),
    ("MedMed", "Median-Median"),
    ("QuadReg", "Quadratic"),
    ("CubicReg", "Cubic"),
    ("QuartReg", "Quartic"),
    ("PowerReg", "Power"),
    ("ExpReg", "Exponential"),
    ("LnReg", "Logarithmic"),
    ("SinReg", "Sinusoidal"),
    ("Logistic", "Logistic (d=0)"),
    ("LogisticD", "Logistic (d≠0)"),
)


def _float_values(values: tuple[DataValue, ...]) -> tuple[float | None, ...]:
    return as_numbers(values)


def _fraction(value: float) -> Fraction:
    return Fraction(str(value))


def _fit_label(command: str, fit: Fit) -> str:
    equation = {
        "LinRegMx": "m·x+b",
        "LinRegBx": "a+b·x",
        "MedMed": "m·x+b",
        "QuadReg": "a·x²+b·x+c",
        "CubicReg": "a·x³+b·x²+c·x+d",
        "QuartReg": "a·x⁴+b·x³+c·x²+d·x+e",
        "PowerReg": "a·x^b",
        "ExpReg": "a·b^x",
        "LnReg": "a+b·ln(x)",
        "SinReg": "a·sin(b·x+c)+d",
        "Logistic": "c/(1+a·ⅇ^(-b·x))",
        "LogisticD": "c/(1+a·ⅇ^(-b·x))+d",
    }[command]
    for name, value in fit.coefficients.items():
        equation = re.sub(rf"(?<![A-Za-z]){name}(?![A-Za-z])", _format(value), equation)
    score = f", r²={fit.r_squared:.6g}" if fit.r_squared is not None else ""
    return f"y = {equation}{score}"


class Statistics:
    """A view over list variables in one Problem; no data is copied into the document."""

    def __init__(self, session: Session | RemoteSession) -> None:
        self.session = session
        self.x_name = ""
        self.y_name = ""
        self.summary_name = ""
        self.split_name = ""
        self.plot_type = PlotType.DOT
        self.force_categorical_x = False
        self.force_numeric_x = False
        self.connect_points = False
        self.show_all_labels = False
        self.extend_whiskers = False
        self.category_order = "Alpha Order"
        self.histogram_width = 1.0
        self.histogram_scale = "Frequency"
        self.regression = ""
        self.residual_plot = False
        self.residual_squares = False
        self.normal_pdf = False
        self.function_text = ""
        self.plot_value_text = ""
        self.window: tuple[float, float, float, float] | None = None
        self.message = ""
        self._rows: dict[str, VariableInfo] = {}
        self._values: dict[str, tuple[DataValue, ...]] = {}
        self._revisions: dict[str, int] = {}
        self._scene_size: tuple[float, float, bool] | None = None
        self._scene: Scene | None = None
        self.update()
        if self.lists:
            self.x_name = self.lists[0]

    @property
    def lists(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                (
                    name
                    for name, row in self._rows.items()
                    if row.items is not None and row.text.startswith("{")
                ),
                key=str.casefold,
            )
        )

    @property
    def numeric_lists(self) -> tuple[str, ...]:
        return tuple(
            name
            for name in self.lists
            if any(isinstance(value, float) for value in self._values.get(name, ()))
        )

    @property
    def category_lists(self) -> tuple[str, ...]:
        return tuple(
            name
            for name in self.lists
            if any(isinstance(value, str) for value in self._values.get(name, ()))
        )

    @property
    def categorical_x(self) -> bool:
        return self.force_categorical_x or (
            not self.force_numeric_x and self._categorical(self.x_name)
        )

    def update(self) -> None:
        rows = self.session.variables()
        names = {row.name for row in rows}
        self._rows = {row.name: row for row in rows}
        self._values = {name: values for name, values in self._values.items() if name in names}
        self._revisions = {
            name: revision for name, revision in self._revisions.items() if name in names
        }
        for row in rows:
            if row.items is None or not row.text.startswith("{"):
                continue
            revision = self.session.revision_of(row.name)
            if self._revisions.get(row.name) != revision:
                self._values[row.name] = parse_items(row.items)
                self._revisions[row.name] = revision
                self._scene = None
        if self.x_name and self.x_name not in self.lists:
            self.x_name = ""
            self._scene = None
        if self.y_name and self.y_name not in self.lists:
            self.y_name = ""
            self._scene = None
        if self.summary_name and self.summary_name not in self.lists:
            self.summary_name = ""
            self._scene = None
        if self.split_name and self.split_name not in self.lists:
            self.split_name = ""
            self._scene = None

    def available_plot_types(self) -> tuple[PlotType, ...]:
        if not self.x_name:
            return ()
        if self.summary_name:
            return (PlotType.BAR,) if self.split_name else (PlotType.BAR, PlotType.PIE)
        if self.y_name and self.categorical_x:
            return (
                PlotType.DOT,
                PlotType.BOX,
                PlotType.HISTOGRAM,
                PlotType.NORMAL_PROBABILITY,
            )
        if self.categorical_x:
            return (
                (PlotType.DOT_CHART, PlotType.BAR)
                if self.split_name
                else (
                    PlotType.DOT_CHART,
                    PlotType.BAR,
                    PlotType.PIE,
                )
            )
        if self.y_name:
            return (
                PlotType.SCATTER,
                PlotType.XY_LINE,
            )
        return (PlotType.DOT, PlotType.BOX, PlotType.HISTOGRAM, PlotType.NORMAL_PROBABILITY)

    def perform(self, action: str) -> None:
        """Apply one menu action and invalidate the cached scene."""
        self.message = ""
        name, _, value = action.partition(":")
        if name in {"x", "y", "summary", "split"}:
            self._select_variable(name, value)
        elif name.startswith("toggle-"):
            self._toggle(name)
        elif name == "wizard":
            self.message = value
            return
        elif name == "clear":
            self._clear()
        elif not self._set_option(name, value):
            self.message = f"Unsupported Data & Statistics action: {action}"
            return
        self._scene = None

    def _select_variable(self, name: str, value: str) -> None:
        match name:
            case "x":
                self.x_name = value
                self.summary_name = ""
                self.force_categorical_x = False
                self.force_numeric_x = False
                self.plot_type = self._default_plot_type()
            case "y":
                self.y_name = value
                if value:
                    self.plot_type = self._default_plot_type()
            case "summary":
                self.summary_name = value
                self.split_name = ""
                self.plot_type = PlotType.BAR
            case "split":
                self.split_name = value
        self._scene = None

    def _default_plot_type(self) -> PlotType:
        if self.categorical_x:
            return PlotType.DOT if self.y_name else PlotType.DOT_CHART
        return PlotType.SCATTER if self.y_name else PlotType.DOT

    def _set_option(self, name: str, value: str) -> bool:
        match name:
            case "plot":
                self.plot_type = PlotType(value)
            case "regression":
                self.regression = "" if value == "none" else value
                self.residual_plot = False
                self.residual_squares = False
            case "set-function":
                self.function_text = value
            case "sort-order":
                if value in ("List Order", "Value Order", "Alpha Order"):
                    self.category_order = value
            case "histogram-scale":
                self.histogram_scale = value
            case "zoom-data":
                self.window = None
            case _:
                return False
        return True

    def _toggle(self, name: str) -> None:
        match name:
            case "toggle-force-x":
                if self._categorical(self.x_name):
                    self.force_numeric_x = not self.force_numeric_x
                    self.force_categorical_x = False
                else:
                    self.force_categorical_x = not self.force_categorical_x
                    self.force_numeric_x = False
                self.plot_type = self._default_plot_type()
            case "toggle-connect":
                self.connect_points = not self.connect_points
            case "toggle-labels":
                self.show_all_labels = not self.show_all_labels
            case "toggle-whiskers":
                self.extend_whiskers = not self.extend_whiskers
            case "toggle-residual-plot":
                self.residual_plot = not self.residual_plot
            case "toggle-residual-squares":
                self.residual_squares = not self.residual_squares
            case "toggle-normal-pdf":
                self.normal_pdf = not self.normal_pdf
            case _:
                self.message = f"Unsupported Data & Statistics action: {name}"
        self._scene = None

    def _clear(self) -> None:
        self.x_name = self.y_name = self.summary_name = self.split_name = ""
        self.force_categorical_x = self.force_numeric_x = False
        self.regression = ""
        self.residual_plot = self.residual_squares = self.normal_pdf = False
        self.function_text = ""
        self.plot_value_text = ""
        self.plot_type = PlotType.DOT
        self._scene = None

    def wizard(self, action: str) -> Wizard:
        match action:
            case "window":
                if self.plot_type is PlotType.HISTOGRAM:
                    xmin, xmax, _, ymax = self.window or self._default_histogram_window()
                    fields = (
                        Field("xmin", "XMin", _format(xmin)),
                        Field("xmax", "XMax", _format(xmax)),
                        Field("ymax", "YMax", _format(ymax)),
                    )
                    return Wizard("Window Settings", fields)
                xmin, xmax, ymin, ymax = self.window or self._default_window()
                fields = tuple(
                    Field(name, label, _format(value))
                    for name, label, value in (
                        ("xmin", "XMin", xmin),
                        ("xmax", "XMax", xmax),
                        ("ymin", "YMin", ymin),
                        ("ymax", "YMax", ymax),
                    )
                )
                return Wizard("Window Settings", fields)
            case "function":
                return Wizard(
                    "Plot Function", (Field("expression", "f(x)", self.function_text or "x"),)
                )
            case "value":
                return Wizard("Plot Value", (Field("x", "x", self.plot_value_text or "0"),))
            case "bin-width":
                return Wizard(
                    "Equal Bin Width Settings",
                    (Field("width", "Width", _format(self.histogram_width)),),
                )
        raise ValueError(f"unknown statistics dialog: {action}")

    def finish_wizard(self, action: str, values: dict[str, str]) -> list[str]:
        problem = ""
        try:
            match action:
                case "window":
                    problem = self._finish_window(values)
                case "function":
                    problem = self._finish_text(values, "expression", "function")
                case "value":
                    problem = self._finish_text(values, "x", "value")
                case "bin-width":
                    problem = self._finish_bin_width(values)
                case _:
                    problem = f"Unknown statistics dialog: {action}"
        except ValueError, KeyError:
            problem = "Enter valid numeric values."
        if problem:
            return [problem]
        self._scene = None
        return []

    def _finish_window(self, values: dict[str, str]) -> str:
        xmin = float(values["xmin"])
        xmax = float(values["xmax"])
        if self.plot_type is PlotType.HISTOGRAM:
            ymax = float(values["ymax"])
            if (
                not all(math.isfinite(value) for value in (xmin, xmax, ymax))
                or xmin >= xmax
                or ymax <= 0
            ):
                return "Window minimums must be less than their maximums."
            self.window = (xmin, xmax, 0.0, ymax)
            return ""
        ymin = float(values["ymin"])
        ymax = float(values["ymax"])
        bounds = xmin, xmax, ymin, ymax
        if not all(math.isfinite(value) for value in bounds) or xmin >= xmax or ymin >= ymax:
            return "Window minimums must be less than their maximums."
        self.window = bounds
        return ""

    def _finish_text(self, values: dict[str, str], key: str, kind: str) -> str:
        expression = values[key].strip()
        if not expression:
            return "Enter a function of x." if kind == "function" else "Enter a numeric x value."
        numeric = NumericExpression(
            {"x": Fraction(1)} if kind == "function" else {},
            self._numeric_lists(),
        )
        try:
            numeric.validate(expression)
        except SyntaxError, ValueError:
            return (
                "Enter a supported numeric function of x."
                if kind == "function"
                else "Enter a supported numeric expression."
            )
        if kind == "function":
            self.function_text = expression
        else:
            self.plot_value_text = expression
        return ""

    def _finish_bin_width(self, values: dict[str, str]) -> str:
        width = float(values["width"])
        if not math.isfinite(width) or width <= 0:
            return "Width must be a positive number."
        self.histogram_width = width
        return ""

    def plot_data(self) -> PlotData:
        self.update()
        x = self._values.get(self.x_name, ())
        if self.force_numeric_x:
            x = tuple(_numeric_text(value) for value in x)
        y = self._values.get(self.y_name, ())
        summary_values = _float_values(self._values.get(self.summary_name, ()))
        split = self._values.get(self.split_name, ())
        regression_points: tuple[PlotPoint, ...] = ()
        residuals: tuple[PlotPoint, ...] = ()
        regression_label = ""
        residual_squares: float | None = None
        if self.regression and x and y:
            pairs = [
                (float(xv), float(yv))
                for xv, yv in zip(x, y, strict=False)
                if isinstance(xv, float) and isinstance(yv, float)
            ]
            if len(pairs) > 1:
                fit = self._fit(pairs)
                if fit is not None:
                    low, high = min(px for px, _ in pairs), max(px for px, _ in pairs)
                    if low == high:
                        low, high = low - 1, high + 1
                    regression_points = self._sample(fit.predict, low, high)
                    residuals = tuple((px, py - fit.predict(px)) for px, py in pairs)
                    residual_squares = sum(value * value for _, value in residuals)
                    regression_label = _fit_label(self.regression, fit)
        function = self._function_points()
        plot_value = self._plot_value()
        distribution = y if y and self.categorical_x else x
        normal_pdf = (
            self._normal_curve(distribution, self.histogram_width, self.histogram_scale)
            if self.normal_pdf
            else ()
        )
        plot_type = self.plot_type
        if self.force_categorical_x and plot_type not in (
            PlotType.DOT_CHART,
            PlotType.BAR,
            PlotType.PIE,
        ):
            plot_type = PlotType.DOT_CHART
        if self.summary_name and plot_type is PlotType.DOT_CHART:
            plot_type = PlotType.BAR
        return PlotData(
            plot_type=plot_type,
            x_name=self.x_name,
            x=x,
            y_name=self.y_name,
            y=y,
            summary=summary_values,
            split_name=self.split_name,
            split=split,
            force_categorical_x=self.force_categorical_x,
            category_order=self.category_order,
            connect_points=self.connect_points,
            show_all_labels=self.show_all_labels,
            extend_whiskers=self.extend_whiskers,
            histogram_width=self.histogram_width,
            histogram_scale=self.histogram_scale,
            regression=regression_points,
            regression_label=regression_label,
            residuals=residuals,
            residual_plot=self.residual_plot and bool(residuals),
            residual_squares=residual_squares if self.residual_squares else None,
            normal_pdf=normal_pdf,
            function=function,
            function_label=self.function_text,
            plot_value=plot_value,
            window=self.window,
        )

    def scene(self, width: float, height: float, *, axis_labels: bool = True) -> Scene:
        self.update()
        if self._scene is None or self._scene_size != (width, height, axis_labels):
            self._scene = plot_scene(self.plot_data(), width, height, axis_labels=axis_labels)
            self._scene_size = (width, height, axis_labels)
        return self._scene

    def plotted_points(self, width: float, height: float) -> tuple[PlottedPoint, ...]:
        data = self.plot_data()
        if self.y_name and self.plot_type in (PlotType.SCATTER, PlotType.XY_LINE):
            return scatter_points(data, width, height)
        if not self.y_name and self.plot_type is PlotType.DOT:
            return dot_points(data, width, height)
        return ()

    def drag_value_at(
        self, width: float, height: float, screen_x: float, screen_y: float
    ) -> tuple[float, float] | None:
        data = self.plot_data()
        if self.y_name and self.plot_type in (PlotType.SCATTER, PlotType.XY_LINE):
            return scatter_data_at(data, width, height, screen_x, screen_y)
        if not self.y_name and self.plot_type is PlotType.DOT:
            x = dot_data_at(data, width, height, screen_x, screen_y)
            return (x, 0.0) if x is not None else None
        return None

    def drag_expression(self, index: int, x: float, y: float) -> str | None:
        if (
            not self.x_name
            or index < 0
            or not math.isfinite(x)
            or not math.isfinite(y)
            or index >= len(self._values.get(self.x_name, ()))
        ):
            return None
        x_values = self._values.get(self.x_name, ())
        x_value = _numeric_text(x_values[index]) if self.force_numeric_x else x_values[index]
        if not isinstance(x_value, float):
            return None
        if not self.y_name and self.plot_type is PlotType.DOT:
            return f"{self.x_name}[{index + 1}]:={_input_number(x)}"
        if (
            self.plot_type not in (PlotType.SCATTER, PlotType.XY_LINE)
            or not self.y_name
            or self.x_name == self.y_name
        ):
            return None
        y_values = self._values.get(self.y_name, ())
        if index >= len(y_values) or not isinstance(y_values[index], float):
            return None
        return (
            f"{self.x_name}[{index + 1}]:={_input_number(x)}:"
            f"{self.y_name}[{index + 1}]:={_input_number(y)}"
        )

    def _fit(self, pairs: list[tuple[float, float]]) -> Fit | None:
        try:
            return fit_regression(
                self.regression,
                [_fraction(x) for x, _ in pairs],
                [_fraction(y) for _, y in pairs],
            )
        except (ValueError, ZeroDivisionError, OverflowError) as error:
            self.message = str(error) or "The selected regression cannot be fitted to these data."
            return None

    @staticmethod
    def _sample(
        function: Callable[[float], float], low: float, high: float
    ) -> tuple[PlotPoint, ...]:
        points = []
        for step in range(101):
            x = low + (high - low) * step / 100
            try:
                y = float(function(x))
            except ValueError, ZeroDivisionError, OverflowError:
                continue
            if math.isfinite(y):
                points.append((x, y))
        return tuple(points)

    def _function_points(self) -> tuple[PlotPoint, ...]:
        if not self.function_text or not self.x_name or not self.y_name:
            return ()
        xs = _float_values(self._values.get(self.x_name, ()))
        if self.force_numeric_x:
            xs = _float_values(
                tuple(_numeric_text(value) for value in self._values.get(self.x_name, ()))
            )
        values = tuple(value for value in xs if value is not None)
        if not values:
            return ()
        low, high = min(values), max(values)
        numeric_lists = self._numeric_lists()

        def evaluate(x: float) -> float:
            return float(
                NumericExpression({"x": _fraction(x)}, numeric_lists).evaluate(self.function_text)
            )

        return self._sample(evaluate, low, high)

    def _numeric_lists(self) -> dict[str, tuple[Fraction, ...]]:
        return {
            name: tuple(_fraction(value) for value in values if isinstance(value, float))
            for name, values in self._values.items()
        }

    def _plot_value(self) -> float | None:
        if not self.plot_value_text:
            return None
        try:
            return float(
                NumericExpression(lists=self._numeric_lists()).evaluate(self.plot_value_text)
            )
        except SyntaxError, ValueError, ZeroDivisionError, OverflowError:
            self.message = "Plot Value must be a numeric expression."
            return None

    @staticmethod
    def _normal_curve(
        values: tuple[DataValue, ...], bin_width: float, scale: str
    ) -> tuple[PlotPoint, ...]:
        numbers = _float_values(values)
        numbers = tuple(value for value in numbers if value is not None)
        if len(numbers) < MIN_NORMAL_SAMPLE:
            return ()
        mean = py_statistics.mean(numbers)
        deviation = py_statistics.pstdev(numbers)
        if deviation == 0:
            return ()
        low, high = min(numbers), max(numbers)
        factor = {
            "Frequency": len(numbers) * bin_width,
            "Percent": 100 * bin_width,
            "Density": 1.0,
        }[scale]
        return tuple(
            (
                x,
                factor
                * math.exp(-0.5 * ((x - mean) / deviation) ** 2)
                / (deviation * math.sqrt(math.tau)),
            )
            for x in (low + (high - low) * step / 100 for step in range(101))
        )

    def _categorical(self, name: str) -> bool:
        return any(isinstance(value, str) for value in self._values.get(name, ()))

    def _default_window(self) -> tuple[float, float, float, float]:
        xs = _float_values(self._values.get(self.x_name, ()))
        if self.force_numeric_x:
            xs = _float_values(
                tuple(_numeric_text(value) for value in self._values.get(self.x_name, ()))
            )
        ys = _float_values(self._values.get(self.y_name, ()))
        x = tuple(value for value in xs if value is not None) or (0.0, 1.0)
        y = tuple(value for value in ys if value is not None) or (0.0, 1.0)
        x_min, y_min = min(x), min(y)
        x_max = max(x) if x_min != max(x) else x_min + 1
        y_max = max(y) if y_min != max(y) else y_min + 1
        return x_min, x_max, y_min, y_max

    def _default_histogram_window(self) -> tuple[float, float, float, float]:
        values = self._values.get(self.y_name, ()) if self.y_name and self.categorical_x else ()
        numbers = _float_values(values or self._values.get(self.x_name, ()))
        if self.force_numeric_x:
            numbers = _float_values(
                tuple(_numeric_text(value) for value in self._values.get(self.x_name, ()))
            )
        numbers = tuple(value for value in numbers if value is not None)
        if not numbers:
            return self._default_window()
        width = self.histogram_width
        low, high = min(numbers), max(numbers)
        xmin = low - width / 2
        xmax = high + width / 2
        counts: dict[int, int] = {}
        for value in numbers:
            index = math.floor((value - low) / width)
            counts[index] = counts.get(index, 0) + 1
        maximum = max(counts.values(), default=1)
        if self.histogram_scale == "Percent":
            maximum = maximum / len(numbers) * 100
        elif self.histogram_scale == "Density":
            maximum = maximum / (len(numbers) * width)
        return xmin, xmax, 0.0, float(maximum) * 1.15


def _format(value: float) -> str:
    return f"{value:.6g}"


def _input_number(value: float) -> str:
    return re.sub(r"[eE]", "ᴇ", format(value, ".15g"))


def _numeric_text(value: DataValue) -> DataValue:
    if not isinstance(value, str):
        return value
    try:
        result = float(NumericExpression().evaluate(value))
    except SyntaxError, ValueError, ZeroDivisionError, OverflowError:
        return None
    return result if math.isfinite(result) else None


def new_statistics(problem: Problem) -> Statistics:
    return Statistics(problem.session)


def dump_statistics(statistics: Statistics) -> dict[str, Any]:
    return {
        "x": statistics.x_name,
        "y": statistics.y_name,
        "summary": statistics.summary_name,
        "split": statistics.split_name,
        "plot": statistics.plot_type.value,
        "force_categorical_x": statistics.force_categorical_x,
        "force_numeric_x": statistics.force_numeric_x,
        "connect_points": statistics.connect_points,
        "show_all_labels": statistics.show_all_labels,
        "extend_whiskers": statistics.extend_whiskers,
        "category_order": statistics.category_order,
        "histogram_width": statistics.histogram_width,
        "histogram_scale": statistics.histogram_scale,
        "regression": statistics.regression,
        "residual_plot": statistics.residual_plot,
        "residual_squares": statistics.residual_squares,
        "normal_pdf": statistics.normal_pdf,
        "function": statistics.function_text,
        "plot_value": statistics.plot_value_text,
        "window": list(statistics.window) if statistics.window is not None else None,
    }


def load_statistics(statistics: Statistics, data: dict[str, Any]) -> Statistics:
    statistics.x_name = _saved_text(data.get("x"))
    statistics.y_name = _saved_text(data.get("y"))
    statistics.summary_name = _saved_text(data.get("summary"))
    statistics.split_name = _saved_text(data.get("split"))
    try:
        statistics.plot_type = PlotType(data.get("plot", PlotType.DOT.value))
    except ValueError:
        statistics.plot_type = PlotType.DOT
    for key in (
        "force_categorical_x",
        "force_numeric_x",
        "connect_points",
        "show_all_labels",
        "extend_whiskers",
        "residual_plot",
        "residual_squares",
        "normal_pdf",
    ):
        setattr(statistics, key, data.get(key) is True)
    if data.get("category_order") in ("List Order", "Value Order", "Alpha Order"):
        statistics.category_order = data["category_order"]
    width = data.get("histogram_width", 1.0)
    if (
        isinstance(width, int | float)
        and not isinstance(width, bool)
        and math.isfinite(width)
        and width > 0
    ):
        statistics.histogram_width = float(width)
    scale = data.get("histogram_scale")
    if scale in ("Frequency", "Percent", "Density"):
        statistics.histogram_scale = scale
    statistics.regression = _saved_text(data.get("regression"))
    if statistics.regression not in {command for command, _ in REGRESSIONS}:
        statistics.regression = ""
    statistics.function_text = _saved_text(data.get("function"))
    statistics.plot_value_text = _saved_text(data.get("plot_value"))
    window = data.get("window")
    if (
        isinstance(window, list)
        and len(window) == WINDOW_FIELDS
        and all(
            isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value)
            for value in window
        )
        and window[0] < window[1]
        and window[2] < window[3]
    ):
        statistics.window = (
            float(window[0]),
            float(window[1]),
            float(window[2]),
            float(window[3]),
        )
    statistics.update()
    statistics._scene = None
    statistics._scene_size = None
    return statistics


def _saved_text(value: object) -> str:
    return value if isinstance(value, str) else ""


def statistics_of(page: Page | None) -> Statistics | None:
    return page.model if page is not None and isinstance(page.model, Statistics) else None
