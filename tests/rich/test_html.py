import pytest

from sulguk import transform_rich_html

BASE = "https://e.com/"


def conv(html, **kwargs):
    return transform_rich_html(html, **kwargs).html


@pytest.mark.parametrize(
    "html, expected, name",
    [
        ("", "", "empty"),
        ("  \n ", "", "blank"),
        (None, "", "none"),
        ("<b>a</b>\n\n   <i>b</i>", "<b>a</b> <i>b</i>", "spaces"),
        ("<p>1 &lt; 2 &amp; 3</p>", "<p>1 &lt; 2 &amp; 3</p>", "escape"),
        ('<b class="x" id="y" onclick="z">t</b>', "<b>t</b>", "attrs"),
        (
            '<a href="/p" title="t">x</a>',
            '<a href="https://e.com/p">x</a>',
            "base url",
        ),
        (
            '<a name="c1"></a><a href="#c1">go</a>',
            '<a name="c1"></a><a href="#c1">go</a>',
            "anchors not rebased",
        ),
        (
            '<span class="tg-spoiler">s</span>',
            "<tg-spoiler>s</tg-spoiler>",
            "span spoiler",
        ),
        ("<span>s</span>", "s", "span plain"),
        ("<cite>c</cite>", "<i>c</i>", "cite italic"),
        ("<kbd>k</kbd>", "<code>k</code>", "kbd code"),
        (
            "<blockquote>q<cite>A</cite></blockquote>",
            "<blockquote>q<cite>A</cite></blockquote>",
            "cite author",
        ),
        ("<div>text</div>", "<p>text</p>", "div to p"),
        ("<div><p>a</p><p>b</p></div>", "<p>a</p><p>b</p>", "div transparent"),
        (
            '<pre class="language-python">x = 1</pre>',
            '<pre><code class="language-python">x = 1</code></pre>',
            "pre class language",
        ),
        (
            '<pre><code class="language-go">a</code></pre>',
            '<pre><code class="language-go">a</code></pre>',
            "pre nested code",
        ),
        (
            '<pre class="language-py"><code>x = 1</code></pre>',
            '<pre><code class="language-py">x = 1</code></pre>',
            "pre language with plain code",
        ),
        (
            '<pre class="language-py"><code class="language-go">x</code>'
            "</pre>",
            '<pre><code class="language-go">x</code></pre>',
            "code language is preferred",
        ),
        (
            "<p>a<!-- c -->b</p>",
            "<p>ab</p>",
            "text after a comment",
        ),
        ("<pre>a\n  b</pre>", "<pre>a\n  b</pre>", "pre whitespace"),
        ("<pre>a<br>b</pre>", "<pre>a\nb</pre>", "br in pre is a line break"),
        (
            "<pre><code>a<br>b</code></pre>",
            "<pre><code>a\nb</code></pre>",
            "br in pre code is a line break",
        ),
        (
            '<pre><code class="language-go">a</code> и <b>b</b></pre>',
            '<pre><code class="language-go">a</code></pre>и <b>b</b>',
            "the text after code is outside of the pre",
        ),
        (
            '<code class="language-go">a</code>',
            "<code>a</code>",
            "code no language",
        ),
        (
            '<ol start="3" type="a" foo="1"><li value="7">x</li></ol>'
            '<ul><li><input type="checkbox" checked>done</li></ul>',
            '<ol start="3" type="a"><li value="7">x</li></ol>'
            '<ul><li><input type="checkbox" checked>done</li></ul>',
            "lists",
        ),
        (
            "<ol reversed><li>x</li><li>y</li><li>z</li></ol>",
            '<ol reversed start="3"><li>x</li><li>y</li><li>z</li></ol>',
            "reversed starts from the count",
        ),
        (
            '<ol reversed start="7"><li>x</li></ol>',
            '<ol reversed start="7"><li>x</li></ol>',
            "reversed keeps start",
        ),
        (
            "<blockquote expandable>q</blockquote>"
            "<details open><summary>s</summary>c</details>",
            "<blockquote expandable>q</blockquote>"
            "<details open><summary>s</summary>c</details>",
            "expandable and details",
        ),
        ("<p><q>x</q></p>", "<p>“x”</p>", "quote"),
        ("<script>alert(1)</script><p>a</p>", "<p>a</p>", "script"),
        (
            "<p>a<noscript>hidden</noscript> b</p>",
            "<p>a b</p>",
            "noscript dropped",
        ),
        (
            '<p><output>o</output> <data value="1">d</data> '
            "<time>t</time></p>",
            "<p>o d t</p>",
            "transparent",
        ),
        ("<p>a<wbr>b</p>", "<p>a​b</p>", "wbr"),
        ("<p>H<sub>2</sub>O</p>", "<p>H<sub>2</sub>O</p>", "sub"),
        ("<p><sup>x</sup></p>", "<p><sup>x</sup></p>", "sup"),
        ("<p><mark>m</mark></p>", "<p><mark>m</mark></p>", "mark"),
        (
            '<p><tg-time unix="1" format="wDT">t</tg-time></p>',
            '<p><tg-time unix="1" format="wDT">t</tg-time></p>',
            "time",
        ),
        (
            '<tg-map lat="1" long="2" zoom="3"/>',
            '<tg-map lat="1" long="2" zoom="3"/>',
            "map",
        ),
        (
            "<table><tr><th>h</th></tr></table>",
            "<table><tbody><tr><th>h</th></tr></tbody></table>",
            "table header",
        ),
        (
            '<table><tr><td><tg-reference name="r">м</tg-reference>'
            "</td></tr></table>",
            '<a name="r"></a><table><tbody><tr><td>'
            '<tg-reference name="r">м</tg-reference></td></tr></tbody>'
            "</table>",
            "reference in a cell gets an anchor before the table",
        ),
        (
            '<table><tr><td><a name="x"></a>а</td>'
            '<td><a name="x"></a>б</td></tr></table>',
            '<a name="x"></a><table><tbody><tr><td><a name="x"></a>а</td>'
            '<td><a name="x"></a>б</td></tr></tbody></table>',
            "anchor of cells once",
        ),
        (
            '<table><tr><td align="center" x="1">v</td></tr></table>',
            '<table><tbody><tr><td align="center">v</td></tr></tbody></table>',
            "table cell attrs",
        ),
        (
            '<p><progress value="5" max="10"></progress> x</p>',
            "<p>🟦🟦🟦🟦🟦🟩⬜⬜⬜⬜ x</p>",
            "space after progress",
        ),
        ("<p><q> x</q></p>", "<p>“ x”</p>", "space in quote"),
        (
            "<p><b>hello </b> world</p>",
            "<p><b>hello </b>world</p>",
            "no double space after a tag",
        ),
        ('<a href="">x</a>', "x", "empty href is no link"),
        (
            '<p><progress value="5" max="10"></progress></p>',
            "<p>🟦🟦🟦🟦🟦🟩⬜⬜⬜⬜</p>",
            "progress",
        ),
    ],
)
def test_conversion(html, expected, name):
    assert conv(html, base_url=BASE) == expected


