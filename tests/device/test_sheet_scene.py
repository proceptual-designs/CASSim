# Requirements traced here: FR-SHEET-001, FR-GRAPH-006, NFR-PERF-006
"""The sheet grid as a scene (slice 3b): layers, alignment, clipping, the cursor and taps."""

from cassim.device.keys import Binding
from cassim.devices.nspire.pages.spreadsheet import FORMULA_ROW, NAME_ROW, Spreadsheet
from cassim.devices.nspire.sheet_scene import (
    FORMULA,
    HEAD,
    ROW,
    ROW_LABELS,
    SLIVER,
    cell_at,
    fit,
    sheet_scene,
)
from cassim.devices.nspire.ui.state import AppState
from cassim.graph.scene import Align, Box, Fill, Label, Segments

W, H = 320.0, 200.0


def sheet_with(*values: str) -> tuple[AppState, Spreadsheet]:
    state = AppState()
    state.run_action("add_page", "spreadsheet")
    sheet = state.sheet
    assert sheet is not None
    for value in values:
        state.run(Binding("insert", value))
        state.run(Binding("enter"))
    state.prepare()
    return state, sheet


def labels(scene, layer):
    found = scene.layer(layer)
    assert found is not None
    return [shape for shape in found.shapes if isinstance(shape, Label)]


def test_layers_and_one_label_a_column_side():
    _, sheet = sheet_with("5", "abc", "7")
    scene = sheet_scene(sheet.screen(), 1.0, W, H)
    assert [layer.name for layer in scene.layers] == ["grid", "heads", "cells", "cursor"]
    cells = labels(scene, "cells")
    assert [(label.align, label.text) for label in cells] == [
        (Align.LEFT, "\nabc\n\n\n\n"),  # five rows and a sixth, part hidden
        (Align.RIGHT, "5\n\n7\n\n\n"),
    ]
    assert cells[0].line_height == ROW


def test_heads_show_letters_names_and_formulas():
    state, sheet = sheet_with("1")
    sheet.go((1, NAME_ROW))
    state.run(Binding("insert", "sq"))
    state.run(Binding("enter"))
    sheet.go((1, FORMULA_ROW))
    state.run(Binding("insert", "=a[]^2"))
    state.run(Binding("enter"))
    state.prepare()
    heads = [label.text for label in labels(sheet_scene(sheet.screen(), 1.0, W, H), "heads")]
    assert heads[:3] == ["A", "B sq", "=a[]^2"]
    assert heads[-1] == "1\n2\n3\n4\n5\n6"


def test_long_text_is_cut_with_dots():
    """Check 6, E13: `123456789012345` in a narrow column shows `1234...`."""
    _, sheet = sheet_with("123456789012345")
    text = labels(sheet_scene(sheet.screen(), 1.0, W, H), "cells")[0].text.split("\n")[0]
    assert text.endswith("...")
    assert len(text) < 15


def test_a_cursor_move_changes_only_the_cursor_layer():
    """Spike A: the cursor is its own layer, so a move sends no text."""
    _, sheet = sheet_with("1", "2")
    before = sheet_scene(sheet.screen(), 1.0, W, H)
    sheet.go((0, 1))
    after = sheet_scene(sheet.screen(), 1.0, W, H)
    changed = [a.name for a, b in zip(before.layers, after.layers, strict=True) if a != b]
    assert changed == ["cursor"]


def test_the_cursor_selection_and_typing_are_drawn():
    state, sheet = sheet_with("1", "2")
    sheet.go((0, 1))
    state.run(Binding("select_cells", "row:1"))
    shapes = sheet_scene(sheet.screen(), 1.0, W, H).layer("cursor")
    assert shapes is not None
    assert [type(shape) for shape in shapes.shapes] == [Fill, Box]
    state.run(Binding("escape"))
    state.run(Binding("insert", "42"))
    cursor = sheet_scene(sheet.screen(), 1.0, W, H).layer("cursor")
    assert cursor is not None
    assert any(isinstance(s, Label) and s.text == "42|" for s in cursor.shapes)


