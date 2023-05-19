from aiogram import Bot
from aiogram.types import Message
from core.handlers import basic
from core.utils import texts


async def get_true_contact(message: Message, bot: Bot):
    await basic.get_start(message, bot)


async def get_fake_contact(message: Message):
    await message.answer(texts.error_fakeContact)
