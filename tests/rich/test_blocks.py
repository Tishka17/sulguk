import pytest

from sulguk import transform_rich_blocks

BASE = "https://e.com/"
IMG = '<img src="https://e.com/a.png">'


def conv(html, **kwargs):
    return transform_rich_blocks(html, **kwargs).blocks


def para(text):
    return {"type": "paragraph", "text": text}


def bold(text):
    return {"type": "bold", "text": text}


def button_row(html):
    return f"<tg-button-row>{html}</tg-button-row>"


def one_button(html):
    return conv(button_row(html))[0]["buttons"][0]


@pytest.mark.parametrize(
    "html, expected, name",
    [
        ("", [], "empty"),
        ("  \n ", [], "blank"),
        (None, [], "none"),
        ("<p>a\n\n   b</p>", [para("a b")], "spaces"),
        (
            "<div>bare <b>text</b><p>para</p>tail</div>",
            [para(["bare ", bold("text")]), para("para"), para("tail")],
            "bare text to paragraph",
        ),
        (
            "<h1>A</h1><h6>B</h6>",
            [
                {"type": "heading", "text": "A", "size": 1},
                {"type": "heading", "text": "B", "size": 6},
            ],
            "headings",
        ),
        (
            "<hr><footer>f</footer>",
            [{"type": "divider"}, {"type": "footer", "text": "f"}],
            "divider footer",
        ),
        (
            "<footer>f</footer>",
            [{"type": "divider"}, {"type": "footer", "text": "f"}],
            "footer gets a divider",
        ),
        (
            "<footer>a</footer><footer>b</footer>",
            [
                {"type": "divider"},
                {"type": "footer", "text": "a"},
                {"type": "footer", "text": "b"},
            ],
            "footers in a row share one divider",
        ),
        (
            "<footer>a</footer><p>x</p><footer>b</footer>",
            [
                {"type": "divider"},
                {"type": "footer", "text": "a"},
                para("x"),
                {"type": "divider"},
                {"type": "footer", "text": "b"},
            ],
            "footer after a paragraph gets its own divider",
        ),
        (
            "<blockquote><p>a</p><hr><p>b</p></blockquote>",
            [{"type": "blockquote",
              "blocks": [para("a"), para("──────────"), para("b")]}],
            "divider in a quote is a line of text",
        ),
        (
            "<blockquote><p>p</p><footer>f</footer></blockquote>",
            [{"type": "blockquote",
              "blocks": [para("p"), para("──────────"),
                         {"type": "footer", "text": "f"}]}],
            "footer in a quote gets a line before it",
        ),
        (
            "<tg-math-block>E=mc^2</tg-math-block>",
            [{"type": "mathematical_expression", "expression": "E=mc^2"}],
            "math block",
        ),
        (
            '<pre class="language-py">x\n y</pre>',
            [{"type": "pre", "text": "x\n y", "language": "py"}],
            "pre class",
        ),
        (
            '<pre><code class="language-go">a</code></pre>',
            [{"type": "pre", "text": "a", "language": "go"}],
            "pre nested code",
        ),
        ("<pre>\n a</pre>", [{"type": "pre", "text": " a"}], "pre lf"),
        (
            "<pre>line1<br>line2</pre>",
            [{"type": "pre", "text": "line1\nline2"}],
            "pre br",
        ),
        (
            "<pre><code>a<br>b</code> <b>c</b></pre>",
            [
                {"type": "pre", "text": "a\nb"},
                {"type": "paragraph", "text": {"type": "bold", "text": "c"}},
            ],
            "pre br in nested tags, the text after code is outside of it",
        ),
        (
            "<blockquote>q<cite>A</cite></blockquote>",
            [{"type": "blockquote", "blocks": [para("q")], "credit": "A"}],
            "blockquote credit",
        ),
        (
            "<blockquote><p>a</p><p>b</p></blockquote>",
            [{"type": "blockquote", "blocks": [para("a"), para("b")]}],
            "blockquote blocks",
        ),
        (
            "<blockquote expandable>e</blockquote>",
            [{"type": "expandable_blockquote", "text": "e"}],
            "expandable blockquote",
        ),
        (
            "<details open><summary>s</summary>c<p>d</p></details>",
            [
                {
                    "type": "details",
                    "summary": "s",
                    "is_open": True,
                    "blocks": [para("c"), para("d")],
                }
            ],
            "details",
        ),
        (
            "<aside>Pull<cite>Who</cite></aside>",
            [{"type": "pullquote", "text": "Pull", "credit": "Who"}],
            "pullquote",
        ),
        (
            "<tg-thinking>Thinking...</tg-thinking>",
            [{"type": "thinking", "text": "Thinking..."}],
            "thinking",
        ),
        (
            '<a name="top"></a><p>x</p>',
            [{"type": "anchor", "name": "top"}, para("x")],
            "anchor block",
        ),
        ("<script>x</script><p>a</p>", [para("a")], "script dropped"),
        (
            "<p>a<noscript>hidden</noscript> b</p>",
            [para("a b")],
            "noscript dropped",
        ),
        (
            '<p><output>o</output> <data value="1">d</data> '
            "<time>t</time></p>",
            [para("o d t")],
            "transparent",
        ),
        (
            "<p>a<!-- c -->b</p>",
            [para("ab")],
            "text after a comment",
        ),
    ],
)
def test_text_blocks(html, expected, name):
    assert conv(html) == expected


