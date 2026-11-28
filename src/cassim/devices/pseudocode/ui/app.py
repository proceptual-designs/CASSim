"""The standalone pseudocode Code view: CodeMirror, console and a vertical trace."""

from __future__ import annotations

import ast
import asyncio
import contextlib
import json
import random
import re
from collections.abc import Callable
from dataclasses import replace
from typing import TYPE_CHECKING, cast

import flet as ft

from cassim.app import about
from cassim.app.appearance import Appearance, appearance_dialog
from cassim.app.cassim_menu import AppMenu, fill_cassim_menu
from cassim.app.saved import SavedDocuments
from cassim.app.shell import BrowserOffers
from cassim.app.theme import DARK, Theme
from cassim.devices.pseudocode.typing_aids import (
    TYPED_BURST,
    convert_region,
    convert_symbols,
    typed_span,
)
from cassim.devices.pseudocode.ui.call_window import CallWindow
from cassim.devices.pseudocode.ui.panes import BoxedPane, PaneOptions
from cassim.devices.pseudocode.ui.trace_grid import (
    CONDITION_COLUMN_WIDTH,
    LINE_COLUMN_WIDTH,
    OUTPUT_COLUMN_WIDTH,
    VARIABLE_COLUMN_WIDTH,
    Column,
    TraceGrid,
)
from cassim.doc.serialize import DocumentFileError
from cassim.doc.share import LinkTooLongError, encode_text, unpack
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

if TYPE_CHECKING:
    from cassim.app.shell import Shell


HELP_PAGE = "Pseudocode.html"  # this app's page on the help site
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
PRIME_SIEVE = (
    "n ← 100\n"
    "is_prime ← []\n"
    "for i from 1 to n\n"
    "  append true to is_prime\n"
    "end for\n"
    "is_prime[1] ← false\n"
    "for p from 2 to n\n"
    "  if is_prime[p] then\n"
    "    multiple ← p*p\n"
    "    while multiple ≤ n do\n"
    "      is_prime[multiple] ← false\n"
    "      multiple ← multiple + p\n"
    "    end while\n"
    "  end if\n"
    "end for\n"
    "primes ← []\n"
    "for i from 2 to n\n"
    "  if is_prime[i] then\n"
    "    append i to primes\n"
    "  end if\n"
    "end for\n"
    "print primes"
)
DICE_MAX_STATS = (
    "seed(42)\n"
    "trials ← 20\n"  # small, so the trace table draws quickly (Simon, 2026-11-22)
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
    "define eval(coeffs, x)\n"
    "  value ← 0\n"
    "  for each coeff in coeffs\n"
    "    value ← value*x + coeff\n"
    "  end for\n"
    "  return value\n"
    "end\n"
    "\n"
    "define derivative(coeffs)\n"
    "  dcoeffs ← []\n"
    "  n ← len(coeffs) - 1\n"
    "  for i from 1 to len(coeffs)-1\n"
    "    append (n - i + 1)*coeffs[i] to dcoeffs\n"
    "  end for\n"
    "  return dcoeffs\n"
    "end\n"
    "\n"
    "# f(x) ← x³ + 0 x² - 2 x - 5\n"
    "# f'(x) ← 3x² + 0 x - 2\n"
    "f ← [1, 0, -2, -5]\n"
    "df ← derivative(f)\n"
    "x ← 1\n"
    "for i from 1 to 8\n"
    "  x ← x - eval(f, x)/eval(df, x)\n"
    "  print x\n"
    "end for"
)
MOBILE_BREAKPOINT = 900
# The typing aid converts once typing has paused this long (seconds). Converting on every
# key sent the whole text back from Python, overwriting keys typed in the meantime.
TYPING_AID_PAUSE = 0.5
EDITOR_FONT_SIZE = 14
# Width the editor keeps from its text: content padding (8 each side) and Flutter's text
# cursor (2), measured 2026-11-22: a 461.2 px line wrapped in a 478 px editor.
EDITOR_SIDE_PADDING = 18
PROBE_LENGTH = 40  # characters in each hidden sample the editor font is measured with
ROW_HEIGHT = 20  # one editor row: font size 14 at line height 20/14
EDITOR_TOP = 8  # the first row's top in the editor box, as the gutter's padding
# Before the samples are measured: character width as a fraction of the font size.
CHAR_EM = {"monospace": 0.6, "formatted": 0.5}


