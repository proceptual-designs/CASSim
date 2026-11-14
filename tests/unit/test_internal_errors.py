# Requirements traced here: FR-EVAL-005
"""An unexpected Python exception is a bug, but it must not escape the engine: the entry shows the
exception's type and message, and the session keeps working."""

import logging

import pytest

from cassim.core import errors
from cassim.core import session as session_module
from cassim.core.compat import sympy_adapter
from cassim.core.session import Session
from cassim.sheet.sheet import Sheet

A = 0


@pytest.fixture
def broken_limit(monkeypatch):
    def limit(*_args):
        raise ValueError("something SymPy did not expect")

    monkeypatch.setattr(sympy_adapter, "limit", limit)


def test_an_unexpected_exception_is_shown_as_an_error(broken_limit, caplog):
    session = Session()
    with caplog.at_level(logging.ERROR):
        result = session.eval("limit(1/x,x,0)")
    assert result.error == "Internal error: ValueError: something SymPy did not expect"
    assert result.text == result.error
    assert caplog.records[0].exc_info  # the traceback goes to the log, not the screen
    assert session.eval("1+1").text == "2"  # the session still works


def test_a_failed_entry_leaves_ans_alone(broken_limit):
    session = Session()
    session.eval("5")
    session.eval("limit(1/x,x,0)")
    assert session.eval("ans+1").text == "6"


def test_an_unexpected_exception_while_formatting_is_shown(monkeypatch):
    def to_text(*_args):
        raise KeyError("shape")

    monkeypatch.setattr(session_module, "to_text", to_text)
    assert Session().eval("1+1").error == "Internal error: KeyError: 'shape'"


def test_a_long_message_is_cut_short():
    error = errors.internal(ValueError("x" * 1000))
    assert len(error.message) < 400
    assert error.message.endswith("…")
    assert errors.internal(ValueError()).message == "Internal error: ValueError"


def test_a_spreadsheet_formula_that_raises_fails_like_any_other_error(broken_limit):
    sheet = Sheet(Session())
    sheet.set_cell(A, 1, "=limit(1/x,x,0)")
    sheet.set_cell(A, 2, "=1+1")
    assert sheet.shown(A, 2).text == "2"
    assert sheet.shown(A, 1).text == "#ERR"
