import asyncio
import logging
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.types import Chat, LinkPreviewOptions, Message

from .chat_info import get_chat
from .exceptions import LinkedMessageNotFoundError
from .file import load_file
from .links import make_link, unparse_link
from .params import SendArgs

logger = logging.getLogger(__name__)


async def get_linked_message_chat(
        bot: Bot, chat: Chat, message: Message,
        pause: float = 1, interval: float = 10, retries: int = 10,
) -> Optional[Message]:
    if not chat.linked_chat_id:
        return None
    await asyncio.sleep(pause)
    for _ in range(retries):
        linked_chat = await get_chat(bot, chat_id=chat.linked_chat_id)
        pinned_message = linked_chat.pinned_message
        if not pinned_message:
            logger.info("No pinned message, retrying")
        elif pinned_message.forward_from_message_id != message.message_id:
            logger.info("Pinned message is not the one we wait for, retrying")
        else:
            return linked_chat.pinned_message
        await asyncio.sleep(interval)
    return None


class EventListener:
    def __init__(self):
        self.message = None

    async def on_message(self, message: Message, dispatcher: Dispatcher):
        self.message = message
        await dispatcher.stop_polling()


async def get_linked_message_polling(
        bot: Bot, chat: Chat, message: Message,
) -> Optional[Message]:
    if not chat.linked_chat_id:
        return
    dp = Dispatcher()
    listener = EventListener()
    dp.message(
        F.chat.id == chat.linked_chat_id,
        F.forward_from_message_id == message.message_id,
    )(listener.on_message)
    await asyncio.wait_for(dp.start_polling(bot), timeout=10)
    return listener.message


get_linked_message = {
    "poll": get_linked_message_polling,
    "getChat": get_linked_message_chat,
}


async def send(bot: Bot, args: SendArgs):
    chat = await get_chat(bot, args.destination.group_id)
    data = load_file(args.file[0], args.base_url)
    message = await bot.send_message(
        chat_id=chat.id,
        text=data.text,
        entities=data.entities,
        link_preview_options=LinkPreviewOptions(
            is_disabled=True,
        ),
    )
    message_link = make_link(chat, message)
    logger.info("Message sent: %s", unparse_link(message_link))
    if len(args.file) < 2:
        return
    linked_message = await get_linked_message[args.mode](bot, chat, message)
    if not linked_message:
        logger.error("Cannot load linked message to leave a comment")
        raise LinkedMessageNotFoundError("No linked message found")
    for file in args.file[1:]:
        data = load_file(file, args.base_url)
        comment = await bot.send_message(
            chat_id=chat.linked_chat_id,
            reply_to_message_id=linked_message.message_id,
            text=data.text,
            entities=data.entities,
            link_preview_options=LinkPreviewOptions(
                is_disabled=True,
            ),
        )
        comment_link = make_link(chat, message, comment)
        logger.info("Comment sent: %s", unparse_link(comment_link))
