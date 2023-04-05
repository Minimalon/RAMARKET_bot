from decimal import Decimal
import re
from core.utils.callbackdata import QuantityProduct
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from core.utils.states import StateCreateOrder
import core.database.query_db as query_db
from loguru import logger
from core.oneC import utils
from core.keyboards import inline


async def error_message(message: Message, exception, state: FSMContext):
    text = f"➖➖➖➖➖➖➖🚨ОШИБКА🚨➖➖➖➖➖➖➖\n" \
           f"{exception}"
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
                text = f"➖➖➖➖➖➖➖🚨ОШИБКА🚨➖➖➖➖➖➖➖\n" \
                       f"Ввод цены разрешен через точку\nПример как надо: <b>10.12</b>"
                await message.answer(text, parse_mode='HTML')
                await state.set_state(StateCreateOrder.GET_PRICE)
                return
            price = price.replace(',', '.')

        check_price = price.replace('.', '')
        if not check_price.isdecimal():
            text = f"➖➖➖➖➖➖➖🚨ОШИБКА🚨➖➖➖➖➖➖➖\n" \
                   f"Цена содержит не нужные символы\nПопробуйте снова\nПример как надо: <b>10.12</b>"
            await message.answer(text, parse_mode='HTML')
            return

        await query_db.update_order(chat_id=message.chat.id, price=Decimal(price))
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
            await message.answer("Введите сотовый клиента\nНапример: <code>79934055805</code>", parse_mode='HTML')
            await state.set_state(StateCreateOrder.GET_CLIENT_PHONE)
        else:
            text = f"➖➖➖➖➖➖➖🚨ОШИБКА🚨➖➖➖➖➖➖➖\n" \
                   f"ФИО состоит из 3 слов, а ваще состоит из {len(name.split())} слов\n" \
                   f"<b>Попробуйте снова.</b>"
            await message.answer(text)
            logger.bind(name=message.chat.first_name, chat_id=message.chat.id, client_name=str(name)).info("Ввели ФИО")
            await state.set_state(StateCreateOrder.GET_CLIENT_NAME)
    except Exception as ex:
        logger.exception(ex)
        await error_message(message, ex, state)


async def check_client_phone(message: Message, state: FSMContext):
    try:
        client_phone = ''.join(re.findall(r'[0-9]*', message.text))
        logger.bind(name=message.chat.first_name, chat_id=message.chat.id, client_phone=str(client_phone))
        if re.findall('[0-9]{11}', client_phone):
            logger.info("Ввели сотовый")
            await query_db.update_order(chat_id=message.chat.id, client_phone=client_phone)
            await create_order(message, state)
        else:
            logger.error("Ввели сотовый")
            text = ("Нужно ввести только цифры, номер должен состоят из 11 цифр\n"
                    "Например: <code>79934055805</code>\n"
                    "<b>Попробуйте снова.</b>")
            await message.answer(text, parse_mode="HTML")
            await state.set_state(StateCreateOrder.GET_CLIENT_PHONE)
    except Exception as ex:
        logger.exception(ex)
        await error_message(message, ex, state)


async def create_order(message: Message, state: FSMContext):
    try:
        chat_id = message.chat.id
        order = await query_db.get_order_info(chat_id=chat_id)
        price = Decimal(order.price).quantize(Decimal('1.00'))
        currency = await query_db.get_currency_name(chat_id=chat_id)
        product_name = (await utils.get_tovar_by_ID(order.product_id))["Наименование"]
        payment_name = (await utils.get_payment_name(order.paymentGateway))["Наименование"]
        seller_phone = (await query_db.get_client_info(chat_id=chat_id)).phone_number
        shop_names = (await utils.get_shops(seller_phone))['Магазины']
        shop_name = [shop['Магазин'] for shop in shop_names if shop['idМагазин'] == order.shop][0]
        sum_rub = Decimal((price * order.quantity) * order.currencyPrice).quantize(Decimal('1.00'))
        text = (f'ℹ️ <b>Информация о заказе:</b>\n'
                f'➖➖➖➖➖➖➖➖➖➖➖\n'
                f'<b>Имя клиента</b>: <code>{order.client_name}</code>\n'
                f'<b>Сотовый клиента</b>: <code>+{order.client_phone}</code>\n'
                f'<b>Название магазина</b>: <code>{shop_name}</code>\n'
                f'<b>Тип оплаты</b>: <code>{payment_name}</code>\n'
                f'<b>Курс валюты</b>: <code>{order.currencyPrice}</code>\n'
                f'<b>Название товара</b>: <code>{product_name}</code>\n'
                f'<b>Цена товара</b>: <code>{price} {currency}</code>\n'
                f'<b>Количество</b>: <code>{order.quantity}</code>\n'
                f'<b>Итого</b>: <code>{Decimal(price) * order.quantity} {currency} / {sum_rub} руб</code>')
        await message.answer(text, reply_markup=inline.getKeyboard_createOrder(), parse_mode="HTML")
    except Exception as ex:
        logger.exception(ex)
        await error_message(message, ex, state)
