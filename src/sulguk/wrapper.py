import re
from dataclasses import dataclass
from typing import List, Optional

from html5lib import HTMLParser, getTreeBuilder
from lxml import etree

from .data import MessageEntity
from .render.state import State
from .walker import Walker


@dataclass
class RenderResult:
    text: str
    entities: List[MessageEntity]


_SELF_CLOSING_CUSTOM = re.compile(r"<(tg-map)\b([^<>]*?)\s*/>", re.IGNORECASE)


def parse_html(raw_html: str, strict: bool = False):
    # HTML5 parsers ignore "/>" on unknown elements, so <tg-map .../> from
    # Telegram docs would swallow all the following siblings
    raw_html = _SELF_CLOSING_CUSTOM.sub(r"<\1\2></\1>", raw_html)
    parser = HTMLParser(
        getTreeBuilder("lxml"),
        strict=strict,
        namespaceHTMLElements=False,
    )
    doc = parser.parse(raw_html)
    # comments go away, the text after a comment (its tail) stays
    etree.strip_tags(doc, etree.Comment)
    return doc


def transform_html(
    raw_html: Optional[str],
    base_url: Optional[str] = None,
    strict: bool = False,
) -> RenderResult:
    if raw_html is None or raw_html.strip() == "":
        return RenderResult(text="", entities=[])

    doc = parse_html(raw_html, strict=strict)
    root = Walker(base_url).walk(doc)
    state = State()
    root.render(state)
    return RenderResult(text=state.canvas.text, entities=state.entities)
