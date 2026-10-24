"""Convert sulguk-flavoured HTML into Telegram Rich Message blocks.

The result is a list of plain dicts matching ``InputRichBlock*`` of Bot API
10.1+, suitable for the ``blocks`` field of ``InputRichMessage``. aiogram
converts such dicts to its models itself, so this module does not import it.

Supported: paragraphs, headings, preformatted text, footers, dividers,
lists (with checkboxes and numbering), block quotations (plain, expandable
and pull quotes), details, tables, all inline formatting, media (photo,
video, animation, audio, voice note, document), figures with captions,
collages, slideshows, maps, anchors, inline buttons and button rows.

Media is referenced by an HTTP(S) URL or a file_id in ``src``; ``tg://``
links of the html format are not applicable here. ``<tg-thinking>`` is
accepted by Telegram only in ``sendRichMessageDraft``.

How it works: every inline element is converted to a flat list of rich
texts (strings and formatted texts) with spaces left as they are in HTML.
``RichTextList.clean`` turns such a list into the final rich text. Block
elements are converted to blocks by the ``_block_*`` methods, and blocks
know how to make the dicts of Telegram.
"""
import posixpath
import re
import urllib.parse
from dataclasses import dataclass
from functools import cached_property, partial
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from lxml.etree import Element

from sulguk.wrapper import parse_html
from .converter import RichConverter
from .dom import children, first_child, plain_text, pre_text
from .entities import (
    Anchor,
    AnchorBlock,
    BlockquoteBlock,
    Button,
    ButtonAction,
    ButtonRowBlock,
    ButtonText,
    CallbackDataAction,
    Caption,
    CopyTextAction,
    CustomEmoji,
    DetailsBlock,
    DisabledAction,
    DividerBlock,
    ExpandableBlockquoteBlock,
    FooterBlock,
    FormattedText,
    GalleryBlock,
    HeadingBlock,
    ListBlock,
    ListItemBlock,
    LoginUrlAction,
    MapBlock,
    MathBlock,
    MathExpression,
    MediaBlock,
    ParagraphBlock,
    PreBlock,
    PullquoteBlock,
    RichBlock,
    RichText,
    RichTextList,
    SwitchInlineQueryAction,
    SwitchInlineQueryChosenChatAction,
    SwitchInlineQueryCurrentChatAction,
    TableBlock,
    TableCell,
    Text,
    ThinkingBlock,
    UrlAction,
    WebAppAction,
)
from .tags import (
    BLOCK_CONTAINERS,
    CONTAINER_TAGS,
    DROPPED_TAGS,
    FLAT_BLOCKS,
    LIST_INDENT,
    FORMAT_TAGS,
    HEADING_TAGS,
    MEDIA_KINDS,
    OL_TYPES,
    QUOTE_MARK,
    RULE,
    SEPARATE_BLOCKS,
    TABLE_INLINE_TAGS,
    TABLE_SECTIONS,
    TRANSPARENT_TAGS,
)
from .html_parsing import (
    BUTTON_LIKE_INPUT_TYPES,
    ZERO_WIDTH_SPACE,
    collapse_html_spaces,
    parse_int_attr,
)

BUTTON_ALIGNS = ("left", "center", "right")
BUTTON_STYLES = ("danger", "success", "primary", "link")
MAX_BUTTONS = 8

_CHAT_KINDS = ("user", "bot", "group", "channel")
_ANIMATION_EXTENSIONS = frozenset({".gif"})
_VOICE_EXTENSIONS = frozenset({".ogg", ".oga", ".opus"})
_SPOILER_KINDS = frozenset({"photo", "video", "animation"})
# file_id of an already uploaded file has only these symbols, so it is
# neither a relative URL nor must it be joined with base_url
_FILE_ID = re.compile("[A-Za-z0-9_-]+")

Items = List[RichText]


@dataclass
class RichBlocksResult:
    blocks: List[Dict[str, Any]]


