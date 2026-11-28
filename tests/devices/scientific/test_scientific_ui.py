"""The CASSim Scientific view, run headless against a stand-in shell.

Requirements: FR-FX-DSP-001, FR-FX-DSP-002, FR-FX-SHR-001, FR-FX-SHR-002, FR-FX-TUT-001,
FR-FX-TUT-002, FR-FX-TUT-005, FR-FX-UI-001 to -004, FR-FX-UI-007 (phones).
Cited: FR-FX-UI-001 FR-FX-UI-002 FR-FX-UI-003 FR-FX-UI-004 FR-FX-UI-007 FR-FX-TUT-003.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable, Coroutine
from types import SimpleNamespace
from typing import Any

import flet as ft
import flet.canvas as cv
import pytest

from cassim.app.appearance import APPEARANCE_KEY, Appearance, load_appearance
from cassim.app.shell import BrowserOffers, Shell
from cassim.app.sizes import DIALOG_MARGIN
from cassim.app.theme import THEMES, contrast
from cassim.devices.scientific import keys as k
from cassim.devices.scientific import layouts
from cassim.devices.scientific.examples import EXAMPLES
from cassim.devices.scientific.layout import Frac, Sqrt, Text
from cassim.devices.scientific.layouts import LAYOUTS
from cassim.devices.scientific.state import ScientificState
from cassim.devices.scientific.ui import app as ui
from cassim.devices.scientific.ui import render
from cassim.devices.scientific.ui.app import BASE_WIDTH, PANEL_WIDTH, ScientificApp
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
        self.shared: dict[str, str] = {}  # shell-wide keys, such as the shared theme
        self.appearance = Appearance()
        self.appearance_saved = False

    async def read(self, key: str) -> str | None:
        return self.store.get(key)

    async def load_appearance(self) -> str:
        async def read_global(key: str) -> str | None:
            return self.shared.get(key)

        loaded = await load_appearance(read_global)
        self.appearance, self.appearance_saved = loaded.appearance, loaded.saved
        return loaded.error

    def save_appearance(self, appearance: Appearance) -> None:
        self.appearance, self.appearance_saved = appearance, True
        self.shared[APPEARANCE_KEY] = appearance.dumps()

    def write(self, key: str, text: str) -> None:
        self.store[key] = text

    def remove(self, key: str) -> None:
        self.store.pop(key, None)

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

    share_link = Shell.share_link  # the real dialog, on this shell's page

    def help(self, page: str = "") -> None: ...
    def about(self) -> None: ...
    def activate_update(self) -> None: ...


def started(
    page: FakePage | None = None,
    route: str = "",
    store: dict[str, str] | None = None,
    shared: dict[str, str] | None = None,
):
    page = page or FakePage()
    shell = FakeShell(page, route)
    shell.store.update(store or {})
    shell.shared.update(shared or {})
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
    small, _, _ = started(FakePage(360, 500))  # a phone: smaller keys rather than scrolling
    assert small.layout_height() * small.scale <= 500 - ui.BAR_HEIGHT
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
    assert app.state.display().text() == "2⌟3+√2\n2.080880229"  # surds are decimals
    keyboard(app, "c", ctrl=True)
    assert shell.copied == ["2.080880229"]
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
    for key in (k.MODE, "3", "2"):
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
def test_appearance_follows_the_shared_theme(name: str) -> None:
    """SDD-15 section 7.1: the theme chosen in any app (or on Home) is the one drawn here,
    and the page, bar and chips use the shared theme's colours."""
    app, shell, page = started()
    dialog = app.open_appearance()
    dialog.select(name)
    assert page.bgcolor == THEMES[name].background  # previewed before Save
    dialog.save.on_click(None)
    assert json.loads(shell.shared[APPEARANCE_KEY])["theme_name"] == name
    assert "theme" not in json.loads(shell.store["prefs"])
    again, _, page2 = started(shared=shell.shared)
    assert page2.bgcolor == THEMES[name].background
    assert again.appearance.theme_name == name
    assert again.skin.lcd == SKINS[name].lcd  # the calculator keeps its own colours
    page.drop_tasks()
    page2.drop_tasks()


def test_cancel_puts_the_saved_theme_back() -> None:
    app, shell, page = started()
    dialog = app.open_appearance()
    dialog.select("Light")
    assert page.bgcolor == THEMES["Light"].background
    dialog.cancel.on_click(None)
    assert page.bgcolor == THEMES["Dark"].background
    assert APPEARANCE_KEY not in shell.shared
    page.drop_tasks()


