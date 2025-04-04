"""
TODO:
* skip all except body
* process styles from file
"""

from dataclasses import dataclass
from functools import lru_cache
from typing import List, Iterable, Optional, Tuple
from xml.etree.ElementTree import Element

import cssselect2
import html5lib
import tinycss2
from cssselect2 import ElementWrapper
from cssselect2.compiler import CompiledSelector
from tinycss2.ast import QualifiedRule, Node, IdentToken

from sulguk import RenderResult
from sulguk.data import NumberFormat
from sulguk.entities import Group, Entity, Text, Bold, Italic, Underline, Strikethrough, ListGroup, ListItem, Link, \
    HorizontalLine, ZeroWidthSpace, NewLine, Spoiler, Code, Pre, Blockquote, Progress, Quote, Uppercase
from sulguk.entities.base import Invisible, Spacer
from sulguk.entities.decoration import Lowercase, Capitalize
from sulguk.entities.wrapper import Wrapper
from sulguk.render import State
from sulguk.transformer import OL_FORMAT

Value = (
        tinycss2.ast.NumberToken |
        tinycss2.ast.StringToken |
        tinycss2.ast.IdentToken |
        tinycss2.ast.LiteralToken |
        tinycss2.ast.UnicodeRangeToken |
        tinycss2.ast.URLToken |
        tinycss2.ast.DimensionToken |
        tinycss2.ast.HashToken
)


def _has_ident_token(values: list[Value] | None, expected: list[str]) -> bool:
    if not values:
        return False
    return any(
        value.lower_value in expected
        for value in values
        if isinstance(value, tinycss2.ast.IdentToken)
    )


