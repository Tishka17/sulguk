from enum import Enum
from typing import Optional, TypedDict

SULGUK_PARSE_MODE = "sulguk"


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
