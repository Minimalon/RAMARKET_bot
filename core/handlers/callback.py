import asyncio
import random
from datetime import timedelta

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile
from loguru import logger

from config import _, develope_mode
from core.database import query_db
from core.database.query_db import *
from core.keyboards import inline
from core.keyboards.inline import *
from core.keyboards.reply import getKeyboard_registration
from core.loggers.bot_logger import BotLogger
from core.middlewares.checkReg_ware import checkRegMessage
from core.models_pydantic.order import Order
from core.oneC import utils as oneC_utils
from core.oneC.models import BankOrder, User
from core.oneC.utils import get_tovar_by_ID, get_pg_by_id
from core.utils import texts
from core.utils.callbackdata import *
from core.utils.history_orders import create_excel_by_agent_id
from core.utils.qr import generateQR
from core.utils.states import StateCreateOrder, StateWithdraw

api = Api()


async def not_reg(call: CallbackQuery):
    await call.message.delete()
    text = _('Вы зашли впервые, нажмите кнопку Регистрация')
    await call.message.answer(text, reply_markup=getKeyboard_registration())


async def menu(call: CallbackQuery, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    await state.clear()
    log.info("Меню")
    client_db = await query_db.get_client_info(chat_id=call.message.chat.id)
    if not client_db:
        await not_reg(call)
        return
    client_info = await oneC.get_client_info(client_db.phone_number)
    if client_info:
        await call.message.edit_text("{menu}".format(menu=texts.menu), reply_markup=getKeyboard_start())
    else:
        await not_reg(call)
        return


async def menu_not_edit_text(call: CallbackQuery, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    await state.clear()
    log.info("Меню")
    client_db = await query_db.get_client_info(chat_id=call.message.chat.id)
    if not client_db:
        await not_reg(call)
        return
    client_info = await oneC.get_client_info(client_db.phone_number)
    if client_info:

        await call.message.answer("{menu}".format(menu=texts.menu), reply_markup=getKeyboard_start())
    else:
        await not_reg(call)
        return


async def profile(call: CallbackQuery):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f"Личный кабинет")
    text = _("ℹ️ <b>Информация о вас:</b>\n"
             "➖➖➖➖➖➖➖➖➖➖➖\n"
             "<b>💳 ID:</b> <code>{chat_id}</code>").format(
        chat_id=call.message.chat.id)
    await call.message.edit_text(text, reply_markup=getKeyboard_profile())


async def select_change_language(call: CallbackQuery):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f"Изменить язык")
    await call.message.edit_text(_('Выберите язык'), reply_markup=getKeyboard_change_language())


async def change_language(call: CallbackQuery, callback_data: ChangeLanguage):
    language = callback_data.language
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f"Изменили язык интерфейса на '{language}'")
    await update_client_language(str(call.message.chat.id), language)
    await call.message.edit_text("{menu}".format(menu=texts.menu_new_language(language)),
                                 reply_markup=getKeyboard_start(language))


async def history_orders(call: CallbackQuery):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f"История заказов")
    await call.message.edit_text(_("Выберите промежуток времени"), reply_markup=kb_historyOrders_by_days())

async def select_historyOrders_days(call: CallbackQuery, callback_data: HistoryOrderDays):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f"Выбрали дни {callback_data.days}")
    db_user = await query_db.get_client_info(chat_id=call.message.chat.id)
    user = User(**(await oneC.get_client_info(db_user.phone_number)))
    if callback_data.days < 0:
        start_date = datetime.strftime(datetime.now() - timedelta(days=1 + abs(callback_data.days)), '%Y-%m-%d')
        end_date = datetime.strftime(datetime.now() - timedelta(days=1), '%Y-%m-%d')
    else:
        start_date = datetime.strftime(datetime.now() - timedelta(days=callback_data.days), '%Y-%m-%d')
        end_date = datetime.strftime(datetime.now() + timedelta(days=1), '%Y-%m-%d')

    path = await create_excel_by_agent_id(user.id, f"{'_'.join(user.name.split())}__{callback_data.days}days", start_date=start_date, end_date=end_date)
    if path:
        await call.message.bot.send_document(call.message.chat.id, document=FSInputFile(path))
    else:
        log.error(
            f"Нет продаж за данный период времени")
        await call.message.answer(
            texts.error_head + 'Нет продаж за данный период времени')

async def selectMainPaymentGateway(call: CallbackQuery, log: BotLogger):
    log.button(f"Продолжить")
    await call.message.edit_text(_('Выберите способ оплаты'),
                                 reply_markup=await getKeyboard_select_Main_PaymentGateway())


