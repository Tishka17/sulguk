from dataclasses import dataclass
from typing import List, Optional

import html5lib

from .data import MessageEntity
from .render.state import State
from .tree_builder import get_sulguk_tree_builder


@dataclass
class RenderResult:
    text: str
    entities: List[MessageEntity]


def transform_html(
    raw_html: Optional[str],
    base_url: Optional[str] = None,
    strict: bool = False,
) -> RenderResult:
    if raw_html is None or raw_html.strip() == "":
        return RenderResult(text="", entities=[])

    parser = html5lib.HTMLParser(
        tree=get_sulguk_tree_builder(base_url),
        namespaceHTMLElements=False,
        strict=strict,
    )
    doc = parser.parse(raw_html)
    root = doc.entity
    state = State()
    root.render(state)
    return RenderResult(
        text=state.canvas.text,
        entities=state.entities,
    )
