import pytest

from sulguk import transform_rich_blocks


def conv(html, **kwargs):
    return transform_rich_blocks(html, **kwargs).blocks


def cell(**extra):
    return {"align": "left", "valign": "middle", **extra}


def table(*rows, **extra):
    return [{"type": "table", "cells": list(rows), **extra}]


@pytest.mark.parametrize(
    "html, expected, name",
    [
        (
            "<table><tr><th>h</th></tr>"
            '<tr><td colspan="2" align="center">v</td></tr></table>',
            table(
                [cell(text="h", is_header=True, align="center")],
                [cell(text="v", align="center", colspan=2)],
            ),
            "header and colspan",
        ),
        (
            "<table><caption>c</caption><thead><tr><th>h</th></tr></thead>"
            "<tbody><tr><td>v</td></tr></tbody></table>",
            table(
                [cell(text="h", is_header=True, align="center")],
                [cell(text="v")],
                caption="c",
            ),
            "sections and caption",
        ),
        (
            '<table><tr><th>a</th><th align="right">b</th>'
            '<th align="left">c</th></tr></table>',
            table(
                [
                    cell(text="a", is_header=True, align="center"),
                    cell(text="b", is_header=True, align="right"),
                    cell(text="c", is_header=True, align="left"),
                ]
            ),
            "header align default is center",
        ),
        (
            "<table><tfoot><tr><td>f</td></tr></tfoot></table>",
            table([cell(text="f")]),
            "tfoot",
        ),
        (
            "<table><tr><td>a</td><td>b</td></tr><tr><td>c</td></tr></table>",
            table([cell(text="a"), cell(text="b")], [cell(text="c")]),
            "rows of different length",
        ),
        (
            '<table><tr><td rowspan="3">v</td></tr></table>',
            table([cell(text="v", rowspan=3)]),
            "rowspan",
        ),
        (
            '<table><tr><td valign="top" align="right">v</td></tr></table>',
            table([cell(text="v", align="right", valign="top")]),
            "alignment",
        ),
        (
            "<table><tr><td></td></tr></table>",
            table([cell()]),
            "empty cell has no text",
        ),
        (
            "<table><tr><td><b>x</b> y</td></tr></table>",
            table([cell(text=[{"type": "bold", "text": "x"}, " y"])]),
            "cell formatting",
        ),
        (
            "<table><tr><td>a</td></tr></table>",
            table([cell(text="a")]),
            "no caption by default",
        ),
        (
            "<table><tr><td><ul><li>a</li><li>b</li></ul></td></tr></table>",
            table([cell(text="• a\n• b")]),
            "list in a cell",
        ),
        (
            '<table><tr><td><ol start="3"><li>a</li><li value="10">b</li>'
            "<li>c</li></ol></td></tr></table>",
            table([cell(text="3. a\n10. b\n11. c")]),
            "ordered list in a cell",
        ),
        (
            '<table><tr><td><ol type="i" reversed><li>a</li><li>b</li></ol>'
            "</td></tr></table>",
            table([cell(text="ii. a\ni. b")]),
            "ordered list type and reversed",
        ),
        (
            "<table><tr><td>x<ul><li>a</li></ul>y</td></tr></table>",
            table([cell(text="x\n• a\ny")]),
            "text around a list in a cell",
        ),
        (
            "<table><tr><td><ul><li>a<ul><li>b</li></ul></li></ul></td></tr>"
            "</table>",
            table([cell(text="• a\n" + "\xa0" * 4 + "• b")]),
            "nested list in a cell",
        ),
        (
            "<table><tr><td><ul><li><b>a</b> b</li></ul></td></tr></table>",
            table([cell(text=["• ", {"type": "bold", "text": "a"}, " b"])]),
            "formatting in a list item of a cell",
        ),
        (
            "<table><tr><td><ul></ul></td></tr></table>",
            table([cell()]),
            "empty list in a cell",
        ),
        (
            "<table><tr><td><table><tr><td>a</td></tr></table></td></tr>"
            "</table>",
            table([cell(text="a")]),
            "table in a cell",
        ),
        (
            "<table><tr><td>x<table><tr><td>a</td><td>b</td></tr>"
            "<tr><td>c</td></tr></table>y</td></tr></table>",
            table([cell(text="xa b\ncy")]),
            "table in a cell keeps the text around",
        ),
        (
            '<table><tr><td><tg-reference name="r">метка</tg-reference>'
            "</td></tr></table>",
            [
                {"type": "anchor", "name": "r"},
                *table([cell(text={
                    "type": "reference", "text": "метка", "name": "r",
                })]),
            ],
            "reference in a cell gets an anchor before the table",
        ),
        (
            '<table><tr><td><a name="x"></a>а</td>'
            '<td><a name="y"></a><a name="x"></a>б</td></tr></table>',
            [
                {"type": "anchor", "name": "x"},
                {"type": "anchor", "name": "y"},
                *table([
                    cell(text=[{"type": "anchor", "name": "x"}, "а"]),
                    cell(text=[
                        {"type": "anchor", "name": "y"},
                        {"type": "anchor", "name": "x"},
                        "б",
                    ]),
                ]),
            ],
            "anchors of cells, once each, in order",
        ),
        (
            '<tg-reference name="r">м</tg-reference>'
            "<table><tr><td>v</td></tr></table>",
            [
                {"type": "paragraph", "text": {
                    "type": "reference", "text": "м", "name": "r",
                }},
                *table([cell(text="v")]),
            ],
            "reference outside of a table gets no anchor",
        ),
    ],
)
def test_table(html, expected, name):
    assert conv(html) == expected


