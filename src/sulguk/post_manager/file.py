import logging

from sulguk import transform_html, RenderResult
from .exceptions import ManagerError

logger = logging.getLogger(__name__)


def load_file(filename) -> RenderResult:
    try:
        with open(filename) as f:
            return transform_html(f.read())
    except FileNotFoundError:
        logger.error("File `%s` not found", filename)
        raise ManagerError
