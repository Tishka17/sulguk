from typing import Optional

from lxml.etree import Element


def children(elem: Element) -> list[Element]:
    """Child elements, comments are skipped."""
    return list(elem.iterchildren("*"))


def first_child(elem: Element, tag: str) -> Optional[Element]:
    """First child element with the tag."""
    return next((c for c in children(elem) if c.tag == tag), None)


def plain_text(elem: Element) -> str:
    """Text of the element and its children without any formatting."""
    return "".join(elem.itertext())


def pre_text(elem: Element) -> str:
    """Text of ``<pre>``: like ``plain_text``, ``<br>`` is a line break."""
    parts = [elem.text or ""]
    for child in children(elem):
        parts.append("\n" if child.tag == "br" else pre_text(child))
        parts.append(child.tail or "")
    return "".join(parts)
