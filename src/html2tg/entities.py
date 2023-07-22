from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional

from aiogram.types import MessageEntity

from .state import State


class Entity(ABC):
    def _add_text(self, state: State, text: str) -> None:
        text = " " * state.indent + text
        if not state.text:
            text = text.lstrip()
        state.text += text
        state.offset += len(text)

    @abstractmethod
    def add(self, entity: "Entity"):
        raise NotImplementedError

    @abstractmethod
    def render(self, state: State) -> None:
        raise NotImplementedError


@dataclass
class Text(Entity):
    text: str

    def render(self, state: State) -> None:
        self._add_text(state, self.text)

    def add(self, entity: "Entity"):
        raise ValueError("Text does not supports children")


@dataclass
class WithText(Entity):
    text: Optional[Text] = None

    def add(self, entity: "Entity"):
        if self.text:
            raise ValueError("Text is already set")
        if not isinstance(entity, Text):
            raise TypeError("Text is expected")
        self.text = entity

    @abstractmethod
    def _get_entity(self, offset: int, length: int) -> MessageEntity:
        raise NotImplementedError

    def render(self, state: State) -> None:
        offset = state.offset
        self.text.render(state)
        state.entities.append(
            self._get_entity(offset, state.offset - offset),
        )


@dataclass
class Link(WithText):
    url: Optional[str] = None

    def _get_entity(self, offset: int, length: int) -> MessageEntity:
        return MessageEntity(
            type="text_link",
            url=self.url,
            offset=offset,
            length=length
        )


@dataclass
class Bold(WithText):
    def _get_entity(self, offset: int, length: int) -> MessageEntity:
        return MessageEntity(
            type="bold",
            offset=offset,
            length=length
        )


@dataclass
class Italic(WithText):
    def _get_entity(self, offset: int, length: int) -> MessageEntity:
        return MessageEntity(
            type="italic",
            offset=offset,
            length=length
        )


@dataclass
class Underline(WithText):
    def _get_entity(self, offset: int, length: int) -> MessageEntity:
        return MessageEntity(
            type="underline",
            offset=offset,
            length=length
        )


@dataclass
class Strikethrough(WithText):
    def _get_entity(self, offset: int, length: int) -> MessageEntity:
        return MessageEntity(
            type="strikethrough",
            offset=offset,
            length=length
        )


@dataclass
class Code(WithText):
    def _get_entity(self, offset: int, length: int) -> MessageEntity:
        return MessageEntity(
            type="code",
            offset=offset,
            length=length
        )


@dataclass
class Group(Entity):
    entities: List[Entity] = field(default_factory=list)

    def add(self, entity: Entity):
        self.entities.append(entity)

    def render(self, state: State) -> None:
        for entity in self.entities:
            entity.render(state)


@dataclass
class ListGroup(Group):
    indent: int = 2
    numbered: bool = False

    def add(self, entity: Entity):
        if isinstance(entity, Text) and not (entity.text.strip()):
            return
        super().add(entity)

    def render(self, state: State) -> None:
        indent = state.indent
        index = state.index
        state.indent += self.indent
        if not state.text.endswith("\n"):
            self._add_text(state, "\n")
        for state.index, entity in enumerate(self.entities, 1):
            print("index", self, state.index)
            entity.render(state)
            self._add_text(state, "\n")
        state.indent = indent
        state.index = index


@dataclass
class ListItem(Group):
    list: ListGroup = field(default_factory=ListGroup)

    def render(self, state: State) -> None:
        if self.list.numbered:
            self._add_text(state, str(state.index))
        else:
            self._add_text(state, "*")
        super().render(state)
