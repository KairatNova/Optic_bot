from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from sqlalchemy import select

from database.models import Person, Vision
from database.session import AsyncSessionLocal
from config import OWNER_IDS
from forms.forms_fsm import AdminClientsStates, AdminVisionAddStates, AdminMainStates
from datetime import date

admin_vision_add_router = Router()

async def has_admin_access(user_id: int) -> bool:
    if user_id in OWNER_IDS:
        return True
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Person.role).where(Person.telegram_id == user_id)
        )
        role = result.scalar_one_or_none()
        return role in ("admin", "owner")

# Начало добавления записи зрения для админа
@admin_vision_add_router.callback_query(AdminClientsStates.viewing_profile, F.data.startswith("admin_add_vision_"))
async def admin_start_add_vision(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not await has_admin_access(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    person_id = int(callback.data.split("_")[3])
    await state.update_data(person_id=person_id)

    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    await bot.send_message(
        callback.from_user.id,
        "➕ <b>Добавление новой записи зрения</b>\n\n"
        "<b>Шаг 1/3: Параметры зрения</b>\n\n"
        "Введите 6 значений через пробел:\n"
        "SPH R   CYL R   AXIS R\n"
        "SPH L   CYL L   AXIS L\n\n"
        "Пример:\n"
        "-1.50 -0.50 180 -2.00 -1.00 90\n\n"
        "Если значения нет — ставьте 0.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀ Отмена", callback_data="admin_cancel_add_vision")]
        ])
    )
    await state.set_state(AdminVisionAddStates.waiting_sph_cyl_axis)
    await callback.answer()

# Отмена добавления (для админа)
@admin_vision_add_router.callback_query(F.data == "admin_cancel_add_vision")
async def admin_cancel_add_vision(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not await has_admin_access(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    data = await state.get_data()
    person_id = data.get("person_id")

    if person_id:
        async with AsyncSessionLocal() as session:
            person = await session.get(Person, person_id)
            if person:
                from handlers.admin.admin_clients_router import admin_show_profile
                await admin_show_profile(callback, person, state, bot)
                await state.set_state(AdminClientsStates.viewing_profile)

    await callback.answer("Добавление отменено")
    
# Шаг 1: SPH, CYL, AXIS
@admin_vision_add_router.message(AdminVisionAddStates.waiting_sph_cyl_axis)
async def admin_process_sph_cyl_axis(message: Message, state: FSMContext, bot: Bot):
    if not await has_admin_access(message.from_user.id):
        await message.answer("❌ Доступ запрещён.")
        return

    values = message.text.strip().split()
    if len(values) != 6:
        await message.answer(
            "❌ Нужно ровно 6 значений. Повторите или отмените.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀ Отмена", callback_data="admin_cancel_add_vision")]
            ])
        )
        return

    try:
        sph_r = float(values[0])
        cyl_r = float(values[1])
        axis_r = int(float(values[2]))
        sph_l = float(values[3])
        cyl_l = float(values[4])
        axis_l = int(float(values[5]))
    except ValueError:
        await message.answer("❌ Все значения должны быть числами. Повторите.")
        return

    await state.update_data(
        sph_r=sph_r, cyl_r=cyl_r, axis_r=axis_r,
        sph_l=sph_l, cyl_l=cyl_l, axis_l=axis_l
    )

    await message.answer(
        "<b>Шаг 2/3: PD, тип линз, модель оправы</b>\n\n"
        "Введите через пробел:\n"
        "PD   lens_type   frame_model\n\n"
        "Пример: 62 progressive Ray-Ban RB2132\n"
        "PD — обязательно. Остальное можно пропустить.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀ Отмена", callback_data="admin_cancel_add_vision")]
        ])
    )
    await state.set_state(AdminVisionAddStates.waiting_pd_lens_frame)

# Шаг 2: PD, lens_type, frame_model
@admin_vision_add_router.message(AdminVisionAddStates.waiting_pd_lens_frame)
async def admin_process_pd_lens_frame(message: Message, state: FSMContext, bot: Bot):
    if not await has_admin_access(message.from_user.id):
        await message.answer("❌ Доступ запрещён.")
        return

    parts = message.text.strip().split(maxsplit=2)

    if not parts:
        await message.answer("❌ Укажите хотя бы PD.")
        return

    try:
        pd = float(parts[0])
    except ValueError:
        await message.answer("❌ PD должен быть числом.")
        return

    lens_type = parts[1] if len(parts) >= 2 else None
    frame_model = parts[2] if len(parts) >= 3 else None

    await state.update_data(pd=pd, lens_type=lens_type, frame_model=frame_model)

    await message.answer(
        "<b>Шаг 3/3: Примечание</b>\n\n"
        "Введите текст (или пустое сообщение).",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀ Отмена", callback_data="admin_cancel_add_vision")]
        ])
    )
    await state.set_state(AdminVisionAddStates.waiting_note)

# Шаг 3: Note и сохранение
@admin_vision_add_router.message(AdminVisionAddStates.waiting_note)
async def admin_process_note_and_save(message: Message, state: FSMContext, bot: Bot):
    if not await has_admin_access(message.from_user.id):
        await message.answer("❌ Доступ запрещён.")
        return

    note = message.text.strip() if message.text else None

    data = await state.get_data()
    person_id = data["person_id"]

    async with AsyncSessionLocal() as session:
        person = await session.get(Person, person_id)
        if not person:
            await message.answer("❌ Клиент не найден.")
            await state.clear()
            return

        new_vision = Vision(
            person_id=person_id,
            visit_date=date.today(),
            sph_r=data.get("sph_r"),
            cyl_r=data.get("cyl_r"),
            axis_r=data.get("axis_r"),
            sph_l=data.get("sph_l"),
            cyl_l=data.get("cyl_l"),
            axis_l=data.get("axis_l"),
            pd=data.get("pd"),
            lens_type=data.get("lens_type"),
            frame_model=data.get("frame_model"),
            note=note
        )
        session.add(new_vision)

        # Обновляем дату последнего визита
        person.last_visit_date = date.today()

        # Сохраняем изменения
        await session.commit()

        # Загружаем свежие данные (чтобы избежать DetachedInstanceError)
        await session.refresh(person)

        # Теперь можно безопасно вызвать профиль
        from handlers.admin.admin_clients_router import admin_show_profile
        await admin_show_profile(message, person, state, bot)

    await message.answer("✅ Новая запись зрения успешно добавлена!")
    await state.set_state(AdminClientsStates.viewing_profile)