"""The CASSim Scientific view, run headless against a stand-in shell.

Requirements: FR-FX-DSP-001, FR-FX-DSP-002, FR-FX-SHR-001, FR-FX-SHR-002, FR-FX-TUT-001,
FR-FX-TUT-002, FR-FX-TUT-005, FR-FX-UI-001 to -004.
Cited: FR-FX-UI-001 FR-FX-UI-002 FR-FX-UI-003 FR-FX-UI-004 FR-FX-TUT-003.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable, Coroutine
from types import SimpleNamespace
from typing import Any

import flet as ft
import pytest

from cassim.devices.scientific import keys as k
from cassim.devices.scientific import layouts
from cassim.devices.scientific.layouts import LAYOUTS
from cassim.devices.scientific.state import ScientificState
from cassim.devices.scientific.ui import app as ui
from cassim.devices.scientific.ui.app import BASE_WIDTH, ScientificApp
from cassim.devices.scientific.ui.skins import SKINS


class FakePage:
    def __init__(self, width: float = 1366, height: float = 650) -> None:
        self.width = width
        self.height = height
        self.fonts: dict[str, str] = {}
        self.controls: list[ft.Control] = []
        self.tasks: list[Coroutine[Any, Any, Any]] = []
        self.dialogs: list[object] = []
        self._dialogs = SimpleNamespace(controls=[])
        self.title = ""
        self.padding = 0
        self.bgcolor = ""
        self.theme_mode = None
        self.on_keyboard_event: Callable[..., None] | None = None
        self.on_resize: Callable[..., None] | None = None

    def add(self, control: ft.Control) -> None:
        self.controls.append(control)

    def update(self) -> None:
        pass

    def run_task(self, handler: Callable[..., Coroutine[Any, Any, Any]], *args: object) -> None:
        self.tasks.append(handler(*args))

    def run_tasks(self) -> None:
        tasks, self.tasks = self.tasks, []
        for task in tasks:
            asyncio.run(task)

    def drop_tasks(self) -> None:
        for task in self.tasks:
            task.close()
        self.tasks = []

    def show_dialog(self, dialog: object) -> None:
        self.dialogs.append(dialog)

    def pop_dialog(self) -> None:
        if self.dialogs:
            self.dialogs.pop()


class FakeShell:
    def __init__(self, page: FakePage, route: str = "") -> None:
        self.page = page
        self.route = route
        self.home: Callable[[], None] | None = lambda: None
        self.update_label = "Check for updates"
        self.changed: Callable[[], None] = lambda: None
        self.store: dict[str, str] = {}
        self.notices: list[tuple[str, str]] = []
        self.copied: list[str] = []
        self.saved: list[tuple[str, str]] = []
        self.picked: str | None = None

    async def read(self, key: str) -> str | None:
        return self.store.get(key)

    def write(self, key: str, text: str) -> None:
        self.store[key] = text

    def notice(self, title: str, message: str) -> None:
        self.notices.append((title, message))

    def copy(self, text: str) -> None:
        self.copied.append(text)

    def link(self, fragment: str) -> str:
        return f"https://example.test/#/{fragment}"

    async def save_file(self, name: str, text: str, title: str = "") -> None:
        self.saved.append((name, text))

    async def pick_file(self, extensions: tuple[str, ...], title: str = "") -> str | None:
        return self.picked

    def confirm(self, title: str, message: str, action: str, accept) -> None:
        asyncio.run(accept())

    def help(self, page: str = "") -> None: ...
    def about(self) -> None: ...
    def activate_update(self) -> None: ...


def started(page: FakePage | None = None, route: str = "", store: dict[str, str] | None = None):
    page = page or FakePage()
    shell = FakeShell(page, route)
    shell.store.update(store or {})
    app = ScientificApp(shell)  # ty: ignore[invalid-argument-type]
    asyncio.run(app.start())
    return app, shell, page


def keyboard(app: ScientificApp, key: str, **mods: bool) -> None:
    event = SimpleNamespace(
        key=key,
        shift=mods.get("shift", False),
        ctrl=mods.get("ctrl", False),
        alt=mods.get("alt", False),
        meta=mods.get("meta", False),
    )
    app.on_keyboard(event)  # ty: ignore[invalid-argument-type]


def test_mount_and_start() -> None:
    app, _, page = started()
    assert page.title == "CASSim Scientific"
    assert page.controls == [app.root]
    assert page.on_keyboard_event == app.on_keyboard
    drawn = {key.id for key in app.layout.all_keys()}
    assert set(app.key_controls) == drawn  # FR-FX-DSP-001: every key is drawn
    app.unmount()
    assert page.on_keyboard_event is None
    assert page.controls == []


def _row_widths(app: ScientificApp) -> list[float]:
    column = app.calculator.content
    assert isinstance(column, ft.Column)
    widths = []
    for row in column.controls:
        if isinstance(row, ft.Row) and row.width and len(row.controls) >= 4:
            total = 0.0
            for cell in row.controls:
                face = cell.controls[-1] if isinstance(cell, ft.Column) else cell
                if isinstance(face, ft.Semantics):
                    face = face.content
                assert isinstance(face, ft.Container)  # a key, or a gap's spacer
                total += face.width or 0
            total += row.spacing * (len(row.controls) - 1)
            widths.append(total - row.width)
    return widths


def _drawn_keys(app: ScientificApp) -> list[tuple[str, float]]:
    """(key id, width) of every key face drawn."""
    return [(key_id, face.width or 0) for key_id, face in app.key_controls.items()]


@pytest.mark.parametrize("layout", LAYOUTS, ids=lambda layout: layout.id)
@pytest.mark.parametrize("size", [(360, 500), (1366, 650), (2560, 1400)])
def test_key_legends_stay_inside_their_key(layout, size: tuple[int, int]) -> None:
    """Legends such as sin⁻¹ D or ab/c⇔d/c Y ran into the gap between keys. As in the design
    mockup they are inset from the key's edges; a pair that would not fit is made smaller."""
    app, _, page = started(FakePage(*size))
    app.set_layout(layout.id)
    scale = app.scale
    for key_id, width in _drawn_keys(app):
        key = app.shown_layout.key(key_id)
        if not (key.shift_label or key.alpha_label):
            continue
        size_ = ui.legend_font_size(key.shift_label, key.alpha_label, width, scale)
        needed = (len(key.shift_label) + len(key.alpha_label)) * ui.LEGEND_ADVANCE * size_
        if key.shift_label and key.alpha_label:
            needed += ui.LEGEND_GAP * scale
        assert needed <= width - 2 * ui.LEGEND_INSET * scale + 1e-9, (layout.id, key_id, scale)
        assert size_ >= ui.LEGEND_MIN * scale
    page.drop_tasks()


