from dataclasses import dataclass, field
from typing import List

from aiogram.types import MessageEntity

from .canvas import Canvas


@dataclass
class State:
    indent: int = 0
    canvas: Canvas = field(default_factory=Canvas)
    index: int = 0
    to_upper: bool = False
    entities: List[MessageEntity] = field(default_factory=list)
