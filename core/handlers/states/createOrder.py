from decimal import Decimal
import re

from core.utils import texts
from core.utils.callbackdata import QuantityProduct
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from core.utils.states import StateCreateOrder
import core.database.query_db as query_db
from loguru import logger
from core.oneC import utils
from core.keyboards import inline


async def error_message(message: Message, exception, state: FSMContext):
    text = f"{texts.error_head}{exception}"
    await message.answer(text)
    await state.set_state(StateCreateOrder.ERROR)


async def get_price(call: CallbackQuery, state: FSMContext, callback_data: QuantityProduct):
    await query_db.update_order(chat_id=call.message.chat.id, quantity=callback_data.quantity)
    await call.message.edit_text("Введите цену товара")
    await state.set_state(StateCreateOrder.GET_PRICE)


async def check_price(message: Message, state: FSMContext):
    try:
        price = message.text
        if re.findall(',', message.text):
            if len(message.text.split(',')) > 2:
                text = f"{texts.error_head}Ввод цены разрешен через точку\nПример как надо: <b>10.12</b>"
                await message.answer(text, parse_mode='HTML')
                await state.set_state(StateCreateOrder.GET_PRICE)
                return
            price = price.replace(',', '.')

        check_price = price.replace('.', '')
        if not check_price.isdecimal():
            text = f"{texts.error_head}Цена содержит не нужные символы\nПопробуйте снова\nПример как надо: <u><b>10.12</b></u>"
            await message.answer(text, parse_mode='HTML')
            return
        order = await query_db.get_order_info(chat_id=message.chat.id)
        sum = Decimal(Decimal(price) * Decimal(order.quantity))
        sum_rub = Decimal(sum * Decimal(order.currencyPrice)).quantize(Decimal('1.00'))
        await query_db.update_order(chat_id=message.chat.id, price=price, sum=sum, sum_rub=sum_rub)
        log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id, price=str(price))
        log.info("Ввели цену")
        await message.answer("Введите ФИО (полностью)")
        await state.set_state(StateCreateOrder.GET_CLIENT_NAME)
    except Exception as ex:
        logger.exception(ex)
        await error_message(message, ex, state)


async def get_client_name_CALLBACK(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Введите ФИО (полностью)")
    await state.set_state(StateCreateOrder.GET_CLIENT_NAME)


async def check_client_name(message: Message, state: FSMContext):
    try:
        name = message.text
        if len(name.split()) == 3:
            await query_db.update_order(chat_id=message.chat.id, client_name=name)
            await message.answer(texts.enter_phone, parse_mode='HTML')
            await state.set_state(StateCreateOrder.GET_CLIENT_PHONE_OR_MAIL)
        else:
            text = f"{texts.error_head}ФИО состоит из 3 слов, а ваше состоит из {len(name.split())} слов\n" \
                   f"<b>Попробуйте снова.</b>"
            await message.answer(text, parse_mode='HTML')
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
            await message.answer(texts.error_needOnlyDigits, parse_mode="HTML")
            await state.set_state(StateCreateOrder.GET_CLIENT_PHONE_OR_MAIL)
    except Exception as ex:
        log.exception(ex)
        await error_message(message, ex, state)


async def create_order(message: Message, state: FSMContext):
    try:
        chat_id = message.chat.id
        order = await query_db.get_order_info(chat_id=chat_id)
        currency = await query_db.get_currency_name(chat_id=chat_id)
        product_name = (await utils.get_tovar_by_ID(order.product_id))["Наименование"]
        payment_name = (await utils.get_payment_name(order.paymentGateway))["Наименование"]
        seller_phone = (await query_db.get_client_info(chat_id=chat_id)).phone_number
        shop_names = (await utils.get_shops(seller_phone))['Магазины']
        shop_name = [shop['Магазин'] for shop in shop_names if shop['idМагазин'] == order.shop][0]
        text = await texts.createOrder(client_name=order.client_name, client_phone=order.client_phone,
                                       shop_name=shop_name, payment_name=payment_name,
                                       currencyPrice=order.currencyPrice,
                                       price=order.price, sum_rub=order.sum_rub, sum=order.sum,
                                       client_mail=order.client_mail,
                                       product_name=product_name, currency=currency, quantity=order.quantity)
        await message.answer(text, reply_markup=inline.getKeyboard_createOrder(), parse_mode="HTML")
    except Exception as ex:
        logger.exception(ex)
        await error_message(message, ex, state)