def test_legends_keep_the_design_size_when_they_fit() -> None:
    assert ui.legend_font_size("STO", "", 51, 1.0) == ui.LEGEND_SIZE
    assert ui.legend_font_size("ab/c⇔d/c", "Y", 51, 1.0) < ui.LEGEND_SIZE


@pytest.mark.parametrize(("width", "height"), [(1366, 650), (1920, 935), (800, 600), (390, 760)])
def test_the_keypad_fits_the_calculator(width: float, height: float) -> None:
    """The review's bug: six-key rows were wider than the calculator, so ln, tan and M+ were
    cut off. Every row must fit inside the body at every size."""
    for layout in LAYOUTS:
        app, _, page = started(FakePage(width, height))
        app.set_layout(layout.id)
        overflow = _row_widths(app)
        assert overflow, layout.id
        assert all(excess <= 0.5 for excess in overflow), (layout.id, overflow)
        page.drop_tasks()


def test_the_calculator_scales_to_the_window() -> None:
    """FR-FX-DSP-001: the whole calculator fits a Chromebook-sized window."""
    for layout in LAYOUTS:
        app, _, page = started(FakePage(1366, 650))
        app.set_layout(layout.id)
        assert app.layout_height() * app.scale <= page.height - ui.BAR_HEIGHT, layout.id
        page.drop_tasks()
    small, _, _ = started(FakePage(360, 500))
    assert small.scale == ui.MIN_SCALE  # then the page scrolls
    big, _, _ = started(FakePage(2560, 1400))
    assert big.scale == ui.MAX_SCALE
    assert BASE_WIDTH * big.scale > BASE_WIDTH


