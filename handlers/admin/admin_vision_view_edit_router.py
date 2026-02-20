from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from sqlalchemy import select, delete

from database.models import Person, Vision
from database.session import AsyncSessionLocal
from config import OWNER_IDS
from forms.forms_fsm import AdminClientsStates, AdminVisionViewStates, AdminVisionEditStates
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

admin_vision_view_edit_router = Router()

async def has_admin_access(user_id: int) -> bool:
    if user_id in OWNER_IDS:
        return True
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Person.role).where(Person.telegram_id == user_id)
        )
        role = result.scalar_one_or_none()
        return role in ("admin", "owner")

# Просмотр всех записей зрения
@admin_vision_view_edit_router.callback_query(AdminClientsStates.viewing_profile, F.data.startswith("admin_view_all_visions_"))
async def admin_view_all_visions(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not await has_admin_access(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    person_id = int(callback.data.split("_")[4])

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Vision).where(Vision.person_id == person_id).order_by(Vision.visit_date.desc())
        )
        visions = result.scalars().all()

    if not visions:
        await callback.answer("У клиента нет записей зрения.", show_alert=True)
        return

    await state.update_data(
        visions_ids=[v.id for v in visions],
        current_vision_index=0,
        person_id=person_id
    )

    await admin_show_single_vision(callback, 0, visions, bot, state)
    await callback.answer()

# Показ одной записи
async def admin_show_single_vision(trigger, index: int, visions: list[Vision], bot: Bot, state: FSMContext):
    v = visions[index]

    text = f"<b>Запись зрения от {v.visit_date}</b>\n\n"
    text += f"Правая: SPH {v.sph_r or '—'} | CYL {v.cyl_r or '—'} | AXIS {v.axis_r or '—'}\n"
    text += f"Левая: SPH {v.sph_l or '—'} | CYL {v.cyl_l or '—'} | AXIS {v.axis_l or '—'}\n"
    text += f"PD: {v.pd or '—'}\n"
    text += f"Тип линз: {v.lens_type or '—'}\n"
    text += f"Модель оправы: {v.frame_model or '—'}\n"
    if v.note:
        text += f"Примечание: {v.note}\n"
    text += f"\nЗапись {index + 1} из {len(visions)}"

    kb = [
        [
            InlineKeyboardButton(text="◀", callback_data=f"admin_vision_prev_{index}"),
            InlineKeyboardButton(text="▶", callback_data=f"admin_vision_next_{index}"),
        ],
        [InlineKeyboardButton(text="✏ Редактировать эту запись", callback_data=f"admin_edit_this_vision_{v.id}")],
        [InlineKeyboardButton(text="🗑 Удалить эту запись", callback_data=f"admin_delete_this_vision_{v.id}")],
        [InlineKeyboardButton(text="📄 Выгрузить в PDF", callback_data=f"admin_export_pdf_{v.id}")],
        [InlineKeyboardButton(text="◀ Назад в профиль", callback_data=f"admin_back_to_profile_{visions[0].person_id}")],
    ]

    # Всегда отправляем новое сообщение
    if isinstance(trigger, Message):
        await trigger.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    else:
        try:
            await trigger.message.delete()
        except TelegramBadRequest:
            pass
        await bot.send_message(
            trigger.from_user.id,
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
        )

