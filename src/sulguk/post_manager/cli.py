import asyncio
import logging
import os

from aiogram import Bot

from .editor import edit
from .exceptions import ManagerError
from .params import parse_args
from .sender import send


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    args = parse_args()
    try:
        if args.command == "edit":
            await edit(bot, args)
        else:
            await send(bot, args)
    except ManagerError:
        logging.error("There were errors during execution. See above")
    finally:
        await bot.session.close()


def cli():
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == '__main__':
    cli()
