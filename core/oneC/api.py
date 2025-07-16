import asyncio
import json
import time

import aiohttp

import config
from core.loggers.make_loggers import api_log
from core.oneC.models import ShopBalance


class Api:
    def __init__(self):
        self.adress = config.adress
        self.log = api_log

    async def _get(self, url, data='None'):
        timeout = aiohttp.ClientTimeout(
            total=120,  # Общий таймаут
            connect=80,  # Таймаут на подключение
            sock_read=60,  # Таймаут на чтение данных
            sock_connect=40  # Таймаут на установление соединения
        )
        start_time = time.time()
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, data=data) as response:
                elapsed_time = time.time() - start_time
                log = self.log.bind(data=data, timeout=round(elapsed_time, 2))
                text = await response.text()
                if response.ok:
                    log.success(f"GET {url}")
                else:
                    log.error(f"GET {url} Status={response.status}")
                    log.error(text)
                    raise ValueError(text)
                return json.loads(text)

    async def _post(self, url, data):
        timeout = aiohttp.ClientTimeout(
            total=120,  # Общий таймаут
            connect=80,  # Таймаут на подключение
            sock_read=60,  # Таймаут на чтение данных
            sock_connect=40  # Таймаут на установление соединения
        )
        start_time = time.time()
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, data=data) as response:
                elapsed_time = time.time() - start_time
                log = self.log.bind(data=data, timeout=round(elapsed_time, 2))
                text = await response.text()
                if response.ok:
                    log.success(f"POST {url}")
                    log.success(text)
                else:
                    log.error(f"POST {url} Status={response.status}")
                    log.error(text)
                    raise ValueError(text)
                return text

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
        return json.loads(await self._post(f"{self.adress}/CreateDoc", data=json.dumps(data)))

    async def delete_order(self, order_id, date):
        """
        Удаляет созданный заказ
        :param order_id: Номер заказа
        :param date: Дата заказа в формате %Y%m%d
        :return:
        """
        return await self._post(f"{self.adress}/DeleteDoc",
                                data=json.dumps({"Номер": order_id, "Дата": date}))

    async def get_balance_shop(self, shop_id: str) -> ShopBalance:
        answer = await self._get(f"{self.adress}/GeDebt",
                                 data=json.dumps({"Shop": shop_id}))
        return ShopBalance.model_validate_json(json.dumps(answer[0]))

    async def create_rko(self,Shop: str, Amount: str, User: str, Currency: str, KursPrice: str) -> dict:
        return await self._post(f"{self.adress}/CreateRKO",
                                data=json.dumps({"Shop": Shop, "Amount": Amount, "User": User, "Currency": Currency, "KursPrice": KursPrice}))


async def test():
    api = Api()
    print(await api.get_balance_shop('5502644'))


if __name__ == '__main__':
    asyncio.run(test())
