from aiogram.types import InputRichMessage
from pydantic import Field

from sulguk.data import RichFormat


class SulgukRichMessage(InputRichMessage):
    """``InputRichMessage`` that sulguk processes before sending.

    A plain ``InputRichMessage`` is passed to Telegram as is.
    ``format`` overrides the default of the middleware (``rich=``),
    it is never sent to Telegram.
    """

    format: RichFormat | None = Field(default=None, exclude=True)
