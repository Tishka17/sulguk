from logging import getLogger
from typing import Union

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from .exceptions import ChatNotFound

logger = getLogger(__name__)


async def get_chat(bot: Bot, chat_id: Union[str, int]):
    try:
        return await bot.get_chat(chat_id)
    except TelegramBadRequest as e:
        if "chat not found" in e.message:
            logger.error("Chat %s not found", chat_id)
            raise ChatNotFound from e
        raise
