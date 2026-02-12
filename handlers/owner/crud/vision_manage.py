from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from sqlalchemy import select

from database.models import Vision, Person
from database.session import AsyncSessionLocal
from config import OWNER_IDS
from forms.forms_fsm import OwnerVisionStates, OwnerClientsStates
from datetime import date
from handlers.owner.crud.clients_router import show_client_profile

vision_manage_router = Router()

def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS
# Просмотр всех записей зрения
@vision_manage_router.callback_query(F.data.startswith("view_all_visions_"))
async def view_all_visions(callback: CallbackQuery, state: FSMContext, bot: Bot):
    person_id = int(callback.data.split("_")[3])

    if not is_owner(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Vision.id)
            .where(Vision.person_id == person_id)
            .order_by(Vision.visit_date.desc())
        )
        vision_ids = [row[0] for row in result.all()]

    if not vision_ids:
        await bot.send_message(
            callback.from_user.id,
            "У клиента нет записей зрения.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀ Назад в профиль", callback_data=f"back_to_profile_{person_id}")]
            ])
        )
        await callback.answer()
        return

    # Сохраняем данные для навигации
    await state.update_data(
        person_id=person_id,
        vision_ids=vision_ids,
        current_index=0  # начинаем с самой новой записи
    )

    await show_vision_detail(callback.from_user.id, state, bot)
    await state.set_state(OwnerVisionStates.viewing_visions)
    await callback.answer()

# Показ одной записи
async def show_vision_detail(chat_id: int, state: FSMContext, bot: Bot):
    data = await state.get_data()
    current_index = data.get("current_index", 0)
    vision_ids = data.get("vision_ids", [])

    if not vision_ids or current_index >= len(vision_ids):
        await bot.send_message(chat_id, "Нет записей зрения.")
        return

    async with AsyncSessionLocal() as session:
        vision = await session.get(Vision, vision_ids[current_index])

    if not vision:
        await bot.send_message(chat_id, "Запись не найдена.")
        return

    text = f"<b>Запись зрения</b> ({current_index + 1} из {len(vision_ids)})\n\n"
    text += f"Дата: {vision.visit_date}\n"
    text += f"Правая: SPH {vision.sph_r or '—'} | CYL {vision.cyl_r or '—'} | AXIS {vision.axis_r or '—'}\n"
    text += f"Левая: SPH {vision.sph_l or '—'} | CYL {vision.cyl_l or '—'} | AXIS {vision.axis_l or '—'}\n"
    text += f"PD: {vision.pd or '—'}\n"
    text += f"Тип линз: {vision.lens_type or '—'}\n"
    text += f"Модель оправы: {vision.frame_model or '—'}\n"
    if vision.note:
        text += f"Примечание: {vision.note}\n"

    kb = [
        [
            InlineKeyboardButton(text="◀ Предыдущая", callback_data="vision_prev"),
            InlineKeyboardButton(text="Следующая ▶", callback_data="vision_next")
        ],
        [InlineKeyboardButton(text="✏ Редактировать эту запись", callback_data=f"edit_vision_{vision.id}")],
        [InlineKeyboardButton(text="🗑 Удалить эту запись", callback_data=f"delete_vision_{vision.id}")],
        [InlineKeyboardButton(text="◀ Назад в профиль", callback_data=f"back_to_profile_{data['person_id']}")],
    ]

    await bot.send_message(chat_id, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# Переключение между записями
@vision_manage_router.callback_query(OwnerVisionStates.viewing_visions, F.data.in_(["vision_prev", "vision_next"]))
async def switch_vision(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    current_index = data.get("current_index", 0)
    vision_ids = data.get("vision_ids", [])

    if callback.data == "vision_prev":
        current_index = max(0, current_index - 1)
    else:
        current_index = min(len(vision_ids) - 1, current_index + 1)

    await state.update_data(current_index=current_index)

    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    await show_vision_detail(callback.from_user.id, state, bot)
    await callback.answer()

# Возврат в профиль (уже должен быть, но на всякий случай)
@vision_manage_router.callback_query(F.data.startswith("back_to_profile_"))
async def back_to_profile(callback: CallbackQuery, state: FSMContext, bot: Bot):
    person_id = int(callback.data.split("_")[3])

    if not is_owner(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    async with AsyncSessionLocal() as session:
        person = await session.get(Person, person_id)
        if not person:
            await callback.answer("Клиент не найден.", show_alert=True)
            return

    await show_client_profile(callback, person, state, bot)
    await callback.answer("Возврат в профиль")