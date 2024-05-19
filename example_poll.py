import asyncio
import os

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from sulguk import SULGUK_PARSE_MODE, AiogramSulgukMiddleware

CHAT_ID = 1


async def main():
    bot = Bot(
        token=os.getenv("BOT_TOKEN"),
        default=DefaultBotProperties(parse_mode=SULGUK_PARSE_MODE),
    )
    bot.session.middleware(AiogramSulgukMiddleware())

    await bot.send_poll(
        CHAT_ID,
        question="Do you like Python?",
        options=[
            "Yes!",
            "No",
            "Probably...",
        ],
        explanation="<b>You</b> <i>like it</i>.",
        correct_option_id=0,
        type="quiz",
    )

    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
