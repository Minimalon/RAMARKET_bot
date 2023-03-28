import json

import config
import aiohttp
import asyncio


class Api:
    def __init__(self):
        self.adress = config.adress

    async def get_payment_gateways(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.adress}/GetSO") as response:
                return await response.json()

    async def get_groups(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.adress}/Groups") as response:
                return await response.json()

    async def get_client_info(self, phone):
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.adress}/GetUP", data=str(phone)) as response:
                return await response.json()

    async def get_tovar_by_groupID(self, groupID):
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.adress}/GetTovarByGroup/{groupID}") as response:
                return await response.json()

    async def get_tovars(self):
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.adress}/GetTovar") as response:
                return await response.json()

    async def post_create_order(self, data):
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.adress}/CreateDoc", data=json.dumps(data)) as response:
                return response, await response.text()


if __name__ == '__main__':
    asyncio.run(Api().get_payment_gateways())
