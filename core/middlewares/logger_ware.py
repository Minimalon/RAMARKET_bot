from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message
from core.loggers.bot_logger import BotLogger


class CallBackMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
            event: CallbackQuery,
            data: dict[str, Any],
    ) -> Any:
        data['log'] = BotLogger(event.message)
        return await handler(event, data)


class MessageMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: dict[str, Any],
    ) -> Any:
        data['log'] = BotLogger(event)
        return await handler(event, data)