@dataclass
class Style:
    custom_tg_spoiler: list[str] | None = None
    display: list[Value] | None = None
    font_weight: list[Value] | None = None
    font_style: list[Value] | None = None
    text_decoration: list[Value] | None = None
    margin_top: list[Value] | None = None
    margin_bottom: list[Value] | None = None
    margin_left: list[Value] | None = None
    margin_right: list[Value] | None = None
    white_space: list[Value] | None = None
    font_family: list[Value] | None = None
    text_transform: list[Value] | None = None

    list_style_type: list[Value] | None = None

    @property
    def list_number_format(self) -> NumberFormat | str | None:
        if not self.list_style_type:
            return None
        value = next(
            (
                value.lower_value
                for value in self.list_style_type
                if isinstance(value, tinycss2.ast.IdentToken)
            ),
            None
        )
        if not value or value == "none":
            return None
        if value == "disc":
            return "•"
        if value == "circle":
            return "◦"
        if value == "square":
            return "▪️"
        if value == "decimal":
            return NumberFormat.DECIMAL
        if value == "lower-roman":
            return NumberFormat.ROMAN_LOWER
        if value == "upper-roman":
            return NumberFormat.ROMAN_UPPER
        if value in ("lower-alpha", "lower-latin"):
            return NumberFormat.LETTERS_LOWER
        if value in ("upper-alpha", "upper-latin"):
            return NumberFormat.LETTERS_UPPER
        return NumberFormat.DECIMAL

    @property
    def is_block(self) -> bool:
        return _has_ident_token(self.display, ["block"])

    @property
    def is_list_item(self) -> bool:
        return _has_ident_token(self.display, ["list-item"])

    @property
    def is_visible(self) -> bool:
        return not _has_ident_token(self.display, ["none"])

    @property
    def is_bold(self) -> bool:
        return _has_ident_token(self.font_weight, ["bolder", "bold"])

    @property
    def is_italic(self) -> bool:
        return _has_ident_token(self.font_style, ["italic"])

    @property
    def is_underline(self) -> bool:
        return _has_ident_token(self.text_decoration, ["underline"])

    @property
    def is_strike_through(self) -> bool:
        return _has_ident_token(self.text_decoration, ["line-through"])

    @property
    def is_pre(self) -> bool:
        return _has_ident_token(self.white_space, ["pre"])

    @property
    def is_code(self) -> bool:
        return _has_ident_token(self.font_family, ["monospace"])

    @property
    def text_transform_value(self) -> str | None:
        if not self.text_transform:
            return None
        return next((v.lower_value for v in self.text_transform if isinstance(v, IdentToken)), None)

    @property
    def top_offset(self):
        if not self.margin_top:
            return 0
        for value in self.margin_top:
            if isinstance(value, tinycss2.ast.DimensionToken | tinycss2.ast.NumberToken):
                return self._normalize_size(value)
        return 0

    @property
    def bottom_offset(self):
        if not self.margin_top:
            return 0
        for value in self.margin_top:
            if isinstance(value, tinycss2.ast.DimensionToken | tinycss2.ast.NumberToken):
                return self._normalize_size(value)
        return 0

    def _normalize_size(self, value: tinycss2.ast.DimensionToken | tinycss2.ast.NumberToken):
        if isinstance(value, tinycss2.ast.NumberToken):
            return int(value.value // 8)
        if value.lower_unit == "px":
            return int(value.value // 8)
        if value.lower_unit == "em":
            return int(value.value)
        return 0

    @property
    def is_tg_spoiler(self) -> bool:
        return bool(self.custom_tg_spoiler)


@dataclass
class Declaration:
    name: str
    important: bool
    value: list[Value]


class CssValueChecker:
    def _unpack_property(self, d: Declaration) -> Iterable[tuple[str, list[Value]]]:
        if d.name == "margin":
            if len(d.value) == 1:
                yield "margin_top", d.value
                yield "margin_right", d.value
                yield "margin_bottom", d.value
                yield "margin_left", d.value
            elif len(d.value) == 2:
                yield "margin_top", [d.value[0]]
                yield "margin_right", [d.value[1]]
                yield "margin_bottom", [d.value[0]]
                yield "margin_left", [d.value[1]]
            elif len(d.value) == 3:
                yield "margin_top", [d.value[0]]
                yield "margin_right", [d.value[1]]
                yield "margin_bottom", [d.value[2]]
                yield "margin_left", [d.value[1]]
            elif len(d.value) == 4:
                yield "margin_top", [d.value[0]]
                yield "margin_right", [d.value[1]]
                yield "margin_bottom", [d.value[2]]
                yield "margin_left", [d.value[3]]
        else:
            if d.name.startswith("--"):
                name = "custom_" + d.name[2:]
            else:
                name = d.name
            yield name.replace("-", "_"), d.value

    def _apply_style(self, style: Style, d: Declaration) -> None:
        for name, value in self._unpack_property(d):
            setattr(style, name, value)

    def calculate_style(self, selectors: list[CompiledSelector]) -> Style:
        style = Style()
        for selector in selectors:
            for d in selector[-1]:
                self._apply_style(style, d)
        for selector in selectors:
            for d in selector[-1]:
                if d.important:
                    self._apply_style(style, d)
        return style


Attrs = List[Tuple[str, Optional[str]]]
XHTML_NAMESPACE = "http://www.w3.org/1999/xhtml"
LANG_CLASS_PREFIX = "language-"


@lru_cache(maxsize=None)
def xhtml_tag(name: str):
    return f"{{{XHTML_NAMESPACE}}}{name}"


class Transformer:
    def __init__(self):
        self.checker = CssValueChecker()
        self.root = Group()
        self.entities: List[Entity] = [self.root]

    def _a(self, entity: Wrapper, element: Element) -> None:
        url = element.attrib.get("href")
        if url:
            entity.enter(Link(url=url))

    def _hr(self, entity: Wrapper, element: Element) -> None:
        entity.enter(HorizontalLine())

    def _wbr(self, entity: Wrapper, element: Element) -> None:
        entity.enter(ZeroWidthSpace())

    def _br(self, entity: Wrapper, element: Element) -> None:
        entity.enter(NewLine())

    def _q(self, entity: Wrapper, element: Element) -> None:
        entity.enter(Quote())

    def _blockquote(self, entity: Wrapper, element: Element) -> None:
        entity.enter(Blockquote())

    def _meter(self, entity: Wrapper, element: Element) -> None:
        entity.enter(Progress(
            value=float(element.attrib.get("value", "0")),
            min=float(element.attrib.get("min", "0")),
            max=float(element.attrib.get("max", "1")),
            is_meter=True,
        ))

    def _progress(self, entity: Wrapper, element: Element) -> None:
        entity.enter(Progress(
            value=float(element.attrib.get("value", "0")),
            max=float(element.attrib.get("max", "1")),
            is_meter=False,
        ))

    def _img(self, entity: Wrapper, element: Element) -> None:
        url = element.attrib.get("src")
        text = element.attrib.get("alt", url)
        if not text and not url:
            return
        if url:
            entity.enter(Link(url=url))
        entity.enter(Text(text="🖼️" + text))

    def _set_li(self, listitem: ListItem, element: Element) -> None:
        value = element.attrib.get("value")
        if value:
            listitem.value = int(value)

    def _set_ol(self, listgroup: ListGroup, element: Element) -> None:
        start = element.attrib.get("start")
        if start is not None:
            listgroup.start = int(start)

        is_reversed = element.attrib.get("reversed", ...)
        if is_reversed is not ...:
            listgroup.reversed = True

        type_ = element.attrib.get("type")
        if type_ is not None:
            listgroup.format = OL_FORMAT[type_]

    def _get_classes(self, element: Element):
        return element.attrib.get("class", "").split()

    def _get_language_class(self, element: Element) -> Optional[str]:
        classes = self._get_classes(element)
        return next(
            (
                c[len(LANG_CLASS_PREFIX):]
                for c in classes
                if c.startswith(LANG_CLASS_PREFIX)
            ),
            None,
        )

    def handle_tag_open(
            self,
            element: Element,
            selectors: list[CompiledSelector],
    ):
        style = self.checker.calculate_style(selectors)
        if not style.is_visible:
            self.entities.append(Invisible())
            return
        entity = Wrapper(
            Group(block=style.is_block),
        )
        if style.is_list_item:
            child = ListItem([entity])
            if element.tag == xhtml_tag("li"):
                self._set_li(child, element)
        else:
            child = entity
        if style.is_bold:
            entity.enter(Bold())
        if style.is_italic:
            entity.enter(Italic())
        if style.is_underline:
            entity.enter(Underline())
        if style.is_strike_through:
            entity.enter(Strikethrough())
        if style.is_tg_spoiler:
            entity.enter(Spoiler())
        if style.is_pre:
            entity.enter(Pre(language=self._get_language_class(element)))
        if style.is_code:
            entity.enter(Code(language=self._get_language_class(element)))
        print(element.tag, style.text_transform_value, style.text_transform)
        if text_transform := style.text_transform_value:
            if text_transform == "uppercase":
                entity.enter(Uppercase())
            if text_transform == "lowercase":
                entity.enter(Lowercase())
            if text_transform == "capitalize":
                entity.enter(Capitalize())
        for _ in range(style.top_offset):
            entity.add(Spacer())

        list_format = style.list_number_format
        if list_format is not None:
            list_group = ListGroup()
            child.enter(list_group)
            if isinstance(list_format, NumberFormat):
                list_group.format = list_format
                list_group.numbered = True
            elif isinstance(list_format, str):
                list_group.symbol = list_format

            if element.tag == xhtml_tag("ol"):
                self._set_ol(list_group, element)
        if element.tag == xhtml_tag("a"):
            self._a(entity, element)
        if element.tag == xhtml_tag("img"):
            self._img(entity, element)
        if element.tag == xhtml_tag("hr"):
            self._hr(entity, element)
        if element.tag == xhtml_tag("wbr"):
            self._wbr(entity, element)
        if element.tag == xhtml_tag("br"):
            self._br(entity, element)
        if element.tag == xhtml_tag("blockquote"):
            self._blockquote(entity, element)
        if element.tag == xhtml_tag("progress"):
            self._progress(entity, element)
        if element.tag == xhtml_tag("meter"):
            self._meter(entity, element)
        if element.tag == xhtml_tag("q"):
            self._q(entity, element)

        self.entities[-1].add(child)
        self.entities.append(child)

    def handle_text(self, text: str | None):
        if text is not None:
            self.entities[-1].add(Text(text))

    def handle_tag_close(self, selectors: list[CompiledSelector]):
        style = self.checker.calculate_style(selectors)
        entity = self.entities[-1]
        for _ in range(style.bottom_offset):
            entity.add(Spacer())
        self.entities.pop()

    def walk(
            self,
            token: ElementWrapper,
            css_matcher: cssselect2.Matcher,
    ):
        selectors = css_matcher.match(token)
        self.handle_tag_open(
            token.etree_element,
            selectors,
        )
        self.handle_text(token.etree_element.text)
        for child in token.iter_children():
            self.walk(child, css_matcher)
        self.handle_tag_close(selectors)
        self.handle_text(token.etree_element.tail)


treebuilder = html5lib.getTreeBuilder('etree')
parser = html5lib.HTMLParser(tree=treebuilder)


def rules_to_matcher(rules: list[Node]):
    matcher = cssselect2.Matcher()
    for rule in rules:
        if not isinstance(rule, QualifiedRule):
            continue
        selectors = cssselect2.compile_selector_list(rule.prelude)
        for selector in selectors:
            declarations = tinycss2.parse_declaration_list(rule.content, skip_whitespace=True, skip_comments=True)
            payload = [
                Declaration(
                    name=d.lower_name,
                    important=d.important,
                    value=[v for v in d.value if not isinstance(v, tinycss2.ast.WhitespaceToken)],
                )
                for d in declarations
            ]
            matcher.add_selector(selector, payload)
    return matcher


def parse_html(css, html):
    rules = tinycss2.parse_stylesheet(css, skip_whitespace=True, skip_comments=True)
    wrapper = cssselect2.ElementWrapper.from_html_root(parser.parse(html))
    transformer = Transformer()
    transformer.walk(wrapper, rules_to_matcher(rules))

    state = State()
    transformer.root.render(state)
    return RenderResult(
        text=state.canvas.text,
        entities=state.entities,
    )
