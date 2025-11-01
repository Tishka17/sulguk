from pathlib import Path

import html5lib
import pytest

from sulguk import transform_html as sulguk_transform
from sulguk2 import transform_html as sulguk2_transform_html


def create_well_formed_html(malformed_html: str):
    doc = html5lib.parse(malformed_html, treebuilder="etree")
    result = html5lib.serialize(
        doc,
        tree="etree",
        quote_attr_values="always",
        omit_optional_tags=False,
    )
    return result


@pytest.mark.parametrize(
    ("html_file, is_malformed"),
    (
        ("basic.html", False),
        ("tags.html", False),
        ("hello_world.html", True),
        ("comprehensive.html", True),
    ),
)
def test_sulguks_equivalence(html_file, is_malformed):
    test_html_path = Path(__file__).parent / html_file
    content = test_html_path.read_text()

    if is_malformed:
        well_formed_content = create_well_formed_html(content)
    else:
        well_formed_content = content

    sulguk_res = sulguk_transform(well_formed_content)
    sulguk2_res = sulguk2_transform_html(content)

    assert sulguk_res == sulguk2_res
