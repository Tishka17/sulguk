from dataclasses import dataclass, field
from typing import List, Optional, TypedDict

from .canvas import Canvas


class User(TypedDict):
    id: int


class MessageEntity(TypedDict, total=False):
    type: str
    offset: int
    length: int
    url: Optional[str]
    user: Optional[User]
    language: Optional[str]
    custom_emoji_id: Optional[str]


@dataclass
class State:
    canvas: Canvas = field(default_factory=Canvas)
    entities: List[MessageEntity] = field(default_factory=list)
