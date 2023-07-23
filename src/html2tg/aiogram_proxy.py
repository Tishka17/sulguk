import logging

from aiogram import Bot
from aiogram.client.session.middlewares.base import (
    BaseRequestMiddleware,
    NextRequestMiddlewareType,
)
from aiogram.methods import TelegramMethod, Response
from aiogram.methods.base import TelegramType

from .wrapper import transform_html

logger = logging.getLogger(__name__)


class Html2TgMiddleware(BaseRequestMiddleware):
    async def __call__(
            self,
            make_request: NextRequestMiddlewareType[TelegramType],
            bot: "Bot",
            method: TelegramMethod[TelegramType],
    ) -> Response[TelegramType]:
        if getattr(method, "parse_mode", "") == "html2tg":
            if hasattr(method, "caption"):
                result = transform_html(method.caption)
                method.caption = result.text
                method.caption_entities = result.entities
            elif hasattr(method, "text"):
                result = transform_html(method.text)
                method.text = result.text
                method.entities = result.entities
            else:
                raise ValueError()
            del method.parse_mode
        return await make_request(bot, method)