async def selectChildPaymentGateway(call: CallbackQuery, callback_data: ChildPaymentGateway, state: FSMContext,
                                    log: BotLogger):
    data = await state.get_data()
    order = Order.model_validate_json(data['order'])
    pay = await oneC_utils.get_paymentWay_by_id(callback_data.id)
    if pay is not None:
        order.payment = pay
        log.info(f'Выбрали способ оплаты "{pay.name}"')
    await state.update_data(order=order.model_dump_json(by_alias=True))
    await call.message.edit_reply_markup(reply_markup=await getKeyboard_select_Child_PaymentGateway(pay))


async def select_prev_page_catalog(call: CallbackQuery, log: BotLogger):
    log.button(f"Назад на способ выбора товара")
    await call.message.edit_text(_('Выберите способ выбора товара'), reply_markup=getKeyboard_ProductStart())


async def show_catalog(call: CallbackQuery, log: BotLogger):
    log.button(f"Каталог")
    await call.message.edit_text(_("Cписок категорий товара"), reply_markup=await getKeyboard_catalog())


async def show_child_categories(call: CallbackQuery, callback_data: Category, log: BotLogger):
    pg = await get_pg_by_id(callback_data.id)
    log.info(f"Выбрали категорию '{pg.name}'")
    markup = await getKeyboard_products_or_categories(pg)
    if markup.inline_keyboard[0][0].callback_data.startswith('product'):
        log.info('Выбирают товар')
        await call.message.edit_text(_("Выберите товар"), reply_markup=markup)
    if markup.inline_keyboard[0][0].callback_data.startswith('category'):
        log.info('Выбирают подкатегорию')
        await call.message.edit_text(_("Cписок подкатегорий"), reply_markup=markup)


async def select_quantity_product(call: CallbackQuery, callback_data: Tovar, state: FSMContext, log: BotLogger):
    product = await get_tovar_by_ID(callback_data.product_id)
    log.info(f'Выбрали товар {product.name}')
    await state.update_data(product=product.model_dump_json(by_alias=True))
    log.info("Выбирает количество товара")
    await state.set_state(StateCreateOrder.SELECT_QUANTITY)
    await call.message.edit_text(_("Выберите количество товара"), reply_markup=getKeyboard_quantity_product())


async def update_quantity_product(call: CallbackQuery, callback_data: QuantityUpdate, log: BotLogger):
    log.info(f'Поменяли количество на "{callback_data.quantity}"')
    await call.message.edit_reply_markup(reply_markup=getKeyboard_quantity_update(callback_data.quantity))


async def delete_order(call: CallbackQuery, callback_data: DeleteOrder, log: BotLogger):
    date_order = datetime.strptime(callback_data.date, '%Y%m%d%H%M')
    if not config.develope_mode:
        await oneC.delete_order(callback_data.order_id, date_order.strftime('%d.%m.%Y %H:%M:%S'))
    await query_db.prepare_delete_history_order(callback_data.order_id, date_order)
    await query_db.delete_document(callback_data.order_id, date_order)
    await call.message.bot.send_message(
        chat_id=call.message.chat.id,
        text=f'<b><u>Заказ удалён❌</u></b>\n<b>Номер заказа</b>: <code>{callback_data.order_id}</code>')
    log.success(f'Удалили заказ {callback_data.order_id}')
    # if date_order + timedelta(days=1) > datetime(day=d_now.day, month=d_now.month, year=d_now.year, hour=10, minute=30):
    #     await oneC.delete_order(callback_data.order_id, date_order.strftime('%d.%m.%Y %H:%M:%S'))
    #     await query_db.delete_history_order(callback_data.order_id)
    #     await call.message.answer(_(f'<b><u>Заказ удалён❌</u></b>\n<b>Номер заказа</b>: <code>{callback_data.order_id}</code>'))
    #     log.success(f'Удалили заказ {callback_data.order_id}')
    # else:
    #     log.error(f"Пытались удалить старый заказ {callback_data.order_id}")
    #     await call.message.answer(_("{text}Заказ слишком старый для удаления".format(text=texts.error_head)))


