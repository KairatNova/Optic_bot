import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from database.init_db import init_db

# Импорты роутеров (группируем по типу)
from handlers.start import start_router
from handlers.client import client_router

from handlers.owner.owner_main import owner_main_router
from handlers.owner.client_button import owner_content_router
from handlers.owner.admins_router import owner_admins_router
from handlers.owner.broadcast_router import owner_broadcast_router
from handlers.owner.crud.clients_router import owner_clients_router
from handlers.owner.crud.vision_router import owner_vision_router
from handlers.owner.crud.edit_and_delete import owner_vision_edit_router
from handlers.owner.export_router import owner_export_router

from handlers.admin.admin_main import admin_main_router
from handlers.admin.admin_clients_router import admin_clients_router
from handlers.admin.admin_broadcast_router import admin_broadcast_router
from handlers.admin.admin_vision_edit_router import admin_vision_edit_router
from handlers.admin.admin_vision_router import admin_vision_router






from middlewares.anti_spam import RateLimitMiddleware
from middlewares.private import PrivateChatOnlyMiddleware



from keyboards.client_kb import set_commands
from middlewares.private import PrivateChatOnlyMiddleware
from services.content import get_bot_content, init_bot_content
from config import BOT_TOKEN, OWNER_IDS

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Запуск бота...")

    # 1. Инициализация базы данных
    try:
        logger.info("Инициализация базы данных...")
        await init_db()
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}", exc_info=True)
        return

    # 2. Создание бота
    bot = Bot(
        token=str(BOT_TOKEN),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # 3. Создание диспетчера
    dp = Dispatcher()



    # 4. Установка команд бота
    try:
        await set_commands(bot)
        logger.info("Команды бота установлены")
    except Exception as e:
        logger.warning(f"Не удалось установить команды: {e}")

    # 5. Инициализация контента
    try:
        await init_bot_content()
        await get_bot_content(force_refresh=True)
        logger.info("Контент бота загружен в кэш")
    except Exception as e:
        logger.error(f"Ошибка инициализации контента: {e}", exc_info=True)

    
    # Антиспам: ограничение частоты сообщений и нажатий кнопок
    spam_guard = RateLimitMiddleware(
        interval_seconds=1.0,
        warning_cooldown_seconds=5.0,
        warnings_before_mute=3,
        warning_window_seconds=60.0,
        mute_durations_seconds=[300, 1800, 3600, 10800],
        exempt_user_ids=OWNER_IDS,
    )
    dp.message.middleware(spam_guard)
    dp.callback_query.middleware(spam_guard)

    dp.update.middleware(PrivateChatOnlyMiddleware())
    # 6. Подключение роутеров (ВАЖНО: порядок!)
    # Сначала общие
    dp.include_router(start_router)
    dp.include_router(client_router)

    # Потом владелец
    dp.include_router(owner_main_router)
    dp.include_router(owner_content_router)
    dp.include_router(owner_admins_router)
    dp.include_router(owner_broadcast_router)
    dp.include_router(owner_clients_router)
    dp.include_router(owner_vision_router)
    dp.include_router(owner_vision_edit_router)
    dp.include_router(owner_export_router)

    # Потом админы
    dp.include_router(admin_main_router)
    dp.include_router(admin_broadcast_router)
    dp.include_router(admin_clients_router)
    dp.include_router(admin_vision_edit_router)
    dp.include_router(admin_vision_router)





    # 7. Запуск поллинга
    try:
        logger.info("Бот запущен! Ожидание обновлений...")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    except Exception as e:
        logger.error(f"Ошибка поллинга: {e}", exc_info=True)
    finally:
        await bot.session.close()
        logger.info("Бот остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске: {e}", exc_info=True)