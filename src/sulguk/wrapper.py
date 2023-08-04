from dataclasses import dataclass
from typing import List

from .state import MessageEntity, State
from .transformer import Transformer


@dataclass
class RenderResult:
    text: str
    entities: List[MessageEntity]


def transform_html(raw_html: str) -> RenderResult:
    transformer = Transformer()
    transformer.feed(raw_html)
    state = State()
    transformer.root.render(state)
    return RenderResult(
        text=state.canvas.text,
        entities=state.entities,
    )
