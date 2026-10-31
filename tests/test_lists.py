import pytest

from sulguk import transform_html
from sulguk.data import MessageEntity


def test_ordered_list_item_first_paragraph_stays_with_marker():
    result = transform_html(
        "<ol>"
        "<li><p><b>First item</b> body</p></li>"
        "<li><p><b>Second item</b> body with <code>code</code></p></li>"
        "</ol>",
    )

    assert result.text == (
        "1. First item body\n2. Second item body with code\n"
    )
    assert result.entities == [
        MessageEntity(type="bold", offset=3, length=10),
        MessageEntity(type="bold", offset=22, length=11),
        MessageEntity(type="code", offset=44, length=4),
    ]


def test_ordered_list_item_ignores_leading_html_whitespace():
    result = transform_html(
        "<ol>\n"
        "<li>\n"
        "<p><b>First item</b> body</p>\n"
        "</li>\n"
        "<li>\n"
        "<p><b>Second item</b> body with <code>code</code></p>\n"
        "</li>\n"
        "</ol>",
    )

    assert result.text == (
        "1. First item body\n2. Second item body with code\n"
    )
    assert result.entities == [
        MessageEntity(type="bold", offset=3, length=10),
        MessageEntity(type="bold", offset=22, length=11),
        MessageEntity(type="code", offset=44, length=4),
    ]


def test_ordered_list_item_first_heading_stays_with_marker():
    result = transform_html(
        "<ol>\n"
        "<li>\n"
        "<h1>First heading</h1>\n"
        "<p>Body text</p>\n"
        "</li>\n"
        "<li>\n"
        "<h2>Second heading</h2>\n"
        "</li>\n"
        "</ol>",
    )

    assert result.text == (
        "1. FIRST HEADING\n\n\xa0Body text\n\n2. Second heading\n"
    )
    assert result.entities == [
        MessageEntity(type="underline", offset=3, length=13),
        MessageEntity(type="bold", offset=3, length=13),
        MessageEntity(type="underline", offset=33, length=14),
        MessageEntity(type="bold", offset=33, length=14),
    ]


def test_unordered_list_item_first_paragraph_stays_with_marker():
    result = transform_html(
        "<ul>"
        "<li><p><b>First item</b> body</p></li>"
        "<li><p><b>Second item</b> body</p></li>"
        "</ul>",
    )

    assert result.text == "• First item body\n• Second item body\n"
    assert result.entities == [
        MessageEntity(type="bold", offset=2, length=10),
        MessageEntity(type="bold", offset=20, length=11),
    ]


def test_later_list_item_paragraphs_stay_separate():
    result = transform_html(
        "<ol>"
        "<li><p><b>First item</b> body</p><p>additional paragraph</p></li>"
        "<li><p><b>Second item</b> body</p></li>"
        "</ol>",
    )

    assert result.text.startswith("1. First item body\n\n")
    assert "1.\n\n" not in result.text
    assert "2.\n\n" not in result.text
    assert "\xa0additional paragraph" in result.text


def test_inline_text_after_first_paragraph_stays_separate():
    result = transform_html("<ol><li><p>first</p>second</li></ol>")

    assert result.text == "1. first\n\xa0second\n"


def test_inline_span_after_first_paragraph_stays_separate():
    result = transform_html(
        "<ol><li><p>first</p><span>second</span></li></ol>",
    )

    assert result.text == "1. first\n\xa0second\n"


def test_pre_after_first_paragraph_stays_block_shaped():
    result = transform_html(
        "<ol><li><p>first</p><pre><code>code</code></pre></li></ol>",
    )

    assert result.text == "1. first\n\n\xa0code\n\n"
    assert result.entities == [
        MessageEntity(type="code", offset=10, length=5),
        MessageEntity(type="pre", offset=10, length=6),
    ]


def test_blockquote_list_item_keeps_entity():
    result = transform_html("<ol><li><blockquote>quote</blockquote></li></ol>")

    assert result.text == "1. quote\n"
    assert result.entities == [
        MessageEntity(type="blockquote", offset=3, length=5),
    ]


@pytest.mark.parametrize("start", [5, 0, -2, 1])
@pytest.mark.parametrize("reversed_", [False, True])
def test_ordered_list_honors_start(start, reversed_):
    reversed_attr = " reversed" if reversed_ else ""
    result = transform_html(
        f'<ol start="{start}"{reversed_attr}>'
        "<li>first</li><li>second</li><li>third</li></ol>",
    )
    step = -1 if reversed_ else 1
    assert result.text == (
        f"{start}. first\n{start + step}. second\n"
        f"{start + 2 * step}. third\n"
    )


def test_reversed_list_counts_only_its_list_items():
    result = transform_html(
        "<ol reversed>\n"
        "<li>first<ul><li>nested</li></ul></li>\n"
        "<li>second</li>\n"
        "</ol>",
    )
    assert result.text == "2. first\n\xa0• nested\n1. second\n"


@pytest.mark.parametrize("reversed_", [False, True])
def test_list_item_value_resets_following_numbers(reversed_):
    reversed_attr = " reversed" if reversed_ else ""
    result = transform_html(
        f'<ol start="5"{reversed_attr}>'
        '<li>first</li><li value="10">reset</li><li>last</li></ol>',
    )
    following = 9 if reversed_ else 11
    assert result.text == f"5. first\n10. reset\n{following}. last\n"


@pytest.mark.parametrize(
    "style, first, second",
    [("a", "a", "b"), ("A", "A", "B"),
     ("i", "i", "ii"), ("I", "I", "II")],
)
@pytest.mark.parametrize(
    "attrs, expected",
    [
        ('start="-2"', "-2. first\n-1. second\n0. third\n"),
        ('start="0"', "0. first\n{first}. second\n{second}. third\n"),
        ('start="1" reversed', "{first}. first\n0. second\n-1. third\n"),
    ],
)
def test_nonpositive_list_ordinals_use_decimal(
    style, first, second, attrs, expected,
):
    result = transform_html(
        f'<ol type="{style}" {attrs}>'
        "<li>first</li><li>second</li><li>third</li></ol>",
    )
    assert result.text == expected.format(first=first, second=second)
