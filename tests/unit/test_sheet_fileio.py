from __future__ import annotations

from io import BytesIO

import pytest
from openpyxl import Workbook, load_workbook

from cassim.sheet.fileio import FileCell, read_csv, read_xlsx, write_csv, write_xlsx


def test_csv_roundtrip_handles_bom_quotes_and_cassim_formulas() -> None:
    rows = read_csv(b'\xef\xbb\xbfName,Value\r\n"cat, dog",=A1+2\r\n')

    assert rows == [
        [FileCell("Name"), FileCell("Value")],
        [FileCell("cat, dog"), FileCell("A1+2", True)],
    ]
    assert write_csv([["Name", "Value"], ["cat, dog", "3"]]) == (b'Name,Value\r\n"cat, dog",3\r\n')


def test_xlsx_roundtrip_keeps_values_and_formulas() -> None:
    source = Workbook()
    source.active["A1"] = 2
    source.active["B1"] = "=A1+3"
    data = BytesIO()
    source.save(data)

    rows = read_xlsx(data.getvalue())

    assert rows == [[FileCell("2"), FileCell("A1+3", True)]]
    saved = load_workbook(BytesIO(write_xlsx(rows)), data_only=False)
    assert saved.active["A1"].value == 2
    assert saved.active["B1"].value == "=A1+3"


def test_csv_rejects_files_that_do_not_fit_the_sheet() -> None:
    with pytest.raises(ValueError, match="more than 26 columns"):
        read_csv(b",".join([b"x"] * 27))

    with pytest.raises(ValueError, match="more than 2500 rows"):
        read_csv(b"x\n" * 2501)


def test_xlsx_reports_invalid_workbooks() -> None:
    with pytest.raises(ValueError, match="Cannot read XLSX file"):
        read_xlsx(b"not an xlsx file")
