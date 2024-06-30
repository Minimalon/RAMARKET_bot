import asyncio
import json
from datetime import timedelta
from decimal import Decimal

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile
from loguru import logger

from config import _, develope_mode
from core.database import query_db
from core.database.query_db import *
from core.keyboards.inline import *
from core.keyboards.reply import getKeyboard_registration
from core.loggers.bot_logger import BotLogger
from core.models_pydantic.order import Order
from core.oneC import utils as oneC_utils
from core.oneC.models import BankOrder
from core.oneC.utils import get_tovar_by_ID, get_pg_by_id
from core.utils import texts
from core.utils.callbackdata import *
from core.utils.qr import generateQR
from core.utils.states import StateCreateOrder


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


async def history_orders(call: CallbackQuery, bot: Bot):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f"История заказов")
    path_file = await query_db.create_excel(chat_id=str(call.message.chat.id))
    if not path_file:
        log.info('Список заказов пуст')
        await bot.send_message(call.message.chat.id, _('Список заказов пуст'))
        await bot.send_message(call.message.chat.id, "{menu}".format(menu=texts.menu), reply_markup=getKeyboard_start())
    else:
        log.info(f"Отправление истории заказов '{path_file}'")
        await bot.send_document(call.message.chat.id, document=FSInputFile(path_file), caption=_("История заказов"))
        await bot.send_message(call.message.chat.id, "{menu}".format(menu=texts.menu), reply_markup=getKeyboard_start())
        os.remove(path_file)


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
    await call.message.bot.send_message(call.message.chat.id, f'<b><u>Заказ удалён❌</u></b>\n<b>Номер заказа</b>: <code>{callback_data.order_id}</code>')
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
    data = await state.get_data()
    order = Order.model_validate_json(data['order'])
    if develope_mode:
        r = {"Ref": "1234567890", "Nomer": "1234567890"}
        order.payment.type = '2'
    else:
        r = await utils.create_order(order)
    for p in order.cart:
        await query_db.create_historyOrder(order_id=r['Nomer'],
                                           order=order, product=p),

    text = await texts.qr(r['Nomer'], order)
    if order.payment.type == '3':
        bankOrder = BankOrder.model_validate_json(json.dumps(r))
        bankOrder.add_sum(str(round(Decimal(order.sum_rub * 100), 0)))
        bankOrder.add_fio(order.client_name)
        textQR = bankOrder.create_order()
        qr_path = await generateQR(textQR, order.payment.type, r['Nomer'])
        await bot.send_photo(call.message.chat.id, FSInputFile(qr_path), caption=text,
                             reply_markup=getKeyboard_delete_order(r["Nomer"]))
    elif order.payment.type == '2':
        qr_path = await generateQR(r['Ref'], order.payment.type, r['Nomer'])
        await bot.send_photo(call.message.chat.id, FSInputFile(qr_path), caption=text,
                             reply_markup=getKeyboard_delete_order(r["Nomer"]))
    else:
        await call.message.edit_text(_("{text}").format(text=text),
                                     reply_markup=getKeyboard_delete_order(r["Nomer"]))
    log.success(f"Заказ под номером '{r['Nomer']}' успешно создан")
    await call.message.answer("{menu}".format(menu=texts.menu), reply_markup=getKeyboard_start())
    await state.clear()


if __name__ == '__main__':
    async def main():
        del_orders = [
            ['ФС00-000652', '202405060900'],
        ]
        for order_id, d in del_orders:
            date_order = datetime.strptime(d, '%Y%m%d%H%M')
            await oneC.delete_order(order_id, date_order.strftime('%d.%m.%Y %H:%M:%S'))
            await query_db.prepare_delete_history_order(order_id, date_order)


    asyncio.run(main())