@pytest.mark.parametrize(
    "html, expected, name",
    [
        (
            "<b>a <i>b</i></b>",
            bold(["a ", {"type": "italic", "text": "b"}]),
            "nesting",
        ),
        (
            '<span class="tg-spoiler">s</span>',
            {"type": "spoiler", "text": "s"},
            "span spoiler",
        ),
        ("<kbd>k</kbd>", {"type": "code", "text": "k"}, "kbd"),
        ("<cite>c</cite>", {"type": "italic", "text": "c"}, "cite"),
        ("<mark>m</mark>", {"type": "marked", "text": "m"}, "mark"),
        ("<sub>1</sub>", {"type": "subscript", "text": "1"}, "sub"),
        ("<sup>2</sup>", {"type": "superscript", "text": "2"}, "sup"),
        (
            '<a href="/x">u</a>',
            {"type": "url", "url": "https://e.com/x", "text": "u"},
            "url base",
        ),
        (
            '<a href="#c">c</a>',
            {"type": "anchor_link", "anchor_name": "c", "text": "c"},
            "anchor link",
        ),
        (
            '<a href="mailto:a@b.c">m</a>',
            {"type": "email_address", "email_address": "a@b.c", "text": "m"},
            "email",
        ),
        (
            '<a href="tel:+1">t</a>',
            {"type": "phone_number", "phone_number": "+1", "text": "t"},
            "phone",
        ),
        (
            '<tg-reference name="r">x</tg-reference>',
            {"type": "reference", "name": "r", "text": "x"},
            "reference",
        ),
        (
            '<tg-emoji emoji-id="1">😀</tg-emoji>',
            {
                "type": "custom_emoji",
                "custom_emoji_id": "1",
                "alternative_text": "😀",
            },
            "custom emoji",
        ),
        (
            '<tg-time unix="5" format="wDT">t</tg-time>',
            {
                "type": "date_time",
                "unix_time": 5,
                "date_time_format": "wDT",
                "text": "t",
            },
            "date time",
        ),
        (
            "<tg-math>x^2</tg-math>",
            {"type": "mathematical_expression", "expression": "x^2"},
            "math",
        ),
        (
            '<tg-button type="url" url="https://e.com">me</tg-button>',
            {
                "type": "button",
                "button": {"text": "me", "url": "https://e.com"},
            },
            "button",
        ),
    ],
)
def test_inline(html, expected, name):
    assert conv(f"<p>{html}</p>", base_url=BASE) == [para(expected)]


def test_anchor_inside_text():
    assert conv('<p>x<a name="n1"></a></p>')[0]["text"] == [
        "x",
        {"type": "anchor", "name": "n1"},
    ]


@pytest.mark.parametrize(
    "html, expected, name",
    [
        ("a<br>b", "a\nb", "br"),
        ("a<q>b</q>c", "a“b”c", "quote"),
        ("a<wbr>b", "a​b", "wbr"),
    ],
)
def test_inline_text_tags(html, expected, name):
    assert conv(f"<p>{html}</p>") == [para(expected)]


def item(*blocks, **extra):
    return {"blocks": list(blocks), **extra}


