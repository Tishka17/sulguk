import pytest

from sulguk import transform_rich_blocks

BASE = "https://e.com/"


def attrs_html(attrs):
    return " ".join(
        f'{key}="{value}"' if value else key for key, value in attrs.items()
    )


def button(attrs, text="b"):
    """Button of ``<tg-button>`` with the attributes, in a paragraph."""
    html = f"<p><tg-button {attrs_html(attrs)}>{text}</tg-button></p>"
    blocks = transform_rich_blocks(html, base_url=BASE).blocks
    return blocks[0]["text"]["button"]


def test_text_is_kept():
    result = transform_rich_blocks(
        '<p><tg-button type="disabled">a<b>b</b></tg-button></p>',
    ).blocks
    assert result[0]["text"]["button"] == {
        "text": ["a", {"type": "bold", "text": "b"}],
        "disabled": {},
    }


def test_style():
    assert button({"type": "disabled", "style": "success"}) == {
        "text": "b",
        "style": "success",
        "disabled": {},
    }


@pytest.mark.parametrize("attrs, expected, name", [
    (
        {"type": "url", "url": "/x"},
        {"url": "https://e.com/x"},
        "url",
    ),
    (
        {"type": "callback_data", "data": "cb"},
        {"callback_data": "cb"},
        "callback data",
    ),
    (
        {"type": "web_app", "url": "/app"},
        {"web_app": {"url": "https://e.com/app"}},
        "web app",
    ),
    (
        {
            "type": "login_url",
            "url": "/login",
            "forward-text": "f",
            "bot-username": "bot",
            "request-write-access": "",
        },
        {
            "login_url": {
                "url": "https://e.com/login",
                "forward_text": "f",
                "bot_username": "bot",
                "request_write_access": True,
            },
        },
        "login url",
    ),
    (
        {"type": "login_url", "url": "https://e.com"},
        {"login_url": {"url": "https://e.com"}},
        "login url minimal",
    ),
    (
        {"type": "switch_inline_query", "query": "q"},
        {"switch_inline_query": "q"},
        "switch inline",
    ),
    (
        {"type": "switch_inline_query_current_chat", "query": "q"},
        {"switch_inline_query_current_chat": "q"},
        "switch current",
    ),
    (
        {
            "type": "switch_inline_query_chosen_chat",
            "query": "q",
            "allow-user-chats": "",
            "allow-channel-chats": "",
        },
        {
            "switch_inline_query_chosen_chat": {
                "query": "q",
                "allow_user_chats": True,
                "allow_channel_chats": True,
            },
        },
        "chosen chat",
    ),
    (
        {"type": "switch_inline_query_chosen_chat"},
        {"switch_inline_query_chosen_chat": {"query": ""}},
        "chosen chat empty query",
    ),
    (
        {"type": "copy_text", "text": "t"},
        {"copy_text": {"text": "t"}},
        "copy text",
    ),
    ({"type": "disabled"}, {"disabled": {}}, "disabled"),
])
def test_action(attrs, expected, name):
    assert button(attrs) == {"text": "b", **expected}


@pytest.mark.parametrize("attrs, message, name", [
    ({}, "Unknown <tg-button> type", "no type"),
    ({"type": "x"}, "Unknown <tg-button> type", "type"),
    (
        {"type": "disabled", "style": "x"},
        "Unknown button style",
        "style",
    ),
])
def test_errors(attrs, message, name):
    with pytest.raises(ValueError, match=message):
        button(attrs)
