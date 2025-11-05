from typing import Any

from lxml.etree import Element, ElementTree

from .entities import Entity, Group, Text
from .mapper import Attrs, Mapper


class Walker:
    def __init__(self, base_url: str | None = None):
        self.mapper = Mapper(base_url)

    def walk(self, tree: ElementTree) -> Group:
        root = tree.getroot()
        entity_root = Group()
        self._visit_element(root, entity_root)
        return entity_root

    def _visit_element(self, elem: Element, parent_entity: Entity) -> None:
        attrs = _attrs_to_list(elem.attrib)
        inner, entity = self.mapper.match(str(elem.tag), attrs)

        if entity is None:
            return

        parent_entity.add(entity)

        target = inner if inner is not None else entity
        if elem.text:
            target.add(Text(text=elem.text))

        for child in elem.iterchildren(tag=Element):
            self._visit_element(child, target)
            if child.tail:
                target.add(Text(text=child.tail))


def _attrs_to_list(attrib: Any) -> Attrs:
    return list(attrib.items())
