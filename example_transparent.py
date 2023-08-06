import asyncio
import os

from aiogram import Bot

from sulguk import AiogramSulgukMiddleware, SULGUK_PARSE_MODE

CHAT_ID = 1


async def main():
    with open("example.html") as f:
        raw_html = f.read()

    bot = Bot(token=os.getenv("BOT_TOKEN"))
    bot.session.middleware(AiogramSulgukMiddleware())
    await bot.send_message(
        chat_id=CHAT_ID,
        text=raw_html,
        parse_mode=SULGUK_PARSE_MODE,
        disable_web_page_preview=True,
    )


asyncio.run(main())
