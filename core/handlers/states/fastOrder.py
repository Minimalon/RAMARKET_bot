from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import _
from core.database import query_db
from core.database.query_db import create_fast_order
from core.keyboards import inline
from core.keyboards.inline import getKeyboard_selectCurrency, kb_rezident
from core.loggers.bot_logger import BotLogger
from core.middlewares.checkReg_ware import checkRegMessage
from core.models_pydantic.order import Order, CurrencyOrder, TelegramUser, FastOrderModel
from core.oneC import utils
from core.oneC.utils import get_shop_by_id
from core.utils import texts
from core.utils.callbackdata import Shop, Currency, CountryRezident
from core.utils.currencyes_cb import get_price_valute_by_one
from core.utils.states import FastOrderState

async def rezident(call: CallbackQuery, state: FSMContext, log: BotLogger):
    log.info(f'Быстрая продажа')
    if not checkRegMessage(call.message):
        await call.message.answer("Нет регистрации")
        return
    await call.message.edit_text("Резидентом какой страны является покупатель?",
                                 reply_markup=kb_rezident())
    await state.set_state(FastOrderState.rezident)

async def check_shops(call: CallbackQuery, state: FSMContext, log: BotLogger, callback_data: CountryRezident):
    client = await query_db.get_client_info(chat_id=call.message.chat.id)
    user = await utils.get_user_info(client.phone_number)
    tg_user = TelegramUser(
        user_id=call.message.from_user.id,
        chat_id=call.message.chat.id,
        is_bot=call.message.from_user.is_bot,
        first_name=call.message.from_user.first_name,
        last_name=call.message.from_user.last_name,
        username=call.message.from_user.username,
        language_code=call.message.from_user.language_code,
    )

    log.info(f'Количество магазинов "{len(user.shops)}"')
    if len(user.shops) == 1:
        shop = user.shops[0]
        if shop.currency == "TRY":
            shop.currencyPrice = round(shop.currencyPrice / 10, 4)
        order = FastOrderModel(user=user, shop=shop, tg_user=tg_user, rezident=callback_data.rezident)
    else:
        order = FastOrderModel(user=user, tg_user=tg_user, rezident=callback_data.rezident)
    await state.update_data(FastOrder=order.model_dump_json(by_alias=True))
    if len(user.shops) > 1:
        await state.set_state(FastOrderState.shop)
        await call.message.edit_text(_("Выберите магазин"), reply_markup=inline.getKeyboard_selectShop(user.shops))
    elif len(user.shops) == 0:
        log.error('Зарегано 0 магазинов')
        await call.message.answer(_("На вас не прикреплено ни одного магазина\nУточните вопрос и попробуйте снова"))
    elif len(user.shops) == 1:
        shop = user.shops[0]
        log.info(f'Выбран магазин "{shop.name}"')
        await state.set_state(FastOrderState.currency)
        await call.message.edit_text(_('Выберите валюту'), reply_markup=await getKeyboard_selectCurrency(order))

async def choise_currency(call: CallbackQuery, callback_data: Shop, state: FSMContext, log: BotLogger):
    shop = await get_shop_by_id(callback_data.id)
    log.info(f'Выбран магазин "{shop.name}"')
    if shop.currency == "TRY":
        shop.currencyPrice = round(shop.currencyPrice / 10, 4)
    data = await state.get_data()
    order = FastOrderModel.model_validate_json(data['FastOrder'])
    order.shop = shop
    await state.update_data(FastOrder=order.model_dump_json(by_alias=True))
    await state.set_state(FastOrderState.currency)
    await call.message.edit_text(_('Выберите валюту'), reply_markup=await getKeyboard_selectCurrency(order))

async def choise_currency_price(call: CallbackQuery, callback_data: Currency, state: FSMContext, log: BotLogger):
    log.info(f'Выбрана валюта "{callback_data.name}"')
    data = await state.get_data()
    order = FastOrderModel.model_validate_json(data['FastOrder'])
    if callback_data.name == 'KZT':
        order.currency = CurrencyOrder(
            name=callback_data.name,
            price=await get_price_valute_by_one('KZT')
        )
    else:
        order.currency = CurrencyOrder(
            name=callback_data.name,
            price=order.shop.currencyPrice
        )
    await state.update_data(FastOrder=order.model_dump_json(by_alias=True))
    await state.set_state(FastOrderState.sum)
    await call.message.edit_text(f'Ответным сообщением напишите итоговую сумму заказа\nПример: 322.12')


async def create_order(message: Message, state: FSMContext, log: BotLogger):
    log.info(f'Сумма заказа "{message.text}"')
    sum_order = message.text.replace(',', '.')
    if not sum_order.replace('.', '').isdecimal():
        await message.answer(texts.error_price_not_decimal)
        return
    data = await state.get_data()
    order = FastOrderModel.model_validate_json(data['FastOrder'])
    order.sum = float(sum_order)
    await create_fast_order(order)
    await message.answer(order.create_order_text())
    log.success('Быстрая продажа созданна')
    await state.clear()
