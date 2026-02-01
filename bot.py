import asyncio
import os
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from database.init_db import init_db
from handlers.start import start_router
from config import BOT_TOKEN

# Настраиваем логирование ПЕРЕД запуском всего остального
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)

async def main():
    # Инициализируем базу данных
    logging.info("Инициализация базы данных...")
    await init_db()

    # Создаем бота и диспетчер
    bot = Bot(
        token=str(BOT_TOKEN), 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Регистрируем роутеры
    dp.include_router(start_router)

    logging.info("Бот запущен!")
    
    # Удаляем вебхуки, если они были, и запускаем опрос
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот выключен пользователем")