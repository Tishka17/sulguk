import pytest

from sulguk import transform_html

BLOCKQUOTE_HTML = "1<blockquote>2</blockquote>3"
BLOCKQUOTE_PLAIN = "123"
BLOCKQUOTE_EXPANDABLE_HTML = "1<blockquote expandable>2</blockquote>3"
BLOCKQUOTE_EXPANDABLE_PLAIN = "123"

@pytest.mark.parametrize("html, plain, name",[
    (BLOCKQUOTE_HTML, BLOCKQUOTE_PLAIN, "blockquote"),
    (BLOCKQUOTE_EXPANDABLE_HTML, BLOCKQUOTE_EXPANDABLE_PLAIN,
     "blockquote expandable"),
])
def test_blockquote(html, plain, name):
    result = transform_html(html)
    print(repr(plain))
    print(repr(html))
    assert result.text != plain