def test_an_older_scientific_theme_becomes_the_shared_one_once() -> None:
    """Before SDD-15 this app saved its own theme; with no shared theme saved, it is kept."""
    store = {"prefs": json.dumps({"theme": "Light"})}
    app, shell, page = started(store=store)
    assert app.appearance.theme_name == "Light"
    assert json.loads(shell.shared[APPEARANCE_KEY])["theme_name"] == "Light"
    shared = {APPEARANCE_KEY: Appearance("High contrast").dumps()}
    again, _, page2 = started(store=store, shared=shared)
    assert again.appearance.theme_name == "High contrast"  # a shared choice wins
    page.drop_tasks()
    page2.drop_tasks()


@pytest.mark.parametrize("name", list(THEMES))
def test_light_menu_bar_follows_the_theme(name: str) -> None:
    """SDD-15 gap 17: the bar was dark even in Light."""
    app, _, page = started(shared={APPEARANCE_KEY: Appearance(name).dumps()})
    assert app.top_bar.bgcolor == THEMES[name].background
    assert contrast(app.skin.bar_text, app.top_bar.bgcolor) >= 4.5
    page.drop_tasks()


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


def save_under(page: FakePage, name: str) -> None:
    """Type `name` into the Save as dialog and press Save."""
    dialog: Any = page.dialogs[-1]
    dialog.content.controls[1].value = name
    dialog.actions[-1].on_click(None)  # Save, last (Material order)
    page.run_tasks()


def test_open_and_save_use_app_storage_and_files_are_import_and_export() -> None:
    """FR-FX-SHR-006, FR-DOC-010 (decision 0033): Save and Open keep calculations by name in
    the app's storage; only Import file and Export file touch a file on disk."""
    app, shell, page = started()
    labels = [
        "|" if isinstance(item, ft.Divider) else str(getattr(item, "content", ""))
        for item in app.doc_menu.controls
    ]
    assert labels[:9] == [
        "New",
        "Open…",
        "Save",
        "Save as…",
        "|",
        "Import file…",
        "Export file…",
        "Share link…",
        "|",
    ]  # SDD-15 section 9.4
    assert not app.saved.dirty()  # a first visit has nothing to lose
    for key in ("5", k.EQ):
        app.on_key(key)
    assert app.saved.dirty()
    app.open_share_link()
    assert page.dialogs

    app.save()  # never saved: asks for a name
    save_under(page, "Homework")
    assert not shell.saved  # nothing was downloaded
    assert "doc:Homework" in shell.store
    assert shell.notices[-1][0] == "Saved"
    assert app.doc_name == "Homework"
    assert not app.saved.dirty()

    for key in (k.AC, "9", k.EQ):
        app.on_key(key)
    app.save_as()
    save_under(page, "Other")
    app.open_saved()  # the saved calculations, newest first
    rows: Any = page.dialogs[-1]
    assert [row.title.value for row in rows.content.controls] == ["Other", "Homework"]
    rows.content.controls[1].on_click(None)
    page.run_tasks()
    assert app.doc_name == "Homework"
    assert app.state.answer_text() == "5"

    asyncio.run(app.export_file())
    name, text = shell.saved[-1]
    assert name == "Homework.cassim.json"

    shell.picked = text.replace('"Homework"', '"From a file"')
    app.import_file()
    page.run_tasks()
    assert app.doc_name == "From a file"
    assert app.saved.current.stored is None  # an imported file is saved nowhere here yet
    assert app.state.answer_text() == "5"
    shell.picked = json.dumps({"format": "cassim-document", "schema": 5, "device": "nspire"})
    app.import_file()
    page.run_tasks()
    assert "nspire" in shell.notices[-1][1]
    page.drop_tasks()


def test_the_saved_name_survives_a_reload() -> None:
    """FR-FX-SHR-001, FR-DOC-010: the autosave keeps which saved calculation is open."""
    app, shell, page = started()
    app.on_key("5")
    app.save()
    save_under(page, "Homework")
    again, _, other_page = started(store=shell.store)
    assert again.doc_name == "Homework"
    assert again.saved.name == "Homework"
    page.drop_tasks()
    other_page.drop_tasks()


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
    for opener in (app.open_settings, app.open_appearance, app.open_shortcuts, app.save_as):
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


def menu_item(app: ScientificApp, label: str) -> Any:
    """The CASSim menu's item with `label`, or None."""
    return next(
        (
            c
            for c in app.cassim_menu.controls
            if isinstance(c, ft.MenuItemButton) and c.content == label
        ),
        None,
    )


