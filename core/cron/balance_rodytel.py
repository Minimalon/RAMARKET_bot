import asyncio

from core.database.query_db import add_rodytel_history
from core.oneC.api import oneC_api


async def balance_rodytel_history() -> None:
    await add_rodytel_history(await oneC_api.get_balance_rodytels())

if __name__ == '__main__':
    asyncio.run(balance_rodytel_history())