import re
from decimal import Decimal

import aiogram.exceptions
from aiogram.types import CallbackQuery, Message
from loguru import logger

from config import _
from core.database import query_db
from core.keyboards import inline, reply
from core.keyboards.inline import getKeyboard_selectCurrency
from core.oneC import utils
from core.oneC.api import Api
from core.utils import texts
from core.utils.callbackdata import Shop, Currency

oneC = Api()


async def error_message(message: Message, exception):
    text = f"{texts.error_head}{exception}"
    await message.answer(text)


async def not_reg(call: CallbackQuery):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    try:
        await call.message.delete()
    except aiogram.exceptions.TelegramBadRequest:
        log.error('TelegramBadRequest (сообщению больше 24 часов и его нельзя удалить)')
        pass
    text = _('Вы зашли впервые, нажмите кнопку Регистрация')
    await call.message.answer(text, reply_markup=reply.getKeyboard_registration())


async def check_shops(call: CallbackQuery):
    try:
        log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
        client = await query_db.get_client_info(chat_id=call.message.chat.id)
        if not client:
            await not_reg(call)
            return
        shop = await utils.get_shops(client.phone_number)
        log.info(f'Количество магазинов "{len(shop["Магазины"])}"')
        await query_db.update_order(chat_id=call.message.chat.id)
        if len(shop['Магазины']) > 1:
            await query_db.update_order(chat_id=call.message.chat.id, seller_id=shop['id'])
            await call.message.edit_text(_("Выберите магазин"),
                                         reply_markup=inline.getKeyboard_selectShop(shop['Магазины']))
        elif len(shop['Магазины']) == 0:
            log.error('Зарегано 0 магазинов')
            await call.message.answer(_("На вас не прикреплено ни одного магазина\nУточните вопрос и попробуйте снова"))
        else:
            await query_db.update_order(chat_id=call.message.chat.id, shop=str(shop['Магазины'][0]['idМагазин']),
                                        seller_id=shop['id'], shop_currency=shop['Магазины'][0]['Валюта'],
                                        currencyPrice=shop['Магазины'][0]['ВалютаКурс'])
            await call.message.edit_text(_('Выберите валюту'), reply_markup=getKeyboard_selectCurrency())
    except Exception as ex:
        await error_message(call.message, ex)
        logger.exception(ex)


async def choise_currency(call: CallbackQuery, callback_data: Shop):
    await query_db.update_order(chat_id=call.message.chat.id, shop=callback_data.shop,
                                shop_currency=callback_data.currency, currencyPrice=callback_data.price)
    await call.message.edit_text(_('Выберите валюту'), reply_markup=getKeyboard_selectCurrency())


async def choise_currency_price(call: CallbackQuery, callback_data: Currency):
    try:
        client_DB = await query_db.get_client_info(chat_id=call.message.chat.id)
        if not client_DB:
            await not_reg(call)
            return
        client = await oneC.get_client_info(client_DB.phone_number)
        if client:
            order = await query_db.get_order_info(chat_id=call.message.chat.id)
            currency_price = order.currencyPrice
            if re.findall(',', currency_price):
                currency_price = currency_price.replace(",", '.')
            else:
                currency_price = currency_price
            currency_price = Decimal(currency_price).quantize(Decimal('1.0000'))
            await query_db.update_order(chat_id=call.message.chat.id, currencyPrice=currency_price,
                                        currency=callback_data.currency)
            text = _('Фактический курс: <code>{currency_price}</code>').format(currency_price=currency_price)
            await call.message.edit_text(text, reply_markup=inline.getKeyboard_selectPriceCurrency())
            await call.answer()
        else:
            await not_reg(call)
            return
    except Exception as ex:
        await error_message(call.message, ex)
        logger.exception(ex)