def test_keypad_clicks_and_annunciators() -> None:
    """FR-FX-DSP-002."""
    app, _, page = started()
    for key in (k.SHIFT,):
        app.on_key(key)
    assert app.state.annunciators()["S"]
    for key in ("9", k.AC, "2", k.FRAC, "3", k.EQ):
        app.on_key(key)
    assert app.state.answer_text() == "2⌟3"
    page.drop_tasks()


def test_keyboard_input() -> None:
    """FR-FX-UI-004: typing, shortcuts and the modifier keys."""
    app, shell, page = started()
    keyboard(app, "2")
    keyboard(app, "Slash", ctrl=True)
    keyboard(app, "3")
    keyboard(app, "Arrow Right")
    keyboard(app, "Equal", shift=True)  # +
    keyboard(app, "r")
    keyboard(app, "2")
    keyboard(app, "Enter")
    assert app.state.display().text() == "2⌟3+√2\n(2+3√2)⌟3"
    keyboard(app, "c", ctrl=True)
    assert shell.copied == ["(2+3√2)⌟3"]
    keyboard(app, "F1")
    keyboard(app, "9")
    assert app.state.menu == "clr"
    keyboard(app, "Escape")
    assert app.state.screen == "calc"
    keyboard(app, "Numpad 7")
    assert app.state.display().text() == "7"
    page.drop_tasks()


def test_keyboard_in_verify_mode_types_equals() -> None:
    app, _, page = started()
    for key in (k.MODE, "4", "2"):
        app.on_key(key)
    keyboard(app, "Equal")
    keyboard(app, "2")
    keyboard(app, "Enter")
    assert app.state.answer_text() == "TRUE"
    page.drop_tasks()


def test_keys_are_ignored_while_a_dialog_is_open() -> None:
    app, _, page = started()
    page._dialogs.controls.append(SimpleNamespace(open=True))
    keyboard(app, "5")
    assert app.state.display().text() == ""


def test_keys_are_ignored_while_a_menu_is_open() -> None:
    """An arrow key that moves through the Doc menu must not also move the entry's cursor."""
    app, _, page = started()
    opened, closed = app.doc_menu.on_open, app.doc_menu.on_close
    assert callable(opened)
    assert callable(closed)
    opened(None)
    keyboard(app, "5")
    assert app.state.display().text() == ""
    closed(None)
    keyboard(app, "5")
    assert app.state.display().text() == "5"
    page.drop_tasks()


def test_hide_menu_bar_and_escape() -> None:
    """FR-FX-UI-002: presentation mode, with Esc bringing the bar back."""
    app, _, page = started()
    app.toggle_menu_bar()
    assert not app.top_bar.visible
    assert app.restore_button.visible
    keyboard(app, "Escape")
    assert app.top_bar.visible
    page.drop_tasks()


def test_status_chips() -> None:
    """FR-FX-UI-001: the chips show the mode, angle and input, and change them."""
    app, _, page = started()
    app.cycle_angle()
    assert app.state.setup.angle == "RAD"
    label = app.angle_chip.content
    assert isinstance(label, ft.Text)
    assert label.value == "Rad"
    app.toggle_io()
    assert app.state.setup.input == "line"
    app.on_key(k.MODE)  # what the chip's click does
    assert app.state.menu == "mode"
    page.drop_tasks()


@pytest.mark.parametrize("name", list(SKINS))
def test_appearance(name: str) -> None:
    app, shell, page = started()
    app.apply_skin(name)
    assert page.bgcolor == SKINS[name].page
    assert json.loads(shell.store["prefs"])["theme"] == name
    again, _, page2 = started(store=shell.store)
    assert page2.bgcolor == SKINS[name].page
    assert again.skin_name == name


