from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from sqlalchemy import select

from database.models import BotContent
from database.session import AsyncSessionLocal
from config import OWNER_IDS
from forms.forms_fsm import OwnerContentStates
from keyboards.client_kb import get_client_keyboard
from services.content import get_content, clear_content_cache  # новый импорт clear_content_cache

owner_router = Router()

SECTION_NAMES = {
    "appointment": "📅 Запись на приём",
    "shop_address": "🕐 График и адрес",
    "promotions": "🎁 Акции и новости",
    "catalog": "🕶 Каталог оправ",
    "about_shop": "🏥 О магазине",
    "faq": "❓ Поддержка и FAQ",
}

def get_sections_keyboard():
    keyboard = [
        [KeyboardButton(text=SECTION_NAMES["appointment"])],
        [KeyboardButton(text=SECTION_NAMES["shop_address"])],
        [KeyboardButton(text=SECTION_NAMES["promotions"])],
        [KeyboardButton(text=SECTION_NAMES["catalog"])],
        [KeyboardButton(text=SECTION_NAMES["about_shop"])],
        [KeyboardButton(text=SECTION_NAMES["faq"])],
        [KeyboardButton(text="◀ Выйти из панели")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS

@owner_router.message(Command("owner"))
async def cmd_owner_panel(message: Message, state: FSMContext):
    if not is_owner(message.from_user.id):
        return

    await message.answer(
        "👑 <b>Панель владельца</b>\n\n"
        "Выберите раздел для редактирования:",
        reply_markup=get_sections_keyboard()
    )
    await state.set_state(OwnerContentStates.choosing_section)

@owner_router.message(OwnerContentStates.choosing_section, F.text.in_(list(SECTION_NAMES.values())))
async def section_chosen(message: Message, state: FSMContext):
    if not is_owner(message.from_user.id):
        await state.clear()
        return

    selected_key = next(k for k, v in SECTION_NAMES.items() if v == message.text)
    
    # Получаем текущий текст, если его нет — None
    current_text = await get_content(selected_key, default=None)

    await state.update_data(edit_key=selected_key)

    if current_text is None:
        # Первый раз — текста нет
        preview_text = "Текст ещё не задан."
        example = (
            "\n\n<i>Пример текста:</i>\n"
            "📅 <b>Запись на приём</b>\n\n"
            "Чтобы записаться, напишите нам в WhatsApp — мы подберём удобное время:\n"
            '<a href="https://wa.me/996XXXXXXXXX">Написать в WhatsApp</a>\n\n'
            "Или позвоните: +996 XXX XXX XX XX"
        ) if selected_key == "appointment" else ""
    else:
        preview_text = current_text
        example = ""

    await message.answer(
        f"<b>Раздел: «{message.text}»</b>\n\n"
        f"{preview_text}{example}\n\n"
        "Отправьте новый текст (HTML-разметка поддерживается).",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="◀ Выйти из панели")]],
            resize_keyboard=True
        ),
        disable_web_page_preview=True
    )
    await state.set_state(OwnerContentStates.waiting_new_text)

@owner_router.message(OwnerContentStates.waiting_new_text, F.text)
async def new_text_received(message: Message, state: FSMContext):
    if not is_owner(message.from_user.id):
        await state.clear()
        return

    data = await state.get_data()
    edit_key = data["edit_key"]
    new_text = message.text.strip()

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(BotContent).where(BotContent.key == edit_key)
        )
        row = result.scalar_one_or_none()

        if row:
            row.value = new_text
        else:
            row = BotContent(key=edit_key, value=new_text)
            session.add(row)

        await session.commit()

    clear_content_cache()  # <-- правильный сброс кэша

    section_name = SECTION_NAMES.get(edit_key, edit_key)
    await message.answer(
        f"✅ Текст «{section_name}» успешно обновлён!\n\n"
        "Выберите следующий раздел:",
        reply_markup=get_sections_keyboard()
    )
    await state.set_state(OwnerContentStates.choosing_section)

@owner_router.message(F.text == "◀ Выйти из панели")
async def exit_panel(message: Message, state: FSMContext):
    if not is_owner(message.from_user.id):
        return

    await state.clear()
    await message.answer(
        "Вы вышли из панели владельца.",
        reply_markup=get_client_keyboard()
    )

@owner_router.message(OwnerContentStates.choosing_section)
async def unknown_choosing(message: Message):
    if is_owner(message.from_user.id):
        await message.answer("Пожалуйста, выберите раздел из списка ниже.")

@owner_router.message(OwnerContentStates.waiting_new_text)
async def unknown_waiting(message: Message):
    if is_owner(message.from_user.id):
        await message.answer("Отправьте новый текст или нажмите «◀ Выйти из панели».")