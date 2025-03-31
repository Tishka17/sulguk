"""
TODO:
* skip all except body
* process styles from file
"""

from dataclasses import dataclass
from typing import List
from xml.etree.ElementTree import Element

import cssselect2
import html5lib
import tinycss2
from cssselect2 import ElementWrapper
from cssselect2.compiler import CompiledSelector
from tinycss2.ast import QualifiedRule, Node

from sulguk import RenderResult
from sulguk.entities import Group, Entity, Text, Bold, Italic, Underline, Strikethrough, Paragraph, Blockquote
from sulguk.entities.base import Invisible
from sulguk.entities.wrapper import Wrapper
from sulguk.render import State

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


@dataclass
class Declaration:
    name: str
    important: bool
    value: list[Value]


class CssValueChecker:
    def _get_first(self, selectors: list[CompiledSelector], names: list[str]) -> Declaration | None:
        for selector in selectors[::-1]:
            for d in selector[-1]:
                if d.important and d.name in names:
                    return d
        for selector in selectors[::-1]:
            for d in selector[-1]:
                if d.name in names:
                    return d
        return None

    def is_block(self, selectors: list[CompiledSelector]):
        if not (d := self._get_first(selectors, ["display"])):
            return False
        for value in d.value:
            if not isinstance(value, tinycss2.ast.IdentToken):
                break
            if value.lower_value == "block":
                return True
        return False

    def is_visible(self, selectors: list[CompiledSelector]):
        if (d := self._get_first(selectors, ["display"])):
            for value in d.value:
                if not isinstance(value, tinycss2.ast.IdentToken):
                    break
                if value.lower_value == "none":
                    return False
        return True

    def is_bold(self, selectors: list[CompiledSelector]):
        if not (d := self._get_first(selectors, ["font-weight"])):
            return False
        for value in d.value:
            if not isinstance(value, tinycss2.ast.IdentToken):
                break
            if value.lower_value in ("bolder", "bold"):
                return True
        return False

    def is_italic(self, selectors: list[CompiledSelector]):
        if not (d := self._get_first(selectors, ["font-style"])):
            return False
        for value in d.value:
            if not isinstance(value, tinycss2.ast.IdentToken):
                break
            if value.lower_value in ("italic",):
                return True
        return False

    def is_underline(self, selectors: list[CompiledSelector]):
        if not (d := self._get_first(selectors, ["text-decoration"])):
            return False
        for value in d.value:
            if not isinstance(value, tinycss2.ast.IdentToken):
                break
            if value.lower_value in ("underline",):
                return True
        return False

    def is_strikethrough(self, selectors: list[CompiledSelector]):
        if not (d := self._get_first(selectors, ["text-decoration"])):
            return False
        for value in d.value:
            if not isinstance(value, tinycss2.ast.IdentToken):
                break
            if value.lower_value in ("line-through",):
                return True
        return False

    def _is_big_offset(self, value: tinycss2.ast.DimensionToken | tinycss2.ast.NumberToken):
        if isinstance(value, tinycss2.ast.NumberToken):
            return value.value > 8
        if value.lower_unit == "px":
            return value.value > 8
        if value.lower_unit == "em":
            return value.value > 1
        return False

    def has_margin_top(self, selectors: list[CompiledSelector]):
        if not (d := self._get_first(selectors, ["margin-top", "margin"])):
            return False
        if d.name == "margin-top":
            return self._is_big_offset(d.value[0])
        elif d.name == "margin":
            return self._is_big_offset(d.value[0])

    def has_margin_left(self, selectors: list[CompiledSelector]):
        if not (d := self._get_first(selectors, ["margin-left", "margin"])):
            return False
        if d.name == "margin-left":
            return self._is_big_offset(d.value[0])
        elif d.name == "margin":
            if len(d.value) == 1:
                return self._is_big_offset(d.value[0])
            elif len(d.value) == 2:
                return self._is_big_offset(d.value[1])
            elif len(d.value) == 3:
                return self._is_big_offset(d.value[1])
            else:
                return self._is_big_offset(d.value[3])


class Transformer:
    def __init__(self):
        self.checker = CssValueChecker()
        self.root = Group()
        self.entities: List[Entity] = [self.root]

    def handle_tag_open(
            self,
            element: Element,
            selectors: list[CompiledSelector],
    ):
        if not self.checker.is_visible(selectors):
            self.entities.append(Invisible())
            return
        entity = Wrapper(
            Group(block=self.checker.is_block(selectors)),
        )
        if self.checker.is_bold(selectors):
            entity.enter(Bold())
        if self.checker.is_italic(selectors):
            entity.enter(Italic())
        if self.checker.is_underline(selectors):
            entity.enter(Underline())
        if self.checker.is_strikethrough(selectors):
            entity.enter(Strikethrough())
        if self.checker.has_margin_top(selectors):
            entity.enter(Paragraph())
        if self.checker.has_margin_left(selectors):
            entity.enter(Blockquote())
        self.entities[-1].add(entity)
        self.entities.append(entity)

    def handle_text(self, text: str | None):
        if text is not None:
            self.entities[-1].add(Text(text))

    def handle_tag_close(self):
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
        self.handle_tag_close()
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
