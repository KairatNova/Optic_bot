import logging
import os
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy import func, select

from config import OWNER_IDS
from database.models import Person, Vision
from database.session import AsyncSessionLocal
from keyboards.owner_kb import get_dev_panel_keyboard, get_owner_main_keyboard


dev_panel_router = Router()
START_TIME = time.monotonic()
logger = logging.getLogger(__name__)


def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS


def _resolve_log_file_path() -> Path:
    for handler in logging.getLogger().handlers:
        if isinstance(handler, RotatingFileHandler):
            return Path(handler.baseFilename)
    return Path("logs") / "bot.log"


def _tail_lines(path: Path, limit: int) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return "\n".join(text.splitlines()[-limit:])


@dev_panel_router.message(Command("dev"))
async def cmd_dev_panel(message: Message):
    if not is_owner(message.from_user.id):
        return

    await message.answer(
        "🛠 <b>Панель разработчика</b>\n\nВыберите действие:",
        reply_markup=get_dev_panel_keyboard(),
    )


@dev_panel_router.callback_query(F.data == "owner_dev_panel")
async def open_dev_panel(callback: CallbackQuery):
    if not is_owner(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    await callback.message.answer(
        "🛠 <b>Панель разработчика</b>\n\nВыберите действие:",
        reply_markup=get_dev_panel_keyboard(),
    )
    await callback.answer()


@dev_panel_router.callback_query(F.data == "dev_status")
async def dev_status(callback: CallbackQuery):
    if not is_owner(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    uptime_seconds = int(time.monotonic() - START_TIME)
    h, rem = divmod(uptime_seconds, 3600)
    m, s = divmod(rem, 60)
    log_path = _resolve_log_file_path()

    text = (
        "✅ <b>Статус бота</b>\n"
        f"• PID: <code>{os.getpid()}</code>\n"
        f"• Uptime: <code>{h:02d}:{m:02d}:{s:02d}</code>\n"
        f"• Лог-файл: <code>{log_path}</code>\n"
        f"• Файл существует: <b>{'да' if log_path.exists() else 'нет'}</b>"
    )
    await callback.message.answer(text, reply_markup=get_dev_panel_keyboard())
    await callback.answer()


@dev_panel_router.callback_query(F.data == "dev_db_stats")
async def dev_db_stats(callback: CallbackQuery):
    if not is_owner(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        users_count = await session.scalar(select(func.count(Person.id)))
        visions_count = await session.scalar(select(func.count(Vision.id)))
        owners_count = await session.scalar(select(func.count(Person.id)).where(Person.role == "owner"))
        admins_count = await session.scalar(select(func.count(Person.id)).where(Person.role == "admin"))

    text = (
        "📊 <b>Статистика БД</b>\n"
        f"• Пользователей: <b>{users_count or 0}</b>\n"
        f"• Записей зрения: <b>{visions_count or 0}</b>\n"
        f"• Владельцев: <b>{owners_count or 0}</b>\n"
        f"• Админов: <b>{admins_count or 0}</b>"
    )
    await callback.message.answer(text, reply_markup=get_dev_panel_keyboard())
    await callback.answer()


@dev_panel_router.callback_query(F.data == "dev_health_check")
async def dev_health_check(callback: CallbackQuery):
    if not is_owner(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    log_path = _resolve_log_file_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.touch(exist_ok=True)
    logger.info("DEV_PANEL_HEALTH_CHECK requested by owner_id=%s", callback.from_user.id)

    await callback.message.answer(
        "🧪 Health-check выполнен: записал тестовую строку в лог и проверил доступ к файлу.",
        reply_markup=get_dev_panel_keyboard(),
    )
    await callback.answer("OK")


@dev_panel_router.callback_query(F.data == "dev_get_logs")
async def dev_get_logs(callback: CallbackQuery):
    if not is_owner(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    log_path = _resolve_log_file_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.touch(exist_ok=True)

    tail_text = _tail_lines(log_path, 400)
    if not tail_text.strip():
        await callback.message.answer(
            "Лог-файл пуст. Нажмите «🧪 Health-check», затем попробуйте снова.",
            reply_markup=get_dev_panel_keyboard(),
        )
        await callback.answer()
        return

    file = BufferedInputFile(tail_text.encode("utf-8", errors="ignore"), filename="bot-log-tail.txt")
    await callback.message.answer_document(document=file, caption="📄 Последние 400 строк логов")
    await callback.message.answer("Готово ✅", reply_markup=get_dev_panel_keyboard())
    await callback.answer()


@dev_panel_router.callback_query(F.data == "dev_get_errors")
async def dev_get_errors(callback: CallbackQuery):
    if not is_owner(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    log_path = _resolve_log_file_path()
    if not log_path.exists():
        await callback.message.answer("Лог-файл не найден.", reply_markup=get_dev_panel_keyboard())
        await callback.answer()
        return

    text = log_path.read_text(encoding="utf-8", errors="ignore")
    error_lines = [line for line in text.splitlines() if " ERROR " in line or " CRITICAL " in line]
    if not error_lines:
        await callback.message.answer("Ошибок в логах не найдено ✅", reply_markup=get_dev_panel_keyboard())
        await callback.answer()
        return

    tail_errors = "\n".join(error_lines[-200:])
    file = BufferedInputFile(tail_errors.encode("utf-8", errors="ignore"), filename="bot-log-errors.txt")
    await callback.message.answer_document(document=file, caption="🚨 Последние ERROR/CRITICAL")
    await callback.message.answer("Готово ✅", reply_markup=get_dev_panel_keyboard())
    await callback.answer()


@dev_panel_router.callback_query(F.data == "dev_back")
async def dev_back(callback: CallbackQuery):
    if not is_owner(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    await callback.message.answer(
        "👑 <b>Панель владельца</b>\n\nВыберите нужный раздел:",
        reply_markup=get_owner_main_keyboard(),
    )
    await callback.answer()
