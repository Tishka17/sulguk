import re
from html.parser import HTMLParser
from typing import List, Tuple, Optional, Any

from .entities import (
    Group, Entity, Text, Link, Bold, Italic,
    Strikethrough, Code, ListItem, ListGroup, NewLine, Spoiler,
    Paragraph,
)

SPACES = re.compile(r"\s+")

Attrs = List[Tuple[str, Optional[str]]]


class Transformer(HTMLParser):
    def __init__(self):
        super().__init__()
        self.root = Group()
        self.entities: List[Entity] = [self.root]

    @property
    def current(self) -> Entity:
        return self.entities[-1]

    def handle_data(self, data: str) -> None:
        self.current.add(Text(SPACES.sub(" ", data)))

    def _find_attr(
            self, name: str, attrs: Attrs, default: Any = "",
    ) -> Optional[str]:
        return next((value for key, value in attrs if key == name), default)

    def _get_a(self, attrs: Attrs) -> Entity:
        url = self._find_attr("href", attrs)
        if url:
            return Link(url=url)
        else:
            return Group()

    def _get_ul(self, attrs: Attrs) -> Entity:
        return ListGroup(numbered=False)

    def _get_ol(self, attrs: Attrs) -> Entity:
        start = self._find_attr("start", attrs)
        if not start:
            start = 1
        else:
            start = int(start)
        is_reversed = self._find_attr("reversed", attrs, ...)
        return ListGroup(
            numbered=True,
            start=start,
            reversed=is_reversed is not ...,
        )

    def _get_li(self, attrs: Attrs) -> Entity:
        return ListItem(list=self.current)

    def _get_span(self, attrs: Attrs) -> Entity:
        classes = self._find_attr("class", attrs).split()
        if "tg-spoiler" in classes:
            return Spoiler()
        return Group()

    def handle_startendtag(self, tag: str, attrs: Attrs) -> None:
        if tag == "br":
            entity = NewLine()
        else:
            raise ValueError(f"Unsupported single tag: {tag}")
        self.current.add(entity)

    def handle_starttag(
            self, tag: str, attrs: Attrs,
    ) -> None:
        if tag in ("ul",):
            entity = self._get_ul(attrs)
        elif tag in ("ol",):
            entity = self._get_ol(attrs)
        elif tag in ("li",):
            entity = self._get_li(attrs)
        elif tag in ("a",):
            entity = self._get_a(attrs)
        elif tag in ("b", "strong"):
            entity = Bold()
        elif tag in ("i", "em"):
            entity = Italic()
        elif tag in ("s", "strike", "del"):
            entity = Strikethrough()
        elif tag in ("code",):
            entity = Code()
        elif tag in ("div",):
            entity = Group(block=True)
        elif tag in ("span",):
            entity = self._get_span(attrs)
        elif tag in ("tg-spiler",):
            entity = Spoiler()
        elif tag in ("p",):
            entity = Paragraph()
        else:
            raise ValueError(f"Unsupported tag: {tag}")
        self.current.add(entity)
        self.entities.append(entity)

    def handle_endtag(self, tag: str) -> None:
        self.entities.pop()
