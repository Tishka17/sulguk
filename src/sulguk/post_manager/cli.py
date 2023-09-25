import asyncio
import logging
import os
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, Chat

from sulguk import transform_html, RenderResult
from sulguk.post_manager.links import make_link, unparse_link
from .params import parse_args, EditArgs, SendArgs

logger = logging.getLogger(__name__)


def load_file(filename) -> RenderResult:
    with open(filename) as f:
        return transform_html(f.read())


async def edit(bot: Bot, args: EditArgs):
    chat = await bot.get_chat(args.destination.group_id)
    if not args.destination.post_id:
        raise ValueError("No post provided to edit")
    if args.destination.comment_id:
        chat_id = chat.linked_chat_id
        message_id = args.destination.comment_id
    else:
        chat_id = chat.id
        message_id = args.destination.post_id

    data = load_file(args.file)
    await bot.edit_message_text(
        chat_id=chat_id, message_id=message_id,
        text=data.text, entities=data.entities,
    )


async def get_linked_message_chat(
        bot: Bot, chat: Chat, message: Message,
        pause: float = 1, interval: float = 10, retries: int = 10,
) -> Optional[Message]:
    if not chat.linked_chat_id:
        return None
    await asyncio.sleep(pause)
    for _ in range(retries):
        linked_chat = await bot.get_chat(chat_id=chat.linked_chat_id)
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
    chat = await bot.get_chat(args.destination.group_id)
    data = load_file(args.file[0])
    message = await bot.send_message(
        chat_id=chat.id,
        text=data.text,
        entities=data.entities,
        disable_web_page_preview=True,
    )
    message_link = make_link(chat, message)
    logger.info("Message sent: %s", unparse_link(message_link))
    if len(args.file) < 2:
        return
    linked_message = await get_linked_message[args.mode](bot, chat, message)
    if not linked_message:
        raise ValueError("No linked message found")
    for file in args.file[1:]:
        data = load_file(file)
        comment = await bot.send_message(
            chat_id=chat.linked_chat_id,
            reply_to_message_id=linked_message.message_id,
            text=data.text,
            entities=data.entities,
            disable_web_page_preview=True,
        )
        comment_link = make_link(chat, message, comment)
        logger.info("Comment sent: %s", unparse_link(comment_link))


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    args = parse_args()
    try:
        if args.command == "edit":
            await edit(bot, args)
        else:
            await send(bot, args)
    finally:
        await bot.session.close()


def cli():
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!")


if __name__ == '__main__':
    cli()
