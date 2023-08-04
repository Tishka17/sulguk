from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional

from aiogram.types import MessageEntity

from .numbers import Format, int_to_number
from .state import State


class Entity(ABC):
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
        state.canvas.add_text(self.text)

    def add(self, entity: "Entity"):
        raise ValueError("Text does not supports children")


@dataclass
class Group(Entity):
    entities: List[Entity] = field(default_factory=list)
    block: bool = False

    def add(self, entity: Entity):
        self.entities.append(entity)

    def render(self, state: State) -> None:
        if self.block:
            state.canvas.add_new_line_soft()
        for entity in self.entities:
            entity.render(state)
        if self.block:
            state.canvas.add_new_line_soft()


@dataclass
class DecoratedEntity(Group):
    @abstractmethod
    def _get_entity(self, offset: int, length: int) -> MessageEntity:
        raise NotImplementedError

    def render(self, state: State) -> None:
        offset = state.canvas.size
        super().render(state)
        state.entities.append(
            self._get_entity(offset, state.canvas.size - offset),
        )


@dataclass
class Link(DecoratedEntity):
    url: Optional[str] = None

    def _get_entity(self, offset: int, length: int) -> MessageEntity:
        return MessageEntity(
            type="text_link",
            url=self.url,
            offset=offset,
            length=length,
        )


@dataclass
class Bold(DecoratedEntity):
    def _get_entity(self, offset: int, length: int) -> MessageEntity:
        return MessageEntity(
            type="bold",
            offset=offset,
            length=length
        )


@dataclass
class Italic(DecoratedEntity):
    def _get_entity(self, offset: int, length: int) -> MessageEntity:
        return MessageEntity(
            type="italic",
            offset=offset,
            length=length
        )


@dataclass
class Underline(DecoratedEntity):
    def _get_entity(self, offset: int, length: int) -> MessageEntity:
        return MessageEntity(
            type="underline",
            offset=offset,
            length=length
        )


@dataclass
class Strikethrough(DecoratedEntity):
    def _get_entity(self, offset: int, length: int) -> MessageEntity:
        return MessageEntity(
            type="strikethrough",
            offset=offset,
            length=length
        )


@dataclass
class Spoiler(DecoratedEntity):
    def _get_entity(self, offset: int, length: int) -> MessageEntity:
        return MessageEntity(
            type="spoiler",
            offset=offset,
            length=length
        )


@dataclass
class Code(DecoratedEntity):
    def _get_entity(self, offset: int, length: int) -> MessageEntity:
        return MessageEntity(
            type="code",
            offset=offset,
            length=length
        )


@dataclass
class Uppercase(Group):
    def render(self, state: State) -> None:
        to_upper = state.to_upper
        state.to_upper = True
        super().render(state)
        state.to_upper = to_upper


@dataclass
class Paragraph(Group):
    block: bool = True

    def render(self, state: State) -> None:
        state.canvas.add_empty_line()
        super().render(state)
        state.canvas.add_empty_line()


@dataclass
class Quote(Group):
    def render(self, state: State) -> None:
        state.canvas.add_text("“")
        super().render(state)
        state.canvas.add_text("”")


@dataclass
class Blockquote(Group):
    block: bool = True

    def render(self, state: State) -> None:
        indent = state.indent
        state.indent += 1
        super().render(state)
        state.indent = indent


@dataclass
class ListGroup(Entity):
    entities: List[Entity] = field(default_factory=list)
    numbered: bool = False
    reversed: bool = False
    format: Format = Format.DECIMAL
    start: int = 1

    def add(self, entity: Entity):
        if isinstance(entity, Text) and not (entity.text.strip()):
            return
        self.entities.append(entity)

    def render(self, state: State) -> None:
        state.canvas.add_new_line_soft()
        if self.reversed:
            index = len(self.entities)
            step = -1
        else:
            index = 0
            step = 1
        for entity in self.entities:
            if isinstance(entity, ListItem):
                if entity.value is not None:
                    index = entity.value
                else:
                    index += step

                if self.numbered:
                    index_value = int_to_number(index, self.format)
                    mark = f"{index_value}. "
                else:
                    mark = "* "
                state.canvas.add_text(mark)
            entity.render(state)
            state.canvas.add_new_line_soft()


@dataclass
class ListItem(Group):
    value: Optional[int] = None

    def render(self, state: State) -> None:
        indent = state.indent
        state.indent += 1
        super().render(state)
        state.indent = indent


class NewLine(Entity):
    def add(self, entity: "Entity"):
        raise ValueError("Unsupported contents for NewLine widget")

    def render(self, state: State) -> None:
        state.canvas.add_new_line()


class HorizontalLine(Entity):
    def add(self, entity: "Entity"):
        raise ValueError("Unsupported contents for HorizontalLine widget")

    def render(self, state: State) -> None:
        state.canvas.add_text("-------------")
