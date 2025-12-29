from sulguk import transform_html
from sulguk.data import MessageEntity

PRE_HTML = "<pre>code</pre>"
PRE_PLAIN = "code\n\n"
PRE_ENTITIES = [
    MessageEntity(type="pre", offset=0, length=5),
]

PRE_LANG_HTML = '<pre class="language-python">code</pre>'
PRE_LANG_ENTITIES = [
    MessageEntity(type="pre", offset=0, length=5, language="python"),
]


def test_pre_without_language():
    result = transform_html(PRE_HTML)
    assert result.text == PRE_PLAIN, (
        f"Expected text {PRE_PLAIN!r}, but got {result.text!r}"
    )
    assert result.entities == PRE_ENTITIES, (
        f"Expected entities {PRE_ENTITIES}, but got {result.entities}"
    )


def test_pre_with_language():
    result = transform_html(PRE_LANG_HTML)
    assert result.entities == PRE_LANG_ENTITIES, (
        f"Expected entities {PRE_LANG_ENTITIES}, but got {result.entities}"
    )
