Sulguk - HTML to telegram entities converter
================================================


[![PyPI version](https://badge.fury.io/py/sulguk.svg)](https://badge.fury.io/py/sulguk)
[![downloads](https://img.shields.io/pypi/dm/sulguk.svg)](https://pypistats.org/packages/sulguk)
[![license](https://img.shields.io/github/license/Tishka17/sulguk.svg)](https://github.com/Tishka17/sulguk/blob/master/LICENSE)


Need to deliver formatted content to your bot clients?
Having a hangover after trying to fit HTML into telegram?
Beautifulsoup is too complicated and not helping with messages?

Try `sulguk` (술국, a hangover
soup) - [delivered since 1800s](https://en.wikipedia.org/wiki/Food_delivery).

## Problem

Telegram supports `parse_mode="html"`, but:

* Telegram processes spaces and new lines incorrectly. So we cannot format HTML source for more readability.
* Amount of supported tags is very low 
* It does not ignore additional attributes in supported tags.

Let's imagine we have HTML like this:

```html
<b>This is a demo of <a href="https://github.com/tishka17/sulguk">Sulguk</a></b>

  <u>Underlined</u>
  <i>Italic</i>
  <b>Bold</b>
```

This is how it is rendered in browser (expected behavior):

![](https://github.com/tishka17/sulguk/blob/master/images/problem_browser.png?raw=True)

But this is how it is rendered in Telegram with `parse_mode="html"`:

![](https://github.com/tishka17/sulguk/blob/master/images/problem_telegram.png?raw=True)

To solve this we can convert HTML to telegram entities with `sulguk`. So that's how it looks now:

![](https://github.com/tishka17/sulguk/blob/master/images/problem_sulguk.png?raw=True)

## Example

1. Create your nice HTML:

```html

<ol start="10">
    <li>some item</li>
    <li>other item</li>
</ol>
<p>Some <b>text</b> in a paragraph</p>
```

2. Convert it into text and entities

```python
result = transform_html(raw_html)
```

3. Send it to telegram.

Depending on your library you may need to convert entities from dict into
proper type

```python
await bot.send_message(
    chat_id=CHAT_ID,
    text=result.text,
    entities=result.entities,
)
```

## Example for aiogram users

1. Add `SulgukMiddleware` to your bot

```python
from sulguk import AiogramSulgukMiddleware

bot.session.middleware(AiogramSulgukMiddleware())
```

2. Create your nice HTML:

```html

<ol start="10">
    <li>some item</li>
    <li>other item</li>
</ol>
<p>Some <b>text</b> in a paragraph</p>
```

3. Send it using `sulguk` as a `parse_mode`:

```python
from sulguk import SULGUK_PARSE_MODE

await bot.send_message(
    chat_id=CHAT_ID,
    text=raw_html,
    parse_mode=SULGUK_PARSE_MODE,
)
```

## Rich messages (Bot API 10.1+)

Telegram can render [rich messages](https://core.telegram.org/bots/api#rich-message-formatting-options):
headings, lists, tables, media, collapsible blocks, footnotes, formulas.
They are sent with `sendRichMessage` and parsed by Telegram itself, so no
entities are produced. `InputRichMessage` holds exactly one of `html`,
`markdown` or `blocks`. What `sulguk` does with each:

| field      | `format="html"`                    | `format="blocks"`                    |
|------------|------------------------------------|--------------------------------------|
| `html`     | normalized to Telegram rich HTML   | converted to `blocks` (`html` unset) |
| `markdown` | passed as is                       | passed as is                         |
| `blocks`   | passed as is                       | passed as is                         |

* `html` normalization collapses whitespace, drops unknown attributes,
  applies `base_url`, maps non-Telegram tags (`div`, `span.tg-spoiler`, `cite`,
  `kbd`, `q`, `progress`, ...) to supported ones and raises an error for
  unknown tags.
* `blocks` conversion builds `InputRichBlock*` structures, so the result does
  not depend on how Telegram parses the HTML. Limits (500 blocks, 16 levels,
  20 table columns, 50 media, 32768 characters) are checked before sending.
  Characters are counted as code points, custom emoji alternative text and
  formulas included, button text is not counted. Besides
  text blocks it supports media (`<img>`, `<video>`, `<audio>`,
  `<tg-document>`; `.gif` video becomes an animation, `.ogg` audio a voice
  note), `<figure>` with `<figcaption>`/`<cite>`, `<tg-collage>`,
  `<tg-slideshow>`, `<tg-map>`, `<aside>`, `<tg-button-row>`, inline
  `<tg-button>` and `<tg-thinking>` (accepted by Telegram only in
  `sendRichMessageDraft`). Media must be a separate block and `src` is an
  HTTP(S) URL or a file_id (`tg://` links work only in the html format).
  A `src` made only of letters, digits, `_` and `-` is taken for a file_id,
  so a relative `src="logo"` is not joined with `base_url`. For the same
  reason `<a href="..."><img ...></a>` is an error: an image cannot be a part
  of a link text, unlike in the html format.
* Both modes agree on empty elements: an empty `<div>` is dropped and splits
  the paragraphs around it, an empty `<ul>` is dropped, an empty `<li>` of
  `<ol>` still takes a number, as in a browser. A list item with only a
  checkbox is kept. `<br>` in `<pre>` is a line break and text after an HTML
  comment is kept.
* A `<footer>` is always preceded by a divider. If there is no `<hr>` right
  before it, one is added, and footers in a row share the first one. Telegram
  does not draw a divider inside of a `<blockquote>`, so there (an `<hr>`
  too) it is a line of `──────────`.
* A table cell holds only a text, and Telegram glues the items of a list in
  it together. So `<ul>` and `<ol>` in `<td>`/`<th>` are written as lines in
  both modes, as the old mode writes lists: `• ` or `1. ` (`start`, `reversed`,
  `type` and `value` are kept), a nested list is indented. A `<blockquote>`
  there cannot be a quotation block either, so it is a separate line that
  starts with `▎ ` (the same goes for `<summary>`, `<caption>` and
  `<figcaption>`). `<pre>` there is plain text with its line breaks kept,
  also on lines of its own, without the monospace font. A media there
  (`<img>`, `<video>`, `<audio>`, `<tg-document>`) cannot be a block, so it is
  an icon (🖼️ 🎞️ 🎵 📎) followed by `alt` or the address of the file, as a link to
  the file. Inside of a link it takes the link text and keeps that link.
  A heading, `<p>`, `<div>`, `<hr>` (a line of `──────────`), `<footer>`,
  `<tg-math-block>` there are lines of their own too, without the formatting
  of a block. `<details>` cannot be folded there: its `<summary>` is a line,
  the rest is under it as a spoiler.

```python
from sulguk import transform_rich_blocks, transform_rich_html

html = transform_rich_html(raw_html, base_url="https://example.com").html
blocks = transform_rich_blocks(raw_html, base_url="https://example.com").blocks
```

With aiogram (3.31+) mark the messages that `sulguk` must process with
`SulgukRichMessage`, like `parse_mode="sulguk"` does for a text:

```python
from aiogram.types import InputRichMessage
from sulguk import AiogramSulgukMiddleware, SulgukRichMessage

bot.session.middleware(AiogramSulgukMiddleware())

# processed, the format is "html" by default
await bot.send_rich_message(
    chat_id=CHAT_ID,
    rich_message=SulgukRichMessage(html=raw_html),
)
# processed with the "blocks" format
await bot.send_rich_message(
    chat_id=CHAT_ID,
    rich_message=SulgukRichMessage(html=raw_html, format="blocks"),
)
# not marked: sent to Telegram as is
await bot.send_rich_message(
    chat_id=CHAT_ID,
    rich_message=InputRichMessage(html=raw_html),
)
```

`SulgukRichMessage` is an `InputRichMessage` with the extra `format` field
(`"html"` or `"blocks"`), it is never sent to Telegram. If `format` is not set,
`AiogramSulgukMiddleware(rich="blocks")` gives the default, otherwise it is
`"html"`.

Marked messages are processed in `sendRichMessage`, `sendRichMessageDraft`,
`editMessageText` (with `rich_message`), `editEphemeralMessageText` and
`InputRichMessageContent` of inline answers. Old aiogram versions keep working;
with `rich` set and an old aiogram an `ImportError` explains that
`aiogram>=3.31` is required.

## Supported tags:

For all supported tags unknown attributes are ignored as well as unknown classes.
Unsupported tags are raising an error. 

#### Standard telegram tags (with some changes):
* `<a>` - a hyperlink with `href` attribute 
* `<b>`, `<strong>` - a bold text
* `<i>`, `<em>` - an italic text
* `<s>`, `<strike>`, `<del>` - a strikethrough text
* `<u>`, `<ins>` - an underlined text
* `<span>` - an inline element with optional attribute `class="tg-spoiler"` to make a spoiler
* `<tg-spoiler>` - a telegram spoiler
* `<pre>` with optional `class="language-<name>"` - a preformatted block with code. `<name>` will be sent as a language attribute in telegram.
* `<code>` - an inline preformatted element. 
* `<details>` - rendered as an expandable blockquote
* `<summary>` - treated as a paragraph, typically used as first child of `<details>` for the heading

**Note:** In standard Telegram HTML you can set a preformatted text language nesting `<code class="language-<name>">` in `<pre>` tag. This works when it is an only child. But any additional symbol outside of `<code>` breaks it.
The same behavior is supported in sulguk. Otherwise, you can set the language on `<pre>` tag itself.

#### Additional tags:
* `<br/>` - new line
* `<hr/>` - horizontal line
* `<wbr/>` - word break opportunity
* `<ul>` - unordered list
* `<ol>` - ordered list with optional attributes
    * `reversed` - to reverse numbers order
    * `type` (`1`/`a`/`A`/`i`/`I`) - to set numbering style
    * `start` - to set starting number
* `<li>` - list item, with optional  `value` attribute to change number. Nested lists have
  indentation
* `<div>` - a block (not inline) element
* `<p>` - a paragraph, emphasized with empty lines
* `<q>` - a quoted text
* `<blockquote>` - a block quote. Like a paragraph with indentation
* `<blockquote expandable>` - a block quote with expandable
* `<h1>`-`<h6>` - text headers, styled using available telegram options
* `<cite>`, `<var>` - italic
* `<progress>`, `<meter>` are rendered using emoji (🟩🟩🟩🟨⬜️⬜️)
* `<kbd>`, `<samp>` - preformatted text
* `<img>` - as a link with picture emoji before. `alt` text is used if provided.
* `<tt>` - as italic text
* `<input>` - as symbols ✅⬜️(checkbox), 🔘⚪️(radio) or `_______`/value in other cases

#### Tags which are treated as block elements (like `<div>`):
`<footer>`, `<header>`, `<main>`, `<nav>`, `<section>`

#### Tags which are treated as inline elements (like `<span>`):
`<html>`, `<body>`, `<output>`, `<data>`, `<time>`

#### Tags which contents is ignored:

`<head>`, `<link>`, `<meta>`, `<noscript>`, `<script>`, `<style>`, `<template>`, `<title>`


## Command line utility for channel management

1. Install with addons
```shell
pip install 'sulguk[cli]'
```

2. Set environment variable `BOT_TOKEN`

```shell
export BOT_TOKEN="your telegram token"
```

3. Send HTML file as a message to your channel. Additional files will be sent as comments to the first one. You can provide a channel name or a public link

```shell
sulguk send @chat_id file.html
```

4. If you want to, edit using the link from shell or from your tg client. Edition of comments is supported as well.

```shell
sulguk edit 'https://t.me/channel/1?comment=42' file.html
```