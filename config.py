import os
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = "sqlite+aiosqlite:///data/database.db"

'''OWNER_IDS: set[int] = {
    int(x)
    for x in os.getenv("OWNER_IDS", "").split(",")
    if x.strip()
}'''

OWNER_IDS = [647302816,636030247]


# Читаемые названия разделов
SECTION_NAMES = {
    "appointment": "📅 Запись на приём",
    "shop_address": "🕐 График и адрес",
    "promotions": "🎁 Акции и новости",
    "catalog": "🕶 Каталог оправ",
    "about_shop": "🏥 О магазине",
    "faq": "❓ Поддержка и FAQ",
}



AUTO_BACKUP_INTERVAL_HOURS = int(os.getenv("AUTO_BACKUP_INTERVAL_HOURS", "24"))
AUTO_BACKUP_TARGET_IDS = [
    int(x)
    for x in os.getenv("AUTO_BACKUP_TARGET_IDS", "").split(",")
    if x.strip().isdigit()
] or OWNER_IDS