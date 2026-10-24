from dataclasses import dataclass
from typing import Optional

from .base import RichBlock
from .text import RichTextList


@dataclass
class ParagraphBlock(RichBlock):
    text: RichTextList
    type = "paragraph"

    def text_length(self) -> int:
        return self.text.length()


@dataclass
class HeadingBlock(RichBlock):
    text: RichTextList
    size: int
    type = "heading"

    def text_length(self) -> int:
        return self.text.length()


@dataclass
class FooterBlock(RichBlock):
    text: RichTextList
    type = "footer"

    def text_length(self) -> int:
        return self.text.length()


@dataclass
class ThinkingBlock(RichBlock):
    text: RichTextList
    type = "thinking"

    def text_length(self) -> int:
        return self.text.length()


@dataclass
class PreBlock(RichBlock):
    text: str
    language: Optional[str] = None
    type = "pre"

    def text_length(self) -> int:
        return len(self.text)


@dataclass
class DividerBlock(RichBlock):
    type = "divider"


@dataclass
class MathBlock(RichBlock):
    expression: str
    type = "mathematical_expression"

    def text_length(self) -> int:
        return len(self.expression)


@dataclass
class AnchorBlock(RichBlock):
    name: str
    type = "anchor"