class ParagraphRun:
    """Blocks of an element: inline items wait here to be a paragraph."""

    def __init__(self) -> None:
        self.blocks: List[RichBlock] = []
        self._items: Items = []
        # the last block is a paragraph made of a container with only text
        self._last_is_lines = False

    def add(self, items: Items) -> None:
        self._items.extend(items)

    def flush(self) -> None:
        """Make a block of the waiting items, if there is anything."""
        text = RichTextList(self._items).clean()
        self._items = []
        if len(text.parts) == 1 and isinstance(text.parts[0], Anchor):
            # an empty <a name="..."></a> on its own is an anchor block
            self.blocks.append(AnchorBlock(text.parts[0].name))
            self._last_is_lines = False
        elif not text.is_empty():
            self.blocks.append(ParagraphBlock(text))
            self._last_is_lines = False

    def add_blocks(self, blocks: List[RichBlock], is_lines: bool) -> None:
        """Add blocks of a child, ``is_lines``: it is a text container."""
        if is_lines and self._last_is_lines:
            # as in the old mode, neighbour containers are lines of one
            # block, only a real <p> is a paragraph of its own
            text = join_paragraphs([self.blocks[-1], *blocks])
            self.blocks[-1] = ParagraphBlock(text)
        else:
            self.blocks.extend(blocks)
            self._last_is_lines = is_lines


def join_paragraphs(blocks: List[RichBlock]) -> RichTextList:
    """Paragraphs of one text, separated by line breaks."""
    parts: Items = []
    for block in blocks:
        if parts:
            parts.append(Text("\n"))
        parts.extend(block.text.parts)  # type: ignore[attr-defined]
    return RichTextList(parts).clean()


def non_empty(text: RichTextList) -> Optional[RichTextList]:
    """The text, ``None`` if there is nothing in it."""
    return None if text.is_empty() else text


