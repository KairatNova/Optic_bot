# Новый файл: routers/owner_export_router.py
# Подключите в main.py: dp.include_router(owner_export_router)

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from sqlalchemy import select

from database.models import Person, Vision
from database.session import AsyncSessionLocal
from config import OWNER_IDS
from forms.forms_fsm import OwnerExportStates, OwnerMainStates  
from keyboards.owner_kb import get_export_submenu_keyboard, get_owner_main_keyboard
import pandas as pd
from io import BytesIO

owner_export_router = Router()

def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS




# Вход в раздел выгрузки (из owner_main_router: добавьте elif action == "owner_exports")
# await bot.send_message(callback.from_user.id, "📊 <b>Выгрузки данных</b>\n\nВыберите тип выгрузки:", reply_markup=get_export_submenu_keyboard())
# await state.set_state(OwnerExportStates.export_menu)

@owner_export_router.callback_query(OwnerExportStates.export_menu, F.data.startswith("export_"))
async def export_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not is_owner(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    action = callback.data

    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    if action == "export_all_clients":
        await bot.send_message(callback.from_user.id, "📊 Генерирую Excel с клиентами...")

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Person))
            persons = result.scalars().all()

        # Создаём DataFrame
        data = {
            'ID': [p.id for p in persons],
            'ФИО': [p.full_name or '—' for p in persons],
            'Имя': [p.first_name or '—' for p in persons],
            'Фамилия': [p.last_name or '—' for p in persons],
            'Возраст': [p.age or '—' for p in persons],
            'Телефон': [p.phone or '—' for p in persons],
            'Telegram ID': [p.telegram_id or '—' for p in persons],
            'Роль': [p.role for p in persons],
            'Дата регистрации': [p.created_at.date() if p.created_at else '—' for p in persons],
            'Последний визит': [p.last_visit_date or '—' for p in persons],
        }

        df = pd.DataFrame(data)

        # Генерируем Excel в памяти
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)

        # Отправляем файл
        await bot.send_document(
            callback.from_user.id,
            FSInputFile(excel_buffer, filename="clients.xlsx"),
            caption="✅ Выгрузка всех клиентов в Excel готова!"
        )

        # Возврат в подменю
        await bot.send_message(
            callback.from_user.id,
            "📊 <b>Выгрузки данных</b>\n\nВыберите тип выгрузки:",
            reply_markup=get_export_submenu_keyboard()
        )

    elif action == "export_all_visions":
        await bot.send_message(callback.from_user.id, "📊 Генерирую Excel с записями зрения...")

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Vision).join(Person))
            visions = result.scalars().all()

        data = {
            'Client ID': [v.person_id for v in visions],
            'ФИО клиента': [v.person.full_name or '—' for v in visions],
            'Дата визита': [v.visit_date for v in visions],
            'SPH R': [v.sph_r or '—' for v in visions],
            'CYL R': [v.cyl_r or '—' for v in visions],
            'AXIS R': [v.axis_r or '—' for v in visions],
            'SPH L': [v.sph_l or '—' for v in visions],
            'CYL L': [v.cyl_l or '—' for v in visions],
            'AXIS L': [v.axis_l or '—' for v in visions],
            'PD': [v.pd or '—' for v in visions],
            'Тип линз': [v.lens_type or '—' for v in visions],
            'Модель оправы': [v.frame_model or '—' for v in visions],
            'Примечание': [v.note or '—' for v in visions],
        }

        df = pd.DataFrame(data)

        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)

        await bot.send_document(
            callback.from_user.id,
            FSInputFile(excel_buffer, filename="visions.xlsx"),
            caption="✅ Выгрузка всех записей зрения в Excel готова!"
        )

        await bot.send_message(
            callback.from_user.id,
            "📊 <b>Выгрузки данных</b>\n\nВыберите тип выгрузки:",
            reply_markup=get_export_submenu_keyboard()
        )

    elif action == "export_back":
        await state.set_state(OwnerMainStates.main_menu)
        await bot.send_message(
            callback.from_user.id,
            "👑 <b>Панель владельца</b>\n\nВыберите раздел:",
            reply_markup=get_owner_main_keyboard()
        )

    await callback.answer()