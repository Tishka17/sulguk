import pytest

from sulguk import transform_rich_blocks

BASE = "https://e.com/"
IMG = '<img src="https://e.com/a.png">'


def conv(html, **kwargs):
    return transform_rich_blocks(html, **kwargs).blocks


def photo(url="https://e.com/a.png", **extra):
    return {"type": "photo", "photo": {"type": "photo", "media": url, **extra}}


@pytest.mark.parametrize(
    "html, kind, name",
    [
        ('<img src="https://e.com/a.png">', "photo", "img"),
        ('<video src="https://e.com/v.mp4"></video>', "video", "video"),
        ('<video src="https://e.com/a.gif"></video>', "animation", "gif"),
        ('<audio src="https://e.com/a.mp3"></audio>', "audio", "audio"),
        ('<audio src="https://e.com/a.ogg"></audio>', "voice_note", "ogg"),
        (
            '<tg-document src="https://e.com/d.zip"></tg-document>',
            "document",
            "document",
        ),
    ],
)
def test_media_kinds(html, kind, name):
    block = conv(html)[0]
    assert block["type"] == kind
    assert block[kind]["type"] == kind


@pytest.mark.parametrize(
    "html, expected, name",
    [
        ('<img src="/a.png">', photo(), "base url"),
        ('<img src="AgACAgIAAxkB-_x">', photo("AgACAgIAAxkB-_x"), "file id"),
        (
            '<img src="https://e.com/a.png" tg-spoiler>',
            photo(has_spoiler=True),
            "spoiler",
        ),
    ],
)
def test_photo(html, expected, name):
    assert conv(html, base_url=BASE) == [expected]


def test_spoiler_ignored_for_audio():
    out = conv('<audio src="https://e.com/a.mp3" tg-spoiler></audio>')
    assert "has_spoiler" not in out[0]["audio"]


def test_extension_is_taken_from_the_path_only():
    out = conv('<video src="https://e.com/v.mp4?name=a.gif"></video>')
    assert out[0]["type"] == "video"


def test_extension_is_case_insensitive():
    out = conv('<video src="https://e.com/A.GIF"></video>')
    assert out[0]["type"] == "animation"


def test_figure_caption_and_credit():
    out = conv(
        f"<figure>{IMG}<figcaption>Cap<cite>Who</cite></figcaption></figure>",
    )
    assert out[0]["caption"] == {"text": "Cap", "credit": "Who"}


def test_figure_without_caption():
    assert conv(f"<figure>{IMG}</figure>") == [photo()]


def test_figure_with_empty_caption():
    assert conv(f"<figure>{IMG}<figcaption> </figcaption></figure>") == [
        photo(),
    ]


def test_map_in_figure():
    assert conv(
        '<figure><tg-map lat="1.5" long="2" zoom="3"/>'
        "<figcaption>m</figcaption></figure>",
    ) == [
        {
            "type": "map",
            "location": {"latitude": 1.5, "longitude": 2.0},
            "zoom": 3,
            "caption": {"text": "m"},
        }
    ]


def test_map_size():
    out = conv('<tg-map lat="1" long="2" width="300" height="200"/>')
    assert out[0]["width"] == 300
    assert out[0]["height"] == 200


@pytest.mark.parametrize(
    ("tag", "inner_kinds"),
    [("tg-collage", ["photo", "video"]), ("tg-slideshow", ["photo", "video"])],
)
def test_galleries(tag, inner_kinds):
    out = conv(
        f'<{tag}>{IMG}<video src="https://e.com/v.mp4"></video>'
        f"<figcaption>c</figcaption></{tag}>",
    )[0]
    assert out["type"] == tag.removeprefix("tg-")
    assert [b["type"] for b in out["blocks"]] == inner_kinds
    assert out["caption"] == {"text": "c"}


def test_gallery_urls_are_made_absolute():
    out = conv('<tg-collage><img src="/a.png"></tg-collage>', base_url=BASE)
    assert out[0]["blocks"] == [photo()]
