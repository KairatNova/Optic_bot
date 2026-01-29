from dataclasses import dataclass
import os

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


class Settings: 
    BOT_TOKEN: str

    def __init__(self, BOT_TOKEN: str):
        self.BOT_TOKEN = BOT_TOKEN


        
def get_settings() -> Settings:
    bot_token = os.getenv("BOT_TOKEN")

    if not bot_token:
        raise ValueError("BOT_TOKEN is not set in environment variables")
    return Settings(
        BOT_TOKEN=bot_token,
    )


settings = get_settings()