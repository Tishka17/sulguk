import logging

from sulguk import RenderResult, transform_html
from .exceptions import ManagerError

logger = logging.getLogger(__name__)


def load_file(filename, base_url: str | None) -> RenderResult:
    try:
        with open(filename) as f:
            return transform_html(f.read(), base_url=base_url)
    except FileNotFoundError as e:
        logger.error("File `%s` not found", filename)
        raise ManagerError from e
