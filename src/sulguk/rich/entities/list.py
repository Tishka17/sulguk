from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .base import RichBlock, RichEntity


@dataclass
class ListItemBlock(RichEntity):
    blocks: List[RichBlock] = field(default_factory=list)
    has_checkbox: bool = False
    is_checked: bool = False
    value: Optional[int] = None
    # ``type`` is the numbering of an ordered list: 1, a, A, i or I
    numbering: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = self._fields()
        if "numbering" in result:
            result["type"] = result.pop("numbering")
        return result


@dataclass
class ListBlock(RichBlock):
    items: List[ListItemBlock] = field(default_factory=list)
    type = "list"

    def own_count(self) -> int:
        # an item is a block itself
        return 1 + len(self.items)

    def nested(self) -> List[Tuple[int, List[RichBlock]]]:
        # an item adds one more level
        return [(2, item.blocks) for item in self.items]

    def text_length(self) -> int:
        return sum(
            block.text_length()
            for item in self.items
            for block in item.blocks
        )
