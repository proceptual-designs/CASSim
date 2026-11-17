"""Value-only CSV and basic XLSX interchange for the Lists & Spreadsheet page (FR-SHEET-003)."""

from __future__ import annotations

import csv
import io
import re
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import TYPE_CHECKING

from cassim.sheet.refs import COLUMNS, ROWS

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True)
class FileCell:
    text: str
    formula: bool = False


def read_csv(data: bytes) -> list[list[FileCell]]:
    try:
        text = data.decode("utf-8-sig")
        rows = [
            [
                FileCell(value[1:], True) if value.startswith("=") else FileCell(value)
                for value in row
            ]
            for row in csv.reader(io.StringIO(text, newline=""))
        ]
    except (UnicodeDecodeError, csv.Error) as error:
        raise ValueError(f"Cannot read CSV file: {error}") from error
    _check_size(rows)
    return rows


def write_csv(rows: Sequence[Sequence[str]]) -> bytes:
    text = io.StringIO(newline="")
    csv.writer(text, lineterminator="\r\n").writerows(rows)
    return text.getvalue().encode("utf-8")


def read_xlsx(data: bytes) -> list[list[FileCell]]:
    try:
        from openpyxl import load_workbook  # noqa: PLC0415 (optional XLSX support)
        from openpyxl.utils.exceptions import InvalidFileException  # noqa: PLC0415

        workbook = load_workbook(io.BytesIO(data), read_only=True, data_only=False)
    except (InvalidFileException, OSError, ValueError, zipfile.BadZipFile) as error:
        raise ValueError(f"Cannot read XLSX file: {error}") from error

    try:
        sheet = workbook.active
        if sheet.max_row is not None and sheet.max_row > ROWS:
            raise ValueError(f"XLSX sheet has more than {ROWS} rows")
        if sheet.max_column is not None and sheet.max_column > COLUMNS:
            raise ValueError(f"XLSX sheet has more than {COLUMNS} columns")
        rows: list[list[FileCell]] = []
        for source_row in sheet.iter_rows():
            row: list[FileCell] = []
            for cell in source_row:
                value = cell.value
                if value is None:
                    row.append(FileCell(""))
                elif cell.data_type == "f":
                    row.append(FileCell(str(value).removeprefix("="), True))
                elif isinstance(value, datetime | date | time):
                    row.append(FileCell(value.isoformat()))
                elif isinstance(value, bool):
                    row.append(FileCell(str(value).lower()))
                else:
                    row.append(FileCell(str(value)))
            rows.append(row)
    finally:
        workbook.close()
    _check_size(rows)
    return rows


def write_xlsx(rows: Sequence[Sequence[FileCell]]) -> bytes:
    _check_size([list(row) for row in rows])
    from openpyxl import Workbook  # noqa: PLC0415 (optional XLSX support)

    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet()
    for row in rows:
        sheet.append([_xlsx_value(cell) for cell in row])
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


def _xlsx_value(cell: FileCell) -> str | int | float:
    if cell.formula:
        return f"={cell.text}"
    if re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", cell.text.strip()):
        return float(cell.text) if any(char in cell.text for char in ".eE") else int(cell.text)
    return cell.text


def _check_size(rows: list[list[FileCell]]) -> None:
    if len(rows) > ROWS:
        raise ValueError(f"File has more than {ROWS} rows")
    if any(len(row) > COLUMNS for row in rows):
        raise ValueError(f"File has more than {COLUMNS} columns")
