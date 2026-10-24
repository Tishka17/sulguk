from abc import ABC, abstractmethod
from dataclasses import fields
from typing import Any, ClassVar, Dict, List, Optional, Tuple


class RichEntity(ABC):
    @abstractmethod
    def to_dict(self) -> Any:
        raise NotImplementedError

    def _fields(self) -> Dict[str, Any]:
        """Fields which are set, as they are sent to Telegram.

        ``None`` and ``False`` are left out: a flag is sent only when set.
        """
        result = {}
        for item in fields(self):  # type: ignore[arg-type]
            value = getattr(self, item.name)
            if value is None or value is False:
                continue
            result[item.name] = _dump(value)
        return result


def _dump(value: Any) -> Any:
    if isinstance(value, RichEntity):
        return value.to_dict()
    if isinstance(value, list):
        return [_dump(item) for item in value]
    return value


class RichText(RichEntity):
    """Part of a text: a string, a formatted text, an emoji, a button..."""

    @abstractmethod
    def length(self) -> int:
        """Number of characters Telegram counts in the text."""
        raise NotImplementedError

    def collapse(
        self, at_space: bool,
    ) -> Tuple[Optional["RichText"], bool]:
        """Remove spaces after a space, a line break or the text start.

        Returns the part (``None`` if nothing is left) and whether the next
        part starts after a space.
        """
        return self, False

    def strip_end(self) -> Optional["RichText"]:
        """The part without spaces at the end, ``None`` if it is empty."""
        return self

    def merged(self) -> "RichText":
        """The part with neighbour strings merged."""
        return self


class RichBlock(RichEntity):
    type: ClassVar[str]

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type, **self._fields()}

    def own_count(self) -> int:
        """Blocks Telegram counts for the block itself, nested not included."""
        return 1

    def nested(self) -> List[Tuple[int, List["RichBlock"]]]:
        """Blocks inside of the block with the levels they add."""
        return []

    def row_widths(self) -> List[int]:
        """Widths of the rows if the block is a table."""
        return []

    def text_length(self) -> int:
        """Characters of the text of the block and of nested blocks."""
        return 0

    def media_count(self) -> int:
        """Media attachments of the block itself, nested not included."""
        return 0
