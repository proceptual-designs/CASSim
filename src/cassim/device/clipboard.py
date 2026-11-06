"""The calculator's own clipboard: it keeps templates intact, so a pasted fraction is stacked (S7).

The GUI also copies the text to the system clipboard. On paste, text that matches this clipboard
brings the nodes back; any other text is typed in.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cassim.device.editor import Row, linear_text


@dataclass
class Clipboard:
    nodes: Row = field(default_factory=list)

    @property
    def text(self) -> str:
        return linear_text(self.nodes)
