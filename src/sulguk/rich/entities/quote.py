from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .base import RichBlock
from .text import RichTextList


def _credit_length(credit: Optional[RichTextList]) -> int:
    return credit.length() if credit is not None else 0


def _blocks_length(blocks: List[RichBlock]) -> int:
    return sum(block.text_length() for block in blocks)


@dataclass
class BlockquoteBlock(RichBlock):
    blocks: List[RichBlock] = field(default_factory=list)
    credit: Optional[RichTextList] = None
    type = "blockquote"

    def nested(self) -> List[Tuple[int, List[RichBlock]]]:
        return [(1, self.blocks)]

    def text_length(self) -> int:
        return _blocks_length(self.blocks) + _credit_length(self.credit)


@dataclass
class ExpandableBlockquoteBlock(RichBlock):
    text: RichTextList
    credit: Optional[RichTextList] = None
    type = "expandable_blockquote"

    def text_length(self) -> int:
        return self.text.length() + _credit_length(self.credit)


@dataclass
class PullquoteBlock(RichBlock):
    text: RichTextList
    credit: Optional[RichTextList] = None
    type = "pullquote"

    def text_length(self) -> int:
        return self.text.length() + _credit_length(self.credit)


@dataclass
class DetailsBlock(RichBlock):
    summary: RichTextList
    blocks: List[RichBlock] = field(default_factory=list)
    is_open: bool = False
    type = "details"

    def nested(self) -> List[Tuple[int, List[RichBlock]]]:
        return [(1, self.blocks)]

    def text_length(self) -> int:
        return self.summary.length() + _blocks_length(self.blocks)
