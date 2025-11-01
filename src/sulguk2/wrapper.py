from typing import Optional

import html5lib

from sulguk.render.state import State
from sulguk.wrapper import RenderResult
from sulguk2.tree_builder import (
    get_sulguk_tree_builder,
)


def transform_html(html: str, base_url: Optional[str] = None) -> RenderResult:
    parser = html5lib.HTMLParser(
        tree=get_sulguk_tree_builder(base_url),
        namespaceHTMLElements=False,
    )
    doc = parser.parse(html)
    root = doc.entity
    state = State()
    root.render(state)
    return RenderResult(
        text=state.canvas.text,
        entities=state.entities,
    )