def mark(item: Any) -> str:
    """The ✓ or ● drawn before a menu item's label ("" when off)."""
    return item.leading.content.value


def test_a_phone_hides_the_tutorials_and_fills_the_screen() -> None:
    """On a phone the tutorials start hidden (whatever was saved), the calculator fills the
    width and its keys grow to use the height; CASSim ▸ Show tutorials brings them back below."""
    store = {"prefs": json.dumps({"panel": True})}
    app, shell, page = started(FakePage(390, 844), store=store)
    assert app.phone
    assert not app.panel_open
    assert not app.panel.visible
    assert app.calculator.width == pytest.approx(390 - 8, abs=2)  # the width, less a thin margin
    assert app.stretch > 1.2
    assert not app.angle_chip.visible
    assert not app.panel_button.visible
    assert mark(menu_item(app, "Tutorials")) == ""  # SDD-15 section 6: ✓ when shown
    menu_item(app, "Tutorials").on_click(None)
    assert app.panel_open
    assert app.panel.visible
    assert app.stretch == 1.0  # room for the tutorials below the calculator
    assert mark(menu_item(app, "Tutorials")) == "✓"
    assert json.loads(shell.store["prefs"])["panel"] is True  # a phone keeps the saved choice
    page.drop_tasks()


def test_tutorials_show_and_hide_from_the_menu_on_a_computer() -> None:
    app, shell, page = started()
    assert not app.phone
    assert app.panel_open
    assert mark(menu_item(app, "Tutorials")) == "✓"
    menu_item(app, "Tutorials").on_click(None)
    assert not app.panel.visible
    assert mark(menu_item(app, "Tutorials")) == ""
    assert json.loads(shell.store["prefs"])["panel"] is False
    page.drop_tasks()


def test_an_installed_phone_can_avoid_the_cutout() -> None:
    """As in the Nspire app: an installed phone draws under the camera cutout until CASSim ▸
    Avoid cutout keeps the calculator inside the safe area."""
    app, shell, page = started(FakePage(390, 844))
    assert menu_item(app, "Avoid cutout") is None  # not installed: Fullscreen instead
    assert menu_item(app, "Fullscreen") is not None
    shell.offers = BrowserOffers(installed=True, safe_area=(40, 0, 20, 0))
    app.on_bridge()
    item = menu_item(app, "Avoid cutout")
    assert item is not None
    assert mark(item) == ""
    assert app.root.padding.top == 0
    item.on_click(None)
    assert mark(menu_item(app, "Avoid cutout")) == "✓"
    assert app.root.padding.top == 40
    assert app.root.padding.bottom == 20
    page.drop_tasks()


# ---- phones (simulated): the app laid out at real phone sizes -------------------------------

PHONES = {
    "small-360x640": (360, 640),
    "iphone-390x844": (390, 844),
    "pixel-412x915": (412, 915),
    "landscape-844x390": (844, 390),
}


def _walk(control: object):
    yield control
    for name in ("content", "controls", "actions", "title"):
        child = getattr(control, name, None)
        for item in child if isinstance(child, list) else [child] if child is not None else []:
            if isinstance(item, ft.Control):
                yield from _walk(item)


def _too_wide(dialog: ft.AlertDialog, room: float) -> list[str]:
    """What in a dialog would run off a screen `room` wide: a fixed width over it, a row of
    radio buttons that cannot wrap, or a radio label (they do not wrap) longer than fits."""
    problems = []
    for control in _walk(dialog.content):
        fixed = getattr(control, "width", None)
        if isinstance(fixed, (int, float)) and fixed > room + 0.5:
            problems.append(f"{type(control).__name__} width {fixed} > {room}")
        if isinstance(control, ft.Row) and not control.wrap:
            radios = [c for c in control.controls if isinstance(c, ft.Radio)]
            if len(radios) > 1:
                problems.append(f"a row of {len(radios)} radios that cannot wrap")
        if isinstance(control, ft.Radio) and control.label:
            label = control.label if isinstance(control.label, str) else ""
            if 48 + len(label) * ui.DIALOG_TEXT * 0.55 > room:
                problems.append(f"radio label {label!r} is too long")
    return problems


