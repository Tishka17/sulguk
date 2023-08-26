from html.parser import HTMLParser
from typing import Any, List, Optional, Tuple

from sulguk.render.numbers import NumberFormat
from .entities import (
    Blockquote, Bold, Code, Entity, Group, HorizontalLine,
    Italic, Link, ListGroup, ListItem, NewLine, Paragraph, Pre, Progress,
    Quote, Spoiler, Strikethrough, Stub, Text, Underline,
    Uppercase,
)

Attrs = List[Tuple[str, Optional[str]]]

OL_FORMAT = {
    "1": NumberFormat.DECIMAL,
    "a": NumberFormat.LETTERS_LOWER,
    "A": NumberFormat.LETTERS_UPPER,
    "i": NumberFormat.ROMAN_LOWER,
    "I": NumberFormat.ROMAN_UPPER,
}

LANG_CLASS_PREFIX = "language-"


class Transformer(HTMLParser):
    def __init__(self):
        super().__init__()
        self.root = Group()
        self.entities: List[Entity] = [self.root]

    @property
    def current(self) -> Entity:
        return self.entities[-1]

    def handle_data(self, data: str) -> None:
        self.current.add(Text(data))

    def _find_attr(
            self,
            name: str,
            attrs: Attrs,
            default: Any = "",
    ) -> Optional[str]:
        return next((value for key, value in attrs if key == name), default)

    def _get_classes(self, attrs: Attrs):
        return self._find_attr("class", attrs).split()

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

        type_ = self._find_attr("type", attrs)
        if not type_:
            ol_format = NumberFormat.DECIMAL
        else:
            ol_format = OL_FORMAT[type_]

        return ListGroup(
            numbered=True,
            start=start,
            format=ol_format,
            reversed=is_reversed is not ...,
        )

    def _get_li(self, attrs: Attrs) -> Entity:
        value = self._find_attr("value", attrs)
        if value:
            value = int(value)
        else:
            value = None
        return ListItem(value=value)

    def _get_span(self, attrs: Attrs) -> Entity:
        classes = self._get_classes(attrs)
        if "tg-spoiler" in classes:
            return Spoiler()
        return Group()

    def _get_code(self, attrs: Attrs) -> Entity:
        return Code()

    def _get_pre(self, attrs: Attrs) -> Entity:
        classes = self._get_classes(attrs)
        language = next(
            (
                c[len(LANG_CLASS_PREFIX):]
                for c in classes
                if c.startswith(LANG_CLASS_PREFIX)
            ),
            None,
        )
        return Pre(language=language)

    def _get_mark(self, attrs: Attrs):
        inner = Group()
        entity = Group()
        entity.add(Italic(entities=[Bold(entities=[inner])]))
        return inner, entity

    def _get_h(self, tag: str, attrs: Attrs):
        inner = Group()
        entity = Group(block=True)
        entity.add(Paragraph())
        if tag == "h1":
            entity.add(
                Bold(
                    entities=[
                        Underline(entities=[Uppercase(entities=[inner])])
                    ]
                )
            )
        elif tag == "h2":
            entity.add(Bold(entities=[Underline(entities=[inner])]))
        elif tag == "h3":
            entity.add(Bold(entities=[inner]))
        elif tag == "h4":
            entity.add(Italic(entities=[Underline(entities=[inner])]))
        elif tag == "h5":
            entity.add(Italic(entities=[inner]))
        if tag == "h6":
            entity.add(Italic(entities=[inner]))
        return inner, entity

    def _get_progress(self, attrs: Attrs) -> Entity:
        return Progress(
            value=float(self._find_attr("value", attrs, "0")),
            max=float(self._find_attr("max", attrs, "1")),
            is_meter=False,
        )

    def _get_meter(self, attrs: Attrs) -> Entity:
        return Progress(
            value=float(self._find_attr("value", attrs, "0")),
            min=float(self._find_attr("min", attrs, "0")),
            max=float(self._find_attr("max", attrs, "1")),
            is_meter=True,
        )

    def handle_startendtag(self, tag: str, attrs: Attrs) -> None:
        if tag == "br":
            entity = NewLine()
        elif tag == "hr":
            entity = HorizontalLine()
        else:
            raise ValueError(f"Unsupported single tag: `{tag}`")
        self.current.add(entity)

    def handle_starttag(
            self,
            tag: str,
            attrs: Attrs,
    ) -> None:
        tag = tag.lower()
        # special
        if tag in ("html", "noscript", "body"):
            nested = entity = Group()
        elif tag in (
                "head", "link", "meta", "script", "style",
                "template", "title",
        ):
            nested = entity = Stub()
        # normal
        elif tag in ("ul",):
            nested = entity = self._get_ul(attrs)
        elif tag in ("ol",):
            nested = entity = self._get_ol(attrs)
        elif tag in ("li",):
            nested = entity = self._get_li(attrs)
        elif tag in ("a",):
            nested = entity = self._get_a(attrs)
        elif tag in ("b", "strong"):
            nested = entity = Bold()
        elif tag in ("i", "em", "cite", "var"):
            nested = entity = Italic()
        elif tag in ("s", "strike", "del"):
            nested = entity = Strikethrough()
        elif tag in ("code",):
            nested = entity = self._get_code(attrs)
        elif tag in ("kbd", "samp",):
            nested = entity = Code()
        elif tag in ("div", "footer", "header", "main", "nav", "section"):
            nested = entity = Group(block=True)
        elif tag in ("span",):
            nested = entity = self._get_span(attrs)
        elif tag in ("output", "data", "time"):
            nested = entity = Group()
        elif tag in ("tg-spoiler",):
            nested = entity = Spoiler()
        elif tag in ("p",):
            nested = entity = Paragraph()
        elif tag in ("u", "ins"):
            nested = entity = Underline()
        elif tag in ("q",):
            nested = entity = Quote()
        elif tag in ("pre",):
            nested = entity = self._get_pre(attrs)
        elif tag in ("blockquote",):
            nested = entity = Blockquote()
        elif tag in ("progress",):
            nested = entity = self._get_progress(attrs)
        elif tag in ("meter",):
            nested = entity = self._get_meter(attrs)
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            nested, entity = self._get_h(tag, attrs)
        elif tag in ("mark",):
            nested, entity = self._get_mark(attrs)
        else:
            raise ValueError(f"Unsupported tag: {tag}")
        self.current.add(entity)
        self.entities.append(nested)

    def handle_endtag(self, tag: str) -> None:
        self.entities.pop()
