import asyncio
import json
import time

import aiohttp


async def _get(url, data='None'):
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.get(url, data=data) as response:
            elapsed_time = time.time() - start_time
            text = await response.text()
            if response.ok:
                print(f"GET {url} timeout={round(elapsed_time, 2)}")
            return json.loads(text)

for i in range(100):
    asyncio.run(_get('http://141.101.204.58:7000/UT/hs/Groups'))