@pytest.mark.parametrize("size", PHONES.values(), ids=PHONES.keys())
@pytest.mark.parametrize("layout", LAYOUTS, ids=lambda layout: layout.id)
def test_phone_calculator_fits_the_screen(size: tuple[int, int], layout) -> None:
    """On a phone the calculator fills the width without running past it, and with the
    tutorials hidden all of it fits the height."""
    app, _, page = started(FakePage(*size))
    app.set_layout(layout.id)
    width, height = size
    drawn = BASE_WIDTH * app.scale
    assert drawn <= width - 4
    tall = (app.layout_height() + (app.stretch - 1) * app.key_height()) * app.scale
    assert tall <= height - ui.BAR_HEIGHT + 1
    # it fills the width, or (a short or landscape screen) the height
    assert drawn >= width - 16 or tall >= height - ui.BAR_HEIGHT - 30
    page.drop_tasks()


@pytest.mark.parametrize("size", PHONES.values(), ids=PHONES.keys())
@pytest.mark.parametrize("dialog", ["settings", "appearance", "shortcuts", "share"])
def test_phone_dialogs_fit_the_screen(size: tuple[int, int], dialog: str) -> None:
    """Every dialog fits a phone: the settings once had a 420 px column and rows of radio
    buttons with long labels, which ran off the screen."""
    app, _, page = started(FakePage(*size))
    for key in ("1", k.ADD, "2", k.EQ):
        app.on_key(key)
    {
        "settings": app.open_settings,
        "appearance": app.open_appearance,
        "shortcuts": app.open_shortcuts,
        "share": app.open_share_link,
    }[dialog]()
    shown = page.dialogs[-1]
    assert isinstance(shown, ft.AlertDialog)
    room = size[0] - DIALOG_MARGIN
    assert _too_wide(shown, room) == []
    page.drop_tasks()


def test_phone_settings_change_the_decimal_point() -> None:
    app, _, page = started(FakePage(390, 844))
    app.open_settings()
    dialog = page.dialogs[-1]
    groups = [c for c in _walk(dialog.content) if isinstance(c, ft.RadioGroup)]
    point = next(g for g in groups if g.value in ("dot", "comma"))
    point.value = "comma"
    apply = next(b for b in dialog.actions if isinstance(b, ft.TextButton) and b.content == "Apply")
    apply.on_click(None)
    assert app.state.setup.comma
    page.drop_tasks()


# ---- the natural display's drawing --------------------------------------------------------


def test_square_root_is_one_stroke_that_reaches_its_vinculum() -> None:
    """√ is drawn as one path, the sign then the vinculum, sized to the argument: the √
    character and a separate line did not meet, least of all over a fraction."""
    renderer = render.Renderer("#000", "#000")
    for arg in ((Text("8"),), (Frac((Text("1"),), (Text("2"),)),)):
        drawn = renderer.node(Sqrt(arg), 20)
        assert isinstance(drawn, cv.Canvas)
        path = drawn.shapes[0]
        assert isinstance(path, cv.Path)
        points = [
            (e.x, e.y) for e in path.elements if isinstance(e, (cv.Path.MoveTo, cv.Path.LineTo))
        ]
        sign_top, line_end = points[-2], points[-1]
        assert sign_top[1] == line_end[1]  # the sign's top is where the vinculum starts
        assert line_end[0] == drawn.width == render.node_width(Sqrt(arg), 20)
        assert points[2][1] > (drawn.height or 0) * 0.9  # the stroke reaches the baseline
    tall = renderer.node(Sqrt((Frac((Text("1"),), (Text("2"),)),)), 20)
    short = renderer.node(Sqrt((Text("8"),)), 20)
    assert isinstance(tall, cv.Canvas)
    assert isinstance(short, cv.Canvas)
    assert (tall.height or 0) > (short.height or 0)  # the sign grows with a fraction under it


def test_mixed_number_answer_is_spaced_like_the_entry() -> None:
    """The answer 1 3/4 had a whole character's space before the fraction; it now has the
    small gap the typed mixed number has."""
    answer = (Text("1 "), Frac((Text("3"),), (Text("4"),)))
    typed = (Text("1"), Frac((Text("3"),), (Text("4"),)))
    gap = render.width(answer, 20) - render.width(typed, 20)
    assert gap == pytest.approx(render.MIXED_GAP * 20)
    assert gap == 0  # the fraction follows the whole part directly, as in the entry


