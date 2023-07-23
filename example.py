import asyncio
import os

from aiogram import Bot
from html2tg import transform_html

CHAT_ID = 1


async def main():
    with open("example.html") as f:
        raw_html = f.read()
    result = transform_html(raw_html)
    print("Text:")
    print(result.text)
    for entity in result.entities:
        print(repr(entity))
    print()

    bot = Bot(token=os.getenv("BOT_TOKEN"))
    await bot.send_message(
        chat_id=CHAT_ID,
        text=raw_html,
    )
    await bot.send_message(
        chat_id=CHAT_ID,
        text=result.text,
        entities=result.entities,
    )


asyncio.run(main())
