import pytest
from lxml.html import fragment_fromstring

from sulguk.rich.converter import RichConverter
from sulguk.rich.dom import children
from sulguk.rich.html_parsing import drop_none_fields


def elem(html):
    return fragment_fromstring(html)


def converter(base_url=None):
    return RichConverter(base_url)


def test_children_skip_comments():
    assert [c.tag for c in children(elem("<p>a<!-- c --><b/><i/></p>"))] == [
        "b",
        "i",
    ]


def test_children_of_empty():
    assert children(elem("<p>text</p>")) == []


def test_compact():
    assert drop_none_fields(a=1, b=None, c=0, d="", e=False) == {
        "a": 1,
        "c": 0,
        "d": "",
        "e": False,
    }


@pytest.mark.parametrize("html, expected, name", [
    ('<pre class="language-py">x</pre>', "py", "class"),
    ('<pre class="a language-py b">x</pre>', "py", "many"),
    ('<pre class="a">x</pre>', None, "other class"),
    ("<pre>x</pre>", None, "no class"),
    ('<pre class="language-">x</pre>', "", "empty name"),
])
def test_language(html, expected, name):
    assert converter().language(elem(html)) == expected


@pytest.mark.parametrize("html, has_code, name", [
    ("<pre><code>x</code></pre>", True, "only code"),
    ("<pre>\n<code>x</code>\n</pre>", True, "spaces"),
    ("<pre>t<code>x</code></pre>", False, "text before"),
    ("<pre><code>x</code>t</pre>", False, "text after"),
    ("<pre><code>x</code><code>y</code></pre>", False, "two codes"),
    ("<pre><b>x</b></pre>", False, "other tag"),
    ("<pre>x</pre>", False, "no code"),
])
def test_single_code(html, has_code, name):
    pre = elem(html)
    code = converter().single_code(pre)
    if has_code:
        assert code is pre[0]
    else:
        assert code is None


@pytest.mark.parametrize("base_url, url, expected, name", [
    (None, "/a", "/a", "no base"),
    ("https://e.com/x/", "a", "https://e.com/x/a", "relative"),
    ("https://e.com/x/", "/a", "https://e.com/a", "root"),
    ("https://e.com/", "https://o.com/a", "https://o.com/a", "absolute"),
    ("https://e.com/", "#top", "#top", "anchor"),
    (None, "#top", "#top", "anchor without base"),
])
def test_url(base_url, url, expected, name):
    assert converter(base_url).url(url) == expected


def test_progress_text():
    text = converter().progress_text(
        elem('<progress value="5" max="10"></progress>'),
    )
    assert text
    assert text == converter().progress_text(
        elem('<progress value="0.5"></progress>'),
    )


def test_progress_and_meter_differ():
    progress = converter().progress_text(
        elem('<progress value="1" max="2"></progress>'),
    )
    meter = converter().progress_text(
        elem('<meter value="1" max="2"></meter>'),
    )
    assert progress != meter


def test_meter_min():
    with_min = converter().progress_text(
        elem('<meter min="10" max="20" value="15"></meter>'),
    )
    assert with_min == converter().progress_text(
        elem('<meter value="0.5"></meter>'),
    )
