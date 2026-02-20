from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from sqlalchemy import select

from database.models import Person
from database.session import AsyncSessionLocal
from config import OWNER_IDS
from forms.forms_fsm import AdminClientsStates, AdminMainStates  # убедитесь, что состояния есть
from handlers.admin.admin_broadcast_router import has_admin_access
from handlers.admin.admin_clients_router import admin_show_profile
from keyboards.admin_kb import get_admin_main_keyboard  # клавиатура админа

admin_client_edit_router = Router()

def is_admin_or_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS

# Начать редактирование данных клиента
@admin_client_edit_router.callback_query(AdminClientsStates.viewing_profile, F.data.startswith("admin_edit_client_"))
async def start_admin_edit_client(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not is_admin_or_owner(callback.from_user.id):
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
        "✏ <b>Редактирование данных клиента (админ)</b>\n\n"
        "Введите новые данные через пробел в формате:\n"
        "Имя Фамилия Возраст\n\n"
        "Примеры:\n"
        "Иван Иванов 25\n"
        "Иван Иванов\n"
        "Иван 25\n"
        "25\n\n"
        "Пропущенные поля останутся без изменений.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀ Отмена", callback_data="admin_cancel_edit_client")]
        ])
    )
    await state.set_state(AdminClientsStates.editing_client_data)
    await callback.answer()

# Отмена редактирования
@admin_client_edit_router.callback_query(AdminClientsStates.editing_client_data, F.data == "admin_cancel_edit_client")
async def admin_cancel_edit_client(callback: CallbackQuery, state: FSMContext, bot: Bot):
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
            await admin_show_profile(callback, person, state, bot)
            await state.set_state(AdminClientsStates.viewing_profile)

    await callback.answer("Редактирование отменено")



# Обработка ввода редактирования
@admin_client_edit_router.message(AdminClientsStates.editing_client_data)
async def admin_process_edit_client(message: Message, state: FSMContext, bot: Bot):
    if not await has_admin_access(message.from_user.id):
        await message.answer("❌ Доступ запрещён.")
        await state.clear()
        return

    data = await state.get_data()
    person_id = data.get("person_id")

    async with AsyncSessionLocal() as session:
        person = await session.get(Person, person_id)
        if not person:
            await message.answer("❌ Клиент не найден.")
            await state.set_state(AdminClientsStates.viewing_profile)
            return

        words = message.text.strip().split()

        changes = []

        if len(words) >= 1:
            person.first_name = words[0]
            changes.append("Имя")

        if len(words) >= 2:
            person.last_name = words[1]
            changes.append("Фамилия")

        if len(words) >= 3 and words[2].isdigit():
            person.age = int(words[2])
            changes.append("Возраст")

        if changes:
            await session.commit()
            await message.answer(f"✅ Данные обновлены: {', '.join(changes)}")
        else:
            await message.answer("Ничего не изменено. Укажите хотя бы одно значение.")

        # Возврат в обновленный профиль
        from .admin_clients_router import admin_show_profile
        await admin_show_profile(message, person, state, bot)
        await state.set_state(AdminClientsStates.viewing_profile)