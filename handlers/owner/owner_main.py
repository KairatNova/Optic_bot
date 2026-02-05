from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest  # для обработки ошибок удаления

from config import OWNER_IDS
from forms.forms_fsm import OwnerContentStates, OwnerMainStates
from keyboards.client_kb import get_client_keyboard
from keyboards.admin_kb import get_owner_main_keyboard, get_sections_keyboard
from services.content import get_content

owner_main_router = Router()

def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS



@owner_main_router.message(Command("owner"))
async def cmd_owner_main(message: Message, state: FSMContext):
    if not is_owner(message.from_user.id):
        return

    await message.answer(
        "👑 <b>Панель владельца</b>\n\n"
        "Выберите нужный раздел:",
        reply_markup=get_owner_main_keyboard()
    )
    await state.set_state(OwnerMainStates.main_menu)

@owner_main_router.callback_query(OwnerMainStates.main_menu, F.data.startswith("owner_"))
async def owner_menu_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not is_owner(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    action = callback.data

    # Удаляем старое сообщение (с защитой от ошибок)
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass  # если сообщение уже удалено или недоступно — игнорируем

    if action == "owner_edit_content":
        await bot.send_message(
            callback.from_user.id,
            "📝 <b>Редактирование контента бота</b>\n\nВыберите раздел:",
            reply_markup=get_sections_keyboard()  # ReplyKeyboard
        )
        await state.set_state(OwnerContentStates.choosing_section)

    elif action == "owner_search_clients":
        await bot.send_message(
            callback.from_user.id,
            "🔍 <b>Поиск клиентов</b>\n\nФункция в разработке.",
            reply_markup=get_owner_main_keyboard()
        )

    elif action == "owner_broadcast":
        await bot.send_message(
            callback.from_user.id,
            "📨 <b>Рассылки</b>\n\nФункция в разработке.",
            reply_markup=get_owner_main_keyboard()
        )

    elif action == "owner_exports":
        await bot.send_message(
            callback.from_user.id,
            "📊 <b>Выгрузки данных</b>\n\nФункция в разработке.",
            reply_markup=get_owner_main_keyboard()
        )

    elif action == "owner_manage_admins":
        await bot.send_message(
            callback.from_user.id,
            "⚙ <b>Управление админами</b>\n\nФункция в разработке.",
            reply_markup=get_owner_main_keyboard()
        )

    elif action == "owner_exit":
        await state.clear()
        await bot.send_message(
            callback.from_user.id,
            "Вы вышли из панели владельца.",
            reply_markup=get_client_keyboard()
        )

    await callback.answer()

# Если владелец отправил текст в главном меню — напоминаем
@owner_main_router.message(OwnerMainStates.main_menu)
async def unknown_in_main_menu(message: Message):
    if is_owner(message.from_user.id):
        await message.answer("Пожалуйста, используйте кнопки 👇", reply_markup=get_owner_main_keyboard())