from decimal import Decimal

import aiogram.exceptions
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from config import _
from core.database import query_db
from core.keyboards import inline, reply
from core.keyboards.inline import getKeyboard_selectCurrency
from core.oneC import utils
from core.oneC.api import Api
from core.oneC.utils import get_shop_by_id
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


async def check_shops(call: CallbackQuery, state: FSMContext):
    try:
        log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)

        client = await query_db.get_client_info(chat_id=call.message.chat.id)
        if not client:
            await not_reg(call)
            return
        client_info = await oneC.get_client_info(client.phone_number)
        if not client_info:
            await not_reg(call)
            return
        shop = await utils.get_shops(client.phone_number)
        await state.update_data(agent_name=shop['Наименование'], agent_id=shop['id'])
        log.info(f'Количество магазинов "{len(shop["Магазины"])}"')
        await state.update_data(chat_id=str(call.message.chat.id))
        if len(shop['Магазины']) > 1:
            await call.message.edit_text(_("Выберите магазин"), reply_markup=inline.getKeyboard_selectShop(shop['Магазины']))
        elif len(shop['Магазины']) == 0:
            log.error('Зарегано 0 магазинов')
            await call.message.answer(_("На вас не прикреплено ни одного магазина\nУточните вопрос и попробуйте снова"))
        else:
            shop = shop['Магазины'][0]
            await state.update_data(shop_id=str(shop['idМагазин']), shop_currency=shop['Валюта'], shop_name=shop['Магазин'],
                                    currencyPrice=''.join(str(shop['ВалютаКурс']).split()), country_code=shop['КодСтраны'],
                                    country_name=shop['Страна'], city_code=shop['КодГород'], city_name=shop['Город'])
            await call.message.edit_text(_('Выберите валюту'), reply_markup=getKeyboard_selectCurrency())
    except Exception as ex:
        await error_message(call.message, ex)
        logger.exception(ex)


async def choise_currency(call: CallbackQuery, callback_data: Shop, state: FSMContext):
    shop = await get_shop_by_id(callback_data.id)
    await state.update_data(shop_name=shop.name, shop_id=shop.id, shop_currency=shop.currency, currencyPrice=shop.currency_price, country_name=shop.country,
                            country_code=shop.country_code, city_name=shop.city, city_code=shop.city_code)
    await call.message.edit_text(_('Выберите валюту'), reply_markup=getKeyboard_selectCurrency())


async def choise_currency_price(call: CallbackQuery, callback_data: Currency, state: FSMContext):
    try:
        client_DB = await query_db.get_client_info(chat_id=call.message.chat.id)
        if not client_DB:
            await not_reg(call)
            return
        client = await oneC.get_client_info(client_DB.phone_number)
        if client:
            order = await state.get_data()
            currency_price = order['currencyPrice']
            if ',' in currency_price:
                currency_price = currency_price.replace(",", '.')
            else:
                currency_price = currency_price
            currency_price = Decimal(currency_price).quantize(Decimal('1.0000'))
            currency_symbol = '$' if callback_data.currency == 'USD' else '₽'
            await state.update_data(currencyPrice=str(currency_price), currency=callback_data.currency, currency_symbol=currency_symbol)
            text = _('Фактический курс: <code>{currency_price}</code>').format(currency_price=currency_price)
            await call.message.edit_text(text, reply_markup=inline.getKeyboard_selectPriceCurrency())
            await call.answer()
        else:
            await not_reg(call)
            return
    except Exception as ex:
        await error_message(call.message, ex)
        logger.exception(ex)
