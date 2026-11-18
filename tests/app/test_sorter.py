# Requirements traced here: FR-DOC-001
"""The page sorter (FR-DOC-001): drawn on the screen, so the Handheld keypad stays usable, and
worked by the arrows, Enter, Esc and Delete like the rest of the calculator."""

from __future__ import annotations

from cassim.devices.nspire.pages.calculator import calculator_of
from cassim.devices.nspire.ui.state import AppState
from cassim.stats.plots import PlotType


def _sorter(pages: tuple[int, ...]) -> AppState:
    """A document with these many pages in each Problem, at 1.1, with the sorter open."""
    state = AppState()
    document = state.document
    for number, count in enumerate(pages):
        if number:
            state.run_action("add_problem", "calculator")
        for _ in range(count - 1):
            state.run_action("add_page", "calculator")
    document.go(0, 0)
    state.key_event("ArrowUp", ctrl=True)
    assert state.sorting
    return state


def _here(state: AppState) -> tuple[int, int]:
    return state.document.problem + 1, state.document.page + 1


def test_ctrl_up_opens_the_sorter_on_the_screen() -> None:
    state = _sorter((2, 3))
    screen = state.screen()
    assert screen.sorter is not None
    assert [len(row) for row in screen.sorter] == [2, 3]
    assert [tile.current for row in screen.sorter for tile in row] == [True] + [False] * 4


def test_statistics_preview_shows_variables_and_plot_type() -> None:
    """FR-DOC-001: built Data & Statistics pages have useful sorter previews."""
    state = AppState()
    state.run_action("add_page", "statistics")
    statistics = state.statistics
    assert statistics is not None
    state.key_event("ArrowUp", ctrl=True)

    def preview() -> tuple[str, ...]:
        sorter = state.screen().sorter
        assert sorter is not None
        return sorter[0][1].lines

    assert preview() == ("Data & Statistics", "(no variables)", "Dot Plot")
    statistics.x_name = "time"
    assert preview() == ("Data & Statistics", "X: time", "Dot Plot")
    statistics.y_name = "distance"
    statistics.plot_type = PlotType.SCATTER
    assert preview() == ("Data & Statistics", "distance vs time", "Scatter Plot")
    statistics.x_name = ""
    assert preview() == ("Data & Statistics", "Y: distance", "Scatter Plot")


def test_left_and_right_go_through_the_pages_in_order() -> None:
    state = _sorter((2, 3))
    for _ in range(3):
        state.key_event("ArrowRight")
    assert _here(state) == (2, 2)
    state.key_event("ArrowLeft")
    assert _here(state) == (2, 1)


def test_up_and_down_change_problem_keeping_the_page_number() -> None:
    state = _sorter((2, 3))
    state.key_event("ArrowDown")
    assert _here(state) == (2, 1)
    state.key_event("ArrowRight")
    state.key_event("ArrowRight")
    state.key_event("ArrowUp")
    assert _here(state) == (1, 2)  # Problem 1 has only two pages
    state.key_event("ArrowUp")
    assert _here(state) == (1, 2)  # nothing above the first Problem


def test_enter_and_esc_close_it_on_the_highlighted_page() -> None:
    state = _sorter((3,))
    state.key_event("ArrowRight")
    state.key_event("Enter")
    assert not state.sorting
    assert _here(state) == (1, 2)
    assert state.screen().sorter is None
    state.key_event("ArrowUp", ctrl=True)
    state.key_event("Escape")
    assert not state.sorting


def test_the_keypad_works_the_sorter_too() -> None:
    state = _sorter((3,))
    state.press_keypad("right")
    state.press_keypad("del")
    assert len(state.document.problems[0].pages) == 2
    state.press_keypad("enter")
    assert not state.sorting


def test_delete_removes_the_page_and_undo_brings_it_back() -> None:
    state = _sorter((3,))
    state.key_event("ArrowRight")
    state.key_event("Delete")
    assert len(state.document.problems[0].pages) == 2
    assert state.sorting  # still sorting
    state.key_event("z", ctrl=True)
    assert len(state.document.problems[0].pages) == 3
    state.key_event("y", ctrl=True)
    assert len(state.document.problems[0].pages) == 2


def test_typing_does_nothing_while_sorting() -> None:
    state = _sorter((1,))
    state.key_event("5")
    state.key_event("Enter")  # closes the sorter: nothing was typed to calculate
    calculator = calculator_of(state.document.current)
    assert calculator is not None
    assert not calculator.history
    state.key_event("Enter")  # the entry line is still empty
    assert not calculator.history


def test_a_tap_highlights_a_tile_and_a_second_tap_opens_it() -> None:
    state = _sorter((2, 2))
    state.run_action("sorter_go", "1.1")
    assert (_here(state), state.sorting) == ((2, 2), True)
    state.run_action("sorter_go", "1.1")
    assert not state.sorting


def test_the_page_menu_key_is_ignored_but_doc_opens() -> None:
    state = _sorter((1,))
    state.run_action("open_menu", "menu")
    assert state.menu is None
    state.run_action("open_menu", "doc")
    assert state.menu is not None


def test_a_new_document_closes_the_sorter() -> None:
    state = _sorter((2,))
    state.run_action("new_document")
    assert not state.sorting
