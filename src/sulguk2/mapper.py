import urllib.parse
from functools import cached_property, partial
from typing import Any, Callable, List, Optional, Tuple

from sulguk.entities import (
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
from sulguk.render.numbers import NumberFormat

Attrs = List[Tuple[str, str]]  # html5lib returns empty string if no value

OL_FORMAT = {
    "1": NumberFormat.DECIMAL,
    "a": NumberFormat.LETTERS_LOWER,
    "A": NumberFormat.LETTERS_UPPER,
    "i": NumberFormat.ROMAN_LOWER,
    "I": NumberFormat.ROMAN_UPPER,
}

LANG_CLASS_PREFIX = "language-"

NO_CLOSING_TAGS = ("br", "wbr", "hr", "meta", "link", "img", "input")


class Mapper:
    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = base_url

    def match(
        self,
        tag: str,
        attrs: Attrs,
    ) -> Tuple[Optional[Entity], Optional[Entity]]:
        factory = self._map.get(tag)
        if factory is None:
            raise ValueError(f"Unsupported tag: {tag}")
        result = factory(attrs)
        if isinstance(result, tuple):
            inner_entity, outer_entity = result
        else:
            inner_entity = None
            outer_entity = result

        return inner_entity, outer_entity

    @cached_property
    def _map(
        self,
    ) -> dict[str, Callable[[Attrs], Tuple[Entity, Entity] | Entity | None]]:
        def _no_attrs(factory):
            return lambda attrs: factory()

        _map = {
            # single tags
            "br": _no_attrs(NewLine),
            "wbr": _no_attrs(ZeroWidthSpace),
            "hr": _no_attrs(HorizontalLine),
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
            "tg-spoiler": _no_attrs(Spoiler),
            "pre": self._get_pre,
            "blockquote": self._get_blockquote,
            "details": _no_attrs(partial(Blockquote, expandable=True)),
            "progress": self._get_progress,
            "meter": self._get_meter,
            "q": _no_attrs(Quote),
            "mark": self._get_mark,
        }

        def _add_map_keys(map, keys, default):
            map.update(dict.fromkeys(keys, default))

        update_map = partial(_add_map_keys, _map)
        group_f = _no_attrs(Group)

        # special
        update_map(("meta", "link"), _no_attrs(lambda: None))
        update_map(("html", "noscript", "body"), group_f)
        update_map(
            ("head", "script", "style", "template", "title"),
            _no_attrs(Stub),
        )
        # normal
        update_map(("b", "strong"), _no_attrs(Bold))
        update_map(("i", "em", "cite", "var", "tt"), _no_attrs(Italic))
        update_map(("s", "strike", "del"), _no_attrs(Strikethrough))
        update_map(("kbd", "samp"), _no_attrs(Code))
        update_map(
            ("div", "footer", "header", "main", "nav", "section"),
            _no_attrs(partial(Group, block=True)),
        )
        update_map(("output", "data", "time"), group_f)
        update_map(("p", "summary"), _no_attrs(Paragraph))
        update_map(("u", "ins"), _no_attrs(Underline))

        # special cases - h1-h6 need tag parameter
        for h_tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            _map[h_tag] = lambda attrs, tag=h_tag: self._get_h(tag, attrs)

        return _map

    def _fix_url(self, url: str | None) -> str | None:
        if url is None:
            return None
        if self._base_url is None:
            return url
        return urllib.parse.urljoin(self._base_url, url)

    def _find_attr(
        self,
        name: str,
        attrs: Attrs,
        default: Any = "",
    ):
        return next((value for key, value in attrs if key == name), default)

    def _get_classes(self, attrs: Attrs):
        return self._find_attr("class", attrs).split()

    def _get_a(self, attrs: Attrs) -> Entity:
        url = self._find_attr("href", attrs)
        if url:
            return Link(url=self._fix_url(url))
        return Group()

    def _get_img(self, attrs: Attrs) -> Optional[Entity]:
        url = self._find_attr("src", attrs)
        text = self._find_attr("alt", attrs, url)
        if not text and not url:
            return None

        text_entity = Text(text="🖼️" + text)
        if not url:
            return text_entity
        link = Link(url=self._fix_url(url))
        link.add(text_entity)
        return link

    def _get_input(self, attrs: Attrs) -> Optional[Entity]:
        type_ = self._find_attr("type", attrs)
        if type_ == "checkbox":
            checked = self._find_attr("checked", attrs, default=...)
            if checked is ...:
                return Text(text="◻️")
            return Text(text="☑️")
        if type_ == "radio":
            checked = self._find_attr("checked", attrs, default=...)
            if checked is ...:
                return Text(text="⚪️")
            return Text(text="🔘")

        value = self._find_attr("value", attrs)
        if value:
            return Underline(entities=[Text(text=value)])
        return Text(text="________")

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

    def _get_code(self, attrs: Attrs) -> Entity:
        return Code(language=self._get_language_class(attrs))

    def _get_pre(self, attrs: Attrs) -> Entity:
        return Pre(language=self._get_language_class(attrs))

    def _get_blockquote(self, attrs: Attrs) -> Entity:
        return Blockquote(
            expandable=self._find_attr("expandable", attrs, None) == "",
        )

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

    def _get_tg_emoji(self, attrs: Attrs) -> Entity:
        emoji_id = self._find_attr("emoji-id", attrs)
        if emoji_id:
            return Emoji(custom_emoji_id=emoji_id)
        else:
            return Group()