@pytest.mark.parametrize(
    "html, expected, name",
    [
        (
            "<details><summary>s<ul><li>a</li><li>b</li></ul></summary>"
            "<p>x</p></details>",
            [{"type": "details", "summary": "s\n• a\n• b",
              "blocks": [{"type": "paragraph", "text": "x"}]}],
            "list in a summary",
        ),
        (
            "<table><caption><ol><li>a</li><li>b</li></ol></caption>"
            "<tr><td>c</td></tr></table>",
            table([cell(text="c")], caption="1. a\n2. b"),
            "list in a caption",
        ),
        (
            '<figure><img src="https://e.com/a.png"><figcaption>'
            "<ul><li>a</li></ul></figcaption></figure>",
            [{"type": "photo",
              "photo": {"type": "photo", "media": "https://e.com/a.png"},
              "caption": {"text": "• a"}}],
            "list in a figcaption",
        ),
        (
            "<table><tr><td>до<blockquote>цитата</blockquote>после</td>"
            "</tr></table>",
            table([cell(text="до\n▎ цитата\nпосле")]),
            "quote in a cell is a line of its own",
        ),
        (
            "<table><tr><td><pre>строка 1\nстрока 2</pre></td></tr></table>",
            table([cell(text="строка 1\nстрока 2")]),
            "pre in a cell keeps its line breaks",
        ),
        (
            "<table><tr><td>до<pre>a\n  b</pre>после</td></tr></table>",
            table([cell(text="до\na\n  b\nпосле")]),
            "pre in a cell keeps the text around",
        ),
        (
            "<table><tr><td><blockquote>a<blockquote>b</blockquote>"
            "</blockquote></td></tr></table>",
            table([cell(text="▎ a\n▎ b")]),
            "nested quotes in a cell",
        ),
        (
            "<details><summary>s<blockquote>q</blockquote></summary>"
            "<p>x</p></details>",
            [{"type": "details", "summary": "s\n▎ q",
              "blocks": [{"type": "paragraph", "text": "x"}]}],
            "quote in a summary",
        ),
        (
            '<table><tr><td>до<img src="https://e.com/a.png" alt="лого">'
            "после</td></tr></table>",
            table([cell(text=[
                "до",
                {"type": "button", "button": {"text": "🖼️лого", "url": "https://e.com/a.png"}},
                "после",
            ])]),
            "image in a cell is an icon with a link",
        ),
        (
            '<table><tr><td><img src="https://e.com/a.png"></td></tr></table>',
            table([cell(text={"type": "button", "button": {"text": "🖼️https://e.com/a.png", "url": "https://e.com/a.png"}})]),
            "image without alt shows its address",
        ),
        (
            '<table><tr><td><video src="https://e.com/a.mp4"></video></td>'
            '<td><audio src="https://e.com/a.mp3"></audio></td>'
            '<td><tg-document src="https://e.com/a.pdf" alt="отчёт">'
            "</tg-document></td></tr></table>",
            table([
                cell(text={"type": "button", "button": {"text": "🎞️https://e.com/a.mp4", "url": "https://e.com/a.mp4"}}),
                cell(text={"type": "button", "button": {"text": "🎵https://e.com/a.mp3", "url": "https://e.com/a.mp3"}}),
                cell(text={"type": "button", "button": {"text": "📎отчёт", "url": "https://e.com/a.pdf"}}),
            ]),
            "video, audio and document in cells",
        ),
        (
            '<table><tr><td><a href="https://e.com/x">'
            '<img src="https://e.com/a.png" alt="pic"></a></td></tr></table>',
            table([cell(text={"type": "button", "button": {"text": "🖼️pic", "url": "https://e.com/a.png"}})]),
            "image in a link in a cell is a button to the image",
        ),
        (
            '<details><summary>s <img src="https://e.com/a.png" alt="pic">'
            "</summary><p>x</p></details>",
            [{"type": "details",
              "summary": ["s ", {"type": "url", "text": "🖼️pic",
                                 "url": "https://e.com/a.png"}],
              "blocks": [{"type": "paragraph", "text": "x"}]}],
            "image in a summary",
        ),
        (
            "<table><tr><td>до<h3>заголовок</h3>после</td>"
            "<td>до<hr>после</td>"
            "<td>до<tg-math-block>x^2</tg-math-block>после</td>"
            "<td>до<footer>футер</footer>после</td></tr></table>",
            table([
                cell(text="до\nзаголовок\nпосле"),
                cell(text="до\n──────────\nпосле"),
                cell(text="до\nx^2\nпосле"),
                cell(text="до\nфутер\nпосле"),
            ]),
            "heading, divider, formula and footer are lines in a cell",
        ),
        (
            "<table><tr><td><p>абзац 1</p><p>абзац 2</p></td>"
            "<td><div>d1</div><div>d2</div></td>"
            "<td><p></p>y</td></tr></table>",
            table([
                cell(text="абзац 1\nабзац 2"),
                cell(text="d1\nd2"),
                cell(text="y"),
            ]),
            "paragraphs in a cell are lines, an empty one is dropped",
        ),
        (
            "<table><tr><td><details><summary>заголовок</summary>"
            "<p>скрытое</p></details></td></tr></table>",
            table([cell(text=[
                "заголовок\n",
                {"type": "spoiler", "text": "скрытое"},
            ])]),
            "details in a cell: the summary and the body as a spoiler",
        ),
        (
            "<table><tr><td>до<details><summary>з</summary>т1<p>п2</p>"
            "</details>после</td></tr></table>",
            table([cell(text=[
                "до\nз\n",
                {"type": "spoiler", "text": "т1\nп2"},
                "\nпосле",
            ])]),
            "details in a cell keeps the text around",
        ),
        (
            "<table><tr><td><details><summary>только</summary></details>"
            "</td></tr></table>",
            table([cell(text="только")]),
            "details without a body in a cell",
        ),
    ],
)
def test_text_only_parents(html, expected, name):
    assert conv(html) == expected
