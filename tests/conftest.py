import pytest

from sulguk import transform_html as sulguk_transform
from sulguk2 import transform_html as sulguk2_transform


@pytest.fixture(
    params=[
        pytest.param(sulguk_transform, id="sulguk"),
        pytest.param(sulguk2_transform, id="sulguk2"),
    ],
)
def transform_html(request):
    return request.param
