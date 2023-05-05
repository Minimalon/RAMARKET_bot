import re
from decimal import Decimal

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

import core.database.query_db as query_db
from core.keyboards.inline import getKeyboard_select_Main_PaymentGateway
from core.utils import texts
from core.utils.states import StateCreateOrder, StateCurrency


async def error_message(message: Message, exception, state: FSMContext):
    text = f"{texts.error_head}{exception}"
    await message.answer(text)
    await state.set_state(StateCreateOrder.ERROR)


async def get_CurrencyPrice(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Введите новый курс\nНапример: <b>75.127</b>", parse_mode="HTML")
    await call.answer()
    await state.set_state(StateCurrency.GET_PRICE)


async def check_CurrencyPrice(message: Message, state: FSMContext):
    try:
        if re.findall(',', message.text):
            if len(message.text.split(',')) > 2:
                text = f"{texts.error_head}Вы написали более 1 запятой. Попробуйте снова\nНапример: <b>75.12</b>"
                await message.answer(text, parse_mode='HTML')
                await state.set_state(StateCreateOrder.GET_PRICE)
                return
            currencyPrice = message.text.replace(',', '.')
        else:
            currencyPrice = message.text
        currencyPrice = Decimal(currencyPrice).quantize(Decimal('1.0000'))
        log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id, currencyPrice=str(currencyPrice))
        log.info("Ввели цену")
        log.info(Decimal(currencyPrice))
        await query_db.update_order(chat_id=message.chat.id, currencyPrice=Decimal(currencyPrice))
        await message.answer(texts.select_payment, reply_markup=await getKeyboard_select_Main_PaymentGateway(),
                             parse_mode='HTML')
        await state.clear()
    except Exception as ex:
        logger.exception(ex)
        await error_message(message, ex, state)
