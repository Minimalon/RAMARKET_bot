import re
from decimal import Decimal

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

import core.database.query_db as query_db
from config import _
from core.keyboards import inline
from core.oneC import utils
from core.utils import texts
from core.utils.callbackdata import QuantityProduct
from core.utils.states import StateCreateOrder


async def error_message(message: Message, exception, state: FSMContext):
    text = f"{texts.error_head}{exception}"
    await message.answer(text)
    await state.set_state(StateCreateOrder.ERROR)


async def get_price(call: CallbackQuery, state: FSMContext, callback_data: QuantityProduct):
    await query_db.update_order(chat_id=call.message.chat.id, quantity=callback_data.quantity)
    await call.message.edit_text(_("Введите цену товара"))
    await state.set_state(StateCreateOrder.GET_PRICE)


async def check_price(message: Message, state: FSMContext):
    try:
        price = message.text
        log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id)
        if re.findall(',', message.text):
            if len(message.text.split(',')) > 2:
                await message.answer(texts.error_price_double_comma)
                await state.set_state(StateCreateOrder.GET_PRICE)
                return
            price = price.replace(',', '.')

        check_price = price.replace('.', '')
        if not check_price.isdecimal():
            await message.answer(texts.error_price_not_decimal)
            return
        order = await query_db.get_order_info(chat_id=message.chat.id)
        if order.currency == 'USD':
            sum_usd = Decimal(Decimal(price) * Decimal(order.quantity)).quantize(Decimal('1'))
            sum_rub = Decimal(sum_usd * Decimal(order.currencyPrice)).quantize(Decimal('1'))
        elif order.currency == 'RUB':
            sum = Decimal(price) * Decimal(order.quantity)
            sum_usd = Decimal(Decimal(sum) / Decimal(order.currencyPrice)).quantize(Decimal('1'))
            sum_rub = Decimal(sum).quantize(Decimal('1'))
        await query_db.update_order(chat_id=message.chat.id, price=price, sum_usd=sum_usd, sum_rub=sum_rub)
        log.info(f"Ввели цену '{str(price)}'")
        await message.answer(_("Введите ФИО (полностью)"))
        await state.set_state(StateCreateOrder.GET_CLIENT_NAME)
    except Exception as ex:
        logger.exception(ex)
        await error_message(message, ex, state)


async def get_client_name_CALLBACK(call: CallbackQuery, state: FSMContext):
    await call.message.answer(_("Введите ФИО (полностью)"))
    await state.set_state(StateCreateOrder.GET_CLIENT_NAME)


async def check_client_name(message: Message, state: FSMContext):
    try:
        name = message.text
        if len(name.split()) == 3:
            await query_db.update_order(chat_id=message.chat.id, client_name=name)
            await message.answer(_("Введите сотовый или почту клиента"))
            await state.set_state(StateCreateOrder.GET_CLIENT_PHONE_OR_MAIL)
        else:
            await message.answer('{text}'.format(text=texts.error_full_name(name)))
            logger.bind(name=message.chat.first_name, chat_id=message.chat.id, client_name=str(name)).info("Ввели ФИО")
            await state.set_state(StateCreateOrder.GET_CLIENT_NAME)
    except Exception as ex:
        logger.exception(ex)
        await error_message(message, ex, state)


async def check_client_phone_or_mail(message: Message, state: FSMContext):
    client_phone = ''.join(re.findall(r'[0-9]*', message.text))
    log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id)
    try:
        if re.findall('^[0-9]{1,11}$', client_phone):
            log.info(f"Ввели сотовый '{client_phone}'")
            await query_db.update_order(chat_id=message.chat.id, client_phone=client_phone, client_mail='')
            await create_order(message, state)
        elif '@' in message.text:
            log.info(f"Ввели почту '{message.text}'")
            await query_db.update_order(chat_id=message.chat.id, client_mail=message.text, client_phone='')
            await create_order(message, state)
        else:
            log.error(f"Ввод сотового или почты '{message.text}'")
            await message.answer(_("{error_head}Номер должен состоят максимум из 11 цифр\n"
                                   "Почта должна содержать знак <u><b>@</b></u>\n"
                                   "<b>Попробуйте снова.</b>").format(error_head=texts.error_head))
            await state.set_state(StateCreateOrder.GET_CLIENT_PHONE_OR_MAIL)
    except Exception as ex:
        log.exception(ex)
        await error_message(message, ex, state)


async def create_order(message: Message, state: FSMContext):
    try:
        chat_id = message.chat.id
        order = await query_db.get_order_info(chat_id=chat_id)
        currency_symbol = await query_db.get_currency_name(chat_id=chat_id)
        product_name = (await utils.get_tovar_by_ID(order.product_id))["Наименование"]
        payment_name = (await utils.get_payment_name(order.paymentGateway))["Наименование"]
        seller_phone = (await query_db.get_client_info(chat_id=chat_id)).phone_number
        shop_names = (await utils.get_shops(seller_phone))['Магазины']
        shop_name = [shop['Магазин'] for shop in shop_names if shop['idМагазин'] == order.shop][0]
        text = await texts.createOrder(client_name=order.client_name, client_phone=order.client_phone,
                                       shop_name=shop_name, payment_name=payment_name,
                                       currencyPrice=order.currencyPrice,
                                       price=order.price, sum_rub=order.sum_rub, sum_usd=order.sum_usd,
                                       client_mail=order.client_mail, currency=order.currency,
                                       product_name=product_name, currency_symbol=currency_symbol,
                                       quantity=order.quantity)
        await message.answer('{text}'.format(text=text), reply_markup=inline.getKeyboard_createOrder())
    except Exception as ex:
        logger.exception(ex)
        await error_message(message, ex, state)
