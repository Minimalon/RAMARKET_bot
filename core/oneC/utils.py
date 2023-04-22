from aiogram import Bot
from core.oneC.api import Api
import requests
from loguru import logger
from core.database import query_db
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


async def create_order(bot: Bot, **kwargs):
    try:
        client = await query_db.get_client_info(chat_id=kwargs['chat_id'])
        shop_name = await get_shop_name(client.phone_number, kwargs['shop'])
        payment_name = (await get_payment_name(kwargs['paymentGateway']))['Наименование']
        product_name = (await get_tovar_by_ID(kwargs['product_id']))['Наименование']

        order = {
            "TypeR": "Doc",
            "Sklad": str(kwargs['shop']),
            "KursPrice": str(kwargs['currencyPrice']),
            "SO": str(kwargs['paymentGateway']),
            "Sotr": str(kwargs['seller_id']),
            "Klient": kwargs.get('client_name', ''),
            "Telefon": kwargs.get('client_phone', ''),
            "Email": kwargs.get('client_mail', ''),
            "Itemc": [
                {
                    "Tov": str(kwargs['product_id']),
                    "Cost": str(kwargs['price']),
                    "Sum": str(kwargs['sum']),
                    "Kol": str(kwargs['quantity'])
                },
            ]
        }
        logger.info(order)
        response, answer = await api.post_create_order(order)
        logger.info(answer)
        logger.info(response)
        logger.info(await response.text())
        logger.info(f"Ответ сервера '{response.status}', order_id: '{answer['Nomer']}'")
        await query_db.create_historyOrder(order_id=answer['Nomer'], chat_id=kwargs['chat_id'],
                                           first_name=kwargs['first_name'],
                                           paymentGateway=kwargs['paymentGateway'], paymentType=kwargs['paymentType'],
                                           payment_name=payment_name,
                                           product_id=kwargs['product_id'], product_name=product_name,
                                           price=kwargs['price'], quantity=kwargs['quantity'], sum=kwargs['sum'],
                                           currency=kwargs['currency'],
                                           currencyPrice=kwargs['currencyPrice'], client_name=kwargs['client_name'],
                                           client_phone=kwargs['client_phone'], client_mail=kwargs['client_mail'],
                                           shop_id=kwargs['shop'], shop_name=shop_name, seller_id=kwargs['seller_id'],
                                           sum_rub=kwargs['sum_rub'])
        return response, answer
    except Exception as ex:
        logger.exception(ex)
        await bot.send_message(kwargs['chat_id'], f'{texts.error_head}{ex}')


if __name__ == '__main__':
    # print(requests.post('http://pr-egais.ddns.net:24142/RAMA/hs/GetUP', data='79831358491').text)
    print(requests.post('http://pr-egais.ddns.net:24142/RAMA/hs/GetUP', data='79934055804').text)
    # print(requests.post('http://pr-egais.ddns.net:24142/RAMA/hs/GetUP', data='905539447374').json())
