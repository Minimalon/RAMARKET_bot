from typing import Dict, Any, Optional

from aiogram.types import TelegramObject, User
from aiogram.utils.i18n import I18n
from aiogram.utils.i18n.middleware import I18nMiddleware

from core.database import query_db as db


async def get_lang(chat_id):
    user = await db.get_client_info(chat_id=chat_id)
    if user:
        return user.language


class ACLMiddleware(I18nMiddleware):
    def __init__(
            self,
            i18n: I18n,
            i18n_key: Optional[str] = "i18n",
            middleware_key: str = "i18n_middleware",
    ) -> None:
        super().__init__(i18n=i18n, i18n_key=i18n_key, middleware_key=middleware_key)
    async def get_locale(self, event: TelegramObject, data: Dict[str, Any]) -> str:
        event_from_user: Optional[User] = data.get("event_from_user", None)
        return await get_lang(event_from_user.id) or event_from_user.language_code
