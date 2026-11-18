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
from cassim.runtime.pseudocode import Settings, arith, run, trace
from cassim.runtime.pseudocode.settings import AngleMode, NumberMode

if TYPE_CHECKING:
    from cassim.app.shell import Shell


EXAMPLE = "x ← 1\nwhile x <= 3\n  x ← x + 1\nend while\nprint x"
BISECTION = (
    "define f(x)\n"
    "  return x*x - 2\n"
    "end\n"
    "a ← -2\n"
    "b ← -1\n"
    "while (b-a)/2 > 0.2\n"
    "  c ← (a+b)/2\n"
    "  if f(a)*f(c) < 0 then\n"
    "    b ← c\n"
    "  else\n"
    "    a ← c\n"
    "  end if\n"
    "end while\n"
    "print c"
)
MOBILE_BREAKPOINT = 700
LINE_COLUMN_WIDTH = 48
VARIABLE_COLUMN_WIDTH = 76
CONDITION_COLUMN_WIDTH = 130
OUTPUT_COLUMN_WIDTH = 140
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


class CodeApp:
    def __init__(self, shell: Shell) -> None:
        self.shell = shell
        self.page = shell.page
        self.result = None
        self.cursor = 0
        self.selection = trace.VerticalSelection()
        self.choices = trace.VerticalSelection()
        self.cancelled = False
        self.running = False
        self.dirty = False
        self.current_source = EXAMPLE
        self.console_visible = False
        self.line_numbers_visible = True
        self.console_inputs: list[str] = []
        self.editor_collapsed = False
        self.editor_share = 0.48
        self.python_console_namespace: dict[str, object] = {"__name__": "cassim_console"}
        self.language = "pseudocode"
        self.number_mode: NumberMode = "approx"
        self.angle_mode: AngleMode = "radian"
        self.theme_name = "Dark"
        self.typing_aids = False
        self.code_style = "monospace"
        self.symbol_style = "unicode"
        self.typing_undo: tuple[str, str] | None = None
        self.cm = None
        self.cm_change_proxy = None

        self.fallback_editor = ft.TextField(
            label="Code",
            value=EXAMPLE,
            multiline=True,
            min_lines=12,
            expand=True,
            autocorrect=False,
            enable_suggestions=False,
            text_style=self.editor_text_style(),
            on_change=self.on_fallback_source,
        )

        self.number_button = ft.Button("Number: Approx", on_click=self.cycle_number)
        self.angle_button = ft.Button("Angle: Radian", on_click=self.toggle_angle)
        self.console_toggle = ft.Switch(
            label="Console",
            value=False,
            on_change=self.toggle_console,
        )
        self.typing_aids_switch = ft.Switch(
            label="Typing aids",
            value=False,
            on_change=self.toggle_typing_aids,
        )
        self.cassim_menu = ft.SubmenuButton(
            content="CASSim",
            controls=[
                ft.MenuItemButton(content="Home", on_click=self.home),
                ft.MenuItemButton(content="Settings…", on_click=self.open_settings),
                ft.MenuItemButton(content="Appearance…", on_click=self.open_appearance),
                ft.MenuItemButton(content="Check for Updates…", on_click=self.check_updates),
                ft.MenuItemButton(content="Help (wiki)…", on_click=self.open_help),
                ft.MenuItemButton(content="About CASSim…", on_click=self.open_about),
            ],
        )
        examples = ft.SubmenuButton(
            content="Examples",
            controls=[
                ft.MenuItemButton(
                    content="Linear",
                    on_click=lambda _: self.load_example("x ← 1\nprint x"),
                ),
                ft.MenuItemButton(
                    content="Loop",
                    on_click=lambda _: self.load_example(
                        "x ← 1\nwhile x <= 3\n  x ← x + 1\nend while\nprint x"
                    ),
                ),
                ft.MenuItemButton(
                    content="Bisection",
                    on_click=lambda _: self.load_example(BISECTION),
                ),
            ],
        )
        self.doc_menu = ft.SubmenuButton(
            content="Doc",
            controls=[
                ft.MenuItemButton(content="Open…", on_click=self.open_file),
                ft.MenuItemButton(content="Save", on_click=self.save_file),
                ft.MenuItemButton(content="Save as…", on_click=self.save_file_as),
                examples,
            ],
        )
        self.app_menu = ft.MenuBar(controls=[self.cassim_menu, self.doc_menu])
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
        self.line_numbers_toggle = ft.Switch(
            label="Line numbers",
            value=True,
            on_change=self.toggle_line_numbers,
        )

        self.run_button = ft.Button("Run", on_click=self.run_code)
        self.step_button = ft.Button("Step", on_click=self.step_forward)
        self.start_button = ft.Button("Start", on_click=self.to_start)
        self.end_button = ft.Button("End", on_click=self.to_end)
        self.vertical_button = ft.Button("Vertical", disabled=True)
        self.trace_layout = ft.PopupMenuButton(
            content="Trace: Vertical",
            items=[
                ft.PopupMenuItem(
                    content="None", on_click=lambda _: self.change_trace_layout("none")
                ),
                ft.PopupMenuItem(
                    content="Vertical",
                    on_click=lambda _: self.change_trace_layout("vertical"),
                ),
                ft.PopupMenuItem(
                    content="Horizontal",
                    on_click=lambda _: self.change_trace_layout("horizontal"),
                ),
            ],
            style=_control_style(),
        )
        self.variables_button = ft.PopupMenuButton(
            content="Variables",
            items=[ft.PopupMenuItem(content="Run to discover items")],
            style=_control_style(),
        )

        self.console = ft.Text(
            "",
            selectable=True,
            font_family=CODE_FONT,
            font_family_fallback=[MATH_FONT, SYMBOL_FONT],
        )
        self.console_input = ft.TextField(
            hint_text="Input or expression",
            dense=True,
            on_submit=self.submit_console,
        )
        self.console_box = ft.Container(
            ft.Column(
                [
                    ft.Text("Console", weight=ft.FontWeight.BOLD),
                    ft.Container(self.console, expand=True),
                    self.console_input,
                ],
                expand=True,
            ),
            border=ft.Border.all(1),
            padding=8,
            expand=True,
            visible=False,
        )
        self.trace = ft.Column(expand=True)
        self.status = ft.Text("")
        self.line_numbers_toggle = ft.Switch(
            label="Line numbers",
            value=True,
            on_change=self.toggle_line_numbers,
        )
        self.editor_toggle = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT,
            tooltip="Collapse code editor",
            on_click=self.toggle_editor,
        )
        self.constants_panel = ft.ExpansionTile(
            title="Values and functions",
            controls=[ft.Text("Run a program to discover values and functions.")],
            maintain_state=True,
            dense=True,
        )

        self.editor_pane = ft.Container(
            ft.Column(
                [
                    ft.Row(
                        [
                            self.line_numbers_toggle,
                            self.language_switch,
                            self.editor_toggle,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self.fallback_editor,
                ],
                expand=True,
            ),
            expand=True,
            padding=8,
            border=ft.Border.all(1),
        )
        self.trace_controls = ft.Row(
            [
                self.run_button,
                self.step_button,
                self.start_button,
                self.end_button,
            ],
            wrap=True,
            spacing=6,
        )
        self.trace_pane = ft.Container(
            ft.Column(
                [
                    self.constants_panel,
                    self.status,
                    self.trace,
                ],
                expand=True,
                spacing=8,
            ),
            expand=True,
            padding=8,
        )

        self.toolbar = ft.Row(
            [
                self.app_menu,
                self.number_button,
                self.angle_button,
                self.console_toggle,
                self.typing_aids_switch,
                self.trace_layout,
                self.variables_button,
            ],
            wrap=True,
            spacing=8,
        )
        self.root = ft.Column(expand=True)

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
        try:
            import js  # ty: ignore[unresolved-import]  # noqa: PLC0415
        except ImportError:
            return
        else:
            del js
            await self.start_codemirror()

    def editor_text_style(self) -> ft.TextStyle:
        family = CODE_FONT if self.code_style == "monospace" else "sans-serif"
        return ft.TextStyle(font_family=family, font_family_fallback=[MATH_FONT, SYMBOL_FONT])

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
        self.typing_aids_switch.value = self.typing_aids
        self.typing_aids_switch.disabled = (
            self.language != "pseudocode" or self.symbol_style == "ascii"
        )
        self.apply_code_style()
        if self.symbol_style == "ascii":
            self.current_source = convert_symbols(self.current_source, "ascii")
            self.fallback_editor.value = self.current_source

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
        self.page.controls.clear()

    def apply_theme(self, name: str) -> None:
        theme = THEMES[name]
        self.theme_name = name
        self.page.theme_mode = ft.ThemeMode.LIGHT if name == "Light" else ft.ThemeMode.DARK
        self.page.bgcolor = theme.background
        self.page.update()

    def settings(self) -> Settings:
        return Settings(number=self.number_mode, angle=self.angle_mode)

    def source(self) -> str:
        if self.cm is not None:
            return str(self.cm.getValue())
        return str(self.fallback_editor.value or "")

    def on_fallback_source(self, _: ft.Event[ft.TextField]) -> None:
        current = str(self.fallback_editor.value or "")
        if self.typing_aids and self.symbol_style == "unicode" and self.language == "pseudocode":
            converted = convert_typing(self.current_source, current)
            if converted != current:
                self.typing_undo = (converted, current)
                self.fallback_editor.value = converted
                self.fallback_editor.update()
                current = converted
            elif self.typing_undo and current != self.typing_undo[0]:
                self.typing_undo = None
        else:
            self.typing_undo = None
        self.current_source = current
        self.mark_dirty()

    def toggle_language(self, event: ft.Event[ft.SegmentedButton]) -> None:
        selected = event.control.selected
        self.language = selected[0] if selected else "pseudocode"
        if self.cm is not None:
            self.cm.setOption("mode", "pseudocode" if self.language == "pseudocode" else "python")
            self.cm.refresh()
        event.control.update()
        self.update_typing_aids()
        self.mark_dirty()

    def toggle_line_numbers(self, event: ft.Event[ft.Switch]) -> None:
        self.line_numbers_visible = bool(event.control.value)
        if self.cm is not None:
            self.cm.setOption("lineNumbers", self.line_numbers_visible)
            self.cm.refresh()

    def change_trace_layout(self, value: str) -> None:
        self.trace_layout.content = f"Trace: {value.title()}"
        if hasattr(self.page, "update"):
            self.trace_layout.update()
        if value == "none":
            self.trace.controls = []
            self.trace.update()
        elif value == "horizontal":
            self.shell.notice(
                "Horizontal trace",
                "The horizontal trace table is available after the vertical trace is complete.",
            )
            self.change_trace_layout("vertical")
            self.update_trace()
        else:
            self.update_trace()

    async def open_file(self, _: ft.Event[ft.MenuItemButton]) -> None:
        text = await self.shell.pick_file(("py", "txt", "pseudo"), "Open code")
        if text is not None:
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
        self.set_source(text)

    def set_source(self, text: str) -> None:
        if self.symbol_style == "ascii":
            text = convert_symbols(text, "ascii")
        if self.cm is not None:
            self.cm.setValue(text)
        self.fallback_editor.value = text
        if hasattr(self.page, "update"):
            self.fallback_editor.update()
        self.current_source = text
        self.result = None
        self.cursor = 0
        self.selection = trace.VerticalSelection()
        self.choices = trace.VerticalSelection()
        self.variables_button.items = [ft.PopupMenuItem(content="Run to discover items")]
        if hasattr(self.page, "update"):
            self.variables_button.update()
        self.status.value = ""
        if hasattr(self.page, "update"):
            self.status.update()
        self.update_trace()
        self.build_constants()
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
            self.console.value = f"{previous}\n> {text}\n{output}".strip()
            self.console.update()
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
            self.console.value = f"{previous}\n> {text}\n{output}".strip()
            self.console.update()
            self.choices = trace.vertical_choices(result, self.settings())
            self.selection = trace.VerticalSelection(
                tuple(
                    name
                    for name in self.choices.variables
                    if name not in getattr(result, "constants", ())
                ),
                self.condition_labels(),
            )
            self.build_variables()
            self.build_constants()
            self.update_trace()
        else:
            console_source = self.pseudocode_console_source(source, text)
            result = run(console_source, self.settings(), trace=True)
            output = "\n".join(result.output)
            if result.error:
                output = "\n".join(part for part in (output, f"Error: {result.error}") if part)
            self.console.value = f"{previous}\n> {text}\n{output}".strip()
            self.console.update()

    def pseudocode_console_source(self, source: str, text: str) -> str:
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

    def submit_python_console(self, text: str) -> str:
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
                expression = ast.Expression(parsed.body[0].value)
                value = eval(
                    compile(expression, "<console>", "eval"),
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

    def mark_dirty(self) -> None:
        if not self.dirty:
            self.dirty = True
            self.run_button.content = "Run *"
            if hasattr(self.page, "update"):
                self.run_button.update()

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
                    "mode": "pseudocode",
                    "theme": "dracula",
                    "lineNumbers": True,
                    "lineWrapping": True,
                    "indentUnit": 2,
                    "tabSize": 2,
                    "autofocus": False,
                    "cassimTypingAids": False,
                },
                dict_converter=js.Object.fromEntries,
            ),
        )
        self.cm = cm
        self.fallback_editor.visible = False
        self.apply_code_style()
        self.update_typing_aids()
        self.install_typing_aids()

        def changed(*_args: object) -> None:
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
  const macro = line;
  const aliases = {"@e": "ⅇ", "@pi": "π"};
  const name = macro.endsWith("@pi") ? "@pi" : macro.endsWith("@e") ? "@e" : null;
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
        height = self.page.height or 700
        if self.editor_collapsed:
            host.style.width = "0px"
            host.style.height = "0px"
            self.cm.refresh()
            return
        if width < MOBILE_BREAKPOINT:
            host.style.left = "8px"
            host.style.top = "150px"
            host.style.width = f"{max(1, width - 16)}px"
            host.style.height = "300px"
        else:
            host.style.left = "8px"
            host.style.top = "112px"
            host.style.width = f"{max(220, width * self.editor_share - 24)}px"
            console_reserve = 230 if self.console_visible else 0
            host.style.height = f"{max(220, height - 112 - console_reserve - 8)}px"
        self.cm.refresh()

    def arrange(self) -> None:
        width = getattr(self.page, "width", 1000) or 1000
        self.editor_pane.visible = not self.editor_collapsed
        if width < MOBILE_BREAKPOINT:
            left = [self.editor_pane]
            if self.console_visible:
                left.append(self.console_box)
            body = ft.Column([*left, self.trace_pane], expand=True, spacing=4)
        else:
            left = ft.Column(
                [self.editor_pane, self.console_box]
                if self.console_visible
                else [self.editor_pane],
                expand=True,
                spacing=4,
            )
            left_width = max(220, int(width * self.editor_share))
            if self.editor_collapsed:
                left_width = 0
                left.visible = False
            divider = ft.GestureDetector(
                ft.Container(
                    ft.Container(width=2, bgcolor=THEMES[self.theme_name].key_label, expand=True),
                    width=10,
                    bgcolor=ft.Colors.TRANSPARENT,
                    alignment=ft.Alignment.CENTER,
                    tooltip="Drag to resize code and trace",
                ),
                mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
                drag_interval=16,
                on_horizontal_drag_update=self.resize_editor,
                visible=not self.editor_collapsed,
            )
            body = ft.Row(
                [
                    ft.Container(left, width=left_width, expand=not self.editor_collapsed),
                    divider,
                    ft.Container(self.trace_pane, expand=True),
                ],
                expand=True,
                spacing=0,
            )
        self.root.controls = [self.toolbar, body]
        self.root.expand = True
        if hasattr(self.page, "update"):
            self.page.update()
            self.position_codemirror()

    def toggle_editor(self, _: ft.Event[ft.IconButton]) -> None:
        self.editor_collapsed = not self.editor_collapsed
        self.editor_toggle.icon = (
            ft.Icons.CHEVRON_RIGHT if self.editor_collapsed else ft.Icons.CHEVRON_LEFT
        )
        self.editor_toggle.tooltip = (
            "Expand code editor" if self.editor_collapsed else "Collapse code editor"
        )
        self.editor_toggle.update()
        self.arrange()

    def resize_editor(self, event: ft.DragUpdateEvent) -> None:
        width = self.page.width or 1000
        delta = event.global_delta.x if event.global_delta is not None else 0
        self.editor_share = min(0.75, max(0.25, self.editor_share + delta / width))
        self.arrange()

    def on_resize(self, _: ft.PageResizeEvent) -> None:
        self.arrange()

    def on_keyboard(self, event: ft.KeyboardEvent) -> None:
        if (event.ctrl or event.meta) and event.key.lower() == "z" and self.typing_undo:
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
        self.number_button.content = f"Number: {self.number_mode.title()}"
        self.number_button.update()

    def toggle_angle(self, _: ft.Event[ft.Button]) -> None:
        self.angle_mode = "degree" if self.angle_mode == "radian" else "radian"
        self.angle_button.content = f"Angle: {self.angle_mode.title()}"
        self.angle_button.update()

    def toggle_console(self, event: ft.Event[ft.Switch]) -> None:
        self.console_visible = bool(event.control.value)
        self.console_box.visible = self.console_visible
        if hasattr(self.page, "update"):
            self.page.update()
        self.arrange()

    def toggle_typing_aids(self, event: ft.Event[ft.Switch]) -> None:
        self.typing_aids = bool(event.control.value)
        self.update_typing_aids()
        self.save_editor_settings()

    def update_typing_aids(self) -> None:
        available = self.language == "pseudocode" and self.symbol_style == "unicode"
        self.typing_aids_switch.disabled = not available
        if not available:
            self.typing_undo = None
        if hasattr(self.page, "update"):
            self.typing_aids_switch.update()
        if self.cm is not None:
            self.cm.setOption("cassimTypingAids", self.typing_aids and available)

    async def run_code(self, _: ft.Event[ft.Button]) -> None:
        if self.language == "python":
            self.shell.notice(
                "Python",
                "Python execution is not included in this trace-table slice.",
            )
            return
        self.running = True
        self.cancelled = False
        self.console_inputs = []
        self.run_button.disabled = True
        self.status.value = "Running..."
        self.status.update()
        await asyncio.sleep(0)
        result = run(
            self.source(),
            self.settings(),
            trace=True,
            cancelled=lambda: self.cancelled,
        )
        self.running = False
        self.run_button.disabled = False
        self.run_button.content = "Run"
        self.dirty = False
        self.current_source = self.source()
        self.result = result
        self.choices = trace.vertical_choices(result, self.settings())
        self.selection = trace.VerticalSelection(
            tuple(
                name
                for name in self.choices.variables
                if name not in getattr(result, "constants", ())
            ),
            self.condition_labels(),
        )
        self.cursor = len([step for step in result.steps if step.kind != "halt"])
        self.console.value = "\n".join(result.output)
        if result.error:
            self.console.value = "\n".join(
                part for part in (self.console.value, f"Error: {result.error}") if part
            )
        self.build_variables()
        self.build_constants()
        self.update_trace()
        self.run_button.update()
        self.console.update()

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

    def variable_toggle(self, name: str) -> Callable[[ft.Event[ft.PopupMenuItem]], None]:
        def toggle(_: ft.Event[ft.PopupMenuItem]) -> None:
            values = set(self.selection.variables)
            if name in values:
                values.remove(name)
            else:
                values.add(name)
            self.selection = trace.VerticalSelection(
                tuple(value for value in self.choices.variables if value in values),
                self.selection.conditions,
            )
            self.build_variables()
            self.update_trace()

        return toggle

    def condition_toggle(self, label: str) -> Callable[[ft.Event[ft.PopupMenuItem]], None]:
        def toggle(_: ft.Event[ft.PopupMenuItem]) -> None:
            values = set(self.selection.conditions)
            if label in values:
                values.remove(label)
            else:
                values.add(label)
            labels = self.condition_labels()
            self.selection = trace.VerticalSelection(
                self.selection.variables,
                tuple(value for value in labels if value in values),
            )
            self.build_variables()
            self.update_trace()

        return toggle

    def build_variables(self) -> None:
        items: list[ft.PopupMenuItem] = []
        if self.choices.variables:
            items.append(ft.PopupMenuItem(content="Variables", checked=False))
            items.extend(
                ft.PopupMenuItem(
                    content=name,
                    checked=name in self.selection.variables,
                    on_click=self.variable_toggle(name),
                )
                for name in self.choices.variables
            )
        if self.choices.conditions:
            items.append(ft.PopupMenuItem(content="Decision conditions", checked=False))
            labels = self.condition_labels()
            items.extend(
                ft.PopupMenuItem(
                    content=label,
                    checked=label in self.selection.conditions,
                    on_click=self.condition_toggle(label),
                )
                for label in labels
            )
        if not items:
            items = [ft.PopupMenuItem(content="Run to discover items")]
        self.variables_button.items = items
        self.variables_button.update()

    def build_constants(self) -> None:
        controls: list[ft.Control] = []
        if self.result is None:
            controls = [ft.Text("Run a program to discover values and functions.")]
        else:
            constants = getattr(self.result, "constants", ())
            functions = getattr(self.result, "functions", {})
            if constants:
                controls.append(ft.Text("Constants", weight=ft.FontWeight.BOLD))
                controls.extend(
                    ft.Row(
                        [
                            ft.Text(name, width=100),
                            ft.Text(
                                arith.format_value(
                                    self.result.variables.get(name),
                                    self.settings(),
                                    minus=arith.MINUS,
                                )
                            ),
                        ],
                        spacing=8,
                    )
                    for name in constants
                )
            if functions:
                controls.append(ft.Text("Functions", weight=ft.FontWeight.BOLD))
                controls.extend(ft.Text(description) for description in functions.values())
            if not controls:
                controls = [ft.Text("No constants or functions detected.")]
        self.constants_panel.controls = controls
        if hasattr(self.page, "update"):
            self.constants_panel.update()

    def condition_labels(self) -> tuple[str, ...]:
        """Each executed boolean expression once, labelled by source line."""
        if self.result is None:
            return ()
        found: dict[tuple[int, str], None] = {}
        for step in self.result.steps:
            if step.cond is not None:
                found.setdefault((step.line, step.cond[0]), None)
        return tuple(f"{line}: {expression}" for line, expression in found)

    def update_trace(self) -> None:
        if self.result is None:
            data = ft.DataTable(
                columns=[
                    ft.DataColumn(
                        label=ft.Container(
                            ft.Text("Line", text_align=ft.TextAlign.CENTER),
                            width=48,
                            alignment=ft.Alignment.CENTER,
                        )
                    )
                ],
                rows=[],
                border=ft.Border.all(1),
                horizontal_lines=ft.BorderSide(width=1),
                vertical_lines=ft.BorderSide(width=1),
                column_spacing=20,
                horizontal_margin=8,
                data_row_min_height=36,
            )
            self.trace.controls = [ft.Row([data], expand=False)]
            if hasattr(self.page, "update"):
                self.trace.update()
            return
        table = trace.selected_vertical(
            self.result,
            self.settings(),
            self.selection,
            cursor=self.cursor,
        )
        source_lines = self.source().splitlines()

        def condition_name(line: int) -> str:
            if not 1 <= line <= len(source_lines):
                return ""
            source = source_lines[line - 1].strip()
            for prefix in ("while ", "if ", "repeat until ", "until "):
                if source.lower().startswith(prefix):
                    return source[len(prefix) :].strip().removesuffix(" do").removesuffix(" then")
            return source

        condition_names = list(
            dict.fromkeys(
                name
                for step in self.result.steps
                if step.cond is not None
                for name in (condition_name(step.line),)
                if name and f"{step.line}: {name}" in self.selection.conditions
            )
        )
        variable_names = [
            name for name in self.choices.variables if name in self.selection.variables
        ]
        columns = [
            ft.DataColumn(
                label=ft.Container(
                    ft.Text("Line", text_align=ft.TextAlign.CENTER),
                    width=48,
                    alignment=ft.Alignment.CENTER,
                )
            ),
            *(
                ft.DataColumn(
                    label=ft.Container(
                        ft.Text(name),
                        width=76,
                        alignment=ft.Alignment.CENTER,
                    )
                )
                for name in variable_names
            ),
            *(
                ft.DataColumn(
                    label=ft.Container(
                        ft.Text(name),
                        width=130,
                        alignment=ft.Alignment.CENTER,
                    )
                )
                for name in condition_names
            ),
            ft.DataColumn(
                label=ft.Container(
                    ft.Text("Output"),
                    width=140,
                    alignment=ft.Alignment.CENTER,
                )
            ),
        ]
        rows: list[ft.DataRow] = []
        for row in table.rows:
            step_output = (
                self.result.steps[row.step].output if row.step < len(self.result.steps) else None
            )
            cells = [
                ft.DataCell(
                    ft.Container(
                        ft.Text(str(row.line), text_align=ft.TextAlign.CENTER),
                        width=48,
                        alignment=ft.Alignment.CENTER,
                    )
                ),
                *(
                    ft.DataCell(
                        ft.Container(
                            ft.Text(row.cells.get(name, "")),
                            width=76,
                            alignment=ft.Alignment.CENTER,
                        )
                    )
                    for name in variable_names
                ),
                *(
                    ft.DataCell(
                        ft.Container(
                            ft.Text(
                                next(iter(row.conditions.values()), "")
                                if condition_name(row.line) == name
                                else ""
                            ),
                            width=130,
                            alignment=ft.Alignment.CENTER,
                        )
                    )
                    for name in condition_names
                ),
                ft.DataCell(
                    ft.Container(
                        ft.Text(step_output or ""),
                        width=140,
                        alignment=ft.Alignment.CENTER,
                    )
                ),
            ]
            rows.append(ft.DataRow(cells=cells))
        data = ft.DataTable(
            columns=columns,
            rows=rows,
            border=ft.Border.all(1),
            horizontal_lines=ft.BorderSide(width=1),
            vertical_lines=ft.BorderSide(width=1),
            column_spacing=20,
            horizontal_margin=8,
            data_row_min_height=36,
        )
        self.trace.controls = [ft.Row([data], expand=True)]
        shown = len([step for step in self.result.steps if step.kind != "halt"])
        self.status.value = f"{self.cursor} / {shown} steps"
        self.status.update()
        self.trace.update()
        if self.cm is not None and table.rows:
            line = table.rows[-1].line
            import js  # ty: ignore[unresolved-import]  # noqa: PLC0415
            from pyodide.ffi import to_js  # ty: ignore[unresolved-import]  # noqa: PLC0415

            self.cm.setCursor(
                to_js(
                    {"line": line - 1},
                    dict_converter=js.Object.fromEntries,
                )
            )

    def home(self, _: ft.Event[ft.MenuItemButton]) -> None:
        async def show_home() -> None:
            from cassim.app.home import Home  # noqa: PLC0415

            self.page.controls.clear()
            await Home(
                self.shell,
                lambda item: self.page.run_task(self.open_device_placeholder, item),
            ).start()

        self.page.run_task(show_home)

    async def open_device_placeholder(self, item: str) -> None:
        """The Home callback target when a device is chosen after returning from Code view."""
        del item

    def open_settings(self, _: ft.Event[ft.MenuItemButton]) -> None:
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
            self.code_style = str(code_style.value or "monospace")
            new_symbol_style = str(symbol_style.value or "unicode")
            if new_symbol_style != self.symbol_style:
                old_source = self.source()
                new_source = convert_symbols(old_source, new_symbol_style)
                if new_source != old_source:
                    self.set_source(new_source)
                    self.typing_undo = (new_source, old_source)
            self.symbol_style = new_symbol_style
            self.number_button.content = f"Number: {self.number_mode.title()}"
            self.angle_button.content = f"Angle: {self.angle_mode.title()}"
            self.number_button.update()
            self.angle_button.update()
            self.apply_code_style()
            self.fallback_editor.update()
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
                        ft.Text(
                            "Formatted keeps linear source; it uses a proportional display face."
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
        choice = ft.Dropdown(
            label="Theme",
            value=self.theme_name,
            options=[ft.DropdownOption(key=name, text=name) for name in THEMES],
        )

        def save(_: ft.Event[ft.TextButton]) -> None:
            if choice.value in THEMES:
                self.apply_theme(choice.value)
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

    def check_updates(self, _: ft.Event[ft.MenuItemButton]) -> None:
        self.shell.check_for_updates()

    def open_help(self, _: ft.Event[ft.MenuItemButton]) -> None:
        self.shell.help()

    def open_about(self, _: ft.Event[ft.MenuItemButton]) -> None:
        self.shell.about()


def mount(shell: Shell) -> CodeApp:
    return CodeApp(shell)