@pytest.mark.parametrize(
    "html, expected, name",
    [
        (
            '<input type="submit" value="Send">',
            '<tg-button type="callback_data" data="submit">Send</tg-button>',
            "submit",
        ),
        (
            '<input type="button" name="go" value="Go">',
            '<tg-button type="callback_data" data="go">Go</tg-button>',
            "button name",
        ),
        (
            '<input type="reset">',
            '<tg-button type="callback_data" data="reset">Reset</tg-button>',
            "no value",
        ),
        ('<input type="checkbox" checked>', "☑️", "checkbox"),
        ('<input type="radio">', "⚪️", "radio"),
        ('<input type="text" value="v">', "<u>v</u>", "text value"),
        ('<input type="text">', "________", "text empty"),
        # only a checkbox which starts <li> is a real checkbox
        (
            '<ul><li><input type="checkbox" checked>x</li></ul>',
            '<ul><li><input type="checkbox" checked>x</li></ul>',
            "list checkbox",
        ),
        (
            '<ul><li>x <input type="checkbox"></li></ul>',
            "<ul><li>x ◻️</li></ul>",
            "checkbox in text",
        ),
    ],
)
def test_input(html, expected, name):
    assert conv(html) == expected


def test_unsupported_tag_raises():
    with pytest.raises(ValueError, match="Unsupported tag"):
        conv("<foo>x</foo>")


