"""The calculator's own clipboard: it keeps templates intact, so a pasted fraction is stacked (S7).

The GUI also copies the text to the system clipboard. On paste, text that matches this clipboard
brings the nodes back; any other text is typed in. Cells copied on a spreadsheet page are kept
here too, so a copy reaches every page; whichever was copied last is what the clipboard holds.
"""

from __future__ import annotations

from cassim.device.editor import Row, linear_text


class Clipboard:
    def __init__(self) -> None:
        self._nodes: Row = []
        self._cells: object = None  # the spreadsheet page's own record of copied cells
        self._cells_text = ""  # the text they were copied as

    @property
    def nodes(self) -> Row:
        return self._nodes

    @nodes.setter
    def nodes(self, nodes: Row) -> None:
        self._nodes = nodes
        self._cells, self._cells_text = None, ""

    @property
    def cells(self) -> object:
        return self._cells

    def copy_cells(self, cells: object, text: str) -> None:
        self._cells, self._cells_text = cells, text
        self._nodes = []

    @property
    def text(self) -> str:
        return self._cells_text if self._cells is not None else linear_text(self._nodes)