def test_autosave_and_restore() -> None:
    """FR-FX-SHR-001: the calculator comes back after a reload."""
    app, shell, page = started()
    for key in (k.SHIFT, k.MODE, "4", "7", k.MPLUS, "3", k.ADD, "4", k.EQ):
        app.on_key(key)
    page.run_tasks()
    assert "autosave" in shell.store
    again, _, _ = started(store=shell.store)
    assert again.state.setup.angle == "RAD"
    assert float(again.state.variables["M"]) == 7
    assert again.state.display().text() == "3+4\n7"


def test_share_link_opens_on_start() -> None:
    """FR-FX-SHR-002: a link fills the calculator and wins over the autosave."""
    shared = ScientificState()
    for key in (k.MODE, "2", "1", "4", k.EQ, "6", k.EQ):
        shared.press(key)
    fragment = shared.share_fragment()
    app, _, _ = started(route=f"/{fragment}", store={"autosave": ScientificState().dumps()})
    assert app.state.mode == "STAT"
    assert len(app.state.stat_rows) == 2
    broken, shell, _ = started(route="/doc=broken!!")
    assert shell.notices
    assert broken.state.mode == "COMP"


def test_share_dialog_and_files() -> None:
    app, shell, page = started()
    for key in ("5", k.EQ):
        app.on_key(key)
    app.open_share_link()
    assert page.dialogs
    asyncio.run(app.save_file())
    name, text = shell.saved[-1]
    assert name == "Untitled.cassim.json"
    shell.picked = text.replace('"Untitled"', '"Homework"')
    other = ScientificApp(shell)
    asyncio.run(other.open_file(None))  # ty: ignore[invalid-argument-type]
    assert other.doc_name == "Homework"
    assert other.state.answer_text() == "5"
    shell.picked = json.dumps({"format": "cassim-document", "schema": 5, "device": "nspire"})
    asyncio.run(other.open_file(None))  # ty: ignore[invalid-argument-type]
    assert "nspire" in shell.notices[-1][1]
    page.drop_tasks()


def test_reset_all_and_examples() -> None:
    app, _, page = started()
    app.load_example(0)
    assert app.state.mode == "STAT"
    app.confirm_reset()
    assert app.state.mode == "COMP"
    page.drop_tasks()


def test_guide_me_lesson() -> None:
    """FR-FX-TUT-001 to -003 in the view: the keypad is not locked, a wrong key only hints."""
    app, shell, page = started()
    for key in ("4", "2"):
        app.on_key(key)
    app.lesson_index = 0  # reset
    app.start_lesson()
    assert app._target_key() == k.SHIFT
    app.on_key("7")
    assert not app.feedback_ok
    assert app.state.display().text() != "7"
    for key in (k.SHIFT, "9", "3", k.EQ, k.AC):
        app.on_key(key)
    assert app.session is not None
    assert app.session.is_complete
    assert "reset" in app.completed
    assert "autosave" not in shell.store or "42" in shell.store["autosave"]
    app.stop_lesson()
    assert app.state.display().text() == "42"  # the student's work is back
    page.drop_tasks()


def test_back_and_skip() -> None:
    app, _, page = started()
    app.lesson_index = [lesson.id for lesson in app.lessons].index("fractions")
    app.start_lesson()
    app.lesson_skip()
    app.lesson_skip()
    assert app.state.display().text() == "2⌟□"
    app.lesson_back()
    assert app.state.display().text() == "□⌟□"
    page.drop_tasks()


def test_show_me_plays_the_lesson(monkeypatch: pytest.MonkeyPatch) -> None:
    """FR-FX-TUT-005: Show me presses the keys itself."""
    monkeypatch.setattr(ui, "DEMO_STEP", 0.0)
    monkeypatch.setattr(ui, "DEMO_NEW_STEP", 0.0)
    app, _, page = started()
    app.set_tutorial_mode("show")
    app.lesson_index = [lesson.id for lesson in app.lessons].index("prime")
    app.start_lesson()
    page.drop_tasks()  # the playback the button scheduled; run it directly
    asyncio.run(app._play())
    page.drop_tasks()
    assert app.state.answer_text() == "2×3×5²×7"


