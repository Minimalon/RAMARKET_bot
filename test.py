import asyncio
import json
import time
import httpx


async def _get(url, data=None):
    start_time = time.time()
    timeout = httpx.Timeout(
        connect=5.0,  # Таймаут на подключение
        read=10.0,  # Таймаут на чтение данных
        write=10.0,  # Таймаут на запись данных
        pool=5.0  # Таймаут на получение соединения из пула
    )
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(url, params=data)
            elapsed_time = time.time() - start_time
            text = response.text
            if response.is_success:
                print(f"GET {url} timeout={round(elapsed_time, 2)}")
            return response.json()
        except httpx.ConnectTimeout:
            print(f"Connect timeout for GET {url}")
        except httpx.ReadTimeout:
            print(f"Read timeout for GET {url}")
        except httpx.WriteTimeout:
            print(f"Write timeout for GET {url}")
        except httpx.PoolTimeout:
            print(f"Pool timeout for GET {url}")
        except httpx.HTTPStatusError as e:
            print(f"HTTP error {e.response.status_code} for GET {url}")
        except Exception as e:
            print(f"An unexpected error occurred for GET {url}: {e}")


def main():
    for i in range(100):
        asyncio.run(_get('http://141.101.204.58:7000/UT/hs/Groups'))


if __name__ == '__main__':
    main()