class BlocksConverter(RichConverter):
    # ---- which method converts which tag

    @cached_property
    def _inline_handlers(self) -> Dict[str, Callable[[Element], Items]]:
        """Inline tags with their own method, formatting tags are in
        ``FORMAT_TAGS``. Each method returns a list of items."""
        return {
            "span": self._inline_span,
            "br": self._inline_br,
            "wbr": self._inline_wbr,
            "q": self._inline_q,
            "a": self._inline_a,
            "input": self._inline_input,
            "progress": self._inline_progress,
            "meter": self._inline_progress,
            "tg-emoji": self._inline_tg_emoji,
            "tg-time": self._inline_tg_time,
            "tg-math": self._inline_tg_math,
            "tg-reference": self._inline_tg_reference,
            "tg-button": self._inline_tg_button,
        }

    @cached_property
    def _block_handlers(
        self,
    ) -> Dict[str, Callable[[Element], List[RichBlock]]]:
        """Every tag which is a separate block. Each method returns a list
        of blocks. Other tags are a part of text."""
        handlers: Dict[str, Callable[[Element], List[RichBlock]]] = {
            # text
            "p": self._block_paragraph,
            "summary": self._block_paragraph,
            "footer": self._block_footer,
            "tg-thinking": self._block_thinking,
            "pre": self._block_pre,
            "tg-math-block": self._block_tg_math_block,
            "hr": self._block_hr,
            # nesting
            "blockquote": self._block_blockquote,
            "details": self._block_details,
            "aside": self._block_aside,
            "ul": self._block_ul,
            "ol": self._block_ol,
            # li outside of a list behaves like a container too
            "li": self._block_container,
            "table": self._block_table,
            # media
            "img": self._block_media,
            "video": self._block_media,
            "audio": self._block_media,
            "tg-document": self._block_media,
            "tg-map": self._block_map,
            "figure": self._block_figure,
            "tg-collage": partial(self._block_gallery, "collage"),
            "tg-slideshow": partial(self._block_gallery, "slideshow"),
            # buttons
            "tg-button-row": self._block_tg_button_row,
        }
        for tag in BLOCK_CONTAINERS:
            handlers[tag] = self._block_container
        for tag in HEADING_TAGS:
            handlers[tag] = self._block_heading
        return handlers

    @cached_property
    def _actions(
        self,
    ) -> Dict[str, Callable[[Mapping[str, str]], ButtonAction]]:
        """Button type -> the action of the button."""
        return {
            "url": self._action_url,
            "callback_data": self._action_callback_data,
            "web_app": self._action_web_app,
            "login_url": self._action_login_url,
            "switch_inline_query": self._action_switch_inline_query,
            "switch_inline_query_current_chat": (
                self._action_switch_inline_query_current_chat
            ),
            "switch_inline_query_chosen_chat": (
                self._action_switch_inline_query_chosen_chat
            ),
            "copy_text": self._action_copy_text,
            "disabled": self._action_disabled,
        }

    # ---- inline: every method returns a list of items

    def _text(self, text: Optional[str]) -> Items:
        return [Text(collapse_html_spaces(text))] if text else []

    def _wrap(self, type_: str, inner: Items, **extra: Any) -> Items:
        """Inline item with formatting, nothing if there is nothing to
        format."""
        if not inner:
            return []
        return [FormattedText(type_, RichTextList(inner), extra)]

    def _inline_children(
        self, elem: Element, skip: Optional[Element] = None,
    ) -> Items:
        items = self._text(elem.text)
        for child in children(elem):
            if child is not skip:
                items.extend(self._inline(child))
            items.extend(self._text(child.tail))
        return items

    def rich(
        self, elem: Optional[Element], skip: Optional[Element] = None,
    ) -> RichTextList:
        """Final rich text of the element content, empty if there is none."""
        if elem is None:
            return RichTextList()
        return RichTextList(self._inline_children(elem, skip)).clean()

    def _inline(self, elem: Element) -> Items:
        tag = str(elem.tag)
        if tag in DROPPED_TAGS:
            return []
        if tag in MEDIA_KINDS and self.inside_text_only(elem):
            return self._inline_media(elem)
        if tag in SEPARATE_BLOCKS:
            raise ValueError(
                f"<{tag}> must be a separate block, "
                "it cannot be a part of inline text",
            )
        if tag == "figcaption":
            raise ValueError(
                "<figcaption> is allowed only inside <figure>, "
                "<tg-collage> or <tg-slideshow>",
            )
        if tag in FORMAT_TAGS:
            return self._wrap(FORMAT_TAGS[tag], self._inline_children(elem))
        if tag in ("ul", "ol") and self.flat_list_depth(elem) is not None:
            return self._inline_list(elem)
        if tag in TABLE_SECTIONS or tag in TABLE_INLINE_TAGS:
            return self._inline_table(elem)
        if tag == "blockquote" and self.inside_text_only(elem):
            return self._inline_quote(elem)
        if tag == "pre" and self.inside_text_only(elem):
            return self._inline_pre(elem)
        if tag == "details" and self.inside_text_only(elem):
            return self._inline_details(elem)
        if tag in FLAT_BLOCKS and self.inside_text_only(elem):
            return self._inline_line(elem)

        handler = self._inline_handlers.get(tag)
        if handler is not None:
            return handler(elem)
        if tag in self._block_handlers or tag in TRANSPARENT_TAGS:
            return self._inline_children(elem)
        raise ValueError(f"Unsupported tag: {tag}")

    def _inline_span(self, elem: Element) -> Items:
        inner = self._inline_children(elem)
        if "tg-spoiler" in elem.get("class", "").split():
            return self._wrap("spoiler", inner)
        return inner

    def _inline_br(self, elem: Element) -> Items:
        return [Text("\n")]

    def _inline_list(self, elem: Element) -> Items:
        """A list in a table cell: a line for every item, with a mark and an
        indent of a nested list, like the old mode writes it."""
        marks = self.list_marks(elem)
        if not marks:
            return []
        indent = LIST_INDENT * (self.flat_list_depth(elem) or 0)
        items: Items = []
        if self.has_content_before(elem):
            items.append(Text("\n"))
        for index, (li, mark) in enumerate(marks):
            if index:
                items.append(Text("\n"))
            items.append(Text(indent + mark))
            items.extend(self._inline_children(li))
        if self.has_content_after(elem):
            items.append(Text("\n"))
        return items

    def _inline_media(self, elem: Element) -> Items:
        """A media in a text-only element: an icon with a link to the file."""
        in_cell = self.in_cell(elem)
        label, href = self.flat_media(elem, nested=in_cell)
        if href is None:
            return [Text(label)]
        if in_cell and self.is_button_url(href):
            return [self._url_button(label, href)]
        type_, extra = self._link(href)
        return self._wrap(type_, [Text(label)], **extra)

    def _url_button(self, label: str, href: str) -> ButtonText:
        return ButtonText(Button(RichTextList([Text(label)]), UrlAction(href)))

    def _inline_quote(self, elem: Element) -> Items:
        """A quotation in a text-only element: Telegram cannot nest a block
        there, so it is a separate line with a bar, not glued to the text
        around it."""
        items: Items = []
        if self.has_content_before(elem):
            items.append(Text("\n"))
        items.append(Text(QUOTE_MARK))
        items.extend(self._inline_children(elem))
        if self.has_content_after(elem):
            items.append(Text("\n"))
        return items

    def _inline_details(self, elem: Element) -> Items:
        """``<details>`` in a text-only element cannot be folded: a line
        with the summary, and the body under it as a spoiler."""
        summary, has_body = self.details_parts(elem)
        items: Items = []
        if self.has_content_before(elem):
            items.append(Text("\n"))
        if summary is not None:
            items.extend(self._inline_children(summary))
        if has_body:
            if summary is not None:
                items.append(Text("\n"))
            items.extend(
                self._wrap("spoiler", self._inline_children(elem, summary)),
            )
        if self.line_after(elem):
            items.append(Text("\n"))
        return items

    def _inline_line(self, elem: Element) -> Items:
        """A heading, a paragraph, a divider, a footer, a formula or
        ``<details>`` in a text-only element: a line of its own, a divider is
        a line of ``RULE``."""
        if self.flat_blank(elem):
            return []
        tag = str(elem.tag)
        body: Items
        if tag == "hr":
            body = [Text(RULE)]
        elif tag == "tg-math-block":
            body = [Text(plain_text(elem))]
        else:
            body = self._inline_children(elem)
        items: Items = []
        if self.has_content_before(elem):
            items.append(Text("\n"))
        items.extend(body)
        if self.line_after(elem):
            items.append(Text("\n"))
        return items

    def _inline_pre(self, elem: Element) -> Items:
        """``<pre>`` in a text-only element: its text with the line breaks
        and spaces kept, on lines of its own."""
        text = pre_text(elem)
        if text.startswith("\n"):
            text = text[1:]
        items: Items = []
        if self.has_content_before(elem):
            items.append(Text("\n"))
        if text.strip():
            items.append(Text(text))
        if self.has_content_after(elem):
            items.append(Text("\n"))
        return items

    def _inline_table(self, elem: Element) -> Items:
        """A table in a text-only element: its cells as text, cells of a
        row separated by a space, rows by a line break."""
        tag = str(elem.tag)
        if tag in ("td", "th", "caption"):
            return self._inline_children(elem)
        separator = " " if tag == "tr" else "\n"
        items: Items = []
        for index, child in enumerate(children(elem)):
            if index:
                items.append(Text(separator))
            items.extend(self._inline(child))
        return items

    def _inline_wbr(self, elem: Element) -> Items:
        return [Text(ZERO_WIDTH_SPACE)]

    def _inline_q(self, elem: Element) -> Items:
        return [Text("“"), *self._inline_children(elem), Text("”")]

    def _inline_a(self, elem: Element) -> Items:
        href = elem.get("href", "")
        name = elem.get("name", "")
        inner = self._inline_children(elem)
        anchor: Items = [Anchor(name)] if name else []

        if href and self.in_cell(elem):
            link = self.cell_link(elem)
            if link is not None:
                media, label, url = link
                items = [b for m in media for b in self._inline_media(m)]
                if label:
                    items.append(self._url_button(label, url))
                return [*anchor, *items]
        if not href:
            return anchor + inner
        if not inner:
            return anchor
        type_, extra = self._link(href)
        return [*anchor, *self._wrap(type_, inner, **extra)]

    def _link(self, href: str) -> Tuple[str, Dict[str, Any]]:
        """Type and fields of a link rich text without its text."""
        if href.startswith("#"):
            return "anchor_link", {"anchor_name": href[1:]}
        if href.startswith("mailto:"):
            return "email_address", {"email_address": href[7:]}
        if href.startswith("tel:"):
            return "phone_number", {"phone_number": href[4:]}
        if href.startswith("tg://user?id="):
            user_id = int(href.split("=", 1)[1])
            user = {"id": user_id, "is_bot": False, "first_name": ""}
            return "text_mention", {"user": user}
        return "url", {"url": self.url(href)}

    def _inline_tg_emoji(self, elem: Element) -> Items:
        emoji_id = elem.get("emoji-id", "")
        alternative = plain_text(elem) or " "
        if not emoji_id:
            return [Text(alternative)]
        return [CustomEmoji(emoji_id, alternative)]

    def _inline_tg_time(self, elem: Element) -> Items:
        inner = self._inline_children(elem)
        unix = elem.get("unix")
        if unix is None:
            return inner
        return self._wrap(
            "date_time",
            inner or [Text(" ")],
            unix_time=int(unix),
            date_time_format=elem.get("format", ""),
        )

    def _inline_tg_math(self, elem: Element) -> Items:
        return [MathExpression(plain_text(elem))]

    def _inline_tg_reference(self, elem: Element) -> Items:
        inner = self._inline_children(elem)
        name = elem.get("name", "")
        if not name:
            return inner
        return self._wrap("reference", inner, name=name)

    def _inline_input(self, elem: Element) -> Items:
        if elem.get("type") in BUTTON_LIKE_INPUT_TYPES:
            label, attrs = self.input_button(elem)
            text = RichTextList([Text(label)])
            return [ButtonText(self._make_button(attrs, text))]
        symbol = self.input_symbol(elem)
        if symbol:
            return [Text(symbol)]
        value = elem.get("value", "")
        if value:
            return self._wrap("underline", [Text(value)])
        return [Text("________")]

    def _inline_progress(self, elem: Element) -> Items:
        return [Text(self.progress_text(elem))]

    def _inline_tg_button(self, elem: Element) -> Items:
        return [ButtonText(self._button(elem))]

    # ---- buttons

    def _button(self, elem: Element) -> Button:
        return self._make_button(elem.attrib, self.rich(elem))

    def _make_button(
        self, attrs: Mapping[str, str], text: RichTextList,
    ) -> Button:
        """Button of ``RichMessageButton`` shape."""
        style = attrs.get("style")
        if style is not None and style not in BUTTON_STYLES:
            raise ValueError(
                f"Unknown button style {style!r}, "
                f"expected one of {BUTTON_STYLES}",
            )
        return Button(text, self._action(attrs), style or None)

    def _action(self, attrs: Mapping[str, str]) -> ButtonAction:
        """What the button does."""
        kind = attrs.get("type", "")
        factory = self._actions.get(kind)
        if factory is None:
            raise ValueError(f"Unknown <tg-button> type: {kind!r}")
        return factory(attrs)

    def _action_url(self, attrs: Mapping[str, str]) -> ButtonAction:
        return UrlAction(self.url(attrs.get("url", "")))

    def _action_callback_data(self, attrs: Mapping[str, str]) -> ButtonAction:
        return CallbackDataAction(attrs.get("data", ""))

    def _action_web_app(self, attrs: Mapping[str, str]) -> ButtonAction:
        return WebAppAction(self.url(attrs.get("url", "")))

    def _action_login_url(self, attrs: Mapping[str, str]) -> ButtonAction:
        return LoginUrlAction(
            url=self.url(attrs.get("url", "")),
            forward_text=attrs.get("forward-text") or None,
            bot_username=attrs.get("bot-username") or None,
            request_write_access="request-write-access" in attrs,
        )

    def _action_switch_inline_query(
        self, attrs: Mapping[str, str],
    ) -> ButtonAction:
        return SwitchInlineQueryAction(attrs.get("query", ""))

    def _action_switch_inline_query_current_chat(
        self, attrs: Mapping[str, str],
    ) -> ButtonAction:
        return SwitchInlineQueryCurrentChatAction(attrs.get("query", ""))

    def _action_switch_inline_query_chosen_chat(
        self, attrs: Mapping[str, str],
    ) -> ButtonAction:
        allowed = {
            f"allow_{chat}_chats": f"allow-{chat}-chats" in attrs
            for chat in _CHAT_KINDS
        }
        return SwitchInlineQueryChosenChatAction(
            attrs.get("query", ""), **allowed,
        )

    def _action_copy_text(self, attrs: Mapping[str, str]) -> ButtonAction:
        return CopyTextAction(attrs.get("text", ""))

    def _action_disabled(self, attrs: Mapping[str, str]) -> ButtonAction:
        return DisabledAction()

    # ---- blocks: every method returns a list of blocks

    def blocks(
        self, elem: Element, skip: Optional[Element] = None,
    ) -> List[RichBlock]:
        """Blocks of an element content; inline runs become paragraphs."""
        run = ParagraphRun()
        run.add(self._text(elem.text))
        for child in children(elem):
            tag = str(child.tag)
            if child is skip or tag in DROPPED_TAGS:
                pass
            elif tag in self._block_handlers:
                run.flush()
                new = self._block_handlers[tag](child)
                if (
                    tag == "footer"
                    and new
                    and not self.has_divider_before(child)
                ):
                    # a footer is always preceded by a divider
                    run.add_blocks([self._divider(child)], False)
                run.add_blocks(new, self._is_text_container(child, new))
            else:
                run.add(self._inline(child))
            run.add(self._text(child.tail))
        run.flush()
        return run.blocks

    def _is_text_container(
        self, elem: Element, blocks: List[RichBlock],
    ) -> bool:
        """Container which became one paragraph made of its text only."""
        return (
            elem.tag in CONTAINER_TAGS
            and len(blocks) == 1
            and isinstance(blocks[0], ParagraphBlock)
            and not any(c.tag in self._block_handlers for c in children(elem))
        )

    def _block_container(self, elem: Element) -> List[RichBlock]:
        return self.blocks(elem)

    def _block_heading(self, elem: Element) -> List[RichBlock]:
        size = int(str(elem.tag)[1])
        return [HeadingBlock(self.rich(elem), size)]

    def _block_paragraph(self, elem: Element) -> List[RichBlock]:
        return self._text_block(ParagraphBlock, elem)

    def _block_footer(self, elem: Element) -> List[RichBlock]:
        return self._text_block(FooterBlock, elem)

    def _block_thinking(self, elem: Element) -> List[RichBlock]:
        return self._text_block(ThinkingBlock, elem)

    def _text_block(
        self, block: Callable[[RichTextList], RichBlock], elem: Element,
    ) -> List[RichBlock]:
        text = self.rich(elem)
        if text.is_empty():
            return []
        return [block(text)]

    def _block_hr(self, elem: Element) -> List[RichBlock]:
        return [self._divider(elem)]

    def _divider(self, elem: Element) -> RichBlock:
        """A divider, as a line of text where Telegram cannot draw one."""
        if self.inside_quote(elem):
            return ParagraphBlock(RichTextList([Text(RULE)]))
        return DividerBlock()

    def _block_tg_math_block(self, elem: Element) -> List[RichBlock]:
        return [MathBlock(plain_text(elem))]

    def _block_pre(self, elem: Element) -> List[RichBlock]:
        code = self.single_code(elem)
        tail_code = self.code_before_text(elem)
        if code is None:
            code = tail_code
        lang = self.language(elem)
        if lang is None and code is not None:
            lang = self.language(code)
        text = pre_text(tail_code if tail_code is not None else elem)
        if text.startswith("\n"):
            text = text[1:]
        block = PreBlock(text, lang or None)
        if tail_code is not None:
            return [block, *self.blocks(elem, skip=tail_code)]
        return [block]

    def _block_blockquote(self, elem: Element) -> List[RichBlock]:
        cite = first_child(elem, "cite")
        content = self.blocks(elem, skip=cite)
        credit = non_empty(self.rich(cite))
        if not content and credit is None:
            # Telegram refuses a message with an empty block
            return []

        if "expandable" not in elem.attrib:
            return [BlockquoteBlock(content, credit)]

        if any(not isinstance(block, ParagraphBlock) for block in content):
            raise ValueError(
                "Expandable blockquote can contain only inline content",
            )
        return [ExpandableBlockquoteBlock(join_paragraphs(content), credit)]

    def _block_details(self, elem: Element) -> List[RichBlock]:
        summary = first_child(elem, "summary")
        return [
            DetailsBlock(
                summary=self.rich(summary),
                blocks=self.blocks(elem, skip=summary),
                is_open="open" in elem.attrib,
            ),
        ]

    def _block_aside(self, elem: Element) -> List[RichBlock]:
        text, credit = self.text_and_credit(elem)
        return [PullquoteBlock(text, credit)]

    def text_and_credit(
        self, elem: Element,
    ) -> Tuple[RichTextList, Optional[RichTextList]]:
        """Text of elem and the content of its ``<cite>`` child."""
        cite = first_child(elem, "cite")
        text = self.rich(elem, skip=cite)
        return text, non_empty(self.rich(cite))

    # ---- lists

    def _block_ul(self, elem: Element) -> List[RichBlock]:
        block = self._list(elem, ordered=False)
        return [block] if block.items else []

    def _block_ol(self, elem: Element) -> List[RichBlock]:
        block = self._list(elem, ordered=True)
        return [block] if block.items else []

    def _list(self, elem: Element, ordered: bool) -> ListBlock:
        li_elems = [c for c in children(elem) if c.tag == "li"]
        items = [self._list_item(li) for li in li_elems]
        if ordered:
            self._number_items(elem, li_elems, items)
        # an item with only a checkbox is not empty
        kept = [item for item in items if item.blocks or item.has_checkbox]
        if kept:
            # an empty item stays with its mark, Telegram refuses a block
            # without text, so there is a zero width space in it
            for item in items:
                if not item.blocks:
                    item.blocks = [
                        ParagraphBlock(RichTextList([Text(ZERO_WIDTH_SPACE)])),
                    ]
            return ListBlock(items)
        return ListBlock([])

    def _list_item(self, li: Element) -> ListItemBlock:
        checkbox = self.leading_checkbox(li)
        return ListItemBlock(
            blocks=self.blocks(li, skip=checkbox),
            has_checkbox=checkbox is not None,
            is_checked=checkbox is not None and "checked" in checkbox.attrib,
        )

    def _number_items(
        self,
        ol: Element,
        li_elems: List[Element],
        items: List[ListItemBlock],
    ) -> None:
        """Set ``value`` and ``numbering`` of items of an ordered list.

        They are set for every item: the list is ordered for Telegram only
        if the items say so (otherwise it shows ``•``), and it shows ``0``
        for an item without ``value`` as soon as any other item has a value
        or a type.
        """
        attrs = ol.attrib
        reverse = "reversed" in attrs
        start = parse_int_attr(attrs.get("start"))
        if start is not None:
            counter = start
        else:
            counter = len(li_elems) if reverse else 1
        step = -1 if reverse else 1

        for li, item in zip(li_elems, items, strict=True):
            if li.get("value"):
                try:
                    counter = int(li.get("value"))
                except ValueError as e:
                    raise ValueError(
                        f"<li value={li.get('value')!r}> must be an integer",
                    ) from e
            item.value = counter
            numbering = li.get("type") or attrs.get("type")
            item.numbering = numbering if numbering in OL_TYPES else "1"
            counter += step

    # ---- tables

    def _block_table(self, elem: Element) -> List[RichBlock]:
        """``<table>``, rows of ``<thead>``, ``<tbody>``, ``<tfoot>``
        included."""
        rows = self.table_rows(elem)
        caption = None
        for child in children(elem):
            if child.tag == "caption":
                caption = non_empty(self.rich(child))

        cells = [
            [
                self._cell(cell)
                for cell in children(row)
                if cell.tag in ("td", "th")
            ]
            for row in rows
        ]
        anchors = [AnchorBlock(n) for n in self.cell_anchor_names(elem)]
        return [*anchors, TableBlock(cells, caption)]

    def _cell(self, cell: Element) -> TableCell:
        # a header cell is centered unless told otherwise, as in html
        default_align = "center" if cell.tag == "th" else "left"
        return TableCell(
            align=cell.get("align", default_align),
            valign=cell.get("valign", "middle"),
            text=non_empty(self.rich(cell)),
            is_header=cell.tag == "th",
            colspan=parse_int_attr(cell.get("colspan")),
            rowspan=parse_int_attr(cell.get("rowspan")),
        )

    # ---- media

    def _block_media(self, elem: Element) -> List[RichBlock]:
        """``<img>``, ``<video>``, ``<audio>`` or ``<tg-document>`` alone."""
        return [self._media_block(elem)]

    def _block_map(self, elem: Element) -> List[RichBlock]:
        """``<tg-map>`` alone."""
        return [self._map_block(elem)]

    def _block_figure(self, elem: Element) -> List[RichBlock]:
        """One media or map with a caption."""
        media: Optional[Element] = None
        figcaption: Optional[Element] = None
        for child in children(elem):
            tag = str(child.tag)
            if tag == "figcaption":
                figcaption = child
            elif tag in MEDIA_KINDS or tag == "tg-map":
                if media is not None:
                    raise ValueError(
                        "<figure> must contain exactly one media element",
                    )
                media = child
            else:
                raise ValueError(f"<{tag}> is not allowed inside <figure>")

        if media is None:
            raise ValueError("<figure> must contain a media element")
        if media.tag == "tg-map":
            return [self._map_block(media, figcaption)]
        return [self._media_block(media, figcaption)]

    def _block_gallery(self, type_: str, elem: Element) -> List[RichBlock]:
        """``<tg-collage>`` or ``<tg-slideshow>``: many media with a
        caption."""
        media: List[MediaBlock] = []
        figcaption: Optional[Element] = None
        for child in children(elem):
            tag = str(child.tag)
            if tag == "figcaption":
                figcaption = child
            elif tag in MEDIA_KINDS:
                media.append(self._media_block(child))
            else:
                raise ValueError(
                    f"<{tag}> is not allowed inside <{elem.tag}>",
                )
        return [GalleryBlock(type_, media, self._caption(figcaption))]

    def _caption(self, figcaption: Optional[Element]) -> Optional[Caption]:
        """Caption made of ``<figcaption>``, ``None`` if it is empty."""
        if figcaption is None:
            return None
        text, credit = self.text_and_credit(figcaption)
        if text.is_empty() and credit is None:
            return None
        return Caption(text, credit)

    def _source(self, elem: Element) -> str:
        src = elem.get("src", "")
        if not src:
            raise ValueError(f"<{elem.tag}> requires the src attribute")
        if src.startswith("tg://"):
            raise ValueError(
                f"<{elem.tag}> src={src!r}: tg:// links are supported "
                "only in the html format, use an URL or a file_id",
            )
        if _FILE_ID.fullmatch(src):
            return src
        return self.url(src)

    def _media_block(
        self, elem: Element, figcaption: Optional[Element] = None,
    ) -> MediaBlock:
        kind = MEDIA_KINDS[str(elem.tag)]
        src = self._source(elem)
        suffix = posixpath.splitext(urllib.parse.urlparse(src).path)[1]
        suffix = suffix.lower()
        if kind == "video" and suffix in _ANIMATION_EXTENSIONS:
            kind = "animation"
        elif kind == "audio" and suffix in _VOICE_EXTENSIONS:
            kind = "voice_note"

        return MediaBlock(
            kind=kind,
            media=src,
            has_spoiler="tg-spoiler" in elem.attrib
            and kind in _SPOILER_KINDS,
            caption=self._caption(figcaption),
        )

    def _map_block(
        self, elem: Element, figcaption: Optional[Element] = None,
    ) -> MapBlock:
        try:
            latitude = float(elem.attrib["lat"])
            longitude = float(elem.attrib["long"])
        except (KeyError, ValueError) as e:
            raise ValueError(
                "<tg-map> requires numeric lat and long attributes",
            ) from e
        return MapBlock(
            latitude=latitude,
            longitude=longitude,
            zoom=parse_int_attr(elem.get("zoom")),
            width=parse_int_attr(elem.get("width")),
            height=parse_int_attr(elem.get("height")),
            caption=self._caption(figcaption),
        )

    # ---- button rows

    def _block_tg_button_row(self, elem: Element) -> List[RichBlock]:
        buttons = []
        for child in children(elem):
            if child.tag != "tg-button":
                raise ValueError(
                    f"<{child.tag}> is not allowed inside <tg-button-row>",
                )
            buttons.append(self._button(child))
        if not 1 <= len(buttons) <= MAX_BUTTONS:
            raise ValueError(
                f"<tg-button-row> must have 1-{MAX_BUTTONS} buttons, "
                f"got {len(buttons)}",
            )

        align = elem.get("align")
        if align and align not in BUTTON_ALIGNS:
            raise ValueError(
                f"Unknown align {align!r}, expected one of {BUTTON_ALIGNS}",
            )
        return [ButtonRowBlock(buttons, align or None)]


def transform_rich_blocks(
    raw_html: Optional[str],
    base_url: Optional[str] = None,
    strict: bool = False,
) -> RichBlocksResult:
    """Convert HTML into blocks for ``InputRichMessage.blocks``."""
    if raw_html is None or raw_html.strip() == "":
        return RichBlocksResult(blocks=[])
    doc = parse_html(raw_html, strict=strict)
    blocks = BlocksConverter(base_url).blocks(doc.getroot())
    return RichBlocksResult(blocks=[block.to_dict() for block in blocks])