def test_test_me() -> None:
    """FR-FX-TUT-005: no glow; Check says right or wrong."""
    app, _, page = started()
    app.set_tutorial_mode("test")
    app.lesson_index = [lesson.id for lesson in app.lessons].index("prime")
    app.start_lesson()
    assert app._target_key() is None
    app.check_test()
    assert not app.feedback_ok
    for key in ("3", "6", "0", k.EQ, k.SHIFT, k.DMS):
        app.on_key(key)
    app.check_test()
    assert app.feedback_ok
    assert "prime" in app.completed
    page.drop_tasks()


def test_dialogs_open() -> None:
    app, _, page = started()
    for opener in (app.open_settings, app.open_appearance, app.open_shortcuts, app.save_file_as):
        opener()
    assert len(page.dialogs) == 4


def test_appearance_chooses_a_calculator() -> None:
    """FR-FX-UI-005: the choice draws that calculator's keys, switches a linear calculator's
    display, and is remembered."""
    app, shell, page = started()
    app.set_layout("el531")
    assert app.shown_layout.id == "el531"
    assert "SETUP" in app.key_controls  # the SET UP key
    assert app.state.setup.input == "line"
    assert json.loads(shell.store["prefs"])["layout"] == "el531"
    again, _, page2 = started(store=shell.store)
    assert again.layout.id == "el531"
    assert "SETUP" in again.key_controls
    page.drop_tasks()
    page2.drop_tasks()


def test_layout_keys_type_on_the_calculator() -> None:
    app, _, page = started()
    app.set_layout("sx2")
    app.on_layout_key(app.layout.key("FACTORIAL"))  # x! has its own key here
    assert app.state.display().text() == "!"
    app.on_key(k.AC)
    for key_id in ("5", "FACTORIAL", k.EQ):
        app.on_layout_key(app.layout.key(key_id))
    assert app.state.answer_text() == "120"
    page.drop_tasks()


def test_guide_me_on_another_keypad() -> None:
    """FR-FX-TUT-001 to -003: the glow, the wording and the checks follow the chosen keys."""
    app, _, page = started()
    app.set_layout("sx2")
    app.lesson_index = 0  # reset: SHIFT 9 3 = AC
    app.start_lesson()
    assert app.shown_layout.id == "sx2"
    assert app._target_face() == "2nd"
    app.on_layout_key(app.layout.key("7"))
    assert not app.feedback_ok
    assert "2nd" in app.feedback
    app.on_layout_key(app.layout.key("SHIFT"))
    assert app._target_face() == "9"
    for key_id in ("9", "3", k.EQ, k.AC):
        app.on_layout_key(app.layout.key(key_id))
    assert app.session is not None
    assert app.session.is_complete
    page.drop_tasks()


def test_a_modifier_waits_for_the_next_key() -> None:
    """On the EL-531, 2ndF then x² is x⁻¹: the lesson only judges the pair."""
    app, _, page = started()
    app.set_layout("el531")
    app.on_layout_key(app.layout.key("SHIFT"))
    assert app.pending == [k.SHIFT]
    app.on_layout_key(app.layout.key(k.X2))
    assert app.pending == []
    assert app.state.display().text() == "⁻¹"
    page.drop_tasks()


def test_a_calculator_offers_only_its_own_lessons() -> None:
    """FR-FX-UI-005: the HP 10s has no TABLE, so it has no TABLE lesson; its lessons use its keys
    and stay on them."""
    app, _, page = started()
    app.lesson_index = [lesson.id for lesson in app.lessons].index("stddev")
    app.set_layout("hp10s")
    assert "table" not in [lesson.id for lesson in app.lessons]
    assert app.lesson.id == "stddev"  # the same lesson, in the HP's keys
    app.start_lesson()
    assert app.shown_layout.id == "hp10s"
    assert app._target_face() == "MODE"
    page.drop_tasks()


