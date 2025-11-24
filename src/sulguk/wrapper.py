from dataclasses import dataclass
from typing import List, Optional

from html5lib import HTMLParser, getTreeBuilder

from .data import MessageEntity
from .render.state import State
from .walker import Walker


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

    parser = HTMLParser(
        getTreeBuilder("lxml"),
        strict=strict,
        namespaceHTMLElements=False,
    )
    doc = parser.parse(raw_html)
    root = Walker(base_url).walk(doc)
    state = State()
    root.render(state)
    return RenderResult(text=state.canvas.text, entities=state.entities)
