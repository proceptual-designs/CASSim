"""Share links (FR-DOC-007): the document in the URL fragment."""

import base64
import zlib

import pytest

from cassim.core.settings import Settings
from cassim.device.keys import Binding
from cassim.devices.nspire.document import Document, decode
from cassim.devices.nspire.pages.calculator import Calculator, calculator_of
from cassim.doc.serialize import DocumentFileError, dumps
from cassim.doc.share import MAX_FRAGMENT, LinkTooLongError, encode


def typed(document: Document, text: str) -> None:
    calculator = calculator_of(document.current)
    assert isinstance(calculator, Calculator)
    for char in text:
        calculator.perform(Binding("insert", char))
    calculator.perform(Binding("enter"))


def test_round_trip() -> None:
    document = Document("Shared", Settings())
    typed(document, "2+3")
    link = encode(document)
    assert link.startswith("doc=")
    loaded = decode("#" + link)
    assert loaded is not None
    assert dumps(loaded) == dumps(document)


def test_not_a_share_fragment() -> None:
    assert decode("") is None
    assert decode("#/somewhere") is None


def test_too_long_is_refused() -> None:
    document = Document("Big", Settings())
    for n in range(400):
        typed(document, f"{n * 7919 % 9973}*{n * 104729 % 9967}+{n}")
    with pytest.raises(LinkTooLongError):
        encode(document)
    assert MAX_FRAGMENT == 2000


@pytest.mark.parametrize("body", ["!!!", "AAAA", base64.urlsafe_b64encode(b"x" * 9).decode()])
def test_damaged_link(body: str) -> None:
    with pytest.raises(DocumentFileError):
        decode("doc=" + body)


def test_decompression_bomb_is_refused() -> None:
    bomb = base64.urlsafe_b64encode(zlib.compress(b" " * 5_000_000)).decode().rstrip("=")
    with pytest.raises(DocumentFileError):
        decode("doc=" + bomb)


def test_foreign_json_is_refused() -> None:
    other = base64.urlsafe_b64encode(zlib.compress(b'{"a": 1}')).decode().rstrip("=")
    with pytest.raises(DocumentFileError):
        decode("doc=" + other)
