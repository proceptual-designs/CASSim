"""Spike 2: pin what we know about the .tns container (decision 0003)."""

import zipfile

import pytest
from tools.evidence import evidence_path

REFS = evidence_path("references")
MAGIC = b"*TIMLP"  # then a four-digit version: 0601 (libraries), 0500, 0703
ENTRY_SIGNATURE = bytes.fromhex("0fced8d28106865b")  # first 8 bytes of every entry payload


def _tns_blobs() -> list[tuple[str, bytes]]:
    blobs = [(str(p.name), p.read_bytes()) for p in REFS.rglob("*.tns")]
    for z in REFS.rglob("*.zip"):
        with zipfile.ZipFile(z) as zf:
            blobs += [(n, zf.read(n)) for n in zf.namelist() if n.endswith(".tns")]
    return blobs


BLOBS = _tns_blobs()


@pytest.mark.skipif(not BLOBS, reason="no .tns reference files present")
@pytest.mark.parametrize(("name", "data"), BLOBS, ids=[n for n, _ in BLOBS])
def test_container_header_is_stable(name: str, data: bytes) -> None:
    assert data.startswith(MAGIC)
    assert data[len(MAGIC) : len(MAGIC) + 4].isdigit()
    assert not zipfile.is_zipfile(__import__("io").BytesIO(data))  # not a plain zip
    assert data[0x30:0x38] == ENTRY_SIGNATURE
    assert b"Document.xml" in data
