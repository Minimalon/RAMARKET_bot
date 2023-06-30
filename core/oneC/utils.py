import re
from collections import namedtuple

import requests
from aiogram import Bot
from funcy import str_join
from loguru import logger

from core.database import query_db
from core.oneC.api import Api
from core.utils import texts

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


async def get_shop_name(phone, shop_id):
    for shop in (await api.get_client_info(phone))['Магазины']:
        if shop['idМагазин'] == shop_id:
            return shop['Магазин']


async def get_shop_by_id(shop_id: str):
    """
    Возвращает магазин по его id
    :param shop_id: id магазина
    :return: Возвращает namedtuple('Shop', 'name id currency currency_price country country_code city city_code')
    """
    response, all_shops = await api.get_all_shops()
    turple = namedtuple('Shop', 'name id currency currency_price country country_code city city_code')
    for shop in all_shops:
        if shop['id'] == shop_id:
            return turple(shop["Наименование"], shop['id'], shop['Валюта'], shop['ВалютаКурс'], shop['Страна'], shop['КодСтраны'], shop['Город'], shop['КодГород'])


async def create_order(bot: Bot, data):
    try:
        payment_name = (await get_payment_name(data['paymentGateway']))['Наименование']
        order = {
            "TypeR": "Doc",
            "Sklad": str(data['shop_id']),
            "KursPrice": str(data['currencyPrice']),
            "SO": str(data['paymentGateway']),
            "Sotr": str(data['agent_id']),
            "Klient": data.get('client_name', ''),
            "Telefon": str_join(seq=re.findall(r'[0-9]*', data.get('client_phone', '')), sep=''),
            "Email": data.get('client_mail', ''),
            "Itemc": data['cart_oneC']
        }
        logger.info(order)
        response, answer = await api.post_create_order(order)
        logger.info(answer)
        logger.info(response)
        logger.info(await response.text())
        logger.info(f"Ответ сервера '{response.status}', order_id: '{answer['Nomer']}'")
        if response.ok:
            for cart in data['cart_bot']:
                await query_db.create_historyOrder(order_id=answer['Nomer'], chat_id=str(data['chat_id']),
                                                   city_name=data['city_name'], country_code=data['country_code'], country_name=data['country_name'], city_code=data['city_code'],
                                                   paymentGateway=data['paymentGateway'], paymentType=data['paymentType'],payment_name=payment_name,
                                                   product_id=cart['product_id'], product_name=cart['product_name'],
                                                   price=cart['price'], quantity=str(cart['quantity']),
                                                   sum_usd=data['sum_usd'], sum_rub=data['sum_rub'],
                                                   currency=data['currency'],currencyPrice=data['currencyPrice'], client_name=data['client_name'],
                                                   client_phone=data['client_phone'], client_mail=data['client_mail'],
                                                   shop_id=data['shop_id'], shop_name=data['shop_name'], agent_id=data['agent_id'], agent_name=data['agent_name'],
                                                   shop_currency=data['shop_currency'])
        return response, answer
    except Exception as ex:
        logger.exception(ex)
        await bot.send_message(data['chat_id'], f'{texts.error_head}{ex}')


if __name__ == '__main__':
    print(requests.post('http://pr-egais.ddns.net:24142/RAMA/hs/GetUP', data='79831358491').text)
    print(requests.post('http://pr-egais.ddns.net:24142/RAMA/hs/GetUP', data='79934055804').text)
    print(requests.post('http://pr-egais.ddns.net:24142/RAMA/hs/GetUP', data='905539447374').text)