# Навигация ◀ ▶
@admin_vision_view_edit_router.callback_query(F.data.startswith("admin_vision_prev_") | F.data.startswith("admin_vision_next_"))
async def admin_navigate_vision(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not await has_admin_access(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    data = await state.get_data()
    visions_ids = data.get("visions_ids", [])
    current_index = int(callback.data.split("_")[3])

    new_index = current_index
    if "prev" in callback.data:
        new_index = max(0, current_index - 1)
    else:
        new_index = min(len(visions_ids) - 1, current_index + 1)

    async with AsyncSessionLocal() as session:
        visions = [await session.get(Vision, vid) for vid in visions_ids]

    await admin_show_single_vision(callback, new_index, visions, bot, state)
    await state.update_data(current_vision_index=new_index)
    await callback.answer()

# Назад в профиль
@admin_vision_view_edit_router.callback_query(F.data.startswith("admin_back_to_profile_"))
async def admin_back_to_profile_from_vision(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not await has_admin_access(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    person_id = int(callback.data.split("_")[3])

    async with AsyncSessionLocal() as session:
        person = await session.get(Person, person_id)
        if not person:
            await callback.answer("Клиент не найден.", show_alert=True)
            return

        from handlers.admin.admin_clients_router import admin_show_profile
        await admin_show_profile(callback, person, state, bot)

    await state.set_state(AdminClientsStates.viewing_profile)
    await callback.answer("Возврат в профиль")

# Редактирование записи
@admin_vision_view_edit_router.callback_query(AdminVisionViewStates.viewing_single_vision, F.data.startswith("admin_edit_this_vision_"))
async def admin_start_edit_vision(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not await has_admin_access(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    vision_id = int(callback.data.split("_")[4])

    async with AsyncSessionLocal() as session:
        vision = await session.get(Vision, vision_id)
        if not vision:
            await callback.answer("Запись не найдена.", show_alert=True)
            return

        person_id = vision.person_id
        current_index = (await state.get_data()).get("current_vision_index", 0)
        await state.update_data(vision_id=vision_id, person_id=person_id, current_vision_index=current_index)

    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    current_values = (
        f"Текущие значения:\n"
        f"Правая: SPH {vision.sph_r or '—'} | CYL {vision.cyl_r or '—'} | AXIS {vision.axis_r or '—'}\n"
        f"Левая: SPH {vision.sph_l or '—'} | CYL {vision.cyl_l or '—'} | AXIS {vision.axis_l or '—'}\n"
    )

    await bot.send_message(
        callback.from_user.id,
        f"✏ <b>Редактирование записи зрения</b>\n\n{current_values}\n\n"
        "<b>Шаг 1/3: Параметры зрения</b>\n\n"
        "Введите 6 новых значений через пробел (или отправьте любое сообщение для пропуска):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀ Отмена", callback_data="admin_cancel_edit_vision")]
        ])
    )
    await state.set_state(AdminVisionEditStates.waiting_sph_cyl_axis)
    await callback.answer()

# Шаг 1 редактирования
@admin_vision_view_edit_router.message(AdminVisionEditStates.waiting_sph_cyl_axis)
async def admin_process_edit_sph_cyl_axis(message: Message, state: FSMContext, bot: Bot):
    if not await has_admin_access(message.from_user.id):
        await message.answer("❌ Доступ запрещён.")
        return

    values = message.text.strip().split()

    data = await state.get_data()
    vision_id = data["vision_id"]

    async with AsyncSessionLocal() as session:
        vision = await session.get(Vision, vision_id)

    updated = False
    if len(values) == 6:
        try:
            sph_r = float(values[0])
            cyl_r = float(values[1])
            axis_r = int(float(values[2]))
            sph_l = float(values[3])
            cyl_l = float(values[4])
            axis_l = int(float(values[5]))

            vision.sph_r = sph_r
            vision.cyl_r = cyl_r
            vision.axis_r = axis_r
            vision.sph_l = sph_l
            vision.cyl_l = cyl_l
            vision.axis_l = axis_l
            updated = True
        except ValueError:
            await message.answer("❌ Неверный формат. Повторите или отмените.")
            return

    await session.commit()

    current_values = f"Текущие: PD {vision.pd or '—'} | Lens: {vision.lens_type or '—'} | Frame: {vision.frame_model or '—'}\n"

    await message.answer(
        f"<b>Шаг 2/3: PD, тип линз, модель оправы</b>\n\n{current_values}\n"
        "Введите новые значения через пробел (или пропустите):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀ Отмена", callback_data="admin_cancel_edit_vision")]
        ])
    )
    await state.set_state(AdminVisionEditStates.waiting_pd_lens_frame)

# Шаг 2
@admin_vision_view_edit_router.message(AdminVisionEditStates.waiting_pd_lens_frame)
async def admin_process_edit_pd_lens_frame(message: Message, state: FSMContext, bot: Bot):
    if not await has_admin_access(message.from_user.id):
        await message.answer("❌ Доступ запрещён.")
        return

    parts = message.text.strip().split(maxsplit=2)
    data = await state.get_data()
    vision_id = data["vision_id"]

    async with AsyncSessionLocal() as session:
        vision = await session.get(Vision, vision_id)

    updated = False
    if len(parts) >= 1:
        try:
            pd = float(parts[0])
            vision.pd = pd
            updated = True
        except ValueError:
            await message.answer("❌ PD должен быть числом.")
            return

        if len(parts) >= 2:
            vision.lens_type = parts[1] or None
            updated = True

        if len(parts) >= 3:
            vision.frame_model = parts[2] or None
            updated = True

        if updated:
            await session.commit()

    current_note = f"Текущий примечание: {vision.note or '—'}\n"

    await message.answer(
        f"<b>Шаг 3/3: Примечание</b>\n\n{current_note}\n"
        "Введите новое примечание (или пропустите):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀ Отмена", callback_data="admin_cancel_edit_vision")]
        ])
    )
    await state.set_state(AdminVisionEditStates.waiting_note)

# Шаг 3 и сохранение
@admin_vision_view_edit_router.message(AdminVisionEditStates.waiting_note)
async def admin_process_edit_note(message: Message, state: FSMContext, bot: Bot):
    if not await has_admin_access(message.from_user.id):
        await message.answer("❌ Доступ запрещён.")
        return

    note = message.text.strip() if message.text else None
    data = await state.get_data()
    vision_id = data["vision_id"]
    current_index = data.get("current_vision_index", 0)

    async with AsyncSessionLocal() as session:
        vision = await session.get(Vision, vision_id)
        if note is not None:
            vision.note = note
            await session.commit()

        # Перезагружаем список visions
        visions_ids = data.get("visions_ids", [])
        visions = [await session.get(Vision, vid) for vid in visions_ids]

    await message.answer("✅ Запись обновлена!")

    # Возврат к просмотру этой записи
    await admin_show_single_vision(message, current_index, visions, bot, state)
    await state.set_state(AdminVisionViewStates.viewing_single_vision)