@pytest.mark.parametrize(
    "html, expected, name",
    [
        (
            "<ul><li>a<ul><li>n</li></ul></li></ul>",
            [
                {
                    "type": "list",
                    "items": [
                        item(
                            para("a"),
                            {"type": "list", "items": [item(para("n"))]},
                        )
                    ],
                }
            ],
            "nested",
        ),
        (
            '<ul><li><input type="checkbox" checked>done</li>'
            '<li><input type="checkbox">todo</li></ul>',
            [
                {
                    "type": "list",
                    "items": [
                        item(para("done"), has_checkbox=True, is_checked=True),
                        item(para("todo"), has_checkbox=True),
                    ],
                }
            ],
            "checkboxes",
        ),
        (
            "<ol><li>x</li><li>y</li></ol>",
            [
                {
                    "type": "list",
                    "items": [
                        item(para("x"), value=1, type="1"),
                        item(para("y"), value=2, type="1"),
                    ],
                }
            ],
            "ordered numbered",
        ),
        (
            '<ol type="I"><li>x</li><li>y</li></ol>',
            [
                {
                    "type": "list",
                    "items": [
                        item(para("x"), value=1, type="I"),
                        item(para("y"), value=2, type="I"),
                    ],
                }
            ],
            "ordered type has values",
        ),
        (
            '<ul><li><input type="checkbox" checked></li></ul>',
            [
                {
                    "type": "list",
                    "items": [
                        item(
                            {"type": "paragraph", "text": "​"},
                            has_checkbox=True,
                            is_checked=True,
                        ),
                    ],
                }
            ],
            "checkbox only item",
        ),
        ("<ul></ul>", [], "empty ul"),
        ("<ol><li></li></ol>", [], "empty ol item"),
        (
            "<ol><li></li><li>a</li></ol>",
            [{
                "type": "list",
                "items": [
                    item({"type": "paragraph", "text": "​"},
                         value=1, type="1"),
                    item({"type": "paragraph", "text": "a"},
                         value=2, type="1"),
                ],
            }],
            "empty item stays with its number",
        ),
    ],
)
def test_lists(html, expected, name):
    assert conv(html) == expected


@pytest.mark.parametrize(
    "html, values, name",
    [
        (
            '<ol start="3"><li>x</li><li value="9">y</li><li>z</li></ol>',
            [3, 9, 10],
            "start and value",
        ),
        ("<ol reversed><li>x</li><li>y</li></ol>", [2, 1], "reversed"),
    ],
)
def test_ordered_list_values(html, values, name):
    items = conv(html)[0]["items"]
    assert [i["value"] for i in items] == values


def test_ordered_list_type():
    items = conv('<ol type="a"><li>x</li><li type="I">y</li></ol>')[0]["items"]
    assert [i["type"] for i in items] == ["a", "I"]


def test_button_row():
    assert conv(
        '<tg-button-row align="center">'
        '<tg-button type="url" style="success" url="/x">u</tg-button>'
        '<tg-button type="callback_data" data="cb">c</tg-button>'
        '<tg-button type="disabled">d</tg-button></tg-button-row>',
        base_url=BASE,
    ) == [
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "u", "style": "success", "url": "https://e.com/x"},
                {"text": "c", "callback_data": "cb"},
                {"text": "d", "disabled": {}},
            ],
        }
    ]


@pytest.mark.parametrize(
    "html, key, expected, name",
    [
        (
            '<tg-button type="login_url" url="https://e.com"'
            ' forward-text="f" request-write-access>b</tg-button>',
            "login_url",
            {
                "url": "https://e.com",
                "forward_text": "f",
                "request_write_access": True,
            },
            "login url",
        ),
        (
            '<tg-button type="switch_inline_query_chosen_chat" query="q"'
            " allow-user-chats allow-channel-chats>b</tg-button>",
            "switch_inline_query_chosen_chat",
            {
                "query": "q",
                "allow_user_chats": True,
                "allow_channel_chats": True,
            },
            "chosen chat",
        ),
        (
            '<tg-button type="copy_text" text="t">b</tg-button>',
            "copy_text",
            {"text": "t"},
            "copy text",
        ),
        (
            '<tg-button type="web_app" url="https://e.com">b</tg-button>',
            "web_app",
            {"url": "https://e.com"},
            "web app",
        ),
        (
            '<tg-button type="switch_inline_query" query="q">b</tg-button>',
            "switch_inline_query",
            "q",
            "switch inline",
        ),
        (
            '<tg-button type="switch_inline_query_current_chat"'
            ' query="q">b</tg-button>',
            "switch_inline_query_current_chat",
            "q",
            "switch current",
        ),
    ],
)
def test_button_types(html, key, expected, name):
    assert one_button(html)[key] == expected


