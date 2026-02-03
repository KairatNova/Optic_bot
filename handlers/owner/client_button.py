from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from sqlalchemy import select, update

from database.models import BotContent
from database.session import AsyncSessionLocal
from config import OWNER_IDS


from functools import lru_cache
from sqlalchemy import select

from database.models import BotContent
from database.session import AsyncSessionLocal
from forms.forms_fsm import OwnerContentStates

from keyboards.client_kb import client_keyboard

from sqlalchemy import select
from typing import Dict

from database.models import BotContent
from database.session import AsyncSessionLocal

# Глобальный кэш (None = не загружен)
_content_cache: Dict[str, str] | None = None

async def _load_content() -> Dict[str, str]:
    """Загрузка контента из БД"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(BotContent))
        rows = result.scalars().all()
        return {row.key: row.value for row in rows}

async def get_bot_content(force_refresh: bool = False) -> Dict[str, str]:
    """Получение кэша с возможностью принудительного обновления"""
    global _content_cache
    if force_refresh or _content_cache is None:
        _content_cache = await _load_content()
    return _content_cache

async def get_content(key: str, default: str = "Информация временно недоступна") -> str:
    """Удобная функция для получения одного значения"""
    content = await get_bot_content()
    return content.get(key, default)

def clear_content_cache() -> None:
    """Сброс кэша (вызывать после изменений в БД)"""
    global _content_cache
    _content_cache = None





owner__content_router = Router()

# Читаемые названия разделов
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

# Проверка владельца — мгновенно, без БД
def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS

@owner__content_router.message(Command("owner"))
async def cmd_owner_panel(message: Message, state: FSMContext):
    if not is_owner(message.from_user.id):
        # Просто игнорируем (или можно await message.delete(), но лучше молча)
        return

    await message.answer(
        "👑 <b>Панель владельца</b>\n\n"
        "Выберите раздел для редактирования:",
        reply_markup=get_sections_keyboard()
    )
    await state.set_state(OwnerContentStates.choosing_section)

# Остальные хендлеры — без изменений (кроме проверки is_owner)
@owner__content_router.message(OwnerContentStates.choosing_section, F.text.in_([v for v in SECTION_NAMES.values()]))
async def section_chosen(message: Message, state: FSMContext):
    if not is_owner(message.from_user.id):
        await state.clear()
        return

    selected_key = next(k for k, v in SECTION_NAMES.items() if v == message.text)
    current_text = await get_content(selected_key, default="Текст не задан")

    await state.update_data(edit_key=selected_key)

    await message.answer(
        f"<b>Текущий текст: «{message.text}»</b>\n\n"
        f"{current_text}\n\n"
        "Отправьте новый текст (HTML-разметка поддерживается).",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="◀ Выйти из панели")]],
            resize_keyboard=True
        )
    )
    await state.set_state(OwnerContentStates.waiting_new_text)

@owner__content_router.message(OwnerContentStates.waiting_new_text, F.text)
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

    clear_content_cache()  # сбрасываем кэш — следующий запрос загрузит свежие данные

    section_name = SECTION_NAMES.get(edit_key, edit_key)
    await message.answer(
        f"✅ Текст «{section_name}» обновлён!\n\nВыберите следующий:",
        reply_markup=get_sections_keyboard()
    )
    await state.set_state(OwnerContentStates.choosing_section)

@owner__content_router.message(F.text == "◀ Выйти из панели")
async def exit_panel(message: Message, state: FSMContext):
    if not is_owner(message.from_user.id):
        return

    await state.clear()
    await message.answer(
        "Вы вышли из панели владельца.",
        reply_markup=client_keyboard
    )

# Защита от случайных сообщений
@owner__content_router.message(OwnerContentStates.choosing_section)
async def unknown_choosing(message: Message):
    if is_owner(message.from_user.id):
        await message.answer("Выберите раздел из списка.")

@owner__content_router.message(OwnerContentStates.waiting_new_text)
async def unknown_waiting(message: Message):
    if is_owner(message.from_user.id):
        await message.answer("Отправьте новый текст или выйдите.")

#