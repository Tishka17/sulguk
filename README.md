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
* `<noscirpt>` - contents is shown as not scripting is supported
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

`<head>`, `<link>`, `<meta>`, `<script>`, `<style>`, `<template>`, `<title>`


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