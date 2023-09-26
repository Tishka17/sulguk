import pytest

from sulguk.post_manager.links import Link, parse_link


@pytest.mark.parametrize(
    "src, result", [
        ("https://t.me/mock_channel_17", Link("@mock_channel_17")),
        ("@mock_channel_17", Link("@mock_channel_17")),
        ("123", Link(123)),
        (
                "https://t.me/mock_channel_17/52?comment=2754",
                Link("@mock_channel_17", 52, 2754),
        ),
        (
                "https://t.me/mock_channel_17/52",
                Link("@mock_channel_17", 52, None),
        ),
    ]
)
def test_links(src, result):
    assert result == parse_link(src)
