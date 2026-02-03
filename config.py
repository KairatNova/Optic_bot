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

OWNER_IDS = [647302816]