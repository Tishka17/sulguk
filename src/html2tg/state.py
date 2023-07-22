from dataclasses import dataclass, field
from typing import List

from aiogram.types import MessageEntity


@dataclass
class State:
    offset: int = 0
    indent: int = 0
    text: str = ""
    index: int = 0
    entities: List[MessageEntity] = field(default_factory=list)
