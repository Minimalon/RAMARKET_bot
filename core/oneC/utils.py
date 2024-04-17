import asyncio
import json

from core.database import query_db
from core.models_pydantic.order import Product, ProductGroup, Order
from core.oneC.api import Api
from core.oneC.models import Shop, User, Payment

api = Api()


async def get_employeeInfo(phone):
    return await api.get_client_info(phone)


async def get_unique_currencys():
    result = []
    for shop in await api.get_all_shops():
        if shop['Валюта'] not in result:
            result.append(shop['Валюта'])
    return result


async def get_main_paymentWay() -> list[Payment]:
    result = []
    for paytype in await api.get_payment_gateways():
        if not paytype['IdParent']:
            result.append(Payment.model_validate_json(json.dumps(paytype)))
    return result


async def get_child_paymentWay(Id: str) -> list[Payment]:
    result = []
    for paytype in await api.get_payment_gateways():
        if paytype['IdParent'] == Id:
            result.append(Payment.model_validate_json(json.dumps(paytype)))
    return result


async def get_paymentWay_by_id(Id: str) -> Payment | None:
    for paytype in await api.get_payment_gateways():
        if paytype['Id'] == Id:
            return Payment.model_validate_json(json.dumps(paytype))


async def get_child_groups(idGroup: str) -> list[ProductGroup]:
    result = []
    for group in await api.get_groups():
        if group['idGroup'] == idGroup:
            result.append(ProductGroup.model_validate_json(json.dumps(group)))
    return result


async def get_pg_by_id(id: str) -> ProductGroup | None:
    for group in await api.get_groups():
        if group['id'] == id:
            return ProductGroup.model_validate_json(json.dumps(group))


async def get_tovar_by_group(idGroup) -> list[Product]:
    result = []
    for tovar in await api.get_tovars():
        if tovar['idGroup'] == idGroup:
            result.append(Product.model_validate_json(json.dumps(tovar)))
    return result


async def get_tovar_by_ID(tovarID) -> Product | None:
    for tovar in await api.get_tovars():
        if tovar['Id'] == tovarID:
            return Product.model_validate_json(json.dumps(tovar))


async def get_payment_name(paymentID):
    for paytype in await api.get_payment_gateways():
        if paytype['Id'] == paymentID:
            return paytype


async def get_user_info(phone) -> User | None:
    client_1c = await api.get_client_info(phone)
    if not client_1c:
        return None
    return User.model_validate_json(json.dumps(client_1c))


async def get_shop_name(phone, shop_id):
    for shop in (await api.get_client_info(phone))['Магазины']:
        if shop['idМагазин'] == shop_id:
            return shop['Магазин']


async def get_shop_by_id(shop_id: str) -> Shop | None:
    """
    Возвращает магазин по его id
    :param shop_id: id магазина
    :return: Shop
    """
    all_shops = await api.get_all_shops()
    count = 0
    for shop in all_shops:
        if shop['id'] == shop_id:
            return Shop.model_validate_json(json.dumps(shop))
    if count == 0:
        raise ValueError(f'Магазин "{shop_id}" не найден в 1С')


async def create_order(order: Order) -> dict:
    response = await api.post_create_order(order.create_1c_order())
    return response


if __name__ == '__main__':
    a = asyncio.run(get_user_info('79934055804'))
    print(a.model_dump_json(by_alias=True))
    # print(requests.post('http://pr-egais.ddns.net:24142/RAMA/hs/GetUP', data='79831358491').text)
    # print(requests.post('http://pr-egais.ddns.net:24142/RAMA/hs/GetUP', data='79934055804').text)
    # print(requests.post('http://pr-egais.ddns.net:24142/RAMA/hs/GetUP', data='905539447374').text)