@pytest.mark.parametrize(
    "html, expected, name",
    [
        ("<div>a<b>b</b></div>", "<p>a<b>b</b></p>", "text"),
        ("<div><div>x</div></div>", "<p>x</p>", "nested"),
        # a block inside makes the container transparent
        ("<div>text<p>x</p></div>", "text<p>x</p>", "block"),
        # <img> is not a block here, so <div> still becomes a paragraph
        # as in the old mode, neighbour containers are lines of one block
        (
            "<div>a</div><main>b</main><nav>c</nav>",
            "<p>a<br>b<br>c</p>",
            "neighbours are lines",
        ),
        (
            "<div>a</div><div>b</div><p>c</p><div>d</div><div>e</div>",
            "<p>a<br>b</p><p>c</p><p>d<br>e</p>",
            "paragraph splits lines",
        ),
        (
            "<div><b>a</b></div><div>b <i>i</i></div>",
            "<p><b>a</b><br>b <i>i</i></p>",
            "neighbours keep formatting",
        ),
        (
            "<div>a</div><section><p>s</p></section><div>b</div>",
            "<p>a</p><p>s</p><p>b</p>",
            "container with block splits",
        ),
        ("<div> </div>", "", "blank"),
        (
            "<div>a</div><div></div><div>b</div>",
            "<p>a</p><p>b</p>",
            "empty container separates",
        ),
        (
            '<div><img src="https://e.com/a.png"></div>',
            '<p><img src="https://e.com/a.png"></p>',
            "media",
        ),
    ],
)
def test_container(html, expected, name):
    assert conv(html) == expected