# Test me for "reset" on each calculator, by its keypad (canonical keys, planned on the layout)
# and by the computer keyboard. The EL-531's M-CLR has no keyboard shortcut.
RESET_BY_KEYPAD = {
    "casio": [k.SHIFT, "9", "1", k.EQ, k.AC],
    "sx2": [k.SHIFT, "9", "1", k.EQ, k.AC],
    "ms": [k.SHIFT, k.MODE, "2", k.EQ],
    "sharp": ["MCLR", "0"],
}
RESET_BY_KEYBOARD = {
    "casio": ["F1", "9", "1", "Enter", "Escape"],
    "sx2": ["F1", "9", "1", "Enter", "Escape"],
    "ms": ["F1", ("m", {"ctrl": True}), "2", "Enter"],
}


@pytest.mark.parametrize("layout", LAYOUTS, ids=lambda layout: layout.id)
@pytest.mark.parametrize("how", ["keypad", "keyboard"])
def test_reset_test_passes_on_every_calculator_by_keypad_or_keyboard(layout, how: str) -> None:
    """Test me for "reset" is judged on the calculator, not the keys: it passes on every
    calculator (a linear one resets to LineIO), whether the keys are clicked or typed."""
    if how == "keyboard" and layout.dialect not in RESET_BY_KEYBOARD:
        pytest.skip("M-CLR has no keyboard shortcut")
    app, _, page = started()
    app.set_layout(layout.id)
    app.set_tutorial_mode("test")
    app.lesson_index = [lesson.id for lesson in app.lessons].index("reset")
    app.start_lesson()
    assert float(app.state.variables["A"]) == 5  # the test's own starting mess
    app.check_test()
    assert not app.feedback_ok
    if how == "keyboard":
        for name in RESET_BY_KEYBOARD[layout.dialect]:
            key, mods = name if isinstance(name, tuple) else (name, {})
            keyboard(app, key, **mods)
    else:
        steps = layouts.plan(app.shown_layout, RESET_BY_KEYPAD[layout.dialect])
        assert steps is not None
        for step in steps:
            for key in step.presses:
                app.on_layout_key(key)
    app.check_test()
    assert app.feedback_ok, (layout.id, how, app.feedback)
    page.drop_tasks()


def _texts(control: object) -> list[str]:
    found = []
    if isinstance(control, ft.Text) and isinstance(control.value, str):
        found.append(control.value)
    for name in ("content", "controls"):
        child = getattr(control, name, None)
        for item in child if isinstance(child, list) else [child] if child is not None else []:
            found.extend(_texts(item))
    return found


@pytest.mark.parametrize(
    ("layout_id", "title"),
    [("fx82", "fx-82"), ("sx2", "SX-II"), ("el531", "EL-531"), ("hp10s", "10s")],
)
def test_calculator_title_names_the_series(layout_id: str, title: str) -> None:
    """The title on the calculator names the class of calculator its keys follow."""
    app, _, page = started()
    app.set_layout(layout_id)
    assert f"CASSim Scientific ({title})" in _texts(app.calculator)
    page.drop_tasks()


def test_model_chip_and_title_cycle_the_calculators() -> None:
    """The model chip in the menu bar, and the title on the calculator, step through the
    calculators in the Appearance list and back to the first."""
    app, _, page = started()
    assert app.model_label.value == "fx-82"
    seen = []
    for _ in LAYOUTS:
        app.model_chip.on_click(None)
        seen.append(app.layout.id)
    assert seen == [layout.id for layout in (*LAYOUTS[1:], LAYOUTS[0])]
    title = app.calculator.content.controls[0].controls[0]
    title.on_click(None)
    assert app.layout.id == LAYOUTS[1].id
    assert app.model_label.value == LAYOUTS[1].series
    assert f"CASSim Scientific ({LAYOUTS[1].series})" in _texts(app.calculator)
    page.drop_tasks()
