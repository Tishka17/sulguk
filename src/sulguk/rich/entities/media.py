from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .base import RichBlock, RichEntity
from .text import RichTextList


@dataclass
class Caption(RichEntity):
    text: RichTextList
    credit: Optional[RichTextList] = None

    def to_dict(self) -> Dict[str, Any]:
        return self._fields()

    def text_length(self) -> int:
        credit = self.credit.length() if self.credit is not None else 0
        return self.text.length() + credit


def _caption_length(caption: Optional[Caption]) -> int:
    return caption.text_length() if caption is not None else 0


@dataclass
class MediaBlock(RichBlock):
    """Photo, video, animation, audio, voice note or document."""

    kind: str
    media: str
    has_spoiler: bool = False
    caption: Optional[Caption] = None

    def to_dict(self) -> Dict[str, Any]:
        media: Dict[str, Any] = {"type": self.kind, "media": self.media}
        if self.has_spoiler:
            media["has_spoiler"] = True
        result: Dict[str, Any] = {"type": self.kind, self.kind: media}
        if self.caption is not None:
            result["caption"] = self.caption.to_dict()
        return result

    def text_length(self) -> int:
        return _caption_length(self.caption)

    def media_count(self) -> int:
        return 1


@dataclass
class MapBlock(RichBlock):
    latitude: float
    longitude: float
    zoom: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    caption: Optional[Caption] = None
    type = "map"

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "type": self.type,
            "location": {
                "latitude": self.latitude,
                "longitude": self.longitude,
            },
        }
        for name in ("zoom", "width", "height"):
            value = getattr(self, name)
            if value is not None:
                result[name] = value
        if self.caption is not None:
            result["caption"] = self.caption.to_dict()
        return result

    def text_length(self) -> int:
        return _caption_length(self.caption)


@dataclass
class GalleryBlock(RichBlock):
    """Collage or slideshow."""

    kind: str
    blocks: List[MediaBlock] = field(default_factory=list)
    caption: Optional[Caption] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "type": self.kind,
            "blocks": [block.to_dict() for block in self.blocks],
        }
        if self.caption is not None:
            result["caption"] = self.caption.to_dict()
        return result

    def nested(self) -> List[Tuple[int, List[RichBlock]]]:
        return [(1, list(self.blocks))]

    def text_length(self) -> int:
        blocks = sum(block.text_length() for block in self.blocks)
        return blocks + _caption_length(self.caption)
