from aiogram import Bot
from aiogram.types import Message
from core.handlers import basic
from core.utils import texts


async def get_true_contact(message: Message):
    await basic.get_start(message)


async def get_fake_contact(message: Message):
    await message.answer(texts.error_fakeContact)