@pytest.mark.parametrize(
    "html, message, name",
    [
        ("<foo>x</foo>", "Unsupported tag", "unknown tag"),
        (f"<p>text {IMG} more</p>", "separate block", "inline media"),
        ("<img>", "requires the src", "no src"),
        (
            '<ol><li value="x">a</li></ol>',
            "must be an integer",
            "li value",
        ),
        ('<img src="tg://photo?id=a">', "tg:// links", "tg link"),
        (
            "<blockquote expandable><ul><li>x</li></ul></blockquote>",
            "only inline",
            "expandable nested",
        ),
        (
            "<figure><figcaption>x</figcaption></figure>",
            "media element",
            "figure empty",
        ),
        (f"<figure>{IMG}{IMG}</figure>", "exactly one", "figure two media"),
        (
            "<p><figcaption>x</figcaption></p>",
            "only inside <figure>",
            "stray figcaption",
        ),
        ('<tg-map lat="x" long="1"/>', "lat and long", "map coordinates"),
        (
            "<tg-collage><p>x</p></tg-collage>",
            "not allowed inside",
            "collage content",
        ),
        (
            button_row('<tg-button type="x">b</tg-button>'),
            "Unknown <tg-button> type",
            "button type",
        ),
        (
            button_row('<tg-button type="disabled" style="x">b</tg-button>'),
            "Unknown button style",
            "button style",
        ),
        (button_row(""), "1-8 buttons", "no buttons"),
        (
            button_row('<tg-button type="disabled">b</tg-button>' * 9),
            "1-8 buttons",
            "too many buttons",
        ),
        (
            '<tg-button-row align="x"><tg-button type="disabled">b'
            "</tg-button></tg-button-row>",
            "Unknown align",
            "button align",
        ),
    ],
)
def test_errors(html, message, name):
    with pytest.raises(ValueError, match=message):
        conv(html)


def test_limits_edge_is_allowed():
    assert len(conv("<p>x</p>" * 500)) == 500


@pytest.mark.parametrize(
    "html",
    [
        "<blockquote> </blockquote>",
        "<blockquote><p></p></blockquote>",
        "<ul><li> </li></ul>",
        "<ul><li><blockquote></blockquote></li></ul>",
    ],
)
def test_empty_blocks_are_dropped(html):
    assert conv(html) == []


@pytest.mark.parametrize(
    "html, expected, name",
    [
        (
            '<p><input type="submit" value="Send"></p>',
            para(
                {
                    "type": "button",
                    "button": {
                        "text": "Send",
                        "callback_data": "submit",
                    },
                }
            ),
            "submit",
        ),
        (
            '<p><input type="button" name="go" value="Go"></p>',
            para(
                {
                    "type": "button",
                    "button": {
                        "text": "Go",
                        "callback_data": "go",
                    },
                }
            ),
            "button name",
        ),
        (
            '<p>a <input type="reset"> b</p>',
            para(
                [
                    "a ",
                    {
                        "type": "button",
                        "button": {
                            "text": "Reset",
                            "callback_data": "reset",
                        },
                    },
                    " b",
                ]
            ),
            "no value",
        ),
        (
            '<p><input type="text" value="v"></p>',
            para({"type": "underline", "text": "v"}),
            "text value",
        ),
    ],
)
def test_input_button(html, expected, name):
    assert conv(html) == [expected]