def _one(_char: str) -> float:
    return 1.0


def wrapped_rows(line: str, width: float, char_width: Callable[[str], float] = _one) -> int:
    """How many rows the editor draws `line` on in `width`, wrapping at spaces as Flutter
    does: a word that does not fit moves to the next row, and a word longer than a row is
    split. `char_width` gives each character's width (by default 1, so `width` counts
    characters); `width` 0 means not known yet, so no wrapping."""

    def measure(text: str) -> float:
        return sum(char_width(char) for char in text)

    if width <= 0 or measure(line) <= width:
        return 1
    rows, used = 1, 0.0
    # A row can end at a space or just after a "/" (Flutter breaks `x)/derivative` there).
    for piece in re.findall(r"\s*[^\s/]*/|\s*[^\s/]+", line):
        text = piece
        if used and used + measure(text) > width:
            rows, used = rows + 1, 0.0
            text = piece.lstrip()  # the spaces before a wrapped word end the last row
        while measure(text) > width:
            fits, total = 0, 0.0
            while fits < len(text) and total + char_width(text[fits]) <= width:
                total += char_width(text[fits])
                fits += 1
            rows, text = rows + 1, text[max(fits, 1) :]
        used += measure(text)
    return rows


SYMBOL_COLUMN_COUNT = 3
EDITOR_SETTINGS_KEY = "editor"
CODE_FONT = "CASSim Code"
MATH_FONT = "CASSim Math"
SYMBOL_FONT = "Symbols"


