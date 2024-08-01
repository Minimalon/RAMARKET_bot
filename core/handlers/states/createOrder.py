import re
from decimal import Decimal

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import _
from core.keyboards import inline
from core.keyboards.inline import getKeyboard_cart
from core.loggers.bot_logger import BotLogger
from core.models_pydantic.order import Order, Product
from core.utils import texts
from core.utils.callbackdata import QuantityProduct, Taxes
from core.utils.states import StateCreateOrder


async def error_message(message: Message, exception, state: FSMContext):
    text = f"{texts.error_head}{exception}"
    await message.answer(text)
    await state.set_state(StateCreateOrder.ERROR)


async def get_price(call: CallbackQuery, state: FSMContext, callback_data: QuantityProduct):
    data = await state.get_data()
    product = Product.model_validate_json(data['product'])
    product.quantity = callback_data.quantity
    await state.update_data(product=product.model_dump_json(by_alias=True))
    await call.message.edit_text(_("Введите цену товара"))
    await state.set_state(StateCreateOrder.GET_PRICE)


async def check_price(message: Message, state: FSMContext, log: BotLogger):
    price = message.text.replace(',', '.')
    if not price.replace('.', '').isdecimal():
        await message.answer(texts.error_price_not_decimal)
        return
    log.info(f"Ввели цену '{price}'")
    data = await state.get_data()
    product = Product.model_validate_json(data['product'])
    product.price = Decimal(price)
    order = Order.model_validate_json(data['order'])
    order.cart.append(product)
    order = await order.correct_order_sums()
    await state.update_data(order=order.model_dump_json(by_alias=True))
    await message.answer(texts.cart(order), reply_markup=getKeyboard_cart())


async def select_tax(call: CallbackQuery, state: FSMContext, log: BotLogger):
    log.button('Продолжить создание заказа')
    data = await state.get_data()
    order = Order.model_validate_json(data['order'])
    if order.rezident == 'Казахстан':
        await call.message.edit_text("Выберите налог",
                                     reply_markup=inline.kb_taxes())
    else:
        await call.message.edit_text(_("Введите ФИО (полностью)"))
        await state.set_state(StateCreateOrder.GET_CLIENT_NAME)


async def enter_client_name(call: CallbackQuery, state: FSMContext, callback_data: Taxes, log: BotLogger):
    log.info(f'Выбрали налог "{callback_data.tax}"')
    data = await state.get_data()
    order = Order.model_validate_json(data['order'])
    order.tax = callback_data.tax
    await state.update_data(order=order.model_dump_json(by_alias=True))
    await call.message.edit_text(_("Введите ФИО (полностью)"))
    await state.set_state(StateCreateOrder.GET_CLIENT_NAME)


async def check_client_name(message: Message, state: FSMContext, log: BotLogger):
    name = message.text
    log.info(f"Ввели ФИО '{name}'")
    if len(name.split()) == 3:
        data = await state.get_data()
        order = Order.model_validate_json(data['order'])
        order.client_name = name
        await state.update_data(order=order.model_dump_json(by_alias=True))
        await message.answer(_("Введите сотовый или почту клиента"))
        await state.set_state(StateCreateOrder.GET_CLIENT_PHONE_OR_MAIL)
    else:
        log.error(f"ФИО не из 3 слов '{name}'")
        await message.answer('{text}'.format(text=texts.error_full_name(name)))
        await state.set_state(StateCreateOrder.GET_CLIENT_NAME)


async def check_client_phone_or_mail(message: Message, state: FSMContext, log: BotLogger):
    client_phone = ''.join(re.findall(r'[0-9]*', message.text))
    data = await state.get_data()
    order = Order.model_validate_json(data['order'])
    if re.findall('^[0-9]{1,11}$', client_phone):
        order.client_phone = client_phone
        log.info(f"Ввели сотовый '{client_phone}'")
    elif '@' in message.text:
        order.client_mail = message.text
        log.info(f"Ввели почту '{message.text}'")
    else:
        log.error(f"Ввод сотового или почты '{message.text}'")
        await message.answer(_("{error_head}Номер должен состоят максимум из 11 цифр\n"
                               "Почта должна содержать знак <u><b>@</b></u>\n"
                               "<b>Попробуйте снова.</b>").format(error_head=texts.error_head))
        await state.set_state(StateCreateOrder.GET_CLIENT_PHONE_OR_MAIL)
    await state.update_data(order=order.model_dump_json(by_alias=True))
    if order.client_mail is not None or order.client_phone is not None:
        await create_order(message, state, log)


async def create_order(message: Message, state: FSMContext, log: BotLogger):
    log.info('Перешли к завершению чека')
    data = await state.get_data()
    order = Order.model_validate_json(data['order'])
    text = await texts.createOrder(order)
    await message.answer('{text}'.format(text=text), reply_markup=inline.getKeyboard_createOrder())