@pytest.mark.parametrize(
    "html, expected, name",
    [
        ("<div>a<b>b</b></div>", [para(["a", bold("b")])], "text"),
        ("<div><div>x</div></div>", [para("x")], "nested"),
        ("<div>text<p>x</p></div>", [para("text"), para("x")], "block"),
        # as in the old mode, neighbour containers are lines of one block
        (
            "<div>a</div><main>b</main><nav>c</nav>",
            [para("a\nb\nc")],
            "neighbours are lines",
        ),
        (
            "<div>a</div><div>b</div><p>c</p><div>d</div><div>e</div>",
            [para("a\nb"), para("c"), para("d\ne")],
            "paragraph splits lines",
        ),
        (
            "<div><b>a</b></div><div>b <i>i</i></div>",
            [para([bold("a"), "\nb ", {"type": "italic", "text": "i"}])],
            "neighbours keep formatting",
        ),
        (
            "<div>a</div><section><p>s</p></section><div>b</div>",
            [para("a"), para("s"), para("b")],
            "container with block splits",
        ),
        ("<div> </div>", [], "blank"),
        (
            "<div>a</div><div></div><div>b</div>",
            [para("a"), para("b")],
            "empty container separates",
        ),
        # media is a block here, unlike in the html mode
        (
            f"<div>{IMG}</div>",
            [
                {
                    "type": "photo",
                    "photo": {"type": "photo", "media": "https://e.com/a.png"},
                }
            ],
            "media",
        ),
    ],
)
def test_container(html, expected, name):
    assert conv(html) == expected


def test_summary_outside_of_details_is_a_paragraph():
    assert conv("<summary>s</summary>") == [para("s")]


@pytest.mark.parametrize(
    "html, model, name",
    [
        ("<h1>T</h1>", "SectionHeading", "heading"),
        (
            "<p>a <b>b</b> <a href='https://e.com'>l</a></p>",
            "Paragraph",
            "paragraph",
        ),
        (
            "<ol start='2'><li><input type='checkbox' checked>x</li></ol>",
            "List",
            "list",
        ),
        (
            "<blockquote>q<cite>A</cite></blockquote>",
            "BlockQuotation",
            "blockquote",
        ),
        (
            "<blockquote expandable>q</blockquote>",
            "ExpandableBlockQuotation",
            "expandable",
        ),
        ("<hr>", "Divider", "divider"),
        ("<footer>f</footer>", "Divider+Footer", "footer"),
        (
            "<details open><summary>s</summary>c</details>",
            "Details",
            "details",
        ),
        (
            "<table><tr><th>h</th><td colspan='2'>v</td></tr></table>",
            "Table",
            "table",
        ),
        ("<pre class='language-py'>x</pre>", "Preformatted", "pre"),
        ("<tg-math-block>x</tg-math-block>", "MathematicalExpression", "math"),
        ('<img src="https://e.com/a.png" tg-spoiler>', "Photo", "photo"),
        ('<video src="https://e.com/v.mp4"></video>', "Video", "video"),
        (
            '<video src="https://e.com/a.gif"></video>',
            "Animation",
            "animation",
        ),
        ('<audio src="https://e.com/a.mp3"></audio>', "Audio", "audio"),
        (
            '<audio src="https://e.com/a.ogg"></audio>',
            "VoiceNote",
            "voice note",
        ),
        (
            '<tg-document src="https://e.com/d.zip"></tg-document>',
            "Document",
            "document",
        ),
        (
            f"<figure>{IMG}<figcaption>c<cite>w</cite></figcaption></figure>",
            "Photo",
            "figure",
        ),
        ('<tg-map lat="1" long="2" zoom="3"/>', "Map", "map"),
        (f"<tg-collage>{IMG}</tg-collage>", "Collage", "collage"),
        (f"<tg-slideshow>{IMG}</tg-slideshow>", "Slideshow", "slideshow"),
        ("<aside>p<cite>w</cite></aside>", "PullQuotation", "pullquote"),
        ("<tg-thinking>t</tg-thinking>", "Thinking", "thinking"),
        ('<a name="n"></a>', "Anchor", "anchor"),
        (
            button_row(
                '<tg-button type="url" style="primary"'
                ' url="https://e.com">u</tg-button>'
                '<tg-button type="disabled">d</tg-button>'
            ),
            "Buttons",
            "buttons",
        ),
        (
            '<p><tg-button type="callback_data" data="x">c</tg-button></p>',
            "Paragraph",
            "inline button",
        ),
    ],
)
def test_blocks_are_accepted_by_aiogram(html, model, name):
    # sulguk itself does not need aiogram, so skip only these tests
    input_rich_message = pytest.importorskip("aiogram.types").InputRichMessage
    message = input_rich_message(blocks=conv(html))
    models = model.split("+")
    assert [type(b).__name__ for b in message.blocks] == [
        f"InputRichBlock{m}" for m in models
    ]
