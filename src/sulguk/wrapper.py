from dataclasses import dataclass
from typing import List, Optional

from sulguk.render.state import MessageEntity, State
from .transformer import Transformer


@dataclass
class RenderResult:
    text: str
    entities: List[MessageEntity]


def transform_html(raw_html: Optional[str]) -> RenderResult:

    if raw_html is None or raw_html.strip() == "":
        return RenderResult(text="", entities=[])

    transformer = Transformer()
    transformer.feed(raw_html)
    state = State()
    transformer.root.render(state)
    return RenderResult(
        text=state.canvas.text,
        entities=state.entities,
    )
