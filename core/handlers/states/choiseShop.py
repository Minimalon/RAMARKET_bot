import re
from core.utils import texts
from aiogram.types import CallbackQuery, Message
from core.utils.callbackdata import Shop
from loguru import logger
from core.oneC import utils
from core.keyboards import inline, reply
from core.oneC.api import Api
from core.database import query_db

oneC = Api()


async def error_message(message: Message, exception):
    text = f"{texts.error_head}{exception}"
    await message.answer(text)


async def not_reg(call: CallbackQuery):
    await call.message.delete()
    text = f'Вы зашли впервые, нажмите кнопку Регистрация'
    await call.message.answer(text, reply_markup=reply.getKeyboard_registration(), parse_mode='HTML')


async def check_shops(call: CallbackQuery):
    try:
        log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
        client = await query_db.get_client_info(chat_id=call.message.chat.id)
        if not client:
            await not_reg(call)
        shop = await utils.get_shops(client.phone_number)
        log.info(f'Количество магазинов "{len(shop["Магазины"])}"')
        await query_db.update_order(chat_id=call.message.chat.id, currency=shop['Валюта'])
        if len(shop['Магазины']) > 1:
            await query_db.update_order(chat_id=call.message.chat.id, seller_id=shop['id'])
            await call.message.edit_text("Выберите магазин",
                                         reply_markup=inline.getKeyboard_selectShop(shop['Магазины']))
        elif len(shop['Магазины']) == 0:
            log.error('Зарегано 0 магазинов')
            await call.message.answer(texts.zero_shops)
        else:
            await query_db.update_order(chat_id=call.message.chat.id, shop=str(shop['Магазины'][0]['idМагазин']),
                                        seller_id=shop['id'])
            await choise_currency_price(call)
            await call.answer()
    except Exception as ex:
        await error_message(call.message, ex)
        logger.exception(ex)


async def choise_currency_price(call: CallbackQuery):
    try:
        client_DB = await query_db.get_client_info(chat_id=call.message.chat.id)
        if not client_DB:
            await not_reg(call)
        client = await oneC.get_client_info(client_DB.phone_number)
        if client:
            if re.findall(',', client["ВалютаКурс"]):
                current_price = client["ВалютаКурс"].replace(",", '.')
            else:
                current_price = client["ВалютаКурс"]
            await query_db.update_order(chat_id=call.message.chat.id, currencyPrice=current_price,
                                        currency=client['Валюта'])
            text = f'Фактический курс: <code>{client["ВалютаКурс"]}</code>'
            await call.message.edit_text(text, reply_markup=inline.getKeyboard_selectPriceCurrency(), parse_mode='HTML')
            await call.answer()
        else:
            await not_reg(call)
    except Exception as ex:
        await error_message(call.message, ex)
        logger.exception(ex)


async def choise_currency_price_Shop(call: CallbackQuery, callback_data: Shop):
    try:
        client_DB = await query_db.get_client_info(chat_id=call.message.chat.id)
        if not client_DB:
            await not_reg(call)
        client = await oneC.get_client_info(client_DB.phone_number)
        if client:
            if re.findall(',', client["ВалютаКурс"]):
                current_price = client["ВалютаКурс"].replace(",", '.')
            else:
                current_price = client["ВалютаКурс"]
            await query_db.update_order(chat_id=call.message.chat.id, currencyPrice=current_price,
                                        shop=callback_data.shop)
            text = f'Фактический курс: <code>{client["ВалютаКурс"]}</code>'
            await call.message.edit_text(text, reply_markup=inline.getKeyboard_selectPriceCurrency(), parse_mode='HTML')
            await call.answer()
        else:
            await not_reg(call)
    except Exception as ex:
        await error_message(call.message, ex)
        logger.exception(ex)
