import asyncio
import logging
from aiogram import Bot, Dispatcher, types 
from aiogram.client.default import DefaultBotProperties

from aiogram.enums import ParseMode

from config import settings
from database.init_db import init_db


bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()




async def on_startup():
    await init_db()
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


asyncio.run(on_startup())