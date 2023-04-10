from aiogram.filters import BaseFilter
from aiogram.types import Message
from loguru import logger


class IsTrueContact(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.contact.user_id == message.from_user.id:
            logger.info(f"Отправили сотовый '{message.contact.phone_number}'")
            return True
        else:
            logger.error(f"Отправили не свой сотовый '{message.contact.phone_number}'")
            return False
