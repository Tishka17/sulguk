from enum import Enum
from typing import Literal, Optional, TypedDict, get_args

SULGUK_PARSE_MODE = "sulguk"
# class of ``<pre>`` and ``<code>`` with the language: ``language-python``
LANG_CLASS_PREFIX = "language-"

RichFormat = Literal["html", "blocks"]
RICH_FORMATS = get_args(RichFormat)


class NumberFormat(Enum):
    DECIMAL = "DECIMAL"
    ROMAN_LOWER = "ROMAN_LOWER"
    ROMAN_UPPER = "ROMAN_UPPER"
    LETTERS_LOWER = "LETTERS_LOWER"
    LETTERS_UPPER = "LETTERS_UPPER"


class User(TypedDict):
    id: int


class MessageEntity(TypedDict, total=False):
    type: str
    offset: int
    length: int
    url: Optional[str]
    user: Optional[User]
    language: Optional[str]
    custom_emoji_id: Optional[str]
