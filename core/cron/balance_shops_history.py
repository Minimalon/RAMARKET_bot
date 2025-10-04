import asyncio

from core.database.query_db import add_shops_history
from core.oneC.api import oneC_api


async def balance_shops_history() -> None:
    await add_shops_history(await oneC_api.get_balance_shops())