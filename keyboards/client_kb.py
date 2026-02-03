from aiogram.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup



# Ваша основная клиентская клавиатура (из предыдущего примера)
client_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📅 Запись на приём"),
            KeyboardButton(text="🕐 График и адрес")
        ],
        [
            KeyboardButton(text="🎁 Акции и новости"),
            KeyboardButton(text="🕶 Каталог оправ")
        ],
        [
            KeyboardButton(text="🏥 О магазине"),
            KeyboardButton(text="❓ Поддержка и FAQ")
        ]
    ],
    resize_keyboard=True
)