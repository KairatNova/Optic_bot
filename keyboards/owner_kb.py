from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from config import SECTION_NAMES, OWNER_IDS                                               


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
[InlineKeyboardButton(text="👥 Клиенты и рецепты", callback_data="owner_clients")],
        [InlineKeyboardButton(text="📨 Рассылки (всем / одному)", callback_data="owner_broadcast")],
        [InlineKeyboardButton(text="📊 Выгрузки данных (Excel/PDF)", callback_data="owner_exports")],
        [InlineKeyboardButton(text="⚙ Управление админами", callback_data="owner_manage_admins")],
        [InlineKeyboardButton(text="◀ Выход из панели владельца", callback_data="owner_exit")],
    ])


def get_admins_submenu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить админа", callback_data="admins_add")],
        [InlineKeyboardButton(text="➖ Удалить админа", callback_data="admins_delete")],
        [InlineKeyboardButton(text="📋 Список админов", callback_data="admins_list")],
        [InlineKeyboardButton(text="◀ Назад в главное меню", callback_data="admins_back")],
    ])

def get_broadcast_submenu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сообщение одному клиенту", callback_data="broadcast_one")],
        [InlineKeyboardButton(text="Рассылка всем клиентам", callback_data="broadcast_all")],
        [InlineKeyboardButton(text="◀ Назад в главное меню", callback_data="broadcast_back")],
    ])


def get_clients_submenu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск клиента", callback_data="clients_search")],
        [InlineKeyboardButton(text="◀ Назад в главное меню", callback_data="clients_back")],
    ])


# Подменю выгрузок
def get_export_submenu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Выгрузить всех клиентов в Excel", callback_data="export_all_clients")],
        [InlineKeyboardButton(text="📊 Выгрузить записи зрения в Excel", callback_data="export_all_visions")],
        [InlineKeyboardButton(text="◀ Назад в главное меню", callback_data="export_back")],
    ])