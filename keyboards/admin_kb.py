from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from config import SECTION_NAMES


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



def get_owner_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Редактировать контент бота", callback_data="owner_edit_content")],
        [InlineKeyboardButton(text="🔍 Поиск клиентов", callback_data="owner_search_clients")],
        [InlineKeyboardButton(text="📨 Рассылки (всем / одному)", callback_data="owner_broadcast")],
        [InlineKeyboardButton(text="📊 Выгрузки данных (Excel/PDF)", callback_data="owner_exports")],
        [InlineKeyboardButton(text="⚙ Управление админами", callback_data="owner_manage_admins")],
        [InlineKeyboardButton(text="◀ Выход из панели владельца", callback_data="owner_exit")],
    ])