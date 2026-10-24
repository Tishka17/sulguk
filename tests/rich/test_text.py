import pytest

from sulguk.rich.entities import FormattedText, RichTextList, Text


def texts(*items):
    """Inline items: a string is a text, a list is a bold text."""
    return RichTextList([
        Text(item) if isinstance(item, str) else bold(*item)
        for item in items
    ])


def bold(*items):
    return FormattedText("bold", texts(*items))


def clean(*items):
    return texts(*items).clean().to_dict()


def bold_dict(text):
    return {"type": "bold", "text": text}


@pytest.mark.parametrize("items, expected, name", [
    ([], "", "empty"),
    ([""], "", "empty string"),
    (["a"], "a", "one string"),
    (["a", "b"], "ab", "strings are merged"),
    (["a", ["b"], "c"], ["a", bold_dict("b"), "c"], "mixed"),
    ([["b"]], bold_dict("b"), "one item is not a list"),
    ([["a", "b"]], bold_dict("ab"), "nested strings are merged"),
    ([["a", ["b"]]], bold_dict(["a", bold_dict("b")]), "nested"),
])
def test_shape(items, expected, name):
    result = clean(*items)
    assert result == expected, f"Expected {expected!r}, but got {result!r}"


@pytest.mark.parametrize("items, expected, name", [
    ([" a"], "a", "start"),
    (["a "], "a", "end"),
    (["  "], "", "only spaces"),
    (["a ", " b"], "a b", "between strings"),
    (["a ", [" b"]], ["a ", bold_dict("b")], "in wrapper"),
    (["a", [" b"]], ["a", bold_dict(" b")], "kept"),
    ([["a "], " b"], [bold_dict("a "), "b"], "after wrapper"),
    (["a\n", " b"], "a\nb", "after line break"),
    (["\n", " a"], "\na", "line break at start"),
])
def test_spaces(items, expected, name):
    result = clean(*items)
    assert result == expected, f"Expected {expected!r}, but got {result!r}"


@pytest.mark.parametrize("items, expected, name", [
    ([[]], "", "empty wrapper"),
    ([[" "]], "", "wrapper of spaces"),
    (["a", []], "a", "empty wrapper after text"),
    (["a ", [" "]], "a", "spaces before empty"),
    ([[[" "]], "a"], "a", "empty wrapper in wrapper"),
    (
        ["a", ["b ", [" "]]],
        ["a", bold_dict("b")],
        "trailing in wrappers",
    ),
])
def test_empty_wrappers(items, expected, name):
    result = clean(*items)
    assert result == expected, f"Expected {expected!r}, but got {result!r}"


def test_items_without_text_are_kept():
    # the anchor and the emoji have no text to collapse
    from sulguk.rich.entities import Anchor, CustomEmoji

    emoji = CustomEmoji("1", "x")
    assert RichTextList([Anchor("n")]).clean().to_dict() == {
        "type": "anchor",
        "name": "n",
    }
    result = RichTextList([Text("a "), emoji, Text(" b")]).clean().to_dict()
    assert result == ["a ", emoji.to_dict(), " b"]


def test_input_is_not_changed():
    text = texts("a ", [" b "])
    text.clean()
    assert text == texts("a ", [" b "])
