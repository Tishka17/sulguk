from dataclasses import dataclass

from sulguk.data import MessageEntity
from .base import DecoratedEntity


@dataclass
class Emoji(DecoratedEntity):
    custom_emoji_id: str = ""

    def _get_entity(self, offset: int, length: int) -> MessageEntity:
        return MessageEntity(
            type="custom_emoji",
            offset=offset, length=length,
            custom_emoji_id=self.custom_emoji_id,
        )
