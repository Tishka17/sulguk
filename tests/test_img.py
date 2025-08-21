import pytest

from sulguk import transform_html

IMG_HTML_NOCLOSE = '0<img src="https://google.com">1'
IMG_HTML_CLOSE = '0<img src="https://google.com" />1'
IMG_HTML_ALT = '0<img src="https://google.com" alt="This is text" />1'
IMG_HTML_EMPTY_ALT = '0<img src="https://google.com" alt="" />1'
IMG_URL = "https://google.com"
IMG_TEXT_URL = "0🖼️https://google.com1"
IMG_TEXT_ALT = "0🖼️This is text1"
IMG_TEXT_EMPTY_ALT = "0🖼️1"


@pytest.mark.parametrize("html, url, text", [
    (IMG_HTML_NOCLOSE, IMG_URL, IMG_TEXT_URL),
    (IMG_HTML_CLOSE, IMG_URL, IMG_TEXT_URL),
    (IMG_HTML_ALT, IMG_URL, IMG_TEXT_ALT),
    (IMG_HTML_EMPTY_ALT, IMG_URL, IMG_TEXT_EMPTY_ALT),
])
def test_link_extracted(html, url, text):
    result = transform_html(html)
    assert result.text == text
    assert len(result.entities) == 1
    entity = result.entities[0]
    assert entity['type'] == 'text_link'
    assert entity['url'] == url


def test_empty_image():
    html = '0<img src="">1'
    result = transform_html(html)
    assert result.text == "01"
    assert not result.entities


def test_base_url():
    html = '<img src="data"><img src="/data"><img src="https://example.com">'
    result = transform_html(html, base_url="http://example.com/root/")
    assert len(result.entities) == 3
    assert result.entities[0]['url'] == "http://example.com/root/data"
    assert result.entities[1]['url'] == "http://example.com/data"
    assert result.entities[2]['url'] == "https://example.com"
