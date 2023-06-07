import re
from decimal import Decimal

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from config import _
from core.keyboards import inline
from core.keyboards.inline import getKeyboard_cart
from core.oneC import utils
from core.utils import texts
from core.utils.callbackdata import QuantityProduct
from core.utils.states import StateCreateOrder


async def error_message(message: Message, exception, state: FSMContext):
    text = f"{texts.error_head}{exception}"
    await message.answer(text)
    await state.set_state(StateCreateOrder.ERROR)


async def get_price(call: CallbackQuery, state: FSMContext, callback_data: QuantityProduct):
    await state.update_data(chat_id=call.message.chat.id, quantity=callback_data.quantity)
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
        order = await state.get_data()
        if order['currency'] == 'USD':
            sum_usd = Decimal(Decimal(price) * Decimal(order['quantity'])).quantize(Decimal('1.00'))
            sum_rub = Decimal(sum_usd * Decimal(order['currencyPrice'])).quantize(Decimal('1'))
        else:
            sum = Decimal(price) * Decimal(order['quantity'])
            sum_usd = Decimal(Decimal(sum) / Decimal(order['currencyPrice'])).quantize(Decimal('1.00'))
            sum_rub = Decimal(sum).quantize(Decimal('1'))

        log.info(f"Ввели цену '{str(price)}'")
        cart_oneC = order.get('cart_oneC')
        cart_bot = order.get('cart_bot')
        if not cart_oneC:
            cart_oneC = [{"Tov": order['product_id'], "Cost": price, "Kol": order['quantity'], 'Sum': str(sum_usd)}]
            cart_bot = [{"product_id": order['product_id'], "product_name": order['product_name'], "price": price,
                         "quantity": order['quantity'], 'sum_usd': str(sum_usd), 'sum_rub': str(sum_rub), 'currency_symbol': order['currency_symbol']}]
            await state.update_data(price=price, sum_usd=str(sum_usd), sum_rub=str(sum_rub), cart_oneC=cart_oneC, cart_bot=cart_bot)
        else:
            cart_oneC.append({"Tov": order['product_id'], "Cost": price, "Kol": order['quantity'], 'Sum': str(sum_usd)})
            cart_bot.append(
                {"product_id": order['product_id'], "product_name": order['product_name'], "price": price,
                 "quantity": order['quantity'], 'sum_usd': str(sum_usd), 'sum_rub': str(sum_rub), 'currency_symbol': order['currency_symbol']})
            sum_usd += Decimal(order['sum_usd'])
            sum_rub += Decimal(order['sum_rub'])
            await state.update_data(sum_usd=str(sum_usd), sum_rub=str(sum_rub), cart_oneC=cart_oneC, cart_bot=cart_bot)

        await message.answer(texts.cart(cart_bot), reply_markup=getKeyboard_cart())

    except Exception as ex:
        logger.exception(ex)
        await error_message(message, ex, state)


async def enter_client_name(call: CallbackQuery, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info('Продолжили создание заказа')
    await call.message.answer(_("Введите ФИО (полностью)"))
    await state.set_state(StateCreateOrder.GET_CLIENT_NAME)


async def check_client_name(message: Message, state: FSMContext):
    try:
        name = message.text
        if len(name.split()) == 3:
            await state.update_data(client_name=name)
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
            await state.update_data(client_phone=client_phone, client_mail='')
            await create_order(message, state)
        elif '@' in message.text:
            log.info(f"Ввели почту '{message.text}'")
            await state.update_data(client_mail=message.text, client_phone='')
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
        order = await state.get_data()
        payment_name = (await utils.get_payment_name(order['paymentGateway']))["Наименование"]
        await state.update_data(payment_name=payment_name)
        order = await state.get_data()
        logger.info(order)
        text = await texts.createOrder(order)
        await message.answer('{text}'.format(text=text), reply_markup=inline.getKeyboard_createOrder())
    except Exception as ex:
        logger.exception(ex)
        await error_message(message, ex, state)
