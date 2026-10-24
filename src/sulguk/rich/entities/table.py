from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .base import RichBlock, RichEntity
from .text import RichTextList


@dataclass
class TableCell(RichEntity):
    align: str = "left"
    valign: str = "middle"
    text: Optional[RichTextList] = None
    is_header: bool = False
    colspan: Optional[int] = None
    rowspan: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return self._fields()

    def width(self) -> int:
        return self.colspan if self.colspan is not None else 1

    def text_length(self) -> int:
        return self.text.length() if self.text is not None else 0


@dataclass
class TableBlock(RichBlock):
    cells: List[List[TableCell]] = field(default_factory=list)
    caption: Optional[RichTextList] = None
    type = "table"

    def own_count(self) -> int:
        # a row is a block itself
        return 1 + len(self.cells)

    def row_widths(self) -> List[int]:
        return [sum(cell.width() for cell in row) for row in self.cells]

    def text_length(self) -> int:
        cells = sum(
            cell.text_length() for row in self.cells for cell in row
        )
        caption = self.caption.length() if self.caption is not None else 0
        return cells + caption