def test_new_clears_the_calculation_and_keeps_the_settings() -> None:
    """SDD-15 section 9.4: Doc > New clears memories and the entry but keeps SETUP (Reset all
    clears those too), and asks first when the work is unsaved."""
    app, shell, page = started()
    asked: list[str] = []
    shell.confirm = lambda title, _m, _a, accept: (asked.append(title), asyncio.run(accept()))
    app.cycle_angle()  # Rad
    for key in ("7", k.MPLUS, "2", k.ADD, "3", k.EQ):
        app.on_key(key)
    app.new_calculation()
    assert asked == ["Discard changes?"]
    assert app.state.setup.angle == "RAD"  # kept
    assert float(app.state.variables["M"]) == 0  # cleared
    assert app.state.display().text() == ""
    page.drop_tasks()


def test_an_example_asks_before_replacing_unsaved_work() -> None:
    app, shell, page = started()
    asked: list[str] = []
    shell.confirm = lambda title, _m, _a, _accept: asked.append(title)
    for key in ("1", k.ADD, "2", k.EQ):
        app.on_key(key)
    before = app.state.display().text()
    app.load_example(0)
    assert asked == ["Discard changes?"]
    assert app.state.display().text() == before
    page.drop_tasks()


# ---- CASSim extras and the hyp key (decision 0041, FR-FX-UI-008) --------------------------


def _face(app: ScientificApp, key_id: str) -> str:
    content = app.key_controls[key_id].content
    assert isinstance(content, ft.Text)
    return str(content.value)


def test_hyp_lights_and_renames_the_trig_keys() -> None:
    """FR-FX-UI-008: while hyp waits it is lit and sin, cos, tan read sinh, cosh, tanh (their
    SHIFT legends too); a setting turns the names off; hyp is not lit afterwards."""
    app, _, page = started()
    plain_fill = app.key_controls[k.HYP].bgcolor
    app.on_key(k.HYP)
    assert app.state.hyp_waiting
    assert app.key_controls[k.HYP].bgcolor != plain_fill
    assert [_face(app, key) for key in (k.SIN, k.COS, k.TAN)] == ["sinh", "cosh", "tanh"]
    assert app.legend_controls[k.SIN].value == "sinh⁻¹"
    app.on_key(k.SIN)  # picks sinh from the menu
    assert not app.state.hyp_waiting
    assert _face(app, k.SIN) == "sin"
    assert app.legend_controls[k.SIN].value == "sin⁻¹"
    assert app.key_controls[k.HYP].bgcolor == plain_fill
    app.hyp_names = False
    app.on_key(k.AC)
    app.on_key(k.HYP)
    assert _face(app, k.SIN) == "sin"  # still lit, but the names stay
    assert app.key_controls[k.HYP].bgcolor != plain_fill
    page.drop_tasks()


def test_settings_extras_are_remembered() -> None:
    """Exact surds go in the calculation's SETUP; TABLE and the hyp names are remembered in this
    browser, and TABLE joins the MODE menu as 4."""
    app, shell, page = started()
    app.open_settings()
    dialog = page.dialogs[-1]
    switches = {c.label: c for c in _walk(dialog.content) if isinstance(c, ft.Switch)}
    switches["Exact surds and π in MathO answers"].value = True
    switches["TABLE mode (MODE 4)"].value = True
    switches["Show sinh, cosh and tanh on the keys after hyp"].value = False
    apply = next(b for b in dialog.actions if isinstance(b, ft.TextButton) and b.content == "Apply")
    apply.on_click(None)
    assert app.state.setup.surds
    assert app.state.allowed_modes[-1] == "TABLE"
    prefs = json.loads(shell.store["prefs"])
    assert prefs["table"] is True
    assert prefs["hyp_names"] is False
    assert "table" in [lesson.id for lesson in app.lessons]
    page.drop_tasks()
    again, _, page = started(store=shell.store)
    assert again.extra_table
    assert not again.hyp_names
    page.drop_tasks()


def test_a_calculation_in_table_mode_switches_the_extra_on() -> None:
    """A shared or saved calculation in TABLE mode brings the TABLE extra with it."""
    sender = ScientificState(allowed_modes=("COMP", "STAT", "VERIFY", "TABLE"))
    for key in (k.MODE, "4", k.ALPHA, k.RPAREN, k.X2):
        sender.press(key)
    app, shell, page = started(route=f"/{sender.share_fragment()}")
    assert app.state.mode == "TABLE"
    assert app.extra_table
    assert "TABLE" in app.state.allowed_modes
    assert json.loads(shell.store["prefs"])["table"] is True
    page.drop_tasks()


