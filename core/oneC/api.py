import asyncio
import json

import aiohttp

import config
from core.loggers.make_loggers import api_log


class Api:
    def __init__(self):
        self.adress = config.adress
        self.log = api_log

    async def _get(self, url, data='None'):
        log = self.log.bind(data=data)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, data=data) as response:
                text = await response.text()
                if response.ok:
                    log.success(f"GET {url}")
                else:
                    log.error(f"GET {url} Status={response.status}")
                    log.error(text)
                    raise ValueError(text)
                return json.loads(text)

    async def _post(self, url, data):
        log = self.log.bind(data=data)
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                text = await response.text()
                if response.ok:
                    log.success(f"POST {url}")
                    log.success(await response.text())
                else:
                    log.error(f"POST {url} Status={response.status}")
                    log.error(text)
                    raise ValueError(text)
                return json.loads(text)

    async def get_payment_gateways(self):
        return await self._get(f"{self.adress}/GetSO")

    async def get_groups(self):
        return await self._get(f"{self.adress}/Groups")

    async def get_client_info(self, phone) -> dict:
        return await self._get(f"{self.adress}/GetUP", phone)

    async def get_tovar_by_groupID(self, groupID):
        return await self._get(f"{self.adress}/GetTovarByGroup/{groupID}")

    async def get_tovars(self):
        return await self._get(f"{self.adress}/GetTovar")

    async def get_all_shops(self) -> dict:
        """
        Список всех магазинов в 1С
        :return: JSON
        """
        return await self._get(f"{self.adress}/GetTTAll")


    async def post_create_order(self, data: dict) -> dict:
        """
        Создает новый заказ
        :param data: Тело запроса
        :return: dict
        """
        return await self._post(f"{self.adress}/CreateDoc", data=json.dumps(data))

    async def delete_order(self, order_id, date):
        """
        Удаляет созданный заказ
        :param order_id: Номер заказа
        :param date: Дата заказа в формате %Y%m%d
        :return:
        """
        return await self._post(f"{self.adress}/DeleteDoc",
                                data=json.dumps({"Номер": order_id, "Дата": date}))


if __name__ == '__main__':
    print(asyncio.run(Api().get_client_info("905334950683")))
