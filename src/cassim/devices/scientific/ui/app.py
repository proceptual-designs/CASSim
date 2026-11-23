"""CASSim fx scientific calculator Flet UI application view."""

from __future__ import annotations

import contextlib
import json
from typing import TYPE_CHECKING

import flet as ft

from cassim.app.theme import DARK, HIGH_CONTRAST, LIGHT, Theme
from cassim.devices.scientific.engine import AngleUnit
from cassim.devices.scientific.state import CalcMode, ScientificState
from cassim.devices.scientific.tutorials import (
    CORE_LESSONS,
    TutorialSession,
)

if TYPE_CHECKING:
    from cassim.app.shell import Shell

THEMES: dict[str, Theme] = {
    "Dark": DARK,
    "Light": LIGHT,
    "High contrast": HIGH_CONTRAST,
}

LCD_BG = "#1b221d"
LCD_TEXT = "#a7f3d0"
LCD_ACCENT = "#34d399"
LCD_ANN_INACTIVE = "#1e3a2b"

CHASSIS_BG = "#1e2227"
BEZEL_BG = "#13161a"
KEY_FN_BG = "#282c34"
KEY_NUM_BG = "#333842"
KEY_DEL_BG = "#4b5263"
KEY_AC_BG = "#b91c1c"
ACCENT_SHIFT = "#eab308"
ACCENT_ALPHA = "#f87171"
ACCENT_TARGET = "#38bdf8"


def _safe_update(control: ft.Control) -> None:
    with contextlib.suppress(RuntimeError):
        control.update()


