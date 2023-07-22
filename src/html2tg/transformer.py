import re
from html.parser import HTMLParser
from typing import List, Tuple, Optional

from .entities import (
    Group, Entity, Text, Link, Bold, Italic,
    Strikethrough, Code, ListItem, ListGroup,
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

    def _find_attr(self, name: str, attrs: Attrs) -> Optional[str]:
        return next((value for key, value in attrs if key == name), None)

    def _get_a(self, attrs: Attrs) -> Entity:
        url = self._find_attr("href", attrs)
        if url:
            return Link(url=url)
        else:
            return Group()

    def _get_ul(self, attrs: Attrs) -> Entity:
        return ListGroup(numbered=False)

    def _get_ol(self, attrs: Attrs) -> Entity:
        return ListGroup(numbered=True)

    def _get_li(self, attrs: Attrs) -> Entity:
        return ListItem(list=self.current)

    def handle_starttag(
            self, tag: str, attrs: Attrs,
    ) -> None:
        if tag == "ul":
            entity = self._get_ul(attrs)
        elif tag == "ol":
            entity = self._get_ol(attrs)
        elif tag == "li":
            entity = self._get_li(attrs)
        elif tag == "a":
            entity = self._get_a(attrs)
        elif tag in ("b", "strong"):
            entity = Bold()
        elif tag in ("i", "em"):
            entity = Italic()
        elif tag in ("s", "strike", "del"):
            entity = Strikethrough()
        elif tag in ("code",):
            entity = Code()
        else:
            raise ValueError(f"Unsupported tag: {tag}")
        self.current.add(entity)
        self.entities.append(entity)

    def handle_endtag(self, tag: str) -> None:
        self.entities.pop()