async def create_order(call: CallbackQuery, bot: Bot, state: FSMContext, log: BotLogger):
    log.button('Создать заказ')
    await call.message.edit_text("Загрузка...")
    if not checkRegMessage(call.message):
        await call.message.answer("Нет регистрации")
        return
    data = await state.get_data()
    order = Order.model_validate_json(data['order'])
    if develope_mode:
        r = {"Ref": "1234567890", "Nomer": "1234567890"}
        order.payment.type = '2'
        order.order_id = str(random.randint(1000000000, 9999999999))
    else:
        r = await utils.create_order(order)
        order.order_id = r["Nomer"]
    log.debug(order.model_dump_json())
    for product in order.cart:
        await query_db.create_historyOrders(order_id=order.order_id, order=order, product=product)
    await query_db.create_document(order=order)

    text = await texts.qr(r['Nomer'], order)

    if r.get('ORG') is not None:
        bankOrder = BankOrder.model_validate_json(json.dumps(r))
        bankOrder.add_sum(str(round(Decimal(order.sum_rub * 100), 0)))
        bankOrder.add_fio(order.client_name)
        textQR = bankOrder.create_order()
        qr_path = await generateQR(textQR, order.payment.type, r['Nomer'])
        await bot.send_photo(call.message.chat.id, FSInputFile(qr_path), caption=text,
                             reply_markup=getKeyboard_delete_order(r["Nomer"]))
    elif r.get('Ref') is not None:
        qr_path = await generateQR(r['Ref'], order.payment.type, r['Nomer'])
        await bot.send_photo(call.message.chat.id, FSInputFile(qr_path), caption=text,
                             reply_markup=getKeyboard_delete_order(r["Nomer"]))
    else:
        await call.message.edit_text(_("{text}").format(text=text),
                                     reply_markup=getKeyboard_delete_order(r["Nomer"]))
    log.success(f"Заказ под номером '{r['Nomer']}' успешно создан")
    await call.message.answer("{menu}".format(menu=texts.menu), reply_markup=getKeyboard_start())
    await state.clear()

async def start_withdraw(call: CallbackQuery, state: FSMContext, log: BotLogger):
    log.button('Выдача наличных')
    db_user = await query_db.get_client_info(chat_id=call.message.chat.id)
    user = await utils.get_user_info(db_user.phone_number)
    log.debug(user.model_dump_json())
    await state.update_data(user_info=user.model_dump_json(by_alias=True))
    await state.set_state(StateWithdraw.select_shop)
    await call.message.edit_text('Выберите магазин', reply_markup=inline.getKeyboard_selectShop(user.shops))

async def withdraw_select_shop(call: CallbackQuery, state: FSMContext, log: BotLogger, callback_data: Shop):
    log.info(f'Выбрали магазин {callback_data.id}')
    data = await state.get_data()
    user = User.model_validate_json(data['user_info'])
    await state.set_state(StateWithdraw.select_currency)
    await state.update_data(withdraw_shop=callback_data.id)
    await call.message.edit_text('Выберите валюту', reply_markup=inline.kb_demo_currency(user))

async def withdraw_select_currency(call: CallbackQuery, state: FSMContext, log: BotLogger, callback_data: Currency):
    log.info(f'Выбрали валюту {callback_data.name}')
    await state.set_state(StateWithdraw.enter_sum)
    await state.update_data(withdraw_currency=callback_data.name)
    await call.message.answer('Введите сумму')

async def withdraw_enter_sum(message: Message, state: FSMContext, log: BotLogger):
    log.info(f'Ввели сумму {message.text}')
    try:
        withdraw_sum = float(message.text)
    except ValueError:
        log.error(f'Ввели некорректную сумму {message.text}')
        await message.answer('Введите корректную сумму')
        return
    data = await state.get_data()
    user = User.model_validate_json(data['user_info'])
    await state.set_state(StateWithdraw.show_info)
    await state.update_data(withdraw_sum=withdraw_sum)
    shop = await utils.get_shop_by_id(data['withdraw_shop'])
    try:
        shop_balance = await api.get_balance_shop(shop.id)
    except IndexError:
        log.error('Нужно сперва создать остаток магазина')
        await message.answer('Нужно сперва создать остаток магазина')
        return
    txt = (
        f'Ответственный: {user.name}\n\n'
        f'Магазин: {shop.name}\n'
        f'Валюта: {data["withdraw_currency"]}\n'
        f'Сумма: {withdraw_sum}\n\n'
        f'Текущий баланс магазина: {shop_balance.balance} {shop_balance.currency}\n'
    )
    await message.answer(txt, reply_markup=inline.kb_withdraw())

async def withdraw_confirm(call: CallbackQuery, state: FSMContext, log: BotLogger):
    log.info('Подтвердили выдачу наличных')
    data = await state.get_data()
    await state.clear()
    user = User.model_validate_json(data['user_info'])
    shop = await utils.get_shop_by_id(data['withdraw_shop'])
    await api.create_rko(shop.id, data['withdraw_sum'], user.id, data['withdraw_currency'], str(shop.currencyPrice))
    txt = (
        f'Выдача наличных завершена✅\n'
        f'Ответственный: {user.name}\n\n'
        f'Магазин: {shop.name}\n'
        f'Валюта: {data["withdraw_currency"]}\n'
        f'Сумма: {data["withdraw_sum"]}\n'
    )
    await call.message.edit_text(txt)