class ScientificApp:
    """The Flet UI view for CASSim fx scientific calculator."""

    def __init__(self, shell: Shell) -> None:
        self.shell = shell
        self.page = shell.page
        self.state = ScientificState()
        self.theme_name = "Dark"
        self.menu_visible = True
        self.tutorials_visible = True

        # Tutorial management
        self.lessons = CORE_LESSONS
        self.current_lesson_index = 0
        self.tutorial_session = TutorialSession(lesson=self.lessons[0])

        # Key buttons map for dynamic tutorial highlighting: key_id -> ft.Container / button
        self.key_controls: dict[str, ft.Container] = {}

        self._build_ui()
        self._sync_lcd()
        self._sync_tutorial()

    def _build_ui(self) -> None:
        # 1. CASSim Top Menu Bar
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

        examples_menu = self._build_examples_menu()
        self.doc_menu = ft.SubmenuButton(
            content="Doc",
            controls=[
                ft.MenuItemButton(content="Open…", on_click=self.open_file),
                ft.MenuItemButton(content="Save", on_click=self.save_file),
                ft.MenuItemButton(content="Save as…", on_click=self.save_file_as),
                ft.MenuItemButton(content="Share link…", on_click=self.open_share_link),
                examples_menu,
                ft.MenuItemButton(content="Reset All", on_click=self.reset_all),
            ],
        )

        # Status Chips
        self.mode_chip_text = ft.Text("COMP", size=12, weight=ft.FontWeight.W_500)
        self.mode_chip = ft.Container(
            content=self.mode_chip_text,
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            bgcolor=DARK.key,
            border_radius=4,
            tooltip="Calculation mode",
            on_click=self.cycle_mode,
        )
        self.angle_chip_text = ft.Text("Deg", size=12, weight=ft.FontWeight.W_500)
        self.angle_chip = ft.Container(
            content=self.angle_chip_text,
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            bgcolor=DARK.key,
            border_radius=4,
            tooltip="Angle mode (click to cycle Deg / Rad / Gra)",
            on_click=self.cycle_angle,
        )
        self.math_chip = ft.Container(
            content=ft.Text("Math", size=12, weight=ft.FontWeight.W_500),
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            bgcolor=DARK.key,
            border_radius=4,
            tooltip="Natural display format",
        )

        self.hide_menu_button = ft.IconButton(
            icon=ft.Icons.FULLSCREEN,
            tooltip="Hide menu (Full-screen presentation mode)",
            on_click=self.toggle_menu_bar,
        )
        self.tutorial_toggle_button = ft.Button(
            "Tutorials",
            icon=ft.Icons.SCHOOL_OUTLINED,
            on_click=self.toggle_tutorials,
            style=ft.ButtonStyle(
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                text_style=ft.TextStyle(size=12),
            ),
        )

        self.top_menu_bar = ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            ft.MenuBar(controls=[self.cassim_menu]),
                            ft.MenuBar(controls=[self.doc_menu]),
                            self.mode_chip,
                            self.angle_chip,
                            self.math_chip,
                        ],
                        spacing=8,
                        tight=True,
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Row(
                        [
                            self.tutorial_toggle_button,
                            self.hide_menu_button,
                        ],
                        spacing=8,
                        tight=True,
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=12, vertical=4),
            bgcolor=DARK.background,
            border=ft.Border(bottom=ft.BorderSide(1, DARK.key_edge)),
            visible=self.menu_visible,
        )

        # Floating button when top menu is hidden
        self.restore_menu_button = ft.Container(
            content=ft.IconButton(
                icon=ft.Icons.FULLSCREEN_EXIT,
                tooltip="Show Menu",
                icon_color="white",
                bgcolor="#374151",
                on_click=self.toggle_menu_bar,
            ),
            top=10,
            right=10,
            visible=not self.menu_visible,
        )

        # 2. LCD Screen View
        self.ann_s = ft.Text("S", size=10, weight=ft.FontWeight.BOLD, color=LCD_ANN_INACTIVE)
        self.ann_a = ft.Text("A", size=10, weight=ft.FontWeight.BOLD, color=LCD_ANN_INACTIVE)
        self.ann_m = ft.Text("M", size=10, weight=ft.FontWeight.BOLD, color=LCD_ANN_INACTIVE)
        self.ann_sto = ft.Text("STO", size=10, weight=ft.FontWeight.BOLD, color=LCD_ANN_INACTIVE)
        self.ann_rcl = ft.Text("RCL", size=10, weight=ft.FontWeight.BOLD, color=LCD_ANN_INACTIVE)
        self.ann_stat = ft.Text("STAT", size=10, weight=ft.FontWeight.BOLD, color=LCD_ANN_INACTIVE)
        self.ann_angle = ft.Text("D", size=10, weight=ft.FontWeight.BOLD, color=LCD_TEXT)
        self.ann_math = ft.Text("Math", size=10, weight=ft.FontWeight.BOLD, color=LCD_TEXT)
        self.ann_up = ft.Text("▲", size=9, color=LCD_ANN_INACTIVE)
        self.ann_down = ft.Text("▼", size=9, color=LCD_ANN_INACTIVE)

        annunciator_row = ft.Row(
            [
                self.ann_s,
                self.ann_a,
                self.ann_m,
                self.ann_sto,
                self.ann_rcl,
                self.ann_stat,
                self.ann_angle,
                self.ann_math,
                ft.Container(expand=True),
                self.ann_up,
                self.ann_down,
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.lcd_expr = ft.Text(
            "",
            size=18,
            font_family="monospace",
            color=LCD_TEXT,
            selectable=True,
            overflow=ft.TextOverflow.ELLIPSIS,
            max_lines=2,
        )
        self.lcd_result = ft.Text(
            "0",
            size=26,
            font_family="monospace",
            weight=ft.FontWeight.BOLD,
            color=LCD_TEXT,
            text_align=ft.TextAlign.RIGHT,
            selectable=True,
        )

        self.lcd_screen = ft.Container(
            content=ft.Column(
                [
                    annunciator_row,
                    ft.Container(self.lcd_expr, height=44, alignment=ft.Alignment.TOP_LEFT),
                    ft.Container(self.lcd_result, height=40, alignment=ft.Alignment.BOTTOM_RIGHT),
                ],
                spacing=4,
                tight=True,
            ),
            bgcolor=LCD_BG,
            border_radius=8,
            padding=12,
            border=ft.Border.all(3, "#0f172a"),
            width=360,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=6, color="#00000088"),
        )

        # 3. Keypad Matrix View
        keypad_column = self._build_keypad()

        # Calculator Handheld Chassis
        self.calculator_chassis = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                "CASSIM fx",
                                size=13,
                                weight=ft.FontWeight.BOLD,
                                color="#94a3b8",
                            ),
                            ft.Text(
                                "NATURAL DISPLAY",
                                size=9,
                                weight=ft.FontWeight.W_600,
                                color="#64748b",
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    self.lcd_screen,
                    ft.Container(height=6),
                    keypad_column,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
                spacing=6,
            ),
            width=380,
            padding=14,
            bgcolor=CHASSIS_BG,
            border_radius=20,
            border=ft.Border.all(1.5, "#334155"),
            shadow=ft.BoxShadow(spread_radius=2, blur_radius=16, color="#000000aa"),
        )

        # 4. Tutorial Sidebar
        self.tutorial_sidebar = self._build_tutorial_sidebar()

        # Main Layout
        self.content_area = ft.Row(
            [
                ft.Container(self.calculator_chassis, alignment=ft.Alignment.TOP_CENTER),
                self.tutorial_sidebar,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=24,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

        self.root = ft.Column(
            [
                self.top_menu_bar,
                ft.Container(self.content_area, expand=True, padding=12),
            ],
            expand=True,
            spacing=0,
        )

        self.page.views.clear()
        self.page.views.append(
            ft.View(
                route="/scientific",
                controls=[
                    ft.Stack(
                        [
                            self.root,
                            self.restore_menu_button,
                        ],
                        expand=True,
                    )
                ],
                padding=0,
                spacing=0,
            )
        )
        self.page.update()

    def _build_examples_menu(self) -> ft.SubmenuButton:
        return ft.SubmenuButton(
            content="Examples",
            controls=[
                ft.MenuItemButton(
                    content="1. Mixed Fractions: 2 1/3 + 5/6",
                    on_click=lambda _: self.load_example("2+1/3+5/6"),
                ),
                ft.MenuItemButton(
                    content="2. Trigonometry: sin(30°) + cos(60°)",
                    on_click=lambda _: self.load_example("sin(30)+cos(60)"),
                ),
                ft.MenuItemButton(
                    content="3. Australian 1-VAR Stats: {12, 15, 18, 22, 25}",
                    on_click=lambda _: self.load_stat_example(),
                ),
                ft.MenuItemButton(
                    content="4. DMS: 12°34'56\" to Decimal",
                    on_click=lambda _: self.load_dms_example(),
                ),
                ft.MenuItemButton(
                    content="5. Polar to Rectangular: Rec(5, 53.13°)",
                    on_click=lambda _: self.load_example("Rec(5, 53.13)"),
                ),
                ft.MenuItemButton(
                    content="6. Prime Factorisation: 360",
                    on_click=lambda _: self.load_prime_example(),
                ),
            ],
        )

    def _build_keypad(self) -> ft.Column:
        rows: list[ft.Control] = []

        # Row 1: Function Modifiers & Navigation
        # SHIFT, ALPHA, D-PAD (Up, Down, Left, Right), MODE, ON
        dpad = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [self._make_key("UP", "▲", width=36, height=22, is_fn=True)],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        [
                            self._make_key("LEFT", "◀", width=36, height=22, is_fn=True),
                            ft.Container(width=4),
                            self._make_key("RIGHT", "▶", width=36, height=22, is_fn=True),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        [self._make_key("DOWN", "▼", width=36, height=22, is_fn=True)],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                spacing=1,
                tight=True,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            width=88,
            height=72,
            alignment=ft.Alignment.CENTER,
        )

        r1 = ft.Row(
            [
                ft.Column(
                    [
                        self._make_key(
                            "SHIFT", "SHIFT", width=48, height=32, accent=ACCENT_SHIFT, is_fn=True
                        ),
                        self._make_key(
                            "ALPHA", "ALPHA", width=48, height=32, accent=ACCENT_ALPHA, is_fn=True
                        ),
                    ],
                    spacing=6,
                ),
                dpad,
                ft.Column(
                    [
                        self._make_key("MODE", "MODE", width=48, height=32, is_fn=True),
                        self._make_key("ON", "ON", width=48, height=32, is_fn=True),
                    ],
                    spacing=6,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        rows.append(r1)

        # Row 2: Abs, x³, x⁻¹, x!
        rows.append(
            ft.Row(
                [
                    self._make_key("Abs", "Abs", sub_s="", sub_a="", is_fn=True),
                    self._make_key("x^3", "x³", sub_s="", sub_a="", is_fn=True),
                    self._make_key("x^-1", "x⁻¹", sub_s="", sub_a="", is_fn=True),
                    self._make_key("x!", "x!", sub_s="", sub_a="", is_fn=True),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )

        # Row 3: ■/□, √, x², x■, log, ln
        rows.append(
            ft.Row(
                [
                    self._make_key("FRAC", "■/□", sub_s="a b/c", sub_a="", is_fn=True),
                    self._make_key("sqrt", "√", sub_s="³√", sub_a="", is_fn=True),
                    self._make_key("x^2", "x²", sub_s="", sub_a="", is_fn=True),
                    self._make_key("x^y", "x■", sub_s="x√", sub_a="", is_fn=True),
                    self._make_key("log", "log", sub_s="10■", sub_a="", is_fn=True),
                    self._make_key("ln", "ln", sub_s="e■", sub_a="", is_fn=True),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )

        # Row 4: (-), ° ' ", hyp, sin, cos, tan
        rows.append(
            ft.Row(
                [
                    self._make_key("(-)", "(-)", sub_s="", sub_a="A", is_fn=True),
                    self._make_key("DMS", "° ' \"", sub_s="FACT", sub_a="B", is_fn=True),
                    self._make_key("hyp", "hyp", sub_s="", sub_a="C", is_fn=True),
                    self._make_key("sin", "sin", sub_s="sin⁻¹", sub_a="D", is_fn=True),
                    self._make_key("cos", "cos", sub_s="cos⁻¹", sub_a="E", is_fn=True),
                    self._make_key("tan", "tan", sub_s="tan⁻¹", sub_a="F", is_fn=True),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )

        # Row 5: RCL, ENG, (, ), S⇔D, M+
        rows.append(
            ft.Row(
                [
                    self._make_key("RCL", "RCL", sub_s="STO", sub_a="", is_fn=True),
                    self._make_key("ENG", "ENG", sub_s="←", sub_a="", is_fn=True),
                    self._make_key("(", "(", sub_s="%", sub_a="", is_fn=True),
                    self._make_key(")", ")", sub_s=",", sub_a="X", is_fn=True),
                    self._make_key("S<=>D", "S⇔D", sub_s="a b/c⇔d/c", sub_a="Y", is_fn=True),
                    self._make_key("M+", "M+", sub_s="M-", sub_a="M", is_fn=True),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )

        # Row 6 (Numeric Block 1): 7, 8, 9, DEL, AC
        rows.append(
            ft.Row(
                [
                    self._make_key("7", "7", sub_s="", sub_a=""),
                    self._make_key("8", "8", sub_s="", sub_a=""),
                    self._make_key("9", "9", sub_s="CLR", sub_a=""),
                    self._make_key("DEL", "DEL", sub_s="INS", sub_a="", bg=KEY_DEL_BG),
                    self._make_key("AC", "AC", sub_s="OFF", sub_a="", bg=KEY_AC_BG),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )

        # Row 7: 4, 5, 6, ×, ÷
        rows.append(
            ft.Row(
                [
                    self._make_key("4", "4", sub_s="", sub_a=""),
                    self._make_key("5", "5", sub_s="", sub_a=""),
                    self._make_key("6", "6", sub_s="", sub_a=""),
                    self._make_key("*", "×", sub_s="nPr", sub_a="GCD"),
                    self._make_key("/", "÷", sub_s="nCr", sub_a="LCM"),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )

        # Row 8: 1, 2, 3, +, −
        rows.append(
            ft.Row(
                [
                    self._make_key("1", "1", sub_s="STAT", sub_a=""),
                    self._make_key("2", "2", sub_s="", sub_a=""),
                    self._make_key("3", "3", sub_s="", sub_a=""),
                    self._make_key("+", "+", sub_s="Pol", sub_a=""),
                    self._make_key("-", "−", sub_s="Rec", sub_a=""),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )

        # Row 9: 0, ·, ×10ˣ, Ans, =
        rows.append(
            ft.Row(
                [
                    self._make_key("0", "0", sub_s="Rnd", sub_a=""),
                    self._make_key(".", "·", sub_s="Ran#", sub_a="RanInt"),
                    self._make_key("EXP", "×10ˣ", sub_s="π", sub_a="e"),
                    self._make_key("Ans", "Ans", sub_s="DRG▶", sub_a=""),
                    self._make_key("=", "=", sub_s="", sub_a="", bg="#2563eb"),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )

        return ft.Column(rows, spacing=7, tight=True)

    def _make_key(  # noqa: PLR0913, PLR0917
        self,
        key_id: str,
        label: str,
        sub_s: str = "",
        sub_a: str = "",
        width: int = 56,
        height: int = 36,
        accent: str | None = None,
        is_fn: bool = False,
        bg: str | None = None,
    ) -> ft.Container:
        bg_color = bg or (KEY_FN_BG if is_fn else KEY_NUM_BG)
        text_color = accent or ("#f1f5f9" if is_fn else "#ffffff")

        # Optional secondary label headers
        labels: list[ft.Control] = []
        if sub_s or sub_a:
            labels.append(
                ft.Row(
                    [
                        ft.Text(sub_s, size=8, color=ACCENT_SHIFT, weight=ft.FontWeight.BOLD),
                        ft.Text(sub_a, size=8, color=ACCENT_ALPHA, weight=ft.FontWeight.BOLD),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    tight=True,
                )
            )

        btn = ft.Container(
            content=ft.Text(label, size=13, weight=ft.FontWeight.W_600, color=text_color),
            alignment=ft.Alignment.CENTER,
            width=width,
            height=height,
            bgcolor=bg_color,
            border_radius=6,
            border=ft.Border.all(1, "#475569"),
            on_click=lambda _: self.on_key_press(key_id),
            ink=True,
        )

        wrapper = ft.Container(
            content=ft.Column(
                [*labels, btn],
                spacing=1,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=0,
        )
        self.key_controls[key_id] = btn
        return wrapper

    def _build_tutorial_sidebar(self) -> ft.Container:
        lesson_dropdown = ft.Dropdown(
            label="Lesson",
            options=[
                ft.DropdownOption(key=str(idx), text=f"{lesson.id}: {lesson.title}")
                for idx, lesson in enumerate(self.lessons)
            ],
            value=str(self.current_lesson_index),
            on_select=self.on_lesson_selected,
            width=320,
        )

        self.tut_title = ft.Text(
            self.tutorial_session.lesson.title,
            size=15,
            weight=ft.FontWeight.BOLD,
            color="#f8fafc",
        )
        self.tut_category = ft.Text(
            self.tutorial_session.lesson.category,
            size=11,
            color="#94a3b8",
            weight=ft.FontWeight.W_500,
        )
        self.tut_step_badge_text = ft.Text(
            "Step 1/1", size=11, weight=ft.FontWeight.BOLD, color="#0284c7"
        )
        self.tut_step_badge = ft.Container(
            content=self.tut_step_badge_text,
            bgcolor="#e0f2fe",
            padding=ft.Padding.symmetric(horizontal=8, vertical=2),
            border_radius=12,
        )

        self.tut_prompt = ft.Text(
            "",
            size=13,
            color="#cbd5e1",
            selectable=True,
        )
        self.tut_target_key = ft.Text(
            "",
            size=13,
            weight=ft.FontWeight.BOLD,
            color="#38bdf8",
        )
        self.tut_expected_screen_text = ft.Text(
            "",
            size=12,
            font_family="monospace",
            color=LCD_TEXT,
        )
        self.tut_expected_screen = ft.Container(
            content=self.tut_expected_screen_text,
            bgcolor=LCD_BG,
            padding=8,
            border_radius=4,
            border=ft.Border.all(1, "#334155"),
            width=320,
        )

        self.tut_history = ft.Text(
            "Keystrokes: (none)",
            size=11,
            color="#64748b",
            font_family="monospace",
        )
        self.tut_feedback = ft.Text(
            "",
            size=12,
            weight=ft.FontWeight.W_500,
            color="#10b981",
        )

        tut_controls = ft.Row(
            [
                ft.TextButton("Back", on_click=self.on_tut_back),
                ft.TextButton("Skip Step", on_click=self.on_tut_skip),
                ft.TextButton("Reset Lesson", on_click=self.on_tut_reset),
            ],
            spacing=4,
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.SCHOOL, size=18, color="#38bdf8"),
                            ft.Text("Interactive Tutorial", size=14, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_size=16,
                                tooltip="Close tutorial",
                                on_click=self.toggle_tutorials,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    lesson_dropdown,
                    ft.Row([self.tut_category, ft.Container(expand=True), self.tut_step_badge]),
                    self.tut_title,
                    ft.Divider(height=1, color="#334155"),
                    ft.Text("Instruction:", size=11, weight=ft.FontWeight.BOLD, color="#94a3b8"),
                    self.tut_prompt,
                    ft.Row(
                        [
                            ft.Text("Required Action: ", size=11, color="#94a3b8"),
                            self.tut_target_key,
                        ]
                    ),
                    ft.Text(
                        "Expected Calculator Readout:",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color="#94a3b8",
                    ),
                    self.tut_expected_screen,
                    self.tut_history,
                    self.tut_feedback,
                    ft.Divider(height=1, color="#334155"),
                    tut_controls,
                ],
                spacing=8,
                tight=True,
                width=340,
            ),
            padding=16,
            bgcolor="#1e293b",
            border_radius=12,
            border=ft.Border.all(1, "#334155"),
            visible=self.tutorials_visible,
        )

    # ---------------------------------------------------------------------------
    # Sync and Update Logic
    # ---------------------------------------------------------------------------

    def _sync_lcd(self) -> None:
        """Update LCD screen elements according to calculator state."""
        self.ann_s.color = ACCENT_SHIFT if self.state.shift_active else LCD_ANN_INACTIVE
        self.ann_a.color = ACCENT_ALPHA if self.state.alpha_active else LCD_ANN_INACTIVE
        has_m = self.state.variables.get("M", 0.0) != 0.0
        self.ann_m.color = LCD_TEXT if has_m else LCD_ANN_INACTIVE
        self.ann_sto.color = ACCENT_SHIFT if self.state.sto_active else LCD_ANN_INACTIVE
        self.ann_rcl.color = LCD_TEXT if self.state.rcl_active else LCD_ANN_INACTIVE
        self.ann_stat.color = LCD_TEXT if self.state.mode == "STAT" else LCD_ANN_INACTIVE

        angle_abbr = {"DEG": "D", "RAD": "R", "GRA": "G"}.get(self.state.angle_unit, "D")
        self.ann_angle.value = angle_abbr

        self.lcd_expr.value = self.state.expr + ("_" if self.state.cursor_visible else "")
        self.lcd_result.value = self.state.result

        self.mode_chip_text.value = self.state.mode
        self.angle_chip_text.value = self.state.angle_unit.title()

        _safe_update(self.lcd_screen)
        _safe_update(self.mode_chip)
        _safe_update(self.angle_chip)

    def _sync_tutorial(self) -> None:
        """Update tutorial sidebar and target key focus outline."""
        # Clear previous key focus highlights
        for key_btn in self.key_controls.values():
            key_btn.border = ft.Border.all(1, "#475569")
            _safe_update(key_btn)

        if not self.tutorials_visible or self.tutorial_session.is_complete:
            self.tut_step_badge_text.value = "Complete ✓"
            self.tut_step_badge.bgcolor = "#dcfce7"
            self.tut_step_badge_text.color = "#15803d"
            self.tut_prompt.value = (
                "Lesson complete! You have successfully completed this interactive tutorial."
            )
            self.tut_target_key.value = "(Finished)"
            self.tut_feedback.value = "Excellent work."
            _safe_update(self.tutorial_sidebar)
            return

        step = self.tutorial_session.current_step
        assert step is not None

        # Highlight current target key
        target_btn = self.key_controls.get(step.key)
        if target_btn:
            target_btn.border = ft.Border.all(2.5, ACCENT_TARGET)
            _safe_update(target_btn)

        # Update text labels
        current_idx = self.tutorial_session.current_step_index + 1
        total_steps = len(self.tutorial_session.lesson.steps)
        self.tut_step_badge_text.value = f"Step {current_idx}/{total_steps}"
        self.tut_step_badge.bgcolor = "#e0f2fe"
        self.tut_step_badge_text.color = "#0284c7"

        self.tut_title.value = self.tutorial_session.lesson.title
        self.tut_category.value = self.tutorial_session.lesson.category
        self.tut_prompt.value = step.instruction
        self.tut_target_key.value = f"[{step.key}]"
        self.tut_expected_screen_text.value = step.expected_screen

        history_str = " ".join(self.tutorial_session.history[-6:])
        self.tut_history.value = f"Keystrokes: {history_str if history_str else '(none)'}"
        _safe_update(self.tutorial_sidebar)

    # ---------------------------------------------------------------------------
    # Event Handlers
    # ---------------------------------------------------------------------------

    def on_key_press(self, key_id: str) -> None:
        """Handle physical or mouse click on calculator button."""
        # 1. Update calculator engine
        self.state.press(key_id)
        self._sync_lcd()

        # 2. Check tutorial progress
        if self.tutorials_visible and not self.tutorial_session.is_complete:
            matched = self.tutorial_session.press(key_id)
            if matched:
                self.tut_feedback.value = "Step completed! Moving to next step."
                self.tut_feedback.color = "#10b981"
            else:
                hint = self.tutorial_session.get_hint()
                self.tut_feedback.value = f"Press [{hint}] to continue."
                self.tut_feedback.color = "#f59e0b"
            self._sync_tutorial()

    def cycle_mode(self, _: object) -> None:
        modes: list[CalcMode] = ["COMP", "STAT", "TABLE"]
        idx = (modes.index(self.state.mode) + 1) % len(modes) if self.state.mode in modes else 0
        self.state.mode = modes[idx]
        self._sync_lcd()

    def cycle_angle(self, _: object) -> None:
        units: list[AngleUnit] = ["DEG", "RAD", "GRA"]
        idx = (units.index(self.state.angle_unit) + 1) % len(units)
        self.state.angle_unit = units[idx]
        self._sync_lcd()

    def toggle_menu_bar(self, _: object) -> None:
        self.menu_visible = not self.menu_visible
        self.top_menu_bar.visible = self.menu_visible
        self.restore_menu_button.visible = not self.menu_visible
        _safe_update(self.top_menu_bar)
        _safe_update(self.restore_menu_button)

    def toggle_tutorials(self, _: object) -> None:
        self.tutorials_visible = not self.tutorials_visible
        self.tutorial_sidebar.visible = self.tutorials_visible
        _safe_update(self.tutorial_sidebar)
        if self.tutorials_visible:
            self._sync_tutorial()

    def on_lesson_selected(self, e: ft.Event[ft.Dropdown]) -> None:
        value = e.control.value
        if value is None:
            return
        try:
            idx = int(value)
            if 0 <= idx < len(self.lessons):
                self.current_lesson_index = idx
                self.tutorial_session = TutorialSession(lesson=self.lessons[idx])
                self.state.reset()
                self._sync_lcd()
                self._sync_tutorial()
        except Exception:
            pass

    def on_tut_back(self, _: ft.Event[ft.TextButton]) -> None:
        self.tutorial_session.back()
        self._sync_tutorial()

    def on_tut_skip(self, _: ft.Event[ft.TextButton]) -> None:
        self.tutorial_session.advance()
        self._sync_tutorial()

    def on_tut_reset(self, _: ft.Event[ft.TextButton]) -> None:
        self.tutorial_session.reset()
        self.state.reset()
        self._sync_lcd()
        self._sync_tutorial()

    # ---------------------------------------------------------------------------
    # Examples and State Actions
    # ---------------------------------------------------------------------------

    def load_example(self, expr: str) -> None:
        self.state.reset()
        self.state.expr = expr
        self.state.press("=")
        self._sync_lcd()

    def load_stat_example(self) -> None:
        self.state.reset()
        self.state.mode = "STAT"
        self.state.stat_1var = [(12, 1), (15, 1), (18, 1), (22, 1), (25, 1)]
        self.state.expr = "1-VAR Stats Loaded (n=5)"
        self.state.result = "x̄=18.4, sx=5.18"
        self._sync_lcd()

    def load_dms_example(self) -> None:
        self.state.reset()
        self.state.expr = "12°34'56\""
        self.state.result = "12.58222222"
        self._sync_lcd()

    def load_prime_example(self) -> None:
        self.state.reset()
        self.state.expr = "360"
        self.state.variables["Ans"] = 360.0
        self.state.prime_factorise()
        self._sync_lcd()

    def reset_all(self, _: ft.Event[ft.MenuItemButton]) -> None:
        self.state.reset(all_settings=True)
        self._sync_lcd()
        self.shell.notice("Reset Complete", "Calculator cleared to factory settings.")

    # ---------------------------------------------------------------------------
    # Shell Menu Handlers
    # ---------------------------------------------------------------------------

    def home(self, _: ft.Event[ft.MenuItemButton]) -> None:
        if self.shell.home is not None:
            self.shell.home()

    def activate_update(self, _: ft.Event[ft.MenuItemButton]) -> None:
        self.shell.activate_update()

    def open_help(self, _: ft.Event[ft.MenuItemButton]) -> None:
        self.shell.help()

    def open_about(self, _: ft.Event[ft.MenuItemButton]) -> None:
        self.shell.about()

    def open_settings(self, _: ft.Event[ft.MenuItemButton]) -> None:
        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Calculator Settings"),
                content=ft.Column(
                    [
                        ft.Text("Calculation Format: Natural Display (MthIO)"),
                        ft.Text(f"Current Angle Unit: {self.state.angle_unit}"),
                        ft.Text(f"Current Mode: {self.state.mode}"),
                    ],
                    tight=True,
                    spacing=8,
                ),
                actions=[
                    ft.TextButton("Close", on_click=lambda _: self.page.pop_dialog()),
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
                self.theme_name = selected
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

    def open_share_link(self, _: ft.Event[ft.MenuItemButton]) -> None:
        url = self.shell.link(self.state.encode_share_fragment())

        def copy_link(_: ft.Event[ft.TextButton]) -> None:
            self.shell.copy(url)
            self.page.pop_dialog()
            self.shell.notice("Link Copied", "Calculator share URL copied to clipboard.")

        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Share Calculator State"),
                content=ft.Column(
                    [
                        ft.Text(
                            "Share your current calculations, memory registers, and statistical "
                            "data using this URL:",
                            size=13,
                        ),
                        ft.TextField(value=url, read_only=True, dense=True),
                    ],
                    tight=True,
                    spacing=8,
                ),
                actions=[
                    ft.TextButton("Copy URL", on_click=copy_link),
                    ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog()),
                ],
            )
        )

    async def open_file(self, _: ft.Event[ft.MenuItemButton]) -> None:
        text = await self.shell.pick_file(("json", "fx"), "Open calculation")
        if text:
            try:
                data = json.loads(text)
                if isinstance(data, dict):
                    self.state.from_dict(data)
                    self._sync_lcd()
                    self.shell.notice("Loaded", "Calculation state restored.")
            except Exception as exc:
                self.shell.notice("Error", f"Failed to open file: {exc}")

    async def save_file(self, _: ft.Event[ft.MenuItemButton]) -> None:
        content = json.dumps(self.state.to_dict(), indent=2)
        await self.shell.save_file("calculation.fx.json", content, "Save calculation")

    def save_file_as(self, _: ft.Event[ft.MenuItemButton]) -> None:
        name_tf = ft.TextField(label="File name", value="calculation.fx.json")

        async def save(_: ft.Event[ft.TextButton]) -> None:
            name = str(name_tf.value or "").strip()
            if name:
                content = json.dumps(self.state.to_dict(), indent=2)
                await self.shell.save_file(name, content, "Save calculation")
            self.page.pop_dialog()

        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Save calculation as"),
                content=name_tf,
                actions=[
                    ft.TextButton("Save", on_click=save),
                    ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog()),
                ],
            )
        )

    async def start(self, **options: object) -> None:
        """Start the scientific app view."""
        self.page.title = "CASSim fx"
        if not self.page.views or self.page.views[-1].route != "/scientific":
            self.page.views.clear()
            self.page.views.append(
                ft.View(
                    route="/scientific",
                    controls=[
                        ft.Stack(
                            [
                                self.root,
                                self.restore_menu_button,
                            ],
                            expand=True,
                        )
                    ],
                    padding=0,
                    spacing=0,
                )
            )
            self.page.update()

    def unmount(self) -> None:
        """Cleanup when unmounting the device."""
        self.page.views.clear()


def mount(shell: Shell) -> ScientificApp:
    """Mount and return a new ScientificApp view."""
    return ScientificApp(shell)