def test_table_example_asks_for_the_extra() -> None:
    app, shell, page = started()
    index = next(i for i, (title, _) in enumerate(EXAMPLES) if title.startswith("Table"))
    app.load_example(index)
    assert shell.notices[-1] == (
        "Examples",
        "TABLE is an extra mode: switch it on in CASSim ▸ Settings first.",
    )
    page.drop_tasks()


def test_table_switched_off_in_table_mode_stays_off() -> None:
    """Switching the TABLE extra off while in TABLE mode goes back to COMP, so the extra does not
    switch itself on again."""
    app, shell, page = started()
    app.extra_table = True
    app.state.use_layout(
        app._modes(app.layout), linear=app.layout.linear, dialect=app.layout.dialect
    )
    for key in (k.MODE, "4"):
        app.state.press(key)
    assert app.state.mode == "TABLE"
    app.open_settings()
    dialog = page.dialogs[-1]
    switches = {c.label: c for c in _walk(dialog.content) if isinstance(c, ft.Switch)}
    switches["TABLE mode (MODE 4)"].value = False
    apply = next(b for b in dialog.actions if isinstance(b, ft.TextButton) and b.content == "Apply")
    apply.on_click(None)
    assert app.state.mode == "COMP"
    assert not app.extra_table
    assert "TABLE" not in app.state.allowed_modes
    assert json.loads(shell.store["prefs"])["table"] is False
    page.drop_tasks()


def test_reload_to_update_asks_about_an_unsaved_calculation() -> None:
    """SDD-15 section 5: Scientific tells the shell about unsaved work, and stops when left."""
    app, shell, page = started()
    assert shell.has_unsaved == app.saved.dirty
    app.unmount()
    assert shell.has_unsaved() is False
    page.drop_tasks()


def test_the_status_chips_take_taps_over_the_bars_height() -> None:
    """SDD-15 section 8.3: each chip is drawn small but takes taps across the bar's 48 px, and a
    tap there does what a tap on the chip does."""
    app, _, page = started()
    row = app.top_bar.content
    areas = [c for c in row.controls if isinstance(c, ft.Container) and c.content is app.mode_chip]
    assert len(areas) == 1
    assert areas[0].height == 48
    assert areas[0].on_click is app.mode_chip.on_click
    page.drop_tasks()


def test_a_phone_opens_in_handheld_upright_and_tablet_on_its_side() -> None:
    """SDD-15 sections 8.2 and 8.4: a phone follows its orientation; a computer opens in
    Computer view."""
    for size, view in (((390, 844), "handheld"), ((844, 390), "tablet"), ((1366, 650), "computer")):
        app, _, page = started(FakePage(*size))
        assert app.view == view
        page.drop_tasks()


def test_tablet_keeps_the_tutorials_beside_and_handheld_puts_them_below() -> None:
    """SDD-15 section 8.1: in the same window, the view decides where the tutorials go."""
    app, _, page = started(FakePage(1000, 700))
    app.set_view("tablet")
    assert app.body.wrap is False
    assert app.panel.width == PANEL_WIDTH
    beside = app.scale
    app.set_view("handheld")
    assert app.body.wrap is True
    assert app.panel.width > PANEL_WIDTH  # as wide as the window, so it wraps below
    assert app.scale >= beside  # the calculator no longer shares the width
    page.drop_tasks()


def test_the_views_are_in_the_cassim_menu_with_their_shortcuts() -> None:
    app, _, page = started()
    app.cassim_action("view:handheld")
    assert app.view == "handheld"
    keyboard(app, "t", alt=True, shift=True)  # Alt+Shift+T
    assert app.view == "tablet"
    app.cassim_action("view:computer")
    assert app.view == "computer"
    page.drop_tasks()
    phone, _, page = started(FakePage(390, 844))
    phone.cassim_action("view:computer")  # greyed on a phone
    assert phone.view == "handheld"
    page.drop_tasks()


def test_start_in_is_kept_and_used_next_time() -> None:
    app, shell, page = started()
    app.open_settings()
    dialog = page.dialogs[-1]
    start = next(
        c for c in _walk(dialog.content) if isinstance(c, ft.Dropdown) and c.label == "Start in"
    )
    start.value = "tablet"
    apply = next(b for b in dialog.actions if isinstance(b, ft.TextButton) and b.content == "Apply")
    apply.on_click(None)
    assert json.loads(shell.store["prefs"])["start"] == "tablet"
    page.drop_tasks()
    again, _, page = started(store=shell.store)
    assert again.view == "tablet"
    page.drop_tasks()
