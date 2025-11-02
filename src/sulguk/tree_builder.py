# ruff: noqa: N815, N802, N803
from copy import copy
from typing import List, Optional

from html5lib.constants import namespaces
from html5lib.treebuilders import base

from .entities import (
    Entity,
    Group,
    Stub,
    Text,
)
from .mapper import Attrs, Mapper


def get_sulguk_tree_builder(base_url: Optional[str] = None):
    mapper = Mapper(base_url)

    class Element(base.Node):
        def __init__(self, name: str, namespace: Optional[str] = None):
            self.name = name
            self.namespace = namespace
            self.inner_entity: Optional[Entity] = None

            if self.name not in ("#text", "#document", "#comment", "#doctype"):
                self.inner_entity, self.entity = mapper.match(name, [])
            if namespace is None:
                self.nameTuple = (namespaces["html"], name)
            else:
                self.nameTuple = (namespace, name)
            self.parent: Optional[Element] = None
            self.childNodes: List[Element] = []
            self._flags: List = []

            self._attributes: dict = {}

        @property
        def attributes(self):
            return self._attributes

        @attributes.setter
        def attributes(self, value):
            # Recreate entity if html5lib sets attributes
            self._attributes = value
            self._update_entity()

        def _update_entity(self):
            attrs: Attrs = list(self.attributes.items())
            self.inner_entity, self.entity = mapper.match(self.name, attrs)

        def appendChild(self, node: "Element") -> None:
            self.childNodes.append(node)
            target = self.inner_entity or self.entity
            if target and node.entity:
                target.add(node.entity)
            node.parent = self

        def insertText(
            self,
            data: str,
            insertBefore: Optional["Element"] = None,
        ) -> None:
            text_entity = Text(data)
            text_node = TextNode(text_entity)

            if insertBefore is None:
                self.appendChild(text_node)
            else:
                # not covered
                index = self.childNodes.index(insertBefore)
                self.childNodes.insert(index, text_node)
                text_node.parent = self

                target = self.inner_entity or self.entity
                if isinstance(target, Group):
                    entity_index = self._get_entity_index(insertBefore)
                    target.entities.insert(entity_index, text_entity)

        def insertBefore(self, node: "Element", refNode: "Element") -> None:
            # not covered
            index = self.childNodes.index(refNode)
            self.childNodes.insert(index, node)
            node.parent = self

            target = self.inner_entity or self.entity
            if isinstance(target, Group) and node.entity:
                entity_index = self._get_entity_index(refNode)
                target.entities.insert(entity_index, node.entity)

        def removeChild(self, node: "Element") -> None:
            # not covered
            self.childNodes.remove(node)
            node.parent = None

            target = self.inner_entity or self.entity
            if isinstance(target, Group) and node.entity:
                try:
                    target.entities.remove(node.entity)
                except ValueError:
                    pass

        def reparentChildren(self, newParent: "Element") -> None:
            # not covered
            for child in self.childNodes[:]:
                self.removeChild(child)
                newParent.appendChild(child)

        def cloneNode(self) -> "Element":  # type: ignore[override]
            element = Element(self.name, self.namespace)
            element.attributes = copy(self.attributes)
            return element

        def hasContent(self) -> bool:  # type: ignore[override]
            # not covered
            return bool(self.childNodes)

        def _get_entity_index(self, element: "Element") -> int:
            # not covered
            target = self.inner_entity or self.entity
            if not isinstance(target, Group):
                return 0

            for i, child in enumerate(self.childNodes):
                if child == element:
                    return i
            return len(target.entities)

    class TextNode(Element):
        def __init__(self, entity: Text):
            super().__init__("#text")
            self.entity = entity

        def appendChild(self, node: Element) -> None:
            raise RuntimeError("Text nodes cannot have children")

    class Document(Element):
        def __init__(self):
            super().__init__("#document")
            self.entity = Group()

    class Comment(Element):
        def __init__(self, data: str):
            super().__init__("#comment")
            self.entity = Stub()

    class Doctype(Element):
        def __init__(self, name: str, publicId: str = "", systemId: str = ""):
            super().__init__("#doctype")
            self.entity = Stub()
            self.publicId = publicId
            self.systemId = systemId

    class TreeBuilder(base.TreeBuilder):
        documentClass = Document
        elementClass = Element
        commentClass = Comment
        doctypeClass = Doctype

        def getDocument(self):
            return self.document

    return TreeBuilder
