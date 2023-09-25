from dataclasses import dataclass, field
from typing import List

from sulguk.data import MessageEntity
from .canvas import Canvas


@dataclass
class State:
    canvas: Canvas = field(default_factory=Canvas)
    entities: List[MessageEntity] = field(default_factory=list)
