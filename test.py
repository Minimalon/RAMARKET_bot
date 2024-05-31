import asyncio
import json
import time

import httpx


async def _get(url, data=None):
    start_time = time.time()
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=data)
        elapsed_time = time.time() - start_time
        text = response.text
        if response.is_success:
            print(f"GET {url} timeout={round(elapsed_time, 2)}")
        return response.json()


def main():
    for i in range(100):
        asyncio.run(_get('http://141.101.204.58:7000/UT/hs/Groups'))

if __name__ == '__main__':
    main()
