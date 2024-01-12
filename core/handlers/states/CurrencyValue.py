import re

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from config import _
from core.keyboards.inline import getKeyboard_select_Main_PaymentGateway
from core.models_pydantic.order import Order
from core.utils import texts
from core.utils.states import StateCreateOrder, StateCurrency


async def get_CurrencyPrice(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(_("Введите новый курс\nНапример: <b>75.127</b>"))
    await state.set_state(StateCurrency.GET_PRICE)


async def check_CurrencyPrice(message: Message, state: FSMContext, log: logger):
    data = await state.get_data()
    if re.findall(',', message.text):
        if len(message.text.split(',')) > 2:
            await message.answer(texts.error_price_double_comma)
            await state.set_state(StateCreateOrder.GET_PRICE)
            return
        currencyPrice = message.text.replace(',', '.')
    else:
        currencyPrice = message.text
    log.info(f"Ввели новую стоимость курса {currencyPrice}")
    order = Order.model_validate_json(data['order'])
    order.currency.price = currencyPrice
    await state.update_data(order=order.model_dump_json(by_alias=True))
    await message.answer(_('Выберите способ оплаты'), reply_markup=await getKeyboard_select_Main_PaymentGateway())
