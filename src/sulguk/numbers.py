from enum import Enum
from string import ascii_uppercase


class Format(Enum):
    DECIMAL = "DECIMAL"
    ROMAN_LOWER = "ROMAN_LOWER"
    ROMAN_UPPER = "ROMAN_UPPER"
    LETTERS_LOWER = "LETTERS_LOWER"
    LETTERS_UPPER = "LETTERS_UPPER"


roman = {
    1000: "M",
    900: "CM",
    500: "D",
    400: "CD",
    100: "C",
    90: "XC",
    50: "L",
    40: "XL",
    10: "X",
    9: "IX",
    5: "V",
    4: "IV",
    1: "I",
}


def _roman_num(num):
    for r in roman.keys():
        x, y = divmod(num, r)
        yield roman[r] * x
        num -= (r * x)
        if num <= 0:
            break


def to_roman(value: int) -> str:
    return "".join(_roman_num(value))


def to_letters(value: int) -> str:
    result = ""
    while value > 0:
        value, y = divmod(value, len(ascii_uppercase))
        result += ascii_uppercase[y - 1]
    return result[::-1]


def int_to_number(value: int, format: Format) -> str:
    if format is Format.DECIMAL:
        return str(value)
    elif format is Format.LETTERS_UPPER:
        return to_letters(value)
    elif format is Format.LETTERS_LOWER:
        return to_letters(value).lower()
    elif format is Format.ROMAN_UPPER:
        return to_roman(value)
    elif format is Format.ROMAN_LOWER:
        return to_roman(value).lower()
