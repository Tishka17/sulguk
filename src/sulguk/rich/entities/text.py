from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .base import RichText


@dataclass
class Text(RichText):
    value: str

    def to_dict(self) -> str:
        return self.value

    def length(self) -> int:
        return len(self.value)

    def collapse(self, at_space: bool) -> Tuple[Optional[RichText], bool]:
        value = self.value.lstrip(" ") if at_space else self.value
        if not value:
            return None, at_space
        return Text(value), value.endswith((" ", "\n"))

    def strip_end(self) -> Optional[RichText]:
        value = self.value.rstrip(" ")
        return Text(value) if value else None


@dataclass
class RichTextList(RichText):
    parts: List[RichText] = field(default_factory=list)

    def to_dict(self) -> Any:
        if not self.parts:
            return ""
        if len(self.parts) == 1:
            return self.parts[0].to_dict()
        return [part.to_dict() for part in self.parts]

    def length(self) -> int:
        return sum(part.length() for part in self.parts)

    def is_empty(self) -> bool:
        return not self.parts

    def clean(self) -> "RichTextList":
        """Make the text of inline parts found in HTML.

        Spaces are collapsed like in a browser, spaces at the ends are
        removed, empty formatting is dropped and neighbour strings are
        merged.
        """
        collapsed, _ = self.collapse(at_space=True)
        stripped = collapsed.strip_end()
        if stripped is None:
            return RichTextList()
        return stripped.merged()

    def collapse(
        self, at_space: bool,
    ) -> Tuple["RichTextList", bool]:  # type: ignore[override]
        parts = []
        for part in self.parts:
            new, at_space = part.collapse(at_space)
            if new is not None:
                parts.append(new)
        return RichTextList(parts), at_space

    def strip_end(self) -> Optional["RichTextList"]:  # type: ignore[override]
        parts = list(self.parts)
        while parts:
            trimmed = parts[-1].strip_end()
            if trimmed is not None:
                parts[-1] = trimmed
                return RichTextList(parts)
            parts.pop()
        return None

    def merged(self) -> "RichTextList":  # type: ignore[override]
        parts: List[RichText] = []
        for part in self.parts:
            part = part.merged()
            if (
                isinstance(part, Text)
                and parts
                and isinstance(parts[-1], Text)
            ):
                parts[-1] = Text(parts[-1].value + part.value)
            else:
                parts.append(part)
        return RichTextList(parts)


@dataclass
class FormattedText(RichText):
    """Bold, italic, a link and other text with a type of its own."""

    type: str
    text: RichTextList
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type, "text": self.text.to_dict(), **self.extra}

    def length(self) -> int:
        return self.text.length()

    def collapse(self, at_space: bool) -> Tuple[Optional[RichText], bool]:
        text, at_space = self.text.collapse(at_space)
        if text.is_empty():
            return None, at_space
        return FormattedText(self.type, text, self.extra), at_space

    def strip_end(self) -> Optional[RichText]:
        text = self.text.strip_end()
        if text is None:
            return None
        return FormattedText(self.type, text, self.extra)

    def merged(self) -> RichText:
        return FormattedText(self.type, self.text.merged(), self.extra)


@dataclass
class Anchor(RichText):
    name: str

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "anchor", "name": self.name}

    def length(self) -> int:
        return 0


@dataclass
class CustomEmoji(RichText):
    custom_emoji_id: str
    alternative_text: str

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "custom_emoji", **self._fields()}

    def length(self) -> int:
        return len(self.alternative_text)


@dataclass
class MathExpression(RichText):
    expression: str

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "mathematical_expression", **self._fields()}

    def length(self) -> int:
        return len(self.expression)
