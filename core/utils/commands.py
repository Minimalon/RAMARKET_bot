from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault
from config import _

async def get_commands(bot: Bot):
    commands = [
        BotCommand(
            command='start',
            description=_('Главное меню')
        ),
        BotCommand(
            command='cancel',
            description=_('Отменить создание заказа')
        ),

    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())
