import urllib.parse
from functools import cached_property, partial
from typing import Any, Callable, List, Optional, ParamSpec, Tuple

from .entities import (
    Blockquote,
    Bold,
    Code,
    Emoji,
    Entity,
    Group,
    HorizontalLine,
    Italic,
    Link,
    ListGroup,
    ListItem,
    NewLine,
    Paragraph,
    Pre,
    Progress,
    Quote,
    Spoiler,
    Strikethrough,
    Stub,
    Text,
    Underline,
    Uppercase,
    ZeroWidthSpace,
)
from .render.numbers import NumberFormat

P = ParamSpec("P")

Attrs = List[Tuple[str, str]]
EntityPair = Tuple[Optional[Entity], Optional[Entity]]

OL_FORMAT = {
    "1": NumberFormat.DECIMAL,
    "a": NumberFormat.LETTERS_LOWER,
    "A": NumberFormat.LETTERS_UPPER,
    "i": NumberFormat.ROMAN_LOWER,
    "I": NumberFormat.ROMAN_UPPER,
}

LANG_CLASS_PREFIX = "language-"


class Mapper:
    def __init__(self, base_url: str | None = None):
        self._base_url = base_url

    def match(self, tag: str, attrs: Attrs) -> EntityPair:
        factory = self._map.get(tag)
        if factory is None:
            raise ValueError(f"Unsupported tag: {tag}")
        inner, entity = factory(attrs)
        return inner, entity

    @cached_property
    def _map(self) -> dict[str, Callable[[Attrs], EntityPair]]:
        _map = {
            # single tags
            "br": self._adapt_factory(NewLine),
            "wbr": self._adapt_factory(ZeroWidthSpace),
            "hr": self._adapt_factory(HorizontalLine),
            "img": self._get_img,
            "input": self._get_input,
            # paired tags
            "ul": self._get_ul,
            "ol": self._get_ol,
            "li": self._get_li,
            "a": self._get_a,
            "code": self._get_code,
            "span": self._get_span,
            "tg-emoji": self._get_tg_emoji,
            "tg-spoiler": self._adapt_factory(Spoiler),
            "pre": self._get_pre,
            "blockquote": self._get_blockquote,
            "details": self._adapt_factory(Blockquote, expandable=True),
            "progress": self._get_progress,
            "meter": self._get_meter,
            "q": self._adapt_factory(Quote),
            "mark": self._get_mark,
        }

        update_map = partial(_add_map_keys, _map)
        group_f = self._adapt_factory(Group)

        # special
        update_map(("meta", "link"), self._adapt_factory(lambda: None))
        update_map(("html", "noscript", "body"), group_f)
        update_map(
            ("head", "script", "style", "template", "title"),
            self._adapt_factory(Stub),
        )
        # normal
        update_map(("b", "strong"), self._adapt_factory(Bold))
        update_map(
            ("i", "em", "cite", "var", "tt"),
            self._adapt_factory(Italic),
        )
        update_map(("s", "strike", "del"), self._adapt_factory(Strikethrough))
        update_map(("kbd", "samp"), self._adapt_factory(Code))
        update_map(
            ("div", "footer", "header", "main", "nav", "section"),
            self._adapt_factory(Group, block=True),
        )
        update_map(("output", "data", "time"), group_f)
        update_map(("p", "summary"), self._adapt_factory(Paragraph))
        update_map(("u", "ins"), self._adapt_factory(Underline))

        # special cases - h1-h6 need tag parameter
        for tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            _map[tag] = partial(self._get_h, tag=tag)

        return _map

    def _adapt_factory(
        self,
        factory: Callable[P, Optional[Entity]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> Callable[[Attrs], EntityPair]:
        def wrapper(attrs):
            inner = None
            entity = factory(*args, **kwargs)
            return inner, entity

        return wrapper

    def _fix_url(self, url: str | None) -> str | None:
        if url is None:
            return None
        if self._base_url is None:
            return url
        return urllib.parse.urljoin(self._base_url, url)

    def _find_attr(self, name: str, attrs: Attrs, default: Any = ""):
        return next((value for key, value in attrs if key == name), default)

    def _get_classes(self, attrs: Attrs):
        return self._find_attr("class", attrs).split()

    def _get_a(self, attrs: Attrs) -> EntityPair:
        inner = None
        url = self._find_attr("href", attrs)
        if url:
            return inner, Link(url=self._fix_url(url))
        return inner, Group()

    def _get_img(self, attrs: Attrs) -> EntityPair:
        inner = None
        url = self._find_attr("src", attrs)
        text = self._find_attr("alt", attrs, url)
        if not text and not url:
            return inner, None

        text_entity = Text(text="🖼️" + text)
        if not url:
            return inner, text_entity
        link = Link(url=self._fix_url(url))
        link.add(text_entity)
        return inner, link

    def _get_input(self, attrs: Attrs) -> EntityPair:
        inner = None
        type_ = self._find_attr("type", attrs)
        if type_ == "checkbox":
            checked = self._find_attr("checked", attrs, default=...)
            if checked is ...:
                return inner, Text(text="◻️")
            return inner, Text(text="☑️")
        if type_ == "radio":
            checked = self._find_attr("checked", attrs, default=...)
            if checked is ...:
                return inner, Text(text="⚪️")
            return inner, Text(text="🔘")

        value = self._find_attr("value", attrs)
        if value:
            return inner, Underline(entities=[Text(text=value)])
        return inner, Text(text="________")

    def _get_ul(self, attrs: Attrs) -> EntityPair:
        inner = None
        return inner, ListGroup(numbered=False)

    def _get_ol(self, attrs: Attrs) -> EntityPair:
        inner = None
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

        return inner, ListGroup(
            numbered=True,
            start=start,
            format=ol_format,
            reversed=is_reversed is not ...,
        )

    def _get_li(self, attrs: Attrs) -> EntityPair:
        inner = None
        value = self._find_attr("value", attrs)
        if value:
            value = int(value)
        else:
            value = None
        return inner, ListItem(value=value)

    def _get_span(self, attrs: Attrs) -> EntityPair:
        inner = None
        classes = self._get_classes(attrs)
        if "tg-spoiler" in classes:
            return inner, Spoiler()
        return inner, Group()

    def _get_language_class(self, attrs: Attrs):
        classes = self._get_classes(attrs)
        return next(
            (
                c[len(LANG_CLASS_PREFIX) :]
                for c in classes
                if c.startswith(LANG_CLASS_PREFIX)
            ),
            None,
        )

    def _get_code(self, attrs: Attrs) -> EntityPair:
        inner = None
        return inner, Code(language=self._get_language_class(attrs))

    def _get_pre(self, attrs: Attrs) -> EntityPair:
        inner = None
        return inner, Pre(language=self._get_language_class(attrs))

    def _get_blockquote(self, attrs: Attrs) -> EntityPair:
        inner = None
        return inner, Blockquote(
            expandable=self._find_attr("expandable", attrs, None) == "",
        )

    def _get_mark(self, attrs: Attrs) -> EntityPair:
        inner = Group()
        entity = Group()
        entity.add(Italic(entities=[Bold(entities=[inner])]))
        return inner, entity

    def _get_h(self, attrs: Attrs, tag: str) -> EntityPair:
        inner = Group()
        entity = Group(block=True)
        entity.add(Paragraph())
        if tag == "h1":
            entity.add(
                Bold(
                    entities=[
                        Underline(entities=[Uppercase(entities=[inner])]),
                    ],
                ),
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

    def _get_progress(self, attrs: Attrs) -> EntityPair:
        inner = None
        return inner, Progress(
            value=float(self._find_attr("value", attrs, "0")),
            max=float(self._find_attr("max", attrs, "1")),
            is_meter=False,
        )

    def _get_meter(self, attrs: Attrs) -> EntityPair:
        inner = None
        return inner, Progress(
            value=float(self._find_attr("value", attrs, "0")),
            min=float(self._find_attr("min", attrs, "0")),
            max=float(self._find_attr("max", attrs, "1")),
            is_meter=True,
        )

    def _get_tg_emoji(self, attrs: Attrs) -> EntityPair:
        inner = None
        emoji_id = self._find_attr("emoji-id", attrs)
        if emoji_id:
            return inner, Emoji(custom_emoji_id=emoji_id)
        else:
            return inner, Group()


def _add_map_keys(map, keys, default):
    map.update(dict.fromkeys(keys, default))