def test_the_fill_range_is_dashed():
    state, sheet = sheet_with("1")
    sheet.go((0, 1))
    state.run(Binding("sheet", "fill"))
    state.run(Binding("down"))
    cursor = sheet_scene(sheet.screen(), 1.0, W, H).layer("cursor")
    assert cursor is not None
    assert any(isinstance(s, Box) and s.stroke.dashed for s in cursor.shapes)


def test_formula_reference_is_outlined_without_moving_the_edit_cursor():
    state, sheet = sheet_with()
    sheet.go((1, 1))
    state.run(Binding("insert", "="))
    state.run(Binding("left"))
    cursor = sheet_scene(sheet.screen(), 1.0, W, H).layer("cursor")
    assert cursor is not None
    assert any(isinstance(s, Box) and s.stroke.dashed for s in cursor.shapes)
    assert any(isinstance(s, Label) and s.text == "=a1|" for s in cursor.shapes)


def test_a_cursor_off_screen_draws_no_box():
    _, sheet = sheet_with()
    sheet.cursor = (25, 1)  # not scrolled into view
    cursor = sheet_scene(sheet.screen(), 1.0, W, H).layer("cursor")
    assert cursor is not None
    assert cursor.shapes == ()


def test_taps_map_to_cells():
    _, sheet = sheet_with()
    screen = sheet.screen()
    x = ROW_LABELS + 5
    assert cell_at(x, 2, screen, 1.0) == (0, NAME_ROW)
    assert cell_at(x, HEAD + 2, screen, 1.0) == (0, FORMULA_ROW)
    assert cell_at(x, HEAD + FORMULA + ROW + 2, screen, 1.0) == (0, 2)
    assert cell_at(2, HEAD + FORMULA + 2, screen, 1.0) == (-1, 1)  # a row number
    assert cell_at(2, 2, screen, 1.0) is None
    assert cell_at(x, H * 5, screen, 1.0) is None
    assert cell_at(W * 5, HEAD + FORMULA + 2, screen, 1.0) is None


def test_fit_counts_rows_and_columns_at_a_scale():
    _, sheet = sheet_with()
    assert fit(320, HEAD + FORMULA + 5 * ROW, sheet, 1.0) == (5, 4)
    assert fit(640, 2 * (HEAD + FORMULA + 5 * ROW), sheet, 2.0) == (5, 4)
    sheet.widths[0] = 1000
    assert fit(320, 200, sheet, 1.0)[1] == 1  # one column always shows


def test_a_part_hidden_row_and_column_hint_at_more():
    _, sheet = sheet_with()
    screen = sheet.screen()
    assert screen.rows == (1, 2, 3, 4, 5, 6)
    assert [c for c, *_ in screen.columns] == [0, 1, 2, 3, 4]
    assert screen.sliver is None
    grid = sheet_scene(screen, 1.0, W, H).layer("grid")
    assert grid is not None
    lines = next(s for s in grid.shapes if isinstance(s, Segments))
    assert max(x for x, _ in lines.points) == W  # the fifth column runs off the right edge


def test_a_sliver_of_the_column_off_to_the_left():
    """Check 6, E13: scrolled right, a sliver of the column to the left still shows."""
    _, sheet = sheet_with()
    sheet.go((7, 1))  # H: the view scrolls right
    screen = sheet.screen()
    assert screen.sliver == sheet.left - 1
    row1 = HEAD + FORMULA + 2
    assert cell_at(ROW_LABELS + SLIVER / 2, row1, screen, 1.0) == (screen.sliver, 1)
    first = screen.columns[0][0]
    assert cell_at(ROW_LABELS + SLIVER + 5, row1, screen, 1.0) == (first, 1)
    heads = labels(sheet_scene(screen, 1.0, W, H), "heads")
    assert heads[0].text == screen.columns[0][1]  # the sliver has no text
    assert fit(285, 200, sheet, 1.0)[1] == 3  # the sliver takes room from the whole columns
    sheet.go((0, 1))
    assert fit(285, 200, sheet, 1.0)[1] == 4  # without it, four fit
