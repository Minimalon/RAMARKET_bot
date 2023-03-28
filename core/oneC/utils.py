import aiohttp
from core.oneC.api import Api
import requests
from loguru import logger
from core.database import query_db

api = Api()


async def get_main_paymentWay():
    result = []
    for paytype in await api.get_payment_gateways():
        if not paytype['IdParent']:
            result.append(paytype)
    return result


async def get_child_paymentWay(Id):
    result = []
    for paytype in await api.get_payment_gateways():
        if paytype['IdParent'] == Id:
            result.append(paytype)
    return result


async def get_child_groups(idGroup: str):
    result = []
    for group in await api.get_groups():
        if group['idGroup'] == idGroup:
            result.append(group)
    return result


async def get_tovar_by_group(idGroup):
    result = []
    for tovar in await api.get_tovars():
        if tovar['idGroup'] == idGroup:
            result.append(tovar)
    return result


async def get_tovar_by_ID(tovarID):
    for tovar in await api.get_tovars():
        if tovar['Id'] == tovarID:
            return tovar


async def get_payment_name(paymentID):
    for paytype in await api.get_payment_gateways():
        if paytype['Id'] == paymentID:
            return paytype


async def get_shops(phone):
    return await api.get_client_info(phone)


async def create_order(**kwargs):
    order = {
        "TypeR": "Doc",
        "Sklad": str(kwargs['shop']),
        "SO": str(kwargs['paymentGateway']),
        "Sotr": str(kwargs['seller_id']),
        "Itemc": [
            {
                "Tov": str(kwargs['product_id']),
                "Cost": str(kwargs['price']),
                "Sum": str(kwargs['price'] * kwargs['quantity']),
                "Kol": str(kwargs['quantity'])
            },
        ]
    }
    logger.info(order)
    response, text = await api.post_create_order(order)
    logger.info(f"Ответ сервера '{response.status}', order_id: '{text}'")
    await query_db.create_historyOrder(order_id=text, chat_id=kwargs['chat_id'],
                                       first_name=kwargs['first_name'],
                                       paymentGateway=kwargs['paymentGateway'], product_id=kwargs['product_id'],
                                       price=kwargs['price'], quantity=kwargs['quantity'], currency=kwargs['currency'],
                                       currencyPrice=kwargs['currencyPrice'], client_name=kwargs['client_name'],
                                       client_phone=kwargs['client_phone'], client_mail=kwargs['client_mail'],
                                       shop=kwargs['shop'], seller_id=kwargs['seller_id'])

    return response, text


if __name__ == '__main__':
    print(requests.post('http://pr-egais.ddns.net:24142/RAMA/hs/GetUP', data='79934055804').text)
    # print(requests.post('http://pr-egais.ddns.net:24142/RAMA/hs/GetUP', data='905539447374').json())
