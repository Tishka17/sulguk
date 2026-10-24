import pytest

from sulguk import transform_html


@pytest.mark.parametrize(
    "tag",
    ["script", "style", "template", "noscript", "title"],
)
def test_content_is_ignored(tag):
    result = transform_html(f"<p>a<{tag}>hidden</{tag}> b</p>")

    assert result.text == "a b\n\n"
    assert result.entities == []


@pytest.mark.parametrize("tag", ["meta", "link"])
def test_empty_tag_is_ignored(tag):
    result = transform_html(f"<p>a<{tag}> b</p>")

    assert result.text == "a b\n\n"
    assert result.entities == []


def test_head_is_ignored():
    result = transform_html(
        "<html><head><title>t</title><style>p {}</style></head>"
        "<body><p>a</p></body></html>",
    )

    assert result.text == "a\n\n"
    assert result.entities == []
