"""The standalone pseudocode Code view: CodeMirror, console and a vertical trace."""

from __future__ import annotations

import ast
import asyncio
import contextlib
import io
import json
from collections.abc import Callable
from typing import TYPE_CHECKING, cast

import flet as ft

from cassim.app.theme import DARK, HIGH_CONTRAST, LIGHT, Theme
from cassim.devices.pseudocode.typing_aids import convert_symbols, convert_typing
from cassim.devices.pseudocode.ui.panes import BoxedPane, PaneOptions
from cassim.runtime.pseudocode import (
    TRANSLATION_MARKER,
    PseudocodeError,
    Settings,
    TranslationError,
    arith,
    parse,
    pseudocode_to_python,
    python_to_pseudocode,
    run,
    trace,
)
from cassim.runtime.pseudocode.settings import AngleMode, NumberMode
from cassim.runtime.pseudocode.typing_aid import replacement_before_cursor

if TYPE_CHECKING:
    from cassim.app.shell import Shell


EXAMPLE = (
    "terms ← 10\n"
    "a ← 0\n"
    "b ← 1\n"
    "for i from 1 to terms\n"
    "  c ← a + b\n"
    "  a ← b\n"
    "  b ← c\n"
    "end for\n"
    "print b"
)
LINEAR = "die1 ← randint(1, 6)\ndie2 ← randint(1, 6)\ntotal ← die1 + die2\nprint total"
BISECTION = (
    "define f(x)\n"
    "  return x*x - 2\n"
    "end\n"
    "precision ← 0.001\n"
    "a ← 1\n"
    "b ← 2\n"
    "while b-a > precision\n"
    "  c ← (a+b)/2\n"
    "  if f(c) < 0 then\n"
    "    a ← c\n"
    "  else\n"
    "    b ← c\n"
    "  end if\n"
    "end while\n"
    "print c"
)
GCD_LCM = (
    "define gcd(a, b)\n"
    "  while b ≠ 0 do\n"
    "    remainder ← a mod b\n"
    "    a ← b\n"
    "    b ← remainder\n"
    "  end while\n"
    "  return a\n"
    "end\n"
    "a ← 84\n"
    "b ← 30\n"
    "g ← gcd(a, b)\n"
    "print g\n"
    "print (a*b) div g"
)
DICE_MAX_STATS = (
    "seed(42)\n"
    "trials ← 200\n"
    "sum ← 0\n"
    "sum_squares ← 0\n"
    "for trial from 1 to trials\n"
    "  die1 ← randint(1, 6)\n"
    "  die2 ← randint(1, 6)\n"
    "  if die1 > die2 then\n"
    "    largest ← die1\n"
    "  else\n"
    "    largest ← die2\n"
    "  end if\n"
    "  sum ← sum + largest\n"
    "  sum_squares ← sum_squares + largest*largest\n"
    "end for\n"
    "mean ← sum/trials\n"
    "sd ← sqrt((sum_squares - trials*mean*mean)/(trials - 1))\n"
    "print mean\n"
    "print sd"
)
D4_SAMPLE_SPACE = (
    "outcomes ← []\n"
    "for first from 1 to 4\n"
    "  for second from 1 to 4\n"
    "    append [first, second] to outcomes\n"
    "  end for\n"
    "end for\n"
    "print outcomes"
)
LEFT_RIEMANN = (
    "define f(x)\n"
    "  return e^x\n"
    "end\n"
    "rectangles ← 10\n"
    "left ← 0\n"
    "right ← 1\n"
    "width ← (right-left)/rectangles\n"
    "total ← 0\n"
    "for i from 0 to rectangles-1\n"
    "  total ← total + f(left + i*width)*width\n"
    "end for\n"
    "print total"
)
POLYNOMIAL_NEWTON = (
    "define polynomial(coefficients, x)\n"
    "  value ← 0\n"
    "  for each coefficient in coefficients\n"
    "    value ← value*x + coefficient\n"
    "  end for\n"
    "  return value\n"
    "end\n"
    "define derivative(coefficients, x)\n"
    "  value ← 0\n"
    "  power ← len(coefficients) - 1\n"
    "  for i from 1 to len(coefficients)-1\n"
    "    value ← value*x + coefficients[i]*power\n"
    "    power ← power - 1\n"
    "  end for\n"
    "  return value\n"
    "end\n"
    "coefficients ← [1, 0, -2, -5]\n"
    "x ← 2\n"
    "for iteration from 1 to 8\n"
    "  x ← x - polynomial(coefficients, x)/derivative(coefficients, x)\n"
    "end for\n"
    "print x"
)
MOBILE_BREAKPOINT = 900
LINE_COLUMN_WIDTH = 40
VARIABLE_COLUMN_WIDTH = 76
CONDITION_COLUMN_WIDTH = 130
OUTPUT_COLUMN_WIDTH = 140
SYMBOL_COLUMN_COUNT = 3
EDITOR_SETTINGS_KEY = "editor"
CODE_FONT = "CASSim Code"
MATH_FONT = "CASSim Math"
SYMBOL_FONT = "Symbols"
THEMES: dict[str, Theme] = {
    "Dark": DARK,
    "Light": LIGHT,
    "High contrast": HIGH_CONTRAST,
}


def _control_style() -> ft.ButtonStyle:
    return ft.ButtonStyle(
        bgcolor={
            ft.ControlState.SELECTED: DARK.accent,
            ft.ControlState.DEFAULT: DARK.key,
        },
        color={
            ft.ControlState.SELECTED: DARK.accent_text,
            ft.ControlState.DEFAULT: DARK.key_text,
        },
        side=ft.BorderSide(1, DARK.key_edge),
        shape=ft.RoundedRectangleBorder(radius=6),
        padding=ft.Padding.symmetric(horizontal=8, vertical=6),
        text_style=ft.TextStyle(size=12),
    )


def _safe_update(control: ft.Control) -> None:
    with contextlib.suppress(RuntimeError):
        control.update()