def _control_style(theme: Theme = DARK) -> ft.ButtonStyle:
    """The toolbar's and the run controls' buttons, in the current theme."""
    return ft.ButtonStyle(
        bgcolor={
            ft.ControlState.SELECTED: theme.accent,
            ft.ControlState.DEFAULT: theme.key,
        },
        color={
            ft.ControlState.SELECTED: theme.accent_text,
            ft.ControlState.DEFAULT: theme.key_text,
        },
        side=ft.BorderSide(1, theme.key_edge),
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
        self.saved = SavedDocuments(
            self.page,
            shell,
            dump=self._dump,
            load=self._load_saved,
            said=lambda text: shell.notice("Saved", text),
            noun="program",
        )
        shell.has_unsaved = self.saved.dirty  # a reload for an update asks first
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
        self.typing_aid = True  # Settings, on by default
        self.typing_undo: tuple[str, str] | None = None
        self.code_style = "monospace"
        self.symbol_style = "unicode"
        self.console_inputs: list[str] = []
        # the Python Console's statements so far, run again before each line (sandboxed)
        self.python_console_lines: list[str] = []
        self.python_console_seed = random.randrange(2**31)
        self.language = "pseudocode"
        self.number_mode: NumberMode = "approx"
        self.angle_mode: AngleMode = "radian"
        # the shared theme, or one the dialog previews (a test may pass a shell without one)
        self.appearance: Appearance = getattr(shell, "appearance", None) or Appearance()
        self.cm = None
        self.cm_change_proxy = None
        self.editor_width = 0.0  # drawn width, reported by the box around the editor
        self.code_char_width = 0.0  # measured from the hidden samples once drawn
        # Typed since the typing aid last converted: (start, end) in the current text.
        self.typed_region: tuple[int, int] | None = None
        self.typed_paste = False
        self.edit_generation = 0  # counts edits, so only the last one before a pause acts
        self.symbol_char_width = 0.0
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
            expand=True,  # fill the pane: lines wrap only when the pane is too narrow
        )
        self.highlighted_line = 0  # the source line the trace has reached (0: none)
        self.line_band = ft.Container(
            left=0, right=0, top=0, height=ROW_HEIGHT, visible=False,
            bgcolor=DARK.line_highlight, border_radius=3,
        )  # fmt: skip
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
                ft.Container(
                    # the band behind the text marks the line the trace has reached
                    ft.Stack([self.line_band, self.fallback_editor]),
                    expand=True,
                    # The text field does not report its size; this box is exactly its width.
                    on_size_change=self.on_editor_size,
                    size_change_interval=100,
                ),
            ],
            expand=True,
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
        # Hidden samples in the editor's font: their drawn widths give the width of a code
        # character and of a symbol, so the gutter knows where long lines wrap.
        self.code_sample = ft.Text("0" * PROBE_LENGTH, style=self.editor_text_style())
        self.symbol_sample = ft.Text("←" * PROBE_LENGTH, style=self.editor_text_style())
        samples = ft.Container(
            ft.Column(
                [
                    ft.Container(self.code_sample, on_size_change=self.measured_sample("code")),
                    ft.Container(self.symbol_sample, on_size_change=self.measured_sample("symbol")),
                ],
                spacing=0,
                tight=True,
            ),
            height=0,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )
        editor_content = ft.Column(
            [samples, editor_row],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=0,
        )

        self.number_button = ft.Button("Approx", on_click=self.cycle_number, style=_control_style())
        self.angle_button = ft.Button("Radian", on_click=self.toggle_angle, style=_control_style())
        self.cassim_menu = ft.SubmenuButton(content="CASSim")
        self.refresh_cassim_menu()
        examples = self.build_examples_menu()
        self.doc_menu = ft.SubmenuButton(
            content="Doc",
            controls=[
                ft.MenuItemButton(content="New", on_click=self.new_program),
                ft.MenuItemButton(content="Open…", on_click=self.saved.open),
                ft.MenuItemButton(content="Save", on_click=self.saved.save),
                ft.MenuItemButton(content="Save as…", on_click=self.saved.save_as),
                ft.Divider(height=1, thickness=1),
                ft.MenuItemButton(content="Import file…", on_click=self.import_file),
                ft.MenuItemButton(content="Export file…", on_click=self.export_file),
                ft.MenuItemButton(content="Share link…", on_click=self.open_share_link),
                ft.Divider(height=1, thickness=1),
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
                    (("GCD and LCM", GCD_LCM), ("Prime sieve (1 to 100)", PRIME_SIEVE)),
                ),
                group(
                    "Probability",
                    (
                        ("Two D6: larger", DICE_MAX_STATS),
                        ("Two D4 sample space", D4_SAMPLE_SPACE),
                    ),
                ),
                group(
                    "Numerical methods",
                    (
                        ("Left Riemann sum", LEFT_RIEMANN),
                        ("Polynomial + Newton", POLYNOMIAL_NEWTON),
                    ),
                ),
            ],
        )

    def _init_workspace_state(self) -> None:
        self.generated_python = False
        self.python_header = ""
        self.column_split = 0.5
        self.left_host: ft.Container | None = None
        self.trace_mode = "vertical"
        self.trace_grid = TraceGrid(self.show_call)
        self.call_windows: list[CallWindow] = []  # open call windows, newest last
        self.trace_widths = self.trace_grid.widths  # kept when the table is redrawn
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
        self.page.title = f"{about.product_name()} Pseudocode & Python"
        self.page.padding = 8
        self.page.on_resize = self.on_resize
        self.page.on_keyboard_event = self.on_keyboard
        self.page.add(self.root)
        error = await self.shell.load_appearance()
        self.apply_theme()
        if error:
            self.shell.notice("Appearance", error)
        self.arrange()
        if self._has_browser_dom():
            await self.start_codemirror()
        await self.saved.start()
        self.saved.fresh()  # the starting program has nothing to lose yet
        self.open_route()

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
        # A new key: the old "typing_aids" mostly holds the old default (off).
        typing_aid = data.get("typing_aid")
        if code_style in ("monospace", "formatted"):
            self.code_style = str(code_style)
        if symbol_style in ("unicode", "ascii"):
            self.symbol_style = str(symbol_style)
        if isinstance(typing_aid, bool):
            self.typing_aid = typing_aid
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
                    "typing_aid": self.typing_aid,
                }
            ),
        )

    def apply_code_style(self) -> None:
        self.fallback_editor.text_style = self.editor_text_style()
        for sample in (self.code_sample, self.symbol_sample):
            sample.style = self.editor_text_style()  # re-measured in the new font
            _safe_update(sample)
        self.refresh_line_numbers()  # the character width sets where lines wrap
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
        self.shell.has_unsaved = lambda: False
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
        """The page reported a change (an update, installing, going offline)."""
        self.refresh_cassim_menu()
        _safe_update(self.cassim_menu)

    @property
    def offers(self) -> BrowserOffers:
        return getattr(self.shell, "offers", None) or BrowserOffers()

    def refresh_cassim_menu(self) -> None:
        """The CASSim menu, shared with every app (SDD-15 section 4)."""
        facts = AppMenu(home=getattr(self.shell, "home", None) is not None)
        fill_cassim_menu(self.cassim_menu, self.offers, facts, self.cassim_action, self.theme)

    def cassim_action(self, action: str) -> None:
        """A CASSim menu item: this app's own, or one the shell does for every app."""
        own: dict[str, Callable[[], object]] = {
            "home": self.home,
            "settings": self.open_settings,
            "appearance": self.open_appearance,
        }
        if action in own:
            own[action]()
        else:
            self.shell.menu_action(action, HELP_PAGE)

    @property
    def theme(self) -> Theme:
        return self.appearance.theme

    @property
    def codemirror_theme(self) -> str:
        return "default" if self.appearance.theme_name == "Light" else "dracula"

    def styled_buttons(self) -> list[ft.Button | ft.SegmentedButton]:
        """The buttons drawn in the theme's key and accent colours."""
        return [
            self.number_button,
            self.angle_button,
            self.language_switch,
            self.trace_layout,
            self.run_button,
            self.stop_button,
            self.step_button,
            self.start_button,
            self.end_button,
        ]

    def apply_theme(self, appearance: Appearance | None = None) -> None:
        """Draw in the shared theme, or in `appearance` while the dialog previews it."""
        self.appearance = appearance or self.shell.appearance
        theme = self.theme
        self.page.theme_mode = self.appearance.mode
        self.page.bgcolor = theme.background
        style = _control_style(theme)
        for button in self.styled_buttons():
            button.style = style
        self.line_band.bgcolor = theme.line_highlight
        if self.cm is not None:
            self.cm.setOption("theme", self.codemirror_theme)
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
        self.current_source = text
        self.highlighted_line = 0  # the trace no longer matches the code
        if self.typing_aid_available():
            self.note_typed(previous, text)
            self.edit_generation += 1
            run_task = getattr(self.page, "run_task", None)
            if run_task is None:  # no event loop (unit tests): convert at once
                self.apply_typing_aid()
            else:
                run_task(self.typing_aid_after_pause, self.edit_generation)
        self.refresh_line_numbers()
        self.mark_dirty()

    def note_typed(self, previous: str, text: str) -> None:
        """Widen the region typed since the last conversion to cover this edit."""
        shortest = min(len(previous), len(text))
        start = 0
        while start < shortest and previous[start] == text[start]:
            start += 1
        tail = 0
        while tail < shortest - start and previous[-1 - tail] == text[-1 - tail]:
            tail += 1
        end = len(text) - tail
        span = typed_span(previous, text)
        if span is None and end - start > TYPED_BURST:
            self.typed_paste = True  # a paste is left as it is
        if self.typed_region is None:
            self.typed_region = (start, end)
            return
        low, high = self.typed_region
        moved = len(text) - len(previous)
        if low >= len(previous) - tail:
            low += moved
        if high > start:
            high = max(start, high + moved)
        self.typed_region = (max(0, min(low, start)), min(len(text), max(high, end)))

    async def typing_aid_after_pause(self, generation: int) -> None:
        await asyncio.sleep(TYPING_AID_PAUSE)
        if generation == self.edit_generation:  # nothing typed since: the pause is real
            self.apply_typing_aid()

    def apply_typing_aid(self) -> None:
        """Convert what was typed since the last conversion, then send the text back once."""
        region, paste = self.typed_region, self.typed_paste
        self.typed_region, self.typed_paste = None, False
        if region is None or paste or not self.typing_aid_available():
            return
        text = self.current_source
        converted = convert_region(text, *region)
        if converted == text:
            return
        self.typing_undo = (converted, text)
        self.fallback_editor.value = converted
        # Setting the text puts the caret at the end; put it back after what was typed. Every
        # conversion ends inside the typed region, so the text before the caret is what shrank.
        caret = max(0, min(len(converted), region[1] + len(converted) - len(text)))
        self.fallback_editor.selection = ft.TextSelection(base_offset=caret, extent_offset=caret)
        self.current_source = converted
        self.refresh_line_numbers()
        _safe_update(self.fallback_editor)

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
    def _line_numbers_for(
        source: str, width: float = 0, char_width: Callable[[str], float] = _one
    ) -> str:
        """One number per source line; a line the editor wraps onto more rows gets blank rows
        after its number, so the numbers stay beside their lines. `width` 0: no wrapping."""
        rows: list[str] = []
        for number, line in enumerate(source.splitlines(), start=1):
            rows.append(str(number))
            rows.extend([""] * (wrapped_rows(line, width, char_width) - 1))
        return "\n".join(rows)

    def text_width(self) -> float:
        """Room for text on one editor row, in pixels (0 before the editor is drawn)."""
        return max(0.0, self.editor_width - EDITOR_SIDE_PADDING) if self.editor_width else 0.0

    def char_width(self, char: str) -> float:
        """A character's drawn width in the editor: measured from the hidden samples, ASCII
        in the code font and other characters (arrows, π, ≤) in the fallback symbol fonts."""
        measured = self.code_char_width if char.isascii() else self.symbol_char_width
        return measured or CHAR_EM[self.code_style] * EDITOR_FONT_SIZE

    def on_editor_size(self, event: ft.LayoutSizeChangeEvent[ft.LayoutControl]) -> None:
        if abs(event.width - self.editor_width) >= 1:
            self.editor_width = event.width
            self.refresh_line_numbers()

    def measured_sample(self, kind: str) -> Callable[[ft.LayoutSizeChangeEvent], None]:
        def measured(event: ft.LayoutSizeChangeEvent) -> None:
            width = event.width / PROBE_LENGTH
            if kind == "code" and width != self.code_char_width:
                self.code_char_width = width
                self.refresh_line_numbers()
            elif kind == "symbol" and width != self.symbol_char_width:
                self.symbol_char_width = width
                self.refresh_line_numbers()

        return measured

    def refresh_line_numbers(self) -> None:
        source = str(self.fallback_editor.value or "")
        self.line_number_gutter.value = self._line_numbers_for(
            source, self.text_width(), self.char_width
        )
        self.fallback_editor.min_lines = max(12, len(source.splitlines()) + 1)
        self.line_number_gutter.visible = self.line_numbers_visible
        _safe_update(self.line_number_gutter)
        _safe_update(self.fallback_editor)
        self.highlight_line(self.highlighted_line)  # wrapping may have moved it

    def highlight_line(self, line: int) -> None:
        """Put the band behind source line `line` (counting the rows wrapped lines take, as
        the gutter does), as the call window highlights its code; 0 hides it."""
        self.highlighted_line = line
        lines = str(self.fallback_editor.value or "").splitlines()
        if not 1 <= line <= len(lines):
            self.line_band.visible = False
        else:
            width = self.text_width()
            rows_before = sum(wrapped_rows(t, width, self.char_width) for t in lines[: line - 1])
            self.line_band.top = EDITOR_TOP + rows_before * ROW_HEIGHT
            self.line_band.height = (
                wrapped_rows(lines[line - 1], width, self.char_width) * ROW_HEIGHT
            )
            self.line_band.visible = True
        _safe_update(self.line_band)

    def cycle_trace_layout(self, _: ft.Event[ft.Button]) -> None:
        modes = ("vertical", "horizontal", "none")
        self.change_trace_layout(modes[(modes.index(self.trace_mode) + 1) % len(modes)])

    def change_trace_layout(self, value: str) -> None:
        self.trace_mode = value
        self.trace_layout.content = f"Trace: {value.title()}"
        _safe_update(self.trace_layout)
        self.update_trace()

    # Open, Save and Save as keep programs by name in this app's storage (`self.saved`,
    # decision 0033, FR-EDT-002); a file on disk comes in and goes out through Import and Export
    # (FR-EDT-003).

    def _dump(self, _name: str) -> str:
        """The program as it is stored: its language and text (FR-EDT-002), and its number and
        angle modes, which belong to the program (SDD-15 section 6)."""
        return json.dumps(
            {
                "format": "cassim-code",
                "device": "pseudocode",
                "language": self.language,
                "number": self.number_mode,
                "angle": self.angle_mode,
                "source": self.python_translation_source()
                if self.language == "python"
                else self.source(),
            },
            ensure_ascii=False,
        )

    def _load_saved(self, text: str, _name: str) -> None:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as error:
            msg = "it is not a saved CASSim program"
            raise ValueError(msg) from error
        if not isinstance(data, dict) or not isinstance(data.get("source"), str):
            msg = "it is not a saved CASSim program"
            raise ValueError(msg)
        self.set_language("python" if data.get("language") == "python" else "pseudocode")
        number, angle = data.get("number"), data.get("angle")
        self.set_modes(
            cast(NumberMode, number) if number in ("approx", "auto", "exact") else "approx",
            cast(AngleMode, angle) if angle in ("radian", "degree") else "radian",
        )
        self.show_text(data["source"])

    def set_modes(self, number: NumberMode, angle: AngleMode) -> None:
        """Show the program's number and angle modes on the toolbar, their only place."""
        self.number_mode, self.angle_mode = number, angle
        self.number_button.content = number.title()
        self.angle_button.content = angle.title()
        _safe_update(self.number_button)
        _safe_update(self.angle_button)

    def new_program(self, _: object = None) -> None:
        """Doc > New: a blank program, asking first if work would be lost (SDD-15 9.4)."""

        def blank() -> None:
            self.show_text("")
            self.saved.fresh()

        self.saved.ask_discard(blank)

    def open_share_link(self, _: object = None) -> None:
        """Doc > Share link…: the program in a link. Opening it never runs it (FR-RUN-004)."""
        try:
            url = self.shell.link(encode_text(self._dump(self.saved.name)))
        except LinkTooLongError:
            self.shell.notice(
                "Share link",
                "This program is too long for a link. Use Doc ▸ Export file… and share that.",
            )
            return
        self.shell.share_link(url, "Anyone who opens this link gets this program, ready to run.")

    def open_route(self) -> None:
        """A share link opens its program, saved nowhere here until Save. It waits for Run."""
        route = getattr(self.shell, "route", "") or ""
        try:
            text = unpack(route.lstrip("/"))
            if text is None:
                return
            self._load_saved(text, "")
        except (DocumentFileError, ValueError) as error:
            self.shell.notice("Share link", f"The link could not be opened: {error}.")
            return
        self.saved.unsaved()

    def set_language(self, target: str) -> None:
        """Show `target` as the language without translating the text (a saved program names
        its own)."""
        self.language = target
        self.language_switch.selected = [target]
        if self.cm is not None:
            self.cm.setOption("mode", "pseudocode" if target == "pseudocode" else "python")
        _safe_update(self.language_switch)
        self.update_typing_aids()

    def show_text(self, text: str) -> None:
        """Put a program's text in the editor (Python made by translation keeps its header)."""
        if TRANSLATION_MARKER in text.splitlines():
            self.set_generated_python(text)
        else:
            self.set_source(text)

    def import_file(self, _: object = None) -> None:
        """Import file…: open a code file, asking first if work would be lost."""
        self.saved.ask_discard(lambda: self.page.run_task(self._import_file))

    async def _import_file(self) -> None:
        try:
            text = await self.shell.pick_file(("py", "txt", "pseudo"), "Import code")
        except UnicodeDecodeError:
            self.shell.notice("Import file", "That file is not text.")
            return
        if text is not None:
            self.show_text(text)
            self.saved.unsaved()  # not in this app's storage until it is saved

    async def export_file(self, _: object = None) -> None:
        """Export file…: download the program as `.py` or `.pseudo.txt` (FR-EDT-003)."""
        extension = "py" if self.language == "python" else "pseudo.txt"
        stem = self.saved.current.stored or "untitled"
        await self.shell.save_file(f"{stem}.{extension}", self.source(), "Export code")

    def load_example(self, text: str) -> None:
        """Doc > Examples: load one, asking first if work would be lost (SDD-15 section 9.4)."""
        try:
            source = (
                pseudocode_to_python(text, self.settings()) if self.language == "python" else text
            )
        except (PseudocodeError, SyntaxError, TranslationError) as error:
            self.shell.notice("Cannot load example", str(error))
            return

        def load() -> None:
            if self.language == "python":
                self.set_generated_python(source)
            else:
                self.set_source(source)
            self.saved.unsaved()  # an example is not the saved program any more

        self.saved.ask_discard(load)

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
        self.typed_region, self.typed_paste = None, False  # nothing typed in the new text
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
        """A Python Console line, run as Run runs a program: translated to pseudocode and run by
        CASSim's own interpreter, never executed as Python, so it cannot reach the page, the
        network, storage or the computer (SDD-15 section 9.5). Statements are kept and run again
        before the next line, with the session's own random seed, so `x = 6` then `x + 1` gives
        7; a bare expression is printed."""
        stripped = text.strip()
        try:
            parsed = ast.parse(stripped, mode="exec")
        except SyntaxError as error:
            return f"Error: SyntaxError: {error.msg}"
        body = parsed.body
        call = body[0].value if len(body) == 1 and isinstance(body[0], ast.Expr) else None
        is_print = (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id == "print"
        )
        # A method call (lst.append(3)) changes what it is called on: a statement to keep
        method = isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
        expression = call is not None and not is_print and not method
        line = f"print({stripped})" if expression else stripped
        settings = replace(self.settings(), seed=self.python_console_seed)
        earlier = self.python_console_lines
        try:
            before = python_to_pseudocode("\n".join(earlier) + "\n") if earlier else ""
            now = python_to_pseudocode("\n".join([*earlier, line]) + "\n")
        except (SyntaxError, TranslationError) as error:
            return f"Error: {error}"
        shown = len(run(before, settings).output) if before else 0
        result = run(now, settings)
        output = list(result.output[shown:])
        if result.error:
            return "\n".join([*output, f"Error: {result.error}"])
        if not expression and not is_print:
            self.python_console_lines.append(stripped)  # a statement the next line can use
        return "\n".join(output)

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
        host.style.background = self.appearance.theme.code_background
        host.style.border = "1px solid #555"
        document.body.appendChild(host)

        cm = js.CodeMirror(
            host,
            to_js(
                {
                    "value": self.current_source,
                    "mode": "pseudocode" if self.language == "pseudocode" else "python",
                    "theme": self.codemirror_theme,
                    "lineNumbers": self.line_numbers_visible,
                    "lineWrapping": True,
                    "indentUnit": 2,
                    "tabSize": 2,
                    "autofocus": False,
                    "cassimTypingAids": self.typing_aid_available(),
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

        def changed(_instance: object, _change: object) -> None:
            # CodeMirror's own `CASSimTypingAids` handler converts while typing.
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

    def typing_aid_available(self) -> bool:
        """The typing aid (Settings) converts only Pseudocode written in Unicode symbols."""
        return self.typing_aid and self.language == "pseudocode" and self.symbol_style == "unicode"

    def update_typing_aids(self) -> None:
        if not self.typing_aid_available():
            self.typing_undo = None
        if self.cm is not None:
            self.cm.setOption("cassimTypingAids", self.typing_aid_available())

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

    def step_stops(self) -> list[int]:
        """Where Step stops: after each top-level row, with the lines of any call on it run
        (step over; they are examined in the call's window)."""
        return [] if self.result is None else trace.step_over_stops(self.result)

    def step_back(self, _: ft.Event[ft.Button] | None) -> None:
        self.cursor = max((stop for stop in self.step_stops() if stop < self.cursor), default=0)
        self.update_trace()

    def step_forward(self, _: ft.Event[ft.Button] | None) -> None:
        stops = self.step_stops()
        self.cursor = next((stop for stop in stops if stop > self.cursor), self.cursor)
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
        """Each boolean expression the program's own lines ran, once, labelled by source line.
        Conditions inside a function belong to its calls' windows, as its variables do."""
        if self.result is None:
            return ()
        source_lines = self.trace_source.splitlines()
        found: dict[tuple[int, str], None] = {}
        for step in self.result.steps:
            if step.cond is None or step.depth > 0:
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

    def resize_trace_column(self, key: str, event: ft.DragUpdateEvent) -> None:
        self.trace_grid.resize(key, event)

    def call_rows(self, table: trace.VerticalTable) -> dict[int, int]:
        """Row number -> step for the rows that call a function defined in the code."""
        if self.result is None:
            return {}
        steps = self.result.steps
        return {
            number: row.step
            for number, row in enumerate(table.rows)
            if row.step < len(steps) and steps[row.step].kind == "call"
        }

    def show_call(self, call: int) -> None:
        """Open one function call in a movable, resizable window: the function's code beside
        its trace (stacked on a phone), with the trace pane's resizable columns and Step /
        First / Last over the call's own rows. The code highlights the line of the last row
        shown. Calls inside it open the same way (FR-TRC-013)."""
        if self.result is None:
            return
        result, settings, cursor = self.result, self.settings(), self.cursor
        reached = trace.call_table(result, settings, call, cursor=cursor)
        total = len(reached.rows)
        grid = TraceGrid(self.show_call)
        host = ft.Container(expand=True)
        counter = ft.Text(size=12)
        shown = [total]  # rows of the call shown: all it has reached when it opens
        columns: list[Column] = [
            ("__line__", "Line", LINE_COLUMN_WIDTH),
            *((f"variable:{name}", name, VARIABLE_COLUMN_WIDTH) for name in reached.variables),
            ("__output__", "Calcs / Output", OUTPUT_COLUMN_WIDTH),
        ]
        source = trace.function_source(parse(self.trace_source), result.steps[call].function)
        code = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=0)

        def draw_code(current: int) -> None:
            code.controls = [
                ft.Container(
                    ft.Row(
                        [
                            ft.Text(str(number), width=28, text_align=ft.TextAlign.RIGHT),
                            ft.Text(text, font_family=CODE_FONT, no_wrap=True),
                        ],
                        spacing=8,
                    ),
                    bgcolor=self.theme.line_highlight if number == current else None,
                    padding=ft.Padding.symmetric(horizontal=4, vertical=1),
                )
                for number, text in source
            ]
            _safe_update(code)

        def draw() -> None:
            table = trace.call_table(result, settings, call, cursor=cursor, rows=shown[0])
            rows = [
                [str(row.line), *(row.cells.get(name, "") for name in reached.variables), row.calc]
                for row in table.rows
            ]
            host.content = grid.build(columns, rows, self.call_rows(table))
            counter.value = f"{shown[0]} / {total} steps"
            draw_code(table.rows[-1].line if table.rows else source[0][0] if source else 0)
            _safe_update(host)
            _safe_update(counter)

        def go(rows: int) -> None:
            shown[0] = max(0, min(total, rows))
            draw()

        controls = ft.Row(
            [
                ft.Button(
                    "Step", on_click=lambda _: go(shown[0] + 1), style=_control_style(self.theme)
                ),
                ft.Button("First", on_click=lambda _: go(0), style=_control_style(self.theme)),
                ft.Button("Last", on_click=lambda _: go(total), style=_control_style(self.theme)),
                counter,
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        draw()
        starting = trace.call_parameters(result, call, settings)
        name = result.steps[call].calc
        trace_side = ft.Column([controls, host], spacing=8, expand=3)
        code_side = ft.Container(  # long lines scroll sideways rather than run under the trace
            ft.Row(
                [code],
                scroll=ft.ScrollMode.AUTO,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            expand=2,
            padding=ft.Padding.only(top=4),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )
        window = CallWindow(  # side by side when it is wide enough, stacked when narrow
            self.page,
            f"{name}: {starting}" if starting else name,
            code_side,
            trace_side,
            offset=len(self.call_windows),
            on_close=self.call_windows.remove,
        )
        self.call_windows.append(window)
        window.open()

    def draw_trace_table(
        self,
        columns: list[tuple[str, str, float]],
        rows: list[list[str]],
        calls: dict[int, int] | None = None,
    ) -> None:
        self.trace.controls = [self.trace_grid.build(columns, rows, calls)]
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
                if step.cond is not None and step.depth == 0
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
                self.draw_trace_table(columns, rows, self.call_rows(vertical))
        else:
            vertical, columns, rows = self.update_vertical_trace()
            self.draw_trace_table(columns, rows, self.call_rows(vertical))
        stops = self.step_stops()
        self.status.value = (
            f"{sum(1 for stop in stops if stop <= self.cursor)} / {len(stops)} steps"
        )
        _safe_update(self.status)
        reached = [
            step
            for step in (self.result.steps[: self.cursor] if self.result is not None else [])
            if step.depth == 0 and step.kind != "halt"
        ]
        self.highlight_line(reached[-1].line if reached else 0)
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

    def home(self, _: object = None) -> None:
        home = getattr(self.shell, "home", None)
        if home is not None:
            home()

    def open_settings(self, _: object = None) -> None:
        def switch_changed(event: ft.Event[ft.Switch]) -> None:
            event.control.value = bool(event.control.value)
            _safe_update(event.control)

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
            self.line_numbers_visible = bool(line_numbers.value)
            self.typing_aid = bool(typing_aid.value)
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
                    ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog()),
                    ft.TextButton("Save", on_click=save),
                ],
            )
        )

    def open_appearance(self, _: object = None) -> None:
        """CASSim > Appearance…: the theme shared with Home and every app (SDD-15 section 7.3)."""

        def save(appearance: Appearance) -> None:
            self.shell.save_appearance(appearance)
            self.apply_theme()

        appearance_dialog(self.page, self.shell.appearance, save, on_preview=self.apply_theme)


def mount(shell: Shell) -> CodeApp:
    return CodeApp(shell)
