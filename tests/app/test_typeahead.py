# Requirements traced here: NFR-USE-001
"""Keys typed while the engine works are kept and run in order once it is free, as a handheld
keeps them, instead of being lost (the flows browser test lost a sheet's typing this way)."""

import asyncio
from types import SimpleNamespace

from tests.app.test_splitter_drag import handheld_app

from cassim.devices.nspire.pages.calculator import calculator_on


def key(app, name: str) -> None:
    event = SimpleNamespace(key=name, shift=False, ctrl=False, alt=False, meta=False)
    asyncio.run(app.on_key(event))


def typed(app) -> str:
    calculator = calculator_on(app.state.document.current)
    assert calculator is not None
    return calculator.editor.linear()


def test_keys_typed_while_busy_run_in_order_when_free() -> None:
    app, page = handheld_app()
    app.starting = True  # busy: as while the engine works
    for name in ("1", "2", "+", "3"):
        key(app, name)
    app.press("4")  # a keypad tap waits too
    assert typed(app) == ""
    app.starting = False
    app.refresh()
    assert typed(app) == "12+34"
    assert not app.typeahead
    for task in page.tasks:
        task.close()


def test_escape_while_busy_drops_the_keys_typed_after_the_run() -> None:
    app, page = handheld_app()
    app.starting = True
    key(app, "7")
    key(app, "Escape")
    app.starting = False
    app.refresh()
    assert typed(app) == ""
    for task in page.tasks:
        task.close()


def test_a_key_after_enter_goes_into_the_next_entry() -> None:
    """Enter runs the entry; the key typed after it starts the next one, as typed."""
    app, page = handheld_app()
    app.starting = True
    for name in ("2", "Enter", "5"):
        key(app, name)
    app.starting = False
    app.refresh()
    calculator = calculator_on(app.state.document.current)
    assert calculator is not None
    assert [entry.result.text for entry in calculator.history] == ["2"]
    assert typed(app) == "5"
    for task in page.tasks:
        task.close()
