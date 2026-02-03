from aiogram import Router
from aiogram.types import Message

from aiogram import F

from handlers.owner.client_button import get_content


client_router = Router()

@client_router.message(F.text == "🕐 График и адрес")
async def shop_address(message: Message):
    text = await get_content("shop_address")
    await message.answer(text, disable_web_page_preview=True)

@client_router.message(F.text == "🎁 Акции и новости")
async def promotions(message: Message):
    text = await get_content("promotions")
    await message.answer(text)

@client_router.message(F.text == "🕶 Каталог оправ")
async def catalog(message: Message):
    text = await get_content("catalog")
    await message.answer(text, disable_web_page_preview=True)

@client_router.message(F.text == "🏥 О магазине")
async def about_shop(message: Message):
    text = await get_content("about_shop")
    await message.answer(text)

@client_router.message(F.text == "❓ Поддержка и FAQ")
async def faq(message: Message):
    text = await get_content("faq")
    await message.answer(text)
