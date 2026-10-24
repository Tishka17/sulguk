import urllib.parse
from typing import List, Optional, Tuple

from lxml.etree import Element

from sulguk.data import LANG_CLASS_PREFIX, NumberFormat
from sulguk.entities import Progress
from sulguk.mapper import OL_FORMAT
from sulguk.render import State
from sulguk.render.numbers import int_to_number
from .dom import children, first_child
from .html_parsing import parse_int_attr
from .tags import (
    FLAT_LINES,
    MEDIA_ICONS,
    TABLE_SECTIONS,
    TEXT_ONLY_PARENTS,
    VISIBLE_EMPTY_TAGS,
)


class RichConverter:
    """What both converters need to know about an element."""

    def __init__(self, base_url: Optional[str]) -> None:
        self._base_url = base_url

    def url(self, url: str) -> str:
        """Make a relative url absolute, anchors are kept as is.

        Unlike the old mode, which joins ``#name`` with ``base_url`` as a
        browser does with ``<base>``, in a rich message such a link points
        to an anchor of the message itself.
        """
        if self._base_url is None or url.startswith("#"):
            return url
        return urllib.parse.urljoin(self._base_url, url)

    def flat_media(
        self, elem: Element, nested: bool = False,
    ) -> Tuple[str, Optional[str]]:
        """Text and link which stand for a media in a text-only element:
        the icon with ``alt`` or the address of the file. There is no link
        without ``src`` or inside of another link, unless ``nested``."""
        src = elem.get("src", "")
        href = self.url(src) if src else None
        if not nested and any(
            parent.tag == "a" for parent in elem.iterancestors()
        ):
            href = None
        label = elem.get("alt") or href or ""
        return MEDIA_ICONS[str(elem.tag)] + label, href

    def in_cell(self, elem: Element) -> bool:
        """The element is inside a table cell, where Telegram does not make
        a link of a text clickable: a link there is a url button."""
        return any(p.tag in ("td", "th") for p in elem.iterancestors())

    def cell_anchor_names(self, table: Element) -> List[str]:
        """Names of anchors and references inside the cells of a table.

        Telegram does not find them by a link, only an anchor of its own
        before the table, so one is written there too."""
        names: List[str] = []
        for elem in table.iterdescendants("a", "tg-reference"):
            name = elem.get("name")
            if name and name not in names and self.in_cell(elem):
                names.append(name)
        return names

    def is_button_url(self, url: str) -> bool:
        return url.startswith(("http://", "https://", "tg://"))

    def cell_link(self, a: Element) -> Optional[Tuple[List[Element], str, str]]:
        """Media, label and address of a link in a table cell, ``None`` if
        the address cannot be a url button (an anchor, mailto:, tel:)."""
        href = self.url(a.get("href", ""))
        if not self.is_button_url(href):
            return None
        media = [d for d in a.iterdescendants() if d.tag in MEDIA_ICONS]
        label = " ".join("".join(a.itertext()).split())
        return media, label, href

    def language(self, elem: Element) -> Optional[str]:
        """Programming language from a ``language-<name>`` class."""
        for cls in elem.get("class", "").split():
            if cls.startswith(LANG_CLASS_PREFIX):
                return cls[len(LANG_CLASS_PREFIX):]
        return None

    def single_code(self, pre: Element) -> Optional[Element]:
        """``<code>`` if it is the only content of ``<pre>``."""
        kids = children(pre)
        if (
            len(kids) == 1
            and kids[0].tag == "code"
            and not (pre.text or "").strip()
            and not (kids[0].tail or "").strip()
        ):
            return kids[0]
        return None

    def code_before_text(self, pre: Element) -> Optional[Element]:
        """``<code>`` which starts ``<pre>`` when something follows it: the
        code is the block, what follows is a text outside of it."""
        kids = children(pre)
        if (
            kids
            and kids[0].tag == "code"
            and not (pre.text or "").strip()
            and self.single_code(pre) is None
        ):
            return kids[0]
        return None

    def leading_checkbox(self, li: Element) -> Optional[Element]:
        """``<input type="checkbox">`` which starts ``<li>``.

        Telegram shows it as the checkbox of the list item. Any other input
        is shown as text or as a button.
        """
        kids = children(li)
        if (
            kids
            and not (li.text or "").strip()
            and kids[0].tag == "input"
            and kids[0].get("type") == "checkbox"
        ):
            return kids[0]
        return None

    def flat_list_depth(self, lst: Element) -> Optional[int]:
        """Nesting of a list in a text-only element, ``None`` elsewhere.

        Such an element holds only a text, so Telegram glues the items of
        a list in it together. The list is written as lines, see
        ``list_marks``.
        """
        depth = 0
        for parent in lst.iterancestors():
            if parent.tag in TEXT_ONLY_PARENTS:
                return depth
            if parent.tag in ("ul", "ol"):
                depth += 1
        return None

    def inside_text_only(self, elem: Element) -> bool:
        """The element is inside a place which holds only a text."""
        return any(
            parent.tag in TEXT_ONLY_PARENTS for parent in elem.iterancestors()
        )

    def inside_quote(self, elem: Element) -> bool:
        """The element is inside of a block quotation, where Telegram does
        not draw a divider."""
        return any(
            parent.tag == "blockquote" for parent in elem.iterancestors()
        )

    def has_divider_before(self, elem: Element) -> bool:
        """A divider is already right before the element: an ``<hr>`` or a
        previous ``<footer>``, which takes the only one."""
        prev = elem.getprevious()
        return prev is not None and prev.tag in ("hr", "footer")

    def table_rows(self, table: Element) -> List[Element]:
        """``<tr>`` of a table, rows of ``<thead>``, ``<tbody>`` and
        ``<tfoot>`` included."""
        rows: List[Element] = []
        for child in children(table):
            tag = str(child.tag)
            if tag == "tr":
                rows.append(child)
            elif tag in TABLE_SECTIONS:
                rows.extend(r for r in children(child) if r.tag == "tr")
        return rows

    def has_content_before(self, elem: Element) -> bool:
        parent = elem.getparent()
        prev = elem.getprevious()
        if (
            prev is not None
            and prev.tag == "summary"
            and parent is not None
            and parent.tag == "details"
            and prev.getprevious() is None
            and not (parent.text or "").strip()
            and not (prev.tail or "").strip()
        ):
            # the body of ``<details>`` starts a line after the summary on
            # its own, there is nothing to break
            return False
        return prev is not None or bool(
            parent is not None and (parent.text or "").strip(),
        )

    def details_parts(
        self, elem: Element,
    ) -> Tuple[Optional[Element], bool]:
        """``<summary>`` of ``<details>`` and whether the body has anything
        to show."""
        summary = first_child(elem, "summary")
        rest = [c for c in children(elem) if c is not summary]
        body = (elem.text or "").strip() or any(
            (c.tail or "").strip() or not self.flat_blank(c) for c in rest
        )
        return summary, bool(body)

    def has_content_after(self, elem: Element) -> bool:
        return elem.getnext() is not None or bool((elem.tail or "").strip())

    def line_after(self, elem: Element) -> bool:
        """A line break is needed after a line of a text-only element. Not if
        the next element is a line of its own, it breaks before itself."""
        if (elem.tail or "").strip():
            return True
        nxt = elem.getnext()
        return nxt is not None and nxt.tag not in FLAT_LINES

    def flat_blank(self, elem: Element) -> bool:
        """A line of a text-only element with nothing to show in it."""
        if elem.tag == "hr":
            return False
        if "".join(elem.itertext()).strip():
            return False
        return not any(
            child.tag in VISIBLE_EMPTY_TAGS for child in elem.iterdescendants()
        )

    def list_numbers(self, lst: Element) -> List[Tuple[Element, int]]:
        """Items of ``<ol>`` with their numbers, an item with a ``value``
        starts the count again."""
        items = [c for c in children(lst) if c.tag == "li"]
        reverse = "reversed" in lst.attrib
        counter = parse_int_attr(lst.get("start"))
        if counter is None:
            counter = len(items) if reverse else 1
        step = -1 if reverse else 1
        result = []
        for li in items:
            if li.get("value"):
                counter = int(li.get("value"))
            result.append((li, counter))
            counter += step
        return result

    def list_marks(self, lst: Element) -> List[Tuple[Element, str]]:
        """Items of ``<ul>``/``<ol>`` with their marks: ``• `` or ``1. ``,
        numbered as in the old mode."""
        if lst.tag == "ul":
            return [(li, "• ") for li in children(lst) if li.tag == "li"]
        result = []
        for li, number in self.list_numbers(lst):
            number_format = OL_FORMAT.get(
                li.get("type") or lst.get("type") or "1",
                NumberFormat.DECIMAL,
            )
            result.append((li, f"{int_to_number(number, number_format)}. "))
        return result

    def input_symbol(self, elem: Element) -> Optional[str]:
        """Emoji of a checkbox or a radio, ``None`` for other inputs."""
        checked = "checked" in elem.attrib
        kind = elem.get("type", "")
        if kind == "checkbox":
            return "☑️" if checked else "◻️"
        if kind == "radio":
            return "🔘" if checked else "⚪️"
        return None

    def input_button(self, elem: Element) -> tuple[str, dict[str, str]]:
        """Label and ``<tg-button>`` attributes of ``<input type="submit">``.

        The button has no action of its own, so it sends ``name`` (or the
        type of the input) as callback data.
        """
        kind = elem.get("type", "")
        label = elem.get("value") or kind.capitalize()
        return label, {
            "type": "callback_data",
            "data": elem.get("name") or kind,
        }

    def progress_text(self, elem: Element) -> str:
        """Emoji bar for ``<progress>`` and ``<meter>``."""
        is_meter = elem.tag == "meter"
        progress = Progress(
            value=float(elem.get("value", "0")),
            min=float(elem.get("min", "0")) if is_meter else 0,
            max=float(elem.get("max", "1")),
            is_meter=is_meter,
        )
        state = State()
        progress.render(state)
        return state.canvas.text
