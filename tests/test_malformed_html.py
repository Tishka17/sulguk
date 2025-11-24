import pytest
from html5lib.html5parser import ParseError

from sulguk import transform_html
from sulguk.data import MessageEntity

IMPROPER_NESTING = "<b><i>hello</b>world</i>"
# Well formed equivalent: <b><i>hello</i></b><i>world</i>
ENTITIES_FOR_IMPROPER_NESTING = [
    MessageEntity(type="italic", offset=0, length=5),
    MessageEntity(type="bold", offset=0, length=5),
    MessageEntity(type="italic", offset=5, length=5),
]


DUPLICATE_CLOSING_TAG = "<b><i>hello</i></i>world</b>"
# Well formed equivalent:: <b><i>hello</i>world</b>
ENTITIES_FOR_DUPLICATE_CLOSING_TAG = [
    MessageEntity(type="italic", offset=0, length=5),
    MessageEntity(type="bold", offset=0, length=10),
]

UNCLOSED_TAG = "<b><i>hello</b>world<i>again</i"
# Well formed equivalent:: <b><i>hello</i></b><i>world<i>again</i></i>
ENTITIES_FOR_UNCLOSED_TAG = [
    MessageEntity(type="italic", offset=0, length=5),
    MessageEntity(type="bold", offset=0, length=5),
    MessageEntity(type="italic", offset=10, length=5),
    MessageEntity(type="italic", offset=5, length=10),
]


@pytest.mark.parametrize(
    ("html", "entities"),
    (
        (IMPROPER_NESTING, ENTITIES_FOR_IMPROPER_NESTING),
        (DUPLICATE_CLOSING_TAG, ENTITIES_FOR_DUPLICATE_CLOSING_TAG),
        (UNCLOSED_TAG, ENTITIES_FOR_UNCLOSED_TAG),
    ),
)
def test_malformed_html(html, entities):
    result = transform_html(html)
    assert result.entities == entities


@pytest.mark.parametrize(
    "html",
    (IMPROPER_NESTING, DUPLICATE_CLOSING_TAG, UNCLOSED_TAG),
)
def test_malformed_html_strict(html):
    with pytest.raises(ParseError):
        transform_html(html, strict=True)
