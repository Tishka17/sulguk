from pathlib import Path

from sulguk import transform_html

FIXTURES = Path("tests/fixtures")


def test_all_supported_tags_parse():
    html = (FIXTURES / "supported_tags.html").read_text()
    transform_html(html)
