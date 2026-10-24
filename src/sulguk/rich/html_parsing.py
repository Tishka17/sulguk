import re
from typing import Any, Optional


ZERO_WIDTH_SPACE = "​"
# carriage return, line feed, tab and space (not nbsp)
HTML_SPACES_RE = re.compile("[\x0d\x0a\x09\x20]+")
# the same symbols for str.strip
HTML_SPACE_CHARS = "\x0d\x0a\x09\x20"
# inputs which are pressed, they become buttons
BUTTON_LIKE_INPUT_TYPES = frozenset({"submit", "button", "reset"})


def collapse_html_spaces(text: str) -> str:
    """Every run of HTML spaces is one space, as in a browser."""
    return HTML_SPACES_RE.sub(" ", text)


def parse_int_attr(value: Optional[str]) -> Optional[int]:
    """Number from an attribute, ``None`` if the attribute is not set."""
    return int(value) if value else None


def drop_none_fields(**fields: Any) -> dict[str, Any]:
    """Dict of the fields which are set (not None)."""
    return {key: value for key, value in fields.items() if value is not None}
