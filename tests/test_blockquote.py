import pytest

from sulguk import transform_html
from sulguk.data import MessageEntity

BLOCKQUOTE_HTML = "1<blockquote>2</blockquote>3"
BLOCKQUOTE_PLAIN = "123"
BLOCKQUOTE_ENTITIES = [
    MessageEntity(type="blockquote", offset=1, length=1),
]
BLOCKQUOTE_EXPANDABLE_HTML = "1<blockquote expandable>2</blockquote>3"
BLOCKQUOTE_EXPANDABLE_PLAIN = "123"
BLOCKQUOTE_EXPANDABLE_ENTITIES = [
    MessageEntity(type="expandable_blockquote", offset=1, length=1),
]


@pytest.mark.parametrize(
    "html, plain, entities, name",
    [
        (BLOCKQUOTE_HTML, BLOCKQUOTE_PLAIN, BLOCKQUOTE_ENTITIES, "blockquote"),
        (
            BLOCKQUOTE_EXPANDABLE_HTML,
            BLOCKQUOTE_EXPANDABLE_PLAIN,
            BLOCKQUOTE_EXPANDABLE_ENTITIES,
            "blockquote expandable",
        ),
    ],
)
def test_blockquote(html, plain, entities, name):
    result = transform_html(html)
    assert result.text == plain, (
        f"Expected text {plain!r}, but got {result.text!r}"
    )
    assert result.entities == entities, (
        f"Expected entities {entities}, but got {result.entities}"
    )
