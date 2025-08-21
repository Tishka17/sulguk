import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import LinkPreviewOptions

from .chat_info import get_chat
from .file import load_file
from .params import EditArgs

logger = logging.getLogger(__name__)


async def edit(bot: Bot, args: EditArgs):
    chat = await get_chat(bot, args.destination.group_id)
    if not args.destination.post_id:
        raise ValueError("No post provided to edit")
    if args.destination.comment_id:
        chat_id = chat.linked_chat_id
        message_id = args.destination.comment_id
    else:
        chat_id = chat.id
        message_id = args.destination.post_id

    data = load_file(args.file, args.base_url)
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=data.text,
            entities=data.entities,
            link_preview_options=LinkPreviewOptions(
                is_disabled=True,
            ),
        )
    except TelegramBadRequest as e:
        if "message is not modified" in e.message:
            logger.debug("Nothing changed")
            return
        raise
