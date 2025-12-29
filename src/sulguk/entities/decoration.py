from dataclasses import dataclass
from typing import Optional

from sulguk.data import MessageEntity
from sulguk.render import State, TextMode
from .base import DecoratedEntity, Group


@dataclass
class Link(DecoratedEntity):
    url: Optional[str] = None

    def _get_entity(self, offset: int, length: int) -> MessageEntity:
        return MessageEntity(
            type="text_link", url=self.url, offset=offset, length=length,
        )


@dataclass
class Bold(DecoratedEntity):
    def _get_entity(self, offset: int, length: int) -> MessageEntity:
        return MessageEntity(type="bold", offset=offset, length=length)


@dataclass
class Italic(DecoratedEntity):
    def _get_entity(self, offset: int, length: int) -> MessageEntity:
        return MessageEntity(type="italic", offset=offset, length=length)


@dataclass
class Underline(DecoratedEntity):
    def _get_entity(self, offset: int, length: int) -> MessageEntity:
        return MessageEntity(type="underline", offset=offset, length=length)


@dataclass
class Strikethrough(DecoratedEntity):
    def _get_entity(self, offset: int, length: int) -> MessageEntity:
        return MessageEntity(
            type="strikethrough", offset=offset, length=length,
        )


@dataclass
class Spoiler(DecoratedEntity):
    def _get_entity(self, offset: int, length: int) -> MessageEntity:
        return MessageEntity(type="spoiler", offset=offset, length=length)


@dataclass
class Code(DecoratedEntity):
    language: Optional[str] = None

    def _get_entity(self, offset: int, length: int) -> MessageEntity:
        return MessageEntity(
            type="code", offset=offset, length=length,
        )


@dataclass
class Uppercase(Group):
    def render(self, state: State) -> None:
        transform = state.canvas.text_transformation
        state.canvas.text_transformation = lambda s: s.upper()
        super().render(state)
        state.canvas.text_transformation = transform


@dataclass
class Quote(Group):
    def render(self, state: State) -> None:
        state.canvas.add_text("“")
        super().render(state)
        state.canvas.add_text("”")


@dataclass
class Blockquote(DecoratedEntity):
    expandable: bool = False

    def _get_entity(self, offset: int, length: int) -> MessageEntity:
        if self.expandable:
            type_entity = "expandable_blockquote"
        else:
            type_entity = "blockquote"
        return MessageEntity(type=type_entity, offset=offset, length=length)


@dataclass
class Paragraph(Group):
    block: bool = True

    def render(self, state: State) -> None:
        state.canvas.add_empty_line()
        super().render(state)
        state.canvas.add_empty_line()


@dataclass
class Pre(DecoratedEntity):
    block: bool = True
    language: Optional[str] = None

    def render(self, state: State) -> None:
        text_mode = state.canvas.text_mode
        state.canvas.add_empty_line()
        state.canvas.text_mode = TextMode.PRE
        super().render(state)
        state.canvas.text_mode = text_mode
        state.canvas.add_empty_line()

    def _get_language(self):
        if self.language:
            return self.language
        if len(self.entities) != 1:
            return None
        nested = self.entities[0]
        if not isinstance(nested, Code):
            return None
        return nested.language

    def _get_entity(self, offset: int, length: int) -> MessageEntity:
        entity = MessageEntity(
            type="pre",
            offset=offset,
            length=length,
        )
        if language := self._get_language():
            entity["language"] = language
        return entity
