import asyncio
from types import SimpleNamespace

import pytest

pytest.importorskip("aiogram")

import aiogram.methods
from aiogram.methods import (
    AnswerInlineQuery,
    EditMessageText,
    SendMessage,
    SendRichMessage,
)
from aiogram.types import (
    InlineQueryResultArticle,
    InputRichMessage,
    InputRichMessageContent,
)

from sulguk import (
    AiogramSulgukMiddleware,
    SULGUK_PARSE_MODE,
    SulgukRichMessage,
)

BASE = "https://e.com/"
MARKDOWN = InputRichMessage(markdown="# <div>x")
BLOCKS = InputRichMessage(blocks=[{"type": "divider"}])


def process(method, **kwargs):
    async def make_request(bot, method):
        return method

    middleware = AiogramSulgukMiddleware(base_url=BASE, **kwargs)
    # the middleware reads only bot.default.parse_mode
    bot = SimpleNamespace(default=SimpleNamespace(parse_mode=None))
    asyncio.run(middleware(make_request, bot, method))
    return method


def send(rich_message):
    return SendRichMessage(chat_id=1, rich_message=rich_message)


def edit(rich_message):
    return EditMessageText(chat_id=1, message_id=2, rich_message=rich_message)


def inline(rich_message):
    content = InputRichMessageContent(rich_message=rich_message)
    article = InlineQueryResultArticle(
        id="1", title="t", input_message_content=content,
    )
    return AnswerInlineQuery(inline_query_id="1", results=[article])


def rich_message_of(method):
    if isinstance(method, AnswerInlineQuery):
        return method.results[0].input_message_content.rich_message
    return method.rich_message


@pytest.mark.parametrize(
    ("rich", "source", "expected"),
    [
        pytest.param(
            None,
            SulgukRichMessage(html="<div>a</div>"),
            InputRichMessage(html="<p>a</p>"),
            id="default-is-html",
        ),
        pytest.param(
            "html",
            SulgukRichMessage(
                html='<div class="x"><a href="/a">l</a>\n\n  <b>b</b></div>',
            ),
            InputRichMessage(
                html='<p><a href="https://e.com/a">l</a> <b>b</b></p>',
            ),
            id="html",
        ),
        pytest.param(
            "blocks",
            SulgukRichMessage(html="<h2>T</h2><p>a</p>"),
            InputRichMessage(
                blocks=[
                    {"type": "heading", "text": "T", "size": 2},
                    {"type": "paragraph", "text": "a"},
                ],
            ),
            id="blocks",
        ),
        pytest.param(
            "html",
            SulgukRichMessage(html="<h2>T</h2>", format="blocks"),
            InputRichMessage(
                blocks=[{"type": "heading", "text": "T", "size": 2}],
            ),
            id="message-format-wins",
        ),
    ],
)
def test_html_field(rich, source, expected):
    method = process(send(source), rich=rich)
    assert method.rich_message == expected
    # a plain model without the sulguk-only field goes to Telegram
    assert type(method.rich_message) is InputRichMessage
    assert "format" not in method.rich_message.model_dump()


@pytest.mark.parametrize("rich", [None, "html", "blocks"])
def test_plain_rich_message_is_untouched(rich):
    source = InputRichMessage(html="<div>a</div>")

    assert process(send(source), rich=rich).rich_message == source


@pytest.mark.parametrize("rich", [None, "html", "blocks"])
@pytest.mark.parametrize("rich_message", [MARKDOWN, BLOCKS])
def test_other_fields_are_untouched(rich, rich_message):
    marked = SulgukRichMessage(**rich_message.model_dump())

    assert process(send(marked), rich=rich).rich_message == rich_message


def test_format_is_not_sent():
    message = SulgukRichMessage(html="<p>a</p>", format="blocks")

    assert "format" not in message.model_dump()


@pytest.mark.parametrize("build", [send, edit, inline])
def test_rich_message_is_processed_in_every_method(build):
    method = process(build(SulgukRichMessage(html="<div>a</div>")), rich="html")

    assert rich_message_of(method).html == "<p>a</p>"


@pytest.mark.parametrize("build", [send, edit, inline])
def test_plain_rich_message_is_untouched_in_every_method(build):
    source = InputRichMessage(html="<div>a</div>")

    method = process(build(source), rich="html")

    assert rich_message_of(method) == source


def test_plain_message_still_uses_entities():
    method = SendMessage(chat_id=1, text="<b>x</b>", parse_mode="sulguk")

    process(method, rich="html")

    assert method.text == "x"
    assert method.entities[0]["type"] == "bold"


@pytest.mark.parametrize("rich", ["xml", True])
def test_unknown_rich_format(rich):
    with pytest.raises(ValueError, match="Unknown rich format"):
        AiogramSulgukMiddleware(rich=rich)


@pytest.mark.parametrize("rich", ["html", "blocks"])
def test_rich_requires_new_aiogram(monkeypatch, rich):
    monkeypatch.delattr(aiogram.methods, "SendRichMessage")

    with pytest.raises(ImportError, match="aiogram>=3.31"):
        AiogramSulgukMiddleware(rich=rich)


def process_sulguk_default(method, **kwargs):
    """Bot with ``parse_mode=sulguk`` by default, as in real projects."""
    async def make_request(bot, method):
        return method

    middleware = AiogramSulgukMiddleware(base_url=BASE, **kwargs)
    bot = SimpleNamespace(
        default=SimpleNamespace(parse_mode=SULGUK_PARSE_MODE),
    )
    asyncio.run(middleware(make_request, bot, method))
    return method


@pytest.mark.parametrize("rich", [None, "html", "blocks"])
def test_edit_rich_message_keeps_no_text_and_parse_mode(rich):
    method = process_sulguk_default(
        edit(InputRichMessage(html="<p>hi</p>")), rich=rich,
    )

    assert method.text is None
    assert method.entities is None
    assert method.parse_mode is None


def test_edit_rich_message_untouched_without_marker():
    source = InputRichMessage(html="<div>a</div>")

    method = process_sulguk_default(edit(source), rich=None)

    assert method.rich_message == source


def test_edit_text_still_uses_entities():
    method = EditMessageText(
        chat_id=1, message_id=2, text="<b>x</b>",
    )

    process_sulguk_default(method, rich="html")

    assert method.text == "x"
    assert method.entities[0]["type"] == "bold"
    assert method.parse_mode is None
