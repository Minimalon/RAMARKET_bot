import re
from decimal import Decimal

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

import core.database.query_db as query_db
from config import _
from core.keyboards.inline import getKeyboard_select_Main_PaymentGateway
from core.utils import texts
from core.utils.states import StateCreateOrder, StateCurrency


async def error_message(message: Message, exception, state: FSMContext):
    text = f"{texts.error_head}{exception}"
    await message.answer(text)
    await state.set_state(StateCreateOrder.ERROR)


async def get_CurrencyPrice(call: CallbackQuery, state: FSMContext):
    await call.message.answer(_("Введите новый курс\nНапример: <b>75.127</b>"))
    await call.answer()
    await state.set_state(StateCurrency.GET_PRICE)


async def check_CurrencyPrice(message: Message, state: FSMContext):
    log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id)
    try:
        if re.findall(',', message.text):
            if len(message.text.split(',')) > 2:
                await message.answer(texts.error_price_double_comma)
                await state.set_state(StateCreateOrder.GET_PRICE)
                return
            currencyPrice = message.text.replace(',', '.')
        else:
            currencyPrice = message.text
        log.info(f"Ввели новую стоимость курса {currencyPrice}")
        currencyPrice = Decimal(currencyPrice).quantize(Decimal('1.0000'))
        await state.update_data(currencyPrice=str(currencyPrice))
        log.info(Decimal(currencyPrice))
        await message.answer(_('Выберите способ оплаты'), reply_markup=await getKeyboard_select_Main_PaymentGateway())
    except Exception as ex:
        logger.exception(ex)
        await error_message(message, ex, state)
