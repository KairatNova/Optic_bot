from aiogram import Router
from aiogram.types import Message

from aiogram import F

from services.content import get_content
from config import SECTION_NAMES


client_router = Router()
@client_router.message(F.text == SECTION_NAMES["appointment"])
async def appointment(message: Message):
    text = await get_content("appointment")
    await message.answer(text, disable_web_page_preview=True)

@client_router.message(F.text == SECTION_NAMES["shop_address"])
async def shop_address(message: Message):
    text = await get_content("shop_address")
    await message.answer(text, disable_web_page_preview=True)

@client_router.message(F.text == SECTION_NAMES["promotions"])
async def promotions(message: Message):
    text = await get_content("promotions")
    await message.answer(text)

@client_router.message(F.text == SECTION_NAMES["catalog"])
async def catalog(message: Message):
    text = await get_content("catalog")
    await message.answer(text, disable_web_page_preview=True)

@client_router.message(F.text == SECTION_NAMES["about_shop"])
async def about_shop(message: Message):
    text = await get_content("about_shop")
    await message.answer(text)

@client_router.message(F.text == SECTION_NAMES["faq"])
async def faq(message: Message):
    text = await get_content("faq")
    await message.answer(text)