class CodeApp:
    def __init__(self, shell: Shell) -> None:  # noqa: PLR0915
        self.shell = shell
        self.page = shell.page
        shell.changed = self.on_bridge
        self.result = None
        self.cursor = 0
        self.selection = trace.VerticalSelection()
        self.choices = trace.VerticalSelection()
        self.cancelled = False
        self.running = False
        self.dirty = False
        self.current_source = EXAMPLE
        self.trace_source = EXAMPLE
        self.line_numbers_visible = True
        self.typing_aid = False
        self.typing_aids = False
        self.typing_undo: tuple[str, str] | None = None
        self.code_style = "monospace"
        self.symbol_style = "unicode"
        self.console_inputs: list[str] = []
        self.python_console_namespace: dict[str, object] = {"__name__": "cassim_console"}
        self.language = "pseudocode"
        self.number_mode: NumberMode = "approx"
        self.angle_mode: AngleMode = "radian"
        self.theme_name = "Dark"
        self.cm = None
        self.cm_change_proxy = None
        self._init_workspace_state()

        self.fallback_editor = ft.TextField(
            value=EXAMPLE,
            multiline=True,
            min_lines=len(EXAMPLE.splitlines()) + 1,
            max_lines=5000,
            autocorrect=False,
            enable_suggestions=False,
            text_style=self.editor_text_style(),
            content_padding=ft.Padding.only(left=8, right=8, top=12, bottom=12),
            border=ft.OutlineInputBorder(side=ft.BorderSide.none()),
            label="Code",
            label_style=ft.TextStyle(size=1, color="transparent"),
            tooltip="Code editor",
            on_change=self.on_fallback_source,
        )
        self.line_number_gutter = ft.Text(
            self._line_numbers_for(EXAMPLE),
            style=ft.TextStyle(font_family="monospace", size=14, height=20 / 14),
            selectable=False,
            width=42,
            text_align=ft.TextAlign.RIGHT,
        )
        editor_row = ft.Row(
            [
                ft.Container(
                    self.line_number_gutter,
                    width=42,
                    padding=ft.Padding.only(top=8),
                    alignment=ft.Alignment.TOP_RIGHT,
                ),
                self.fallback_editor,
            ],
            expand=True,
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
        editor_content = ft.Column(
            [editor_row],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=0,
        )

        self.number_button = ft.Button("Approx", on_click=self.cycle_number, style=_control_style())
        self.angle_button = ft.Button("Radian", on_click=self.toggle_angle, style=_control_style())
        self.update_item = ft.MenuItemButton(
            content=getattr(self.shell, "update_label", "Check for Updates"),
            on_click=self.activate_update,
        )
        self.cassim_menu = ft.SubmenuButton(
            content="CASSim",
            controls=[
                *(
                    [ft.MenuItemButton(content="Home", on_click=self.home)]
                    if getattr(self.shell, "home", None) is not None
                    else []
                ),
                ft.MenuItemButton(content="Settings…", on_click=self.open_settings),
                ft.MenuItemButton(content="Appearance…", on_click=self.open_appearance),
                self.update_item,
                ft.MenuItemButton(content="Help (wiki)…", on_click=self.open_help),
                ft.MenuItemButton(content="About CASSim…", on_click=self.open_about),
            ],
        )
        examples = self.build_examples_menu()
        self.doc_menu = ft.SubmenuButton(
            content="Doc",
            controls=[
                ft.MenuItemButton(content="Open…", on_click=self.open_file),
                ft.MenuItemButton(content="Save", on_click=self.save_file),
                ft.MenuItemButton(content="Save as…", on_click=self.save_file_as),
                examples,
            ],
        )
        self.app_menu = ft.Row(
            [
                ft.MenuBar(controls=[self.cassim_menu]),
                ft.MenuBar(controls=[self.doc_menu]),
            ],
            spacing=4,
            tight=True,
        )
        self.language_switch = ft.SegmentedButton(
            selected=["pseudocode"],
            segments=[
                ft.Segment(value="pseudocode", label="Pseudocode"),
                ft.Segment(value="python", label="Python"),
            ],
            show_selected_icon=False,
            style=_control_style(),
            on_change=self.toggle_language,
        )
        self.trace_layout = ft.Button(
            "Trace: Vertical",
            on_click=self.cycle_trace_layout,
            style=_control_style(),
        )
        self.typing_aids_switch = ft.Switch(
            label="Typing aids",
            value=False,
            on_change=self.toggle_typing_aids,
        )
        self.trace_items = ft.Column(
            [ft.Text("Run to discover constants, variables, functions, and conditions", size=12)],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=4,
        )

        self.console = ft.Text(
            "",
            selectable=True,
            font_family=CODE_FONT,
            font_family_fallback=[MATH_FONT, SYMBOL_FONT],
            expand=True,
        )
        self.console_input = ft.TextField(
            hint_text="Input or expression",
            dense=True,
            width=180,
            on_submit=self.submit_console,
        )
        self.console_scroll = ft.Column(
            [
                self.console,
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        console_content = ft.Container(self.console_scroll, expand=True)
        self.trace = ft.Column(expand=True, spacing=0)
        self.trace_controls = self._build_trace_controls()

        self.editor_pane = BoxedPane(
            "Code",
            editor_content,
            PaneOptions(
                height=470,
                minimum=240,
                title_controls=[self.language_switch],
                on_change=self.position_codemirror,
            ),
        )
        self.console_pane = BoxedPane(
            "Console",
            console_content,
            PaneOptions(
                height=190,
                minimum=120,
                collapsed=True,
                on_change=self.position_codemirror,
                title_controls=[self.console_input],
            ),
        )
        self.items_pane = BoxedPane(
            "Symbols",
            self.trace_items,
            PaneOptions(height=180, minimum=120),
        )
        self.trace_pane = BoxedPane(
            "Trace Table",
            self.trace,
            PaneOptions(height=420, minimum=240),
        )
        self.toolbar = ft.Row(
            [
                self.app_menu,
                self.number_button,
                self.angle_button,
                self.trace_layout,
                self.typing_aids_switch,
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=8,
            tight=True,
        )
        self.root = ft.Column(expand=True)

    def build_examples_menu(self) -> ft.SubmenuButton:
        def group(title: str, items: tuple[tuple[str, str], ...]) -> ft.SubmenuButton:
            return ft.SubmenuButton(
                content=title,
                controls=[
                    ft.MenuItemButton(
                        content=label,
                        on_click=lambda _event, source=source: self.load_example(source),
                    )
                    for label, source in items
                ],
            )

        return ft.SubmenuButton(
            content="Examples",
            controls=[
                group(
                    "Intro",
                    (("Linear", LINEAR), ("Loop", EXAMPLE), ("Bisection", BISECTION)),
                ),
                group(
                    "Number theory",
                    (
                        ("GCD and LCM", GCD_LCM),
                        ("Polynomial + Newton", POLYNOMIAL_NEWTON),
                    ),
                ),
                group(
                    "Probability",
                    (
                        ("Two D6: larger", DICE_MAX_STATS),
                        ("Two D4 sample space", D4_SAMPLE_SPACE),
                    ),
                ),
                group("Numerical methods", (("Left Riemann sum", LEFT_RIEMANN),)),
            ],
        )

    def _init_workspace_state(self) -> None:
        self.generated_python = False
        self.python_header = ""
        self.column_split = 0.5
        self.left_host: ft.Container | None = None
        self.trace_mode = "vertical"
        self.trace_widths: dict[str, float] = {
            "__line__": LINE_COLUMN_WIDTH,
            "__output__": OUTPUT_COLUMN_WIDTH,
        }
        self.trace_active_columns: list[str] = []
        self.trace_resize_controls: dict[str, list[ft.Container]] = {}
        self.trace_table_container: ft.Container | None = None
        self.symbol_widths = [150.0, 150.0, 150.0]
        self.symbol_columns: list[ft.Container] = []

    def _build_trace_controls(self) -> ft.Row:
        self.status = ft.Text("")
        self.run_button = ft.Button("Run", on_click=self.run_code)
        self.stop_button = ft.Button("Stop", on_click=self.stop_code, visible=False)
        self.step_button = ft.Button("Step", on_click=self.step_forward)
        self.start_button = ft.Button("First", on_click=self.to_start)
        self.end_button = ft.Button("Last", on_click=self.to_end)
        for button in (
            self.run_button,
            self.stop_button,
            self.step_button,
            self.start_button,
            self.end_button,
        ):
            button.style = _control_style()
        return ft.Row(
            [
                self.run_button,
                self.stop_button,
                self.step_button,
                self.start_button,
                self.end_button,
                self.status,
            ],
            wrap=True,
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    async def start(self, **_options: object) -> None:
        self.page.fonts = {
            CODE_FONT: "fonts/RobotoMono-Regular.ttf",
            MATH_FONT: "fonts/NotoSansMath-Regular.ttf",
            SYMBOL_FONT: "fonts/NotoSansSymbols2-Regular.ttf",
        }
        await self.load_editor_settings()
        self.page.title = "CASSim-pseudocode"
        self.page.padding = 8
        self.page.on_resize = self.on_resize
        self.page.on_keyboard_event = self.on_keyboard
        self.page.add(self.root)
        self.apply_theme("Dark")
        self.arrange()
        if self._has_browser_dom():
            await self.start_codemirror()

    def editor_text_style(self) -> ft.TextStyle:
        family = CODE_FONT if self.code_style == "monospace" else "sans-serif"
        return ft.TextStyle(
            font_family=family,
            font_family_fallback=[MATH_FONT, SYMBOL_FONT],
            size=14,
            height=20 / 14,
        )

    async def load_editor_settings(self) -> None:
        saved = await self.shell.read(EDITOR_SETTINGS_KEY)
        if saved is None:
            return
        try:
            data = json.loads(saved)
        except json.JSONDecodeError:
            self.shell.notice("Code settings", "Saved code display settings could not be read.")
            return
        if not isinstance(data, dict):
            self.shell.notice("Code settings", "Saved code display settings could not be read.")
            return
        code_style = data.get("code_style")
        symbol_style = data.get("symbol_style")
        typing_aids = data.get("typing_aids")
        if code_style in ("monospace", "formatted"):
            self.code_style = str(code_style)
        if symbol_style in ("unicode", "ascii"):
            self.symbol_style = str(symbol_style)
        if isinstance(typing_aids, bool):
            self.typing_aids = typing_aids
            self.typing_aid = typing_aids
        self.typing_aids_switch.value = self.typing_aids
        self.update_typing_aids()
        self.apply_code_style()
        if self.symbol_style == "ascii":
            self.set_source(convert_symbols(self.current_source, "ascii"))

    def save_editor_settings(self) -> None:
        self.shell.write(
            EDITOR_SETTINGS_KEY,
            json.dumps(
                {
                    "code_style": self.code_style,
                    "symbol_style": self.symbol_style,
                    "typing_aids": self.typing_aids,
                }
            ),
        )

    def apply_code_style(self) -> None:
        self.fallback_editor.text_style = self.editor_text_style()
        if self.cm is not None:
            family = (
                f'"{CODE_FONT}", "{MATH_FONT}", monospace'
                if self.code_style == "monospace"
                else f'sans-serif, "{MATH_FONT}"'
            )
            self.cm.getWrapperElement().style.fontFamily = family

    def unmount(self) -> None:
        if self.cm is not None:
            import js  # ty: ignore[unresolved-import]  # noqa: PLC0415

            host = js.document.getElementById("cassim-codemirror")
            if host:
                host.remove()
        self.shell.changed = lambda: None
        self.page.on_keyboard_event = None
        self.page.on_resize = None
        self.page.controls.clear()

    @staticmethod
    def _has_browser_dom() -> bool:
        """True only with a page document: the web build's UI runs in a worker, which has `js`
        but no `document`, so CodeMirror cannot be mounted there."""
        try:
            import js  # ty: ignore[unresolved-import]  # noqa: PLC0415
        except ImportError:
            return False
        return hasattr(js, "document")

    def on_bridge(self) -> None:
        self.update_item.content = getattr(self.shell, "update_label", "Check for Updates")
        _safe_update(self.update_item)

    def apply_theme(self, name: str) -> None:
        theme = THEMES[name]
        self.theme_name = name
        self.page.theme_mode = ft.ThemeMode.LIGHT if name == "Light" else ft.ThemeMode.DARK
        self.page.bgcolor = theme.background
        if self.cm is not None:
            self.cm.setOption("theme", "default" if name == "Light" else "dracula")
            self.cm.refresh()
        self.page.update()

    def settings(self) -> Settings:
        return Settings(number=self.number_mode, angle=self.angle_mode)

    def source(self) -> str:
        if self.cm is not None:
            return str(self.cm.getValue())
        return str(self.fallback_editor.value or "")

    def on_fallback_source(self, event: ft.Event[ft.TextField]) -> None:
        text = str(event.control.value or "")
        previous = self.current_source
        if self.typing_aid and not self.typing_aids:
            selection = event.control.selection
            cursor = selection.end if selection is not None else len(text)
            replacement = replacement_before_cursor(text, cursor)
            if replacement is not None:
                event.control.value = (
                    text[: replacement.start] + replacement.replacement + text[replacement.end :]
                )
                event.control.update()
                self.typing_undo = (str(event.control.value or ""), text)
                self.current_source = str(event.control.value or "")
                self.refresh_line_numbers()
                self.mark_dirty()
                return
        if self.typing_aids and self.symbol_style == "unicode":
            converted = convert_typing(previous, text)
            if converted != text:
                self.typing_undo = (converted, text)
                event.control.value = converted
                event.control.update()
                text = converted
        self.current_source = text
        self.refresh_line_numbers()
        self.mark_dirty()

    def toggle_language(self, event: ft.Event[ft.SegmentedButton]) -> None:
        selected = event.control.selected
        target = selected[0] if selected else "pseudocode"
        if target == self.language:
            return
        try:
            translated = (
                pseudocode_to_python(self.source(), self.settings())
                if target == "python"
                else python_to_pseudocode(self.python_translation_source())
            )
        except (PseudocodeError, SyntaxError, TranslationError) as error:
            event.control.selected = [self.language]
            event.control.update()
            self.shell.notice("Translation not available", str(error))
            return
        self.language = target
        if target == "python":
            self.set_generated_python(translated)
        else:
            self.set_source(translated, generated_python=False)
        if self.cm is not None:
            self.cm.setOption("mode", "pseudocode" if self.language == "pseudocode" else "python")
            self.cm.refresh()
        event.control.update()
        self.update_typing_aids()
        self.mark_dirty()

    def toggle_line_numbers(self, event: ft.Event[ft.Switch]) -> None:
        self.line_numbers_visible = bool(event.control.value)
        self.line_number_gutter.visible = self.line_numbers_visible
        _safe_update(self.line_number_gutter)
        if self.cm is not None:
            self.cm.setOption("lineNumbers", self.line_numbers_visible)
            self.cm.refresh()

    @staticmethod
    def _line_numbers_for(source: str) -> str:
        return "\n".join(str(number) for number in range(1, len(source.splitlines()) + 1))

    def refresh_line_numbers(self) -> None:
        source = str(self.fallback_editor.value or "")
        self.line_number_gutter.value = self._line_numbers_for(source)
        self.fallback_editor.min_lines = max(12, len(source.splitlines()) + 1)
        self.line_number_gutter.visible = self.line_numbers_visible
        _safe_update(self.line_number_gutter)
        _safe_update(self.fallback_editor)

    def cycle_trace_layout(self, _: ft.Event[ft.Button]) -> None:
        modes = ("vertical", "horizontal", "none")
        self.change_trace_layout(modes[(modes.index(self.trace_mode) + 1) % len(modes)])

    def change_trace_layout(self, value: str) -> None:
        self.trace_mode = value
        self.trace_layout.content = f"Trace: {value.title()}"
        _safe_update(self.trace_layout)
        self.update_trace()

    async def open_file(self, _: ft.Event[ft.MenuItemButton]) -> None:
        text = await self.shell.pick_file(("py", "txt", "pseudo"), "Open code")
        if text is not None:
            if TRANSLATION_MARKER in text.splitlines():
                self.set_generated_python(text)
            else:
                self.set_source(text)

    async def save_file(self, _: ft.Event[ft.MenuItemButton]) -> None:
        extension = "py" if self.language == "python" else "txt"
        await self.shell.save_file(
            f"untitled.{extension}",
            self.source(),
            "Save code",
        )

    def save_file_as(self, _: ft.Event[ft.MenuItemButton]) -> None:
        name = ft.TextField(
            label="File name",
            value="untitled.py" if self.language == "python" else "untitled.txt",
        )

        async def save(_: ft.Event[ft.TextButton]) -> None:
            file_name = str(name.value or "").strip()
            if file_name:
                await self.shell.save_file(file_name, self.source(), "Save code")
            self.page.pop_dialog()

        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Save code"),
                content=name,
                actions=[
                    ft.TextButton("Save", on_click=save),
                    ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog()),
                ],
            )
        )

    def load_example(self, text: str) -> None:
        try:
            source = (
                pseudocode_to_python(text, self.settings()) if self.language == "python" else text
            )
        except (PseudocodeError, SyntaxError, TranslationError) as error:
            self.shell.notice("Cannot load example", str(error))
            return
        if self.language == "python":
            self.set_generated_python(source)
        else:
            self.set_source(source)

    @staticmethod
    def split_generated_python(source: str) -> tuple[str, str]:
        lines = source.splitlines()
        if TRANSLATION_MARKER in lines:
            marker = lines.index(TRANSLATION_MARKER)
            return "\n".join(lines[: marker + 1]), "\n".join(lines[marker + 1 :]) + "\n"
        return "", source

    def set_generated_python(self, source: str) -> None:
        self.python_header, visible = self.split_generated_python(source)
        self.set_source(visible, generated_python=True)

    def python_translation_source(self) -> str:
        source = self.source()
        if self.generated_python:
            return f"{self.python_header}\n{source}"
        return source

    def set_source(self, text: str, *, generated_python: bool = False) -> None:
        if self.symbol_style == "ascii":
            text = convert_symbols(text, "ascii")
        self.generated_python = generated_python
        if not generated_python:
            self.python_header = ""
        if self.cm is not None:
            self.cm.setValue(text)
        self.fallback_editor.value = text
        self.refresh_line_numbers()
        if hasattr(self.page, "update"):
            self.fallback_editor.update()
        self.current_source = text
        self.trace_source = text
        self.result = None
        self.cursor = 0
        self.selection = trace.VerticalSelection()
        self.choices = trace.VerticalSelection()
        self.trace_items.controls = [
            ft.Text("Run to discover constants, variables, functions, and conditions", size=12)
        ]
        if hasattr(self.page, "update"):
            _safe_update(self.trace_items)
        self.status.value = ""
        if hasattr(self.page, "update"):
            _safe_update(self.status)
        self.update_trace()
        self.mark_dirty()

    def submit_console(self, event: ft.Event[ft.TextField]) -> None:
        text = str(event.control.value or "").strip()
        if not text:
            return
        event.control.value = ""
        event.control.update()
        previous = self.console.value or ""

        source = self.source()
        if self.language == "python":
            output = self.submit_python_console(text)
            self.console.value = self.console_entry(previous, text, output)
            _safe_update(self.console)
            self.scroll_console_end()
            return
        if "input " in source.lower() or "input(" in source.lower():
            self.console_inputs.append(text)
            inputs = tuple(self.console_inputs)
            result = run(source, self.settings(), inputs, trace=True)
            self.result = result
            self.cursor = len([step for step in result.steps if step.kind != "halt"])
            output = "\n".join(result.output)
            if result.error:
                output = "\n".join(part for part in (output, f"Error: {result.error}") if part)
            self.console.value = self.console_entry(previous, text, output)
            _safe_update(self.console)
            self.scroll_console_end()
            self.choices = trace.vertical_choices(result, self.settings())
            constants = set(self.constant_names())
            self.selection = trace.VerticalSelection(
                tuple(name for name in self.choices.variables if name not in constants),
                self.condition_selection_values(),
            )
            self.build_variables()
            self.update_trace()
        else:
            baseline = run(source, self.settings(), trace=True)
            console_source = self.pseudocode_console_source(source, text)
            result = run(console_source, self.settings(), trace=True)
            output = "\n".join(result.output[len(baseline.output) :])
            if result.error:
                output = "\n".join(part for part in (output, f"Error: {result.error}") if part)
            self.console.value = self.console_entry(previous, text, output)
            _safe_update(self.console)
            self.scroll_console_end()

    @staticmethod
    def console_entry(previous: str, entered: str, output: str) -> str:
        parts = [previous.rstrip("\n"), f"> {entered}", output.rstrip("\n")]
        return "\n".join(part for part in parts if part).strip()

    def scroll_console_end(self) -> None:
        try:
            page = self.console_scroll.page
        except RuntimeError:
            return
        page.run_task(self.scroll_console_after_render)

    async def scroll_console_after_render(self) -> None:
        await asyncio.sleep(0.05)
        await self.console_scroll.scroll_to(offset=-1, duration=100)

    def mark_dirty(self) -> None:
        if not self.dirty:
            self.dirty = True
            self.run_button.content = "Run *"
            if hasattr(self.page, "update"):
                _safe_update(self.run_button)

    def submit_python_console(self, text: str) -> str:
        """Execute a Python console line or expression in a persistent namespace."""
        try:
            parsed = ast.parse(text, mode="exec")
            is_print_call = (
                len(parsed.body) == 1
                and isinstance(parsed.body[0], ast.Expr)
                and isinstance(parsed.body[0].value, ast.Call)
                and isinstance(parsed.body[0].value.func, ast.Name)
                and parsed.body[0].value.func.id == "print"
            )
            if len(parsed.body) == 1 and isinstance(parsed.body[0], ast.Expr) and not is_print_call:
                parsed = ast.Expression(parsed.body[0].value)
                value = eval(
                    compile(parsed, "<console>", "eval"),
                    {"__builtins__": __builtins__},
                    self.python_console_namespace,
                )
                return str(value)
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                exec(
                    compile(parsed, "<console>", "exec"),
                    {"__builtins__": __builtins__},
                    self.python_console_namespace,
                )
            return buffer.getvalue().rstrip("\n")
        except Exception as error:
            return f"Error: {type(error).__name__}: {error}"

    def pseudocode_console_source(self, source: str, text: str) -> str:
        """Turn a console line into valid pseudocode in the selected language."""
        stripped = text.strip()
        statement_prefixes = (
            "print ",
            "input ",
            "append ",
            "return ",
            "if ",
            "while ",
            "for ",
            "repeat ",
            "define ",
            "end ",
        )
        is_assignment = "←" in stripped or "<-" in stripped or stripped.count("=") == 1
        if stripped.startswith(statement_prefixes) or is_assignment:
            return f"{source}\n{stripped}"
        return f"{source}\nprint {stripped}"

    async def start_codemirror(self) -> None:
        import js  # ty: ignore[unresolved-import]  # noqa: PLC0415
        from pyodide.ffi import create_proxy, to_js  # ty: ignore[unresolved-import]  # noqa: PLC0415

        document = js.document
        for url in (
            "codemirror/codemirror.min.css",
            "codemirror/dracula.css",
        ):
            link = document.createElement("link")
            link.rel = "stylesheet"
            link.href = f"assets/{url}"
            document.head.appendChild(link)
        for url in (
            "codemirror/codemirror.min.js",
            "codemirror/simple.min.js",
            "codemirror/python.min.js",
        ):
            script = document.createElement("script")
            script.src = f"assets/{url}"
            document.head.appendChild(script)
        for _ in range(100):
            await asyncio.sleep(0.05)
            if bool(getattr(js, "CodeMirror", None)):
                break
        if not bool(getattr(js, "CodeMirror", None)):
            self.shell.notice("Code editor", "CodeMirror could not load; using the text fallback.")
            self.fallback_editor.visible = True
            self.page.update()
            return

        js.eval(r"""
if (!window.CASSimPseudocodeModeDefined) {
  window.CASSimPseudocodeModeDefined = true;
  CodeMirror.defineSimpleMode("pseudocode", {
    start: [
      {regex: /\b(if|then|else|while|for|define|end|return)\b/i, token:"keyword"},
      {regex: /\b(print|input|append|and|or|not|true|false)\b/i, token:"keyword"},
      {regex: /(?:←|<-|=|<=|>=|!=|<|>|\+|-|×|÷|\*|\/|\^)/, token:"operator"},
      {regex: /[0-9]+(?:\.[0-9]+)?/, token:"number"},
      {regex: /"(?:[^\\]|\\.)*"?/, token:"string"},
      {regex: /#.*/, token:"comment"},
    ],
  });
}
""")
        host = document.createElement("div")
        host.id = "cassim-codemirror"
        host.style.position = "fixed"
        host.style.zIndex = "20"
        host.style.background = "#282a36"
        host.style.border = "1px solid #555"
        document.body.appendChild(host)

        cm = js.CodeMirror(
            host,
            to_js(
                {
                    "value": self.current_source,
                    "mode": "pseudocode" if self.language == "pseudocode" else "python",
                    "theme": "dracula",
                    "lineNumbers": self.line_numbers_visible,
                    "lineWrapping": True,
                    "indentUnit": 2,
                    "tabSize": 2,
                    "autofocus": False,
                    "cassimTypingAids": self.typing_aids
                    and self.language == "pseudocode"
                    and self.symbol_style == "unicode",
                },
                dict_converter=js.Object.fromEntries,
            ),
        )
        self.cm = cm
        self.fallback_editor.visible = False
        self.line_number_gutter.visible = False
        _safe_update(self.line_number_gutter)
        self.apply_code_style()
        self.update_typing_aids()
        self.install_typing_aids()

        def changed(_instance: object, change: object) -> None:
            if (
                self.typing_aid
                and not self.typing_aids
                and str(getattr(change, "origin", "")) == "+input"
            ):
                cursor = cm.getCursor()
                source = str(cm.getValue())
                line = int(cursor.line)
                offset = sum(len(part) + 1 for part in source.splitlines()[:line])
                index = offset + int(cursor.ch)
                replacement = replacement_before_cursor(source, index)
                if replacement is not None:
                    from_cursor = to_js(
                        {
                            "line": line,
                            "ch": int(cursor.ch) - (replacement.end - replacement.start),
                        },
                        dict_converter=js.Object.fromEntries,
                    )
                    cm.replaceRange(replacement.replacement, from_cursor, cursor, "+typingAid")
                    return
            self.current_source = str(cm.getValue())
            self.mark_dirty()

        self.cm_change_proxy = create_proxy(changed)
        cm.on("change", self.cm_change_proxy)
        self.position_codemirror()

    def install_typing_aids(self) -> None:
        import js  # ty: ignore[unresolved-import]  # noqa: PLC0415

        assert self.cm is not None

        js.eval(r"""
window.CASSimTypingAids = function(editor, change) {
  if (!editor.getOption("cassimTypingAids") || change.origin !== "+input") return;
  if (change.text.length !== 1 || change.text[0].length !== 1) return;
  const inserted = change.text[0];
  const end = change.from.ch + 1;
  const pos = CodeMirror.Pos(change.from.line, change.from.ch);
  const token = editor.getTokenAt(pos);
  if (token && token.type && /string|comment/.test(token.type)) return;
  const line = editor.getLine(change.from.line).slice(0, end);
  const operators = {"-": ["<", "←"], "=": ["<", "≤"]};
  if (inserted in operators) {
    const pair = operators[inserted];
    if (line.endsWith(pair[0] + inserted)) {
      editor.replaceRange(pair[1], CodeMirror.Pos(change.from.line, end - 2),
                          CodeMirror.Pos(change.from.line, end), "+typingAid");
      return;
    }
  }
  const extra = {">=": "≥", "!=": "≠"};
  const operator = line.slice(-2);
  if (operator in extra) {
    editor.replaceRange(extra[operator], CodeMirror.Pos(change.from.line, end - 2),
                        CodeMirror.Pos(change.from.line, end), "+typingAid");
    return;
  }
  const aliases = {"@e": "ⅇ", "@pi": "π"};
  const name = line.endsWith("@pi") ? "@pi" : line.endsWith("@e") ? "@e" : null;
  if (name) {
    const start = end - name.length;
    editor.replaceRange(aliases[name], CodeMirror.Pos(change.from.line, start),
                        CodeMirror.Pos(change.from.line, end), "+typingAid");
  }
};
""")
        self.cm.on("change", js.window.CASSimTypingAids)

    def position_codemirror(self) -> None:
        if self.cm is None:
            return
        import js  # ty: ignore[unresolved-import]  # noqa: PLC0415

        host = js.document.getElementById("cassim-codemirror")
        if not host:
            return
        width = self.page.width or 1000
        editor_height = 0 if self.editor_pane.collapsed else self.editor_pane.height - 58
        host.style.display = "none" if self.editor_pane.collapsed else "block"
        host.style.top = "58px"
        host.style.left = "16px"
        if width < MOBILE_BREAKPOINT:
            host.style.width = f"{max(1, width - 32)}px"
        else:
            host.style.width = f"{max(1, (width - 28) * self.column_split - 20)}px"
        host.style.height = f"{max(120, editor_height)}px"
        if self.cm is not None:
            self.cm.refresh()

    def arrange(self) -> None:
        width = getattr(self.page, "width", 1000) or 1000
        left = ft.Column(
            [self.editor_pane.container, self.console_pane.container],
            expand=width >= MOBILE_BREAKPOINT,
            spacing=8,
        )
        right = ft.Column(
            [
                self.trace_controls,
                self.items_pane.container,
                self.trace_pane.container,
            ],
            expand=width >= MOBILE_BREAKPOINT,
            spacing=8,
        )
        if width < MOBILE_BREAKPOINT:
            body = ft.Column([left, right], scroll=ft.ScrollMode.AUTO, expand=True, spacing=8)
        else:
            available = max(640, width - 28)
            self.left_host = ft.Container(
                left,
                width=available * self.column_split,
                expand=False,
            )
            divider = ft.GestureDetector(
                ft.Container(
                    ft.Icon(ft.Icons.DRAG_INDICATOR, size=14),
                    width=12,
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                    tooltip="Resize columns",
                ),
                mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
                on_horizontal_drag_update=self.resize_columns,
                drag_interval=25,
            )
            body = ft.Row(
                [
                    self.left_host,
                    divider,
                    ft.Container(right, expand=True),
                ],
                expand=True,
                spacing=4,
                tight=True,
            )
        self.root.controls = [self.toolbar, body]
        self.root.expand = True
        if hasattr(self.page, "update"):
            self.page.update()
            self.position_codemirror()

    def on_resize(self, _: ft.PageResizeEvent) -> None:
        self.arrange()

    def resize_columns(self, event: ft.DragUpdateEvent) -> None:
        if event.global_delta is None or self.left_host is None:
            return
        width = max(640, (getattr(self.page, "width", 1000) or 1000) - 28)
        self.column_split = min(
            0.72,
            max(0.28, self.column_split + event.global_delta.x / width),
        )
        self.left_host.width = width * self.column_split
        _safe_update(self.left_host)
        self.position_codemirror()

    def on_keyboard(self, event: ft.KeyboardEvent) -> None:
        if (
            self.cm is None
            and (event.ctrl or event.meta)
            and event.key.lower() == "z"
            and self.typing_undo
        ):
            converted, original = self.typing_undo
            if self.source() == converted:
                self.fallback_editor.value = original
                self.fallback_editor.update()
                self.current_source = original
                self.typing_undo = None
                self.mark_dirty()
                return
        if event.key == "ArrowLeft":
            self.step_back(None)
        elif event.key == "ArrowRight":
            self.step_forward(None)
        elif event.key == "Home":
            self.to_start(None)
        elif event.key == "End":
            self.to_end(None)

    def cycle_number(self, _: ft.Event[ft.Button]) -> None:
        modes = ("approx", "auto", "exact")
        index = modes.index(self.number_mode)
        self.number_mode = modes[(index + 1) % len(modes)]
        self.number_button.content = self.number_mode.title()
        _safe_update(self.number_button)

    def toggle_angle(self, _: ft.Event[ft.Button]) -> None:
        self.angle_mode = "degree" if self.angle_mode == "radian" else "radian"
        self.angle_button.content = self.angle_mode.title()
        _safe_update(self.angle_button)

    def toggle_typing_aids(self, event: ft.Event[ft.Switch]) -> None:
        enabled = bool(event.control.value)
        self.typing_aids = enabled
        self.typing_aid = enabled
        self.update_typing_aids()
        self.save_editor_settings()

    def update_typing_aids(self) -> None:
        available = self.language == "pseudocode" and self.symbol_style == "unicode"
        self.typing_aids_switch.disabled = not available
        self.typing_aids_switch.value = self.typing_aids
        if not available:
            self.typing_undo = None
        if hasattr(self.page, "update"):
            self.typing_aids_switch.update()
        if self.cm is not None:
            self.cm.setOption("cassimTypingAids", self.typing_aids and available)

    async def run_code(self, _: ft.Event[ft.Button]) -> None:
        source = self.source()
        try:
            trace_source = (
                python_to_pseudocode(self.python_translation_source())
                if self.language == "python"
                else source
            )
        except (SyntaxError, TranslationError) as error:
            self.shell.notice("Cannot trace Python", str(error))
            return
        self.running = True
        self.cancelled = False
        self.console_inputs = []
        self.run_button.disabled = True
        self.stop_button.visible = True
        self.status.value = "Running..."
        _safe_update(self.status)
        await asyncio.sleep(0)
        result = run(
            trace_source,
            self.settings(),
            trace=True,
            cancelled=lambda: self.cancelled,
        )
        self.running = False
        self.run_button.disabled = False
        self.stop_button.visible = False
        self.run_button.content = "Run"
        self.dirty = False
        self.current_source = self.source()
        self.trace_source = trace_source
        self.result = result
        self.choices = trace.vertical_choices(result, self.settings())
        constants = set(self.constant_names())
        self.selection = trace.VerticalSelection(
            tuple(name for name in self.choices.variables if name not in constants),
            self.condition_selection_values(),
        )
        self.cursor = 0
        self.console.value = "\n".join(result.output)
        if result.error:
            self.console.value = "\n".join(
                part for part in (self.console.value, f"Error: {result.error}") if part
            )
        self.build_variables()
        self.update_trace()
        _safe_update(self.run_button)
        _safe_update(self.stop_button)
        _safe_update(self.console)
        self.scroll_console_end()
        if result.output or result.error:
            self.console_pane.set_collapsed(False)
            _safe_update(self.console_pane.container)
            self.position_codemirror()

    def stop_code(self, _: ft.Event[ft.Button]) -> None:
        self.cancelled = True

    def to_start(self, _: ft.Event[ft.Button] | None) -> None:
        self.cursor = 0
        self.update_trace()

    def to_end(self, _: ft.Event[ft.Button] | None) -> None:
        if self.result is not None:
            self.cursor = len([step for step in self.result.steps if step.kind != "halt"])
        self.update_trace()

    def step_back(self, _: ft.Event[ft.Button] | None) -> None:
        self.cursor = max(0, self.cursor - 1)
        self.update_trace()

    def step_forward(self, _: ft.Event[ft.Button] | None) -> None:
        if self.result is not None:
            shown = len([step for step in self.result.steps if step.kind != "halt"])
            self.cursor = min(shown, self.cursor + 1)
        self.update_trace()

    def variable_toggle(self, name: str) -> Callable[[ft.Event[ft.Checkbox]], None]:
        def toggle(event: ft.Event[ft.Checkbox]) -> None:
            values = set(self.selection.variables)
            if bool(event.control.value):
                values.add(name)
            else:
                values.discard(name)
            self.selection = trace.VerticalSelection(
                tuple(value for value in self.choices.variables if value in values),
                self.selection.conditions,
            )
            self.update_trace()

        return toggle

    def condition_toggle(self, label: str) -> Callable[[ft.Event[ft.Checkbox]], None]:
        def toggle(event: ft.Event[ft.Checkbox]) -> None:
            values = set(self.selection.conditions)
            if bool(event.control.value):
                values.add(label)
            else:
                values.discard(label)
            labels = self.condition_labels()
            selected = set()
            for item in labels:
                if item in values:
                    selected.add(item)
                    selected_line = item.partition(":")[0].strip()
                    if selected_line.isdigit():
                        selected.update(
                            step.cond[0]
                            for step in (self.result.steps if self.result is not None else [])
                            if step.line == int(selected_line) and step.cond is not None
                        )
            self.selection = trace.VerticalSelection(
                self.selection.variables,
                tuple(selected),
            )
            self.update_trace()

        return toggle

    def function_toggle(self, name: str) -> Callable[[ft.Event[ft.Checkbox]], None]:
        labels = tuple(label for label in self.condition_labels() if f"{name}(" in label)

        def toggle(event: ft.Event[ft.Checkbox]) -> None:
            selected_labels = set(
                label for label in self.condition_labels() if label in self.selection.conditions
            )
            if bool(event.control.value):
                selected_labels.update(labels)
            else:
                selected_labels.difference_update(labels)
            self.selection = trace.VerticalSelection(
                self.selection.variables,
                self.condition_values_for(selected_labels),
            )
            self.update_trace()

        return toggle

    def constant_names(self) -> tuple[str, ...]:
        if self.result is None:
            return ()
        counts: dict[str, int] = {}
        for step in self.result.steps:
            for change in step.changes:
                counts[change.name] = counts.get(change.name, 0) + 1
        return tuple(name for name in self.choices.variables if counts.get(name) == 1)

    def function_names(self) -> tuple[str, ...]:
        if self.result is None:
            return ()
        found: dict[str, None] = {}
        for step in self.result.steps:
            if step.function:
                found.setdefault(step.function, None)
        return tuple(found)

    def constant_value(self, name: str) -> str:
        if self.result is None:
            return ""
        for step in self.result.steps:
            for change in step.changes:
                if change.name == name:
                    return arith.format_value(change.new, self.settings(), minus=arith.MINUS)
        return ""

    @staticmethod
    def symbol_section(label: str, controls: list[ft.Control]) -> ft.Column:
        return ft.Column(
            [
                ft.Text(label, weight=ft.FontWeight.BOLD, size=13),
                *controls,
            ],
            spacing=3,
            tight=True,
        )

    def resize_symbol_columns(
        self,
        divider: int,
        event: ft.DragUpdateEvent,
    ) -> None:
        if event.global_delta is None or len(self.symbol_columns) != SYMBOL_COLUMN_COUNT:
            return
        left = divider
        right = divider + 1
        total = self.symbol_widths[left] + self.symbol_widths[right]
        left_width = min(
            total - 90,
            max(90, self.symbol_widths[left] + event.global_delta.x),
        )
        self.symbol_widths[left] = left_width
        self.symbol_widths[right] = total - left_width
        for control, width in zip(self.symbol_columns, self.symbol_widths, strict=True):
            control.width = width
            _safe_update(control)

    def symbol_divider(self, index: int) -> ft.GestureDetector:
        def resize(event: ft.DragUpdateEvent) -> None:
            self.resize_symbol_columns(index, event)

        return ft.GestureDetector(
            ft.Container(
                ft.Icon(ft.Icons.DRAG_INDICATOR, size=12),
                width=14,
                expand=True,
                tooltip=f"Resize Symbols column {index + 1}",
                alignment=ft.Alignment.CENTER,
            ),
            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
            on_horizontal_drag_update=resize,
            drag_interval=25,
        )

    def build_variables(self) -> None:
        constants = set(self.constant_names())
        variables = tuple(name for name in self.choices.variables if name not in constants)
        functions = self.function_names()
        labels = self.condition_labels()
        variable_controls: list[ft.Control] = [
            ft.Checkbox(
                label=name,
                value=name in self.selection.variables,
                on_change=self.variable_toggle(name),
            )
            for name in variables
        ]
        constant_controls: list[ft.Control] = [
            ft.Checkbox(
                label=f"{name} = {self.constant_value(name)}",
                value=name in self.selection.variables,
                on_change=self.variable_toggle(name),
            )
            for name in self.choices.variables
            if name in constants
        ]
        function_controls: list[ft.Control] = [
            *(
                ft.Checkbox(
                    label=name,
                    value=any(
                        f"{name}(" in label and label in self.selection.conditions
                        for label in labels
                    ),
                    on_change=self.function_toggle(name),
                )
                for name in functions
            ),
            *(
                ft.Checkbox(
                    label=label,
                    value=label in self.selection.conditions,
                    on_change=self.condition_toggle(label),
                )
                for label in labels
            ),
        ]
        for controls in (variable_controls, constant_controls, function_controls):
            if not controls:
                controls.append(ft.Text("None", size=12))
        sections = [
            self.symbol_section("Variables", variable_controls),
            self.symbol_section("Constants", constant_controls),
            self.symbol_section("Functions", function_controls),
        ]
        self.symbol_columns = [
            ft.Container(section, width=width, alignment=ft.Alignment.TOP_LEFT)
            for section, width in zip(sections, self.symbol_widths, strict=True)
        ]
        self.trace_items.controls = [
            ft.Row(
                [
                    self.symbol_columns[0],
                    self.symbol_divider(0),
                    self.symbol_columns[1],
                    self.symbol_divider(1),
                    self.symbol_columns[2],
                ],
                spacing=2,
                tight=True,
                scroll=ft.ScrollMode.AUTO,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
        ]
        if hasattr(self.page, "update"):
            _safe_update(self.trace_items)

    def condition_labels(self) -> tuple[str, ...]:
        """Each executed boolean expression once, labelled by source line."""
        if self.result is None:
            return ()
        source_lines = self.trace_source.splitlines()
        found: dict[tuple[int, str], None] = {}
        for step in self.result.steps:
            if step.cond is None:
                continue
            line = step.line
            if not 1 <= line <= len(source_lines):
                continue
            source = source_lines[line - 1].strip()
            expression = source
            for prefix in ("while ", "if ", "repeat until ", "until "):
                if source.lower().startswith(prefix):
                    expression = (
                        source[len(prefix) :].strip().removesuffix(" do").removesuffix(" then")
                    )
                    break
            found.setdefault((line, expression), None)
        return tuple(f"{line}: {expression}" for line, expression in found)

    def condition_selection_values(self) -> tuple[str, ...]:
        """Labels plus runtime condition text, so the trace view can filter by source line."""
        return self.condition_values_for(self.condition_labels())

    def condition_values_for(self, labels: tuple[str, ...] | set[str]) -> tuple[str, ...]:
        values: set[str] = set(labels)
        if self.result is not None:
            for label in labels:
                line_text = label.partition(":")[0].strip()
                if line_text.isdigit():
                    line = int(line_text)
                    values.update(
                        step.cond[0]
                        for step in self.result.steps
                        if step.line == line and step.cond is not None
                    )
        return tuple(values)

    def _trace_header(
        self,
        key: str,
        title: str,
        width: float,
    ) -> ft.Container:
        if key == "__line__":
            return ft.Container(
                ft.Text(
                    title,
                    weight=ft.FontWeight.BOLD,
                    size=12,
                    no_wrap=True,
                    text_align=ft.TextAlign.CENTER,
                ),
                width=LINE_COLUMN_WIDTH,
                height=38,
                padding=0,
                border=ft.Border.all(1),
                alignment=ft.Alignment.CENTER,
            )

        def resize(event: ft.DragUpdateEvent) -> None:
            self.resize_trace_column(key, event)

        grip = ft.GestureDetector(
            ft.Icon(ft.Icons.DRAG_INDICATOR, size=12),
            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
            on_horizontal_drag_update=resize,
            drag_interval=25,
            tooltip=f"Resize {title} column",
        )
        return ft.Container(
            ft.Row(
                [ft.Text(title, weight=ft.FontWeight.BOLD, size=12, expand=True), grip],
                tight=True,
                spacing=2,
            ),
            width=width,
            height=38,
            padding=ft.Padding.symmetric(horizontal=6),
            border=ft.Border.all(1),
            alignment=ft.Alignment.CENTER_LEFT,
        )

    def resize_trace_column(self, key: str, event: ft.DragUpdateEvent) -> None:
        if key == "__line__" or event.global_delta is None:
            return
        current = self.trace_widths.get(key, VARIABLE_COLUMN_WIDTH)
        self.trace_widths[key] = min(420, max(48, current + event.global_delta.x))
        for control in self.trace_resize_controls.get(key, []):
            control.width = self.trace_widths[key]
            _safe_update(control)
        if self.trace_table_container is not None:
            self.trace_table_container.width = sum(
                self.trace_widths[column] for column in self.trace_active_columns
            )
            _safe_update(self.trace_table_container)

    def _trace_cell(self, key: str, value: str, *, header: bool = False) -> ft.Container:
        return ft.Container(
            ft.Text(
                value,
                size=12,
                weight=ft.FontWeight.BOLD if header else None,
                selectable=not header,
                no_wrap=key == "__line__",
            ),
            width=self.trace_widths.get(key, VARIABLE_COLUMN_WIDTH),
            height=38,
            padding=ft.Padding.symmetric(horizontal=6, vertical=4),
            border=ft.Border.all(1),
            alignment=ft.Alignment.CENTER_LEFT,
        )

    def draw_trace_table(
        self,
        columns: list[tuple[str, str, float]],
        rows: list[list[str]],
    ) -> None:
        for key, _, default in columns:
            self.trace_widths.setdefault(key, default)
        self.trace_active_columns = [key for key, _, _ in columns]
        self.trace_resize_controls = {key: [] for key in self.trace_active_columns}
        header_containers = [
            self._trace_header(key, title, self.trace_widths[key]) for key, title, _ in columns
        ]
        for (key, _, _), control in zip(columns, header_containers, strict=True):
            self.trace_resize_controls[key].append(control)
        header_controls: list[ft.Control] = list(header_containers)
        header = ft.Row(
            header_controls,
            spacing=0,
            tight=True,
        )
        body_rows: list[ft.Control] = []
        for row in rows:
            row_containers = [
                self._trace_cell(key, value)
                for (key, _, _), value in zip(columns, row, strict=True)
            ]
            for (key, _, _), control in zip(columns, row_containers, strict=True):
                self.trace_resize_controls[key].append(control)
            row_controls: list[ft.Control] = list(row_containers)
            body_rows.append(
                ft.Row(
                    row_controls,
                    spacing=0,
                    tight=True,
                    height=38,
                )
            )
        body = ft.Column(
            body_rows,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=0,
        )
        total_width = sum(self.trace_widths[key] for key, _, _ in columns)
        table = ft.Container(
            ft.Column([header, body], spacing=0, expand=True),
            width=total_width,
            expand=True,
        )
        self.trace_table_container = table
        self.trace.controls = [ft.Row([table], scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)]
        _safe_update(self.trace)

    def condition_name(self, line: int) -> str:
        source_lines = self.trace_source.splitlines()
        if not 1 <= line <= len(source_lines):
            return ""
        source = source_lines[line - 1].strip()
        for prefix in ("while ", "if ", "repeat until ", "until "):
            if source.lower().startswith(prefix):
                return source[len(prefix) :].strip().removesuffix(" do").removesuffix(" then")
        return source

    def update_vertical_trace(
        self,
    ) -> tuple[trace.VerticalTable, list[tuple[str, str, float]], list[list[str]]]:
        columns: list[tuple[str, str, float]] = [("__line__", "Line", LINE_COLUMN_WIDTH)]
        rows: list[list[str]] = []
        if self.result is None:
            return trace.VerticalTable([]), columns, rows
        table = trace.selected_vertical(
            self.result,
            self.settings(),
            self.selection,
            cursor=self.cursor,
        )

        condition_names = list(
            dict.fromkeys(
                name
                for step in self.result.steps
                if step.cond is not None
                for name in (self.condition_name(step.line),)
                if name and f"{step.line}: {name}" in self.selection.conditions
            )
        )
        variable_names = [
            name for name in self.choices.variables if name in self.selection.variables
        ]
        columns.extend((f"variable:{name}", name, VARIABLE_COLUMN_WIDTH) for name in variable_names)
        columns.extend(
            (f"condition:{name}", name, CONDITION_COLUMN_WIDTH) for name in condition_names
        )
        columns.append(("__output__", "Calcs / Output", OUTPUT_COLUMN_WIDTH))
        for row in table.rows:
            step_output = (
                self.result.steps[row.step].output if row.step < len(self.result.steps) else None
            )
            rows.append(
                [
                    str(row.line),
                    *(row.cells.get(name, "") for name in variable_names),
                    *(
                        next(iter(row.conditions.values()), "")
                        if self.condition_name(row.line) == name
                        else ""
                        for name in condition_names
                    ),
                    row.calc or step_output or "",
                ]
            )
        return table, columns, rows

    def update_horizontal_trace(self) -> list[list[str]] | None:
        if self.result is None:
            self.draw_trace_table(
                [("__code__", "Code", VARIABLE_COLUMN_WIDTH)],
                [],
            )
            return []
        table = trace.horizontal(
            self.result,
            parse(self.trace_source),
            self.settings(),
            cursor=self.cursor,
        )
        if table is None:
            return None
        columns: list[tuple[str, str, float]] = [
            ("__code__", "Code", 220),
            *((f"pass:{column}", column, VARIABLE_COLUMN_WIDTH) for column in table.columns),
        ]
        self.draw_trace_table(
            columns,
            [[row.code, *row.cells] for row in table.rows],
        )
        return [[row.code, *row.cells] for row in table.rows]

    def update_trace(self) -> None:
        if self.trace_mode == "none":
            self.trace.controls = []
            _safe_update(self.trace)
            return
        if self.trace_mode == "horizontal":
            if self.update_horizontal_trace() is not None:
                vertical = None
                rows: list[object] = []
            else:
                self.shell.notice(
                    "Horizontal trace unavailable",
                    "This run does not have exactly one non-nested loop.",
                )
                self.trace_mode = "vertical"
                self.trace_layout.content = "Trace: Vertical"
                _safe_update(self.trace_layout)
                vertical, columns, rows = self.update_vertical_trace()
                self.draw_trace_table(columns, rows)
        else:
            vertical, columns, rows = self.update_vertical_trace()
            self.draw_trace_table(columns, rows)
        shown = (
            len([step for step in self.result.steps if step.kind != "halt"])
            if self.result is not None
            else 0
        )
        self.status.value = f"{self.cursor} / {shown} steps"
        _safe_update(self.status)
        if self.cm is not None and vertical is not None and vertical.rows:
            line = vertical.rows[-1].line
            import js  # ty: ignore[unresolved-import]  # noqa: PLC0415
            from pyodide.ffi import to_js  # ty: ignore[unresolved-import]  # noqa: PLC0415

            self.cm.setCursor(
                to_js(
                    {"line": line - 1},
                    dict_converter=js.Object.fromEntries,
                )
            )

    def home(self, _: ft.Event[ft.MenuItemButton]) -> None:
        home = getattr(self.shell, "home", None)
        if home is not None:
            home()

    def open_settings(self, _: ft.Event[ft.MenuItemButton]) -> None:
        def switch_changed(event: ft.Event[ft.Switch]) -> None:
            event.control.value = bool(event.control.value)
            _safe_update(event.control)

        number = ft.SegmentedButton(
            selected=[self.number_mode],
            segments=[
                ft.Segment(value="approx", label="Approx"),
                ft.Segment(value="auto", label="Auto"),
                ft.Segment(value="exact", label="Exact"),
            ],
        )
        angle = ft.SegmentedButton(
            selected=[self.angle_mode],
            segments=[
                ft.Segment(value="radian", label="Radian"),
                ft.Segment(value="degree", label="Degree"),
            ],
        )
        line_numbers = ft.Switch(
            label="Line numbers",
            value=self.line_numbers_visible,
            tooltip="Show source line numbers in the Code pane.",
            on_change=switch_changed,
        )
        typing_aid = ft.Switch(
            label="Typing aid",
            value=self.typing_aid,
            on_change=switch_changed,
            tooltip=(
                "Convert unambiguous spellings such as <-, <= and \\theta while typing. "
                "Plain names such as pi are never changed."
            ),
        )
        code_style = ft.Dropdown(
            label="Code style",
            value=self.code_style,
            options=[
                ft.DropdownOption(key="monospace", text="Monospace"),
                ft.DropdownOption(key="formatted", text="Formatted (linear)"),
            ],
        )
        symbol_style = ft.Dropdown(
            label="Symbols",
            value=self.symbol_style,
            options=[
                ft.DropdownOption(key="unicode", text="Unicode symbols"),
                ft.DropdownOption(key="ascii", text="Plain ASCII"),
            ],
        )

        def save(_: ft.Event[ft.TextButton]) -> None:
            self.number_mode = cast(NumberMode, number.selected[0])
            self.angle_mode = cast(AngleMode, angle.selected[0])
            self.line_numbers_visible = bool(line_numbers.value)
            self.typing_aid = bool(typing_aid.value)
            self.typing_aids = self.typing_aid
            self.code_style = str(code_style.value or "monospace")
            new_symbol_style = str(symbol_style.value or "unicode")
            if new_symbol_style != self.symbol_style:
                old_source = self.source()
                self.symbol_style = new_symbol_style
                new_source = convert_symbols(old_source, new_symbol_style)
                if new_source != old_source:
                    self.set_source(new_source)
                    self.typing_undo = (new_source, old_source)
            self.symbol_style = new_symbol_style
            self.number_button.content = self.number_mode.title()
            self.angle_button.content = self.angle_mode.title()
            _safe_update(self.number_button)
            _safe_update(self.angle_button)
            if self.cm is not None:
                self.cm.setOption("lineNumbers", self.line_numbers_visible)
                self.cm.refresh()
            else:
                self.line_number_gutter.visible = self.line_numbers_visible
                _safe_update(self.line_number_gutter)
            self.apply_code_style()
            _safe_update(self.fallback_editor)
            self.update_typing_aids()
            self.save_editor_settings()
            self.page.pop_dialog()

        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Settings"),
                content=ft.Column(
                    [
                        ft.Text("Number mode"),
                        number,
                        ft.Text("Angle"),
                        angle,
                        code_style,
                        symbol_style,
                        ft.Divider(),
                        line_numbers,
                        typing_aid,
                        ft.Text(
                            "Typing aid converts unambiguous symbols while you type. "
                            "Plain names such as pi are never changed.",
                            size=12,
                        ),
                        ft.Text(
                            "Formatted keeps linear source; it uses a proportional display face.",
                            size=12,
                        ),
                    ],
                    tight=True,
                    spacing=8,
                ),
                actions=[
                    ft.TextButton("Save", on_click=save),
                    ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog()),
                ],
            )
        )

    def open_appearance(self, _: ft.Event[ft.MenuItemButton]) -> None:
        choice = ft.SegmentedButton(
            selected=[self.theme_name],
            segments=[ft.Segment(value=name, label=name) for name in THEMES],
        )

        def save(_: ft.Event[ft.TextButton]) -> None:
            selected = choice.selected[0] if choice.selected else self.theme_name
            if selected in THEMES:
                self.apply_theme(selected)
            self.page.pop_dialog()

        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Appearance"),
                content=choice,
                actions=[
                    ft.TextButton("Apply", on_click=save),
                    ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog()),
                ],
            )
        )

    def activate_update(self, _: ft.Event[ft.MenuItemButton]) -> None:
        self.shell.activate_update()

    def open_help(self, _: ft.Event[ft.MenuItemButton]) -> None:
        self.shell.help()

    def open_about(self, _: ft.Event[ft.MenuItemButton]) -> None:
        self.shell.about()


def mount(shell: Shell) -> CodeApp:
    return CodeApp(shell)
