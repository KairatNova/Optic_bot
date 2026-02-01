from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from database.session import AsyncSessionLocal
from crud.person import create_client_if_not_exists

start_router = Router()

@start_router.message(CommandStart())
async def start_handler(message: Message):
    # Проверяем, что пользователь существует
    if not message.from_user:
        return

    # Теперь Pylance видит, что ниже from_user точно не None
    telegram_id = message.from_user.id
    username = message.from_user.username

    async with AsyncSessionLocal() as session:
        await create_client_if_not_exists(
            session=session,
            telegram_id=telegram_id,
            username=username
        )
    
    await message.answer("Добро пожаловать!")