@pytest.mark.parametrize(
    "html, expected, name",
    [
        (
            "<table><tr><td>до<blockquote>цитата</blockquote>после</td>"
            "</tr></table>",
            "<table><tbody><tr><td>до<br>▎ цитата<br>после</td></tr>"
            "</tbody></table>",
            "quote in a cell is a line of its own",
        ),
        (
            "<details><summary>s<blockquote>q</blockquote></summary>"
            "<p>x</p></details>",
            "<details><summary>s<br>▎ q</summary><p>x</p></details>",
            "quote in a summary",
        ),
        (
            '<table><tr><td>до<img src="https://e.com/a.png" alt="лого">после</td></tr>'
            "</table>",
            "<table><tbody><tr><td>до<tg-button type=\"url\" "
            "url=\"https://e.com/a.png\">🖼️лого</tg-button>после"
            "</td></tr></tbody></table>",
            "image in a cell is an icon with a link",
        ),
        (
            '<table><tr><td><img src="https://e.com/a.png"></td></tr></table>',
            "<table><tbody><tr><td><tg-button type=\"url\" "
            "url=\"https://e.com/a.png\">🖼️https://e.com/a.png"
            "</tg-button></td></tr></tbody></table>",
            "image without alt shows its address",
        ),
        (
            '<table><tr><td><a href="https://e.com/x">'
            '<img src="https://e.com/a.png" alt="pic"></a></td></tr></table>',
            "<table><tbody><tr><td><tg-button type=\"url\" "
            "url=\"https://e.com/a.png\">🖼️pic</tg-button>"
            "</td></tr></tbody></table>",
            "image in a link in a cell is a button to the image",
        ),
        (
            '<details><summary>s <img src="https://e.com/a.png" alt="pic">'
            "</summary><p>x</p></details>",
            "<details><summary>s <a href=\"https://e.com/a.png\">🖼️pic</a>"
            "</summary><p>x</p></details>",
            "image in a summary",
        ),
        (
            "<table><tr><td>до<h3>заголовок</h3>после</td>"
            "<td>до<hr>после</td>"
            "<td>до<tg-math-block>x^2</tg-math-block>после</td>"
            "<td>до<footer>футер</footer>после</td></tr></table>",
            "<table><tbody><tr><td>до<br>заголовок<br>после</td>"
            "<td>до<br>──────────<br>после</td>"
            "<td>до<br>x^2<br>после</td>"
            "<td>до<br>футер<br>после</td></tr></tbody></table>",
            "heading, divider, formula and footer are lines in a cell",
        ),
        (
            "<table><tr><td><p>абзац 1</p><p>абзац 2</p></td>"
            "<td><div>d1</div><div>d2</div></td>"
            "<td><p></p>y</td></tr></table>",
            "<table><tbody><tr><td>абзац 1<br>абзац 2</td>"
            "<td>d1<br>d2</td><td>y</td></tr></tbody></table>",
            "paragraphs in a cell are lines, an empty one is dropped",
        ),
        (
            "<table><tr><td><details><summary>заголовок</summary>"
            "<p>скрытое</p></details></td></tr></table>",
            "<table><tbody><tr><td>заголовок<br>"
            "<tg-spoiler>скрытое</tg-spoiler></td></tr></tbody></table>",
            "details in a cell: the summary and the body as a spoiler",
        ),
        (
            "<table><tr><td>до<details><summary>з</summary>т1<p>п2</p>"
            "</details>после</td></tr></table>",
            "<table><tbody><tr><td>до<br>з<br>"
            "<tg-spoiler>т1<br>п2</tg-spoiler><br>после</td></tr></tbody>"
            "</table>",
            "details in a cell keeps the text around",
        ),
        (
            "<table><tr><td><details><summary>только</summary></details>"
            "</td></tr></table>",
            "<table><tbody><tr><td>только</td></tr></tbody></table>",
            "details without a body in a cell",
        ),
        (
            "<table><tr><td><pre>строка 1\nстрока 2</pre></td></tr></table>",
            "<table><tbody><tr><td>строка 1<br>строка 2</td></tr>"
            "</tbody></table>",
            "pre in a cell keeps its line breaks",
        ),
        ("<blockquote> </blockquote><p>a</p>", "<p>a</p>", "empty quote"),
        ("<ul><li> </li></ul><p>a</p>", "<p>a</p>", "list of empty items"),
        (
            "<ul><li></li><li>a</li></ul>",
            "<ul><li>\u200b</li><li>a</li></ul>",
            "empty item stays with its mark",
        ),
        (
            "<ol><li></li><li>a</li><li>b</li></ol>",
            '<ol><li>\u200b</li><li>a</li><li>b</li></ol>',
            "empty item of an ordered list stays with its number",
        ),
        (
            "<ol reversed><li>a</li><li></li><li>b</li></ol>",
            '<ol reversed start="3"><li>a</li><li>\u200b</li><li>b</li></ol>',
            "empty item of a reversed list stays with its number",
        ),
        (
            "<ul><li><blockquote></blockquote></li></ul>",
            "",
            "empty quote in an item",
        ),
        (
            "<blockquote><p></p></blockquote>",
            "",
            "quote of an empty paragraph",
        ),
        (
            "<blockquote><cite>a</cite></blockquote>",
            "<blockquote><cite>a</cite></blockquote>",
            "quote with a credit only",
        ),
        (
            "<blockquote><hr></blockquote>",
            "<blockquote><p>──────────</p></blockquote>",
            "quote with a divider",
        ),
        ("<footer>f</footer>", "<hr><footer>f</footer>", "footer divider"),
        (
            "<hr><footer>a</footer><footer>b</footer>",
            "<hr><footer>a</footer><footer>b</footer>",
            "footers share one divider",
        ),
        (
            "<blockquote><p>p</p><footer>f</footer></blockquote>",
            "<blockquote><p>p</p><p>──────────</p><footer>f</footer>"
            "</blockquote>",
            "footer in a quote",
        ),
    ],
)
def test_empty_blocks(html, expected, name):
    assert conv(html) == expected


@pytest.mark.parametrize(
    "html, expected, name",
    [
        (
            "<details><summary>s<ul><li>a</li><li>b</li></ul></summary>"
            "<p>x</p></details>",
            "<details><summary>s<br>• a<br>• b</summary><p>x</p></details>",
            "list in a summary",
        ),
        (
            "<table><tr><td><table><tr><td>a</td><td>b</td></tr>"
            "<tr><td>c</td></tr></table></td></tr></table>",
            "<table><tbody><tr><td>a b<br>c</td></tr></tbody></table>",
            "table in a cell",
        ),
    ],
)
def test_text_only_parents(html, expected, name):
    assert conv(html) == expected


def test_summary_outside_of_details_is_kept():
    assert conv("<summary>s</summary>") == "<summary>s</summary>"
