from decimal import Decimal
from aiogram import Bot
from aiogram.types import CallbackQuery, FSInputFile
from core.database import query_db
from core.database.query_db import *
from core.keyboards.inline import *
from core.keyboards.reply import getKeyboard_registration
from core.oneC.api import Api
from core.utils import texts
from core.utils.callbackdata import *
from core.utils.qr import generateQR

oneC = Api()


async def not_reg(call: CallbackQuery):
    await call.message.delete()
    text = f'Вы зашли впервые, нажмите кнопку Регистрация'
    await call.message.answer(text, reply_markup=getKeyboard_registration(), parse_mode='HTML')


async def menu(call: CallbackQuery):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info("Меню")
    client_db = await query_db.get_client_info(chat_id=call.message.chat.id)
    if not client_db:
        await not_reg(call)
        return
    client_info = await oneC.get_client_info(client_db.phone_number)
    if client_info:
        await call.message.edit_text(texts.menu, reply_markup=getKeyboard_start(), parse_mode='HTML')
    else:
        await not_reg(call)
        return


async def menu_not_edit_text(call: CallbackQuery):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info("Меню")
    client_db = await query_db.get_client_info(chat_id=call.message.chat.id)
    if not client_db:
        await not_reg(call)
        return
    client_info = await oneC.get_client_info(client_db.phone_number)
    if client_info:

        await call.message.answer(texts.menu, reply_markup=getKeyboard_start(), parse_mode='HTML')
    else:
        await not_reg(call)
        return


async def profile(call: CallbackQuery):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f"Личный кабинет")
    client_info = await query_db.get_client_info(chat_id=call.message.chat.id)
    client_by_oneC = await oneC.get_client_info(client_info.phone_number)
    text = (f"ℹ️ <b>Информация о вас:</b>\n"
            f"➖➖➖➖➖➖➖➖➖➖➖\n"
            f"<b>💳 ID:</b> <code>{call.message.chat.id}</code>\n"
            f"<b>Валюта:</b> <code>{client_by_oneC['Валюта']}</code>\n"
            f"<b>Курс валюты:</b> <code>{client_by_oneC['ВалютаКурс']}</code>")
    await call.message.edit_text(text, reply_markup=getKeyboard_profile(), parse_mode='HTML')


async def history_orders(call: CallbackQuery, bot: Bot):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f"История заказов")
    path_file = await query_db.create_excel(chat_id=call.message.chat.id)
    if not path_file:
        await bot.send_message(call.message.chat.id, 'Список заказов пуст')
        await bot.send_message(call.message.chat.id, texts.menu, reply_markup=getKeyboard_start(), parse_mode='HTML')
    await bot.send_document(call.message.chat.id, document=FSInputFile(path_file), caption="История заказов")
    await bot.send_message(call.message.chat.id, texts.menu, reply_markup=getKeyboard_start(), parse_mode='HTML')
    os.remove(path_file)


async def selectMainPaymentGateway(call: CallbackQuery):
    order = await query_db.get_order_info(chat_id=call.message.chat.id)
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id,
                      currencyPrice=order.currencyPrice)
    log.info(f"Переход на способ оплаты")
    await update_order(chat_id=call.message.chat.id, first_name=call.message.chat.first_name)
    await call.message.edit_text(texts.select_payment, reply_markup=await getKeyboard_select_Main_PaymentGateway())
    await call.answer()


async def selectChildPaymentGateway(call: CallbackQuery, callback_data: ChildPaymentGateway):
    await update_order(chat_id=call.message.chat.id, paymentGateway=callback_data.id, paymentType=callback_data.type)
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id, paymentID=callback_data.id)
    log.info(f"Выбор способа оплаты")
    await call.message.edit_reply_markup(
        reply_markup=await getKeyboard_select_Child_PaymentGateway(callback_data.id, callback_data.idParent))
    await call.answer()


async def select_input_method_Product(call: CallbackQuery, callback_data: PaymentGateway):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id, payment=callback_data.id)
    log.info(f"Выбрали тип оплаты")
    await update_order(chat_id=call.message.chat.id, paymentGateway=callback_data.id)
    await call.message.edit_text("Выберите способ выбора товара", reply_markup=getKeyboard_ProductStart())
    await call.answer()


async def select_prev_page_catalog(call: CallbackQuery):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f"Назад на способ выбора товара")
    await call.message.edit_text("Выберите способ выбора товара", reply_markup=getKeyboard_ProductStart())
    await call.answer()


async def show_catalog(call: CallbackQuery):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f"Нажали кнопку 'Каталог'")
    await call.message.edit_text("Cписок категорий товара", reply_markup=await getKeyboard_catalog())
    await call.answer()


async def show_childcategories(call: CallbackQuery, callback_data: Category):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id, group_id=callback_data.id,
                      parent_id=callback_data.parent_id)
    log.info(f"Выбрали категорию '{callback_data.id}'")
    markup = await getKeyboard_products_or_categories(callback_data.id, callback_data.parent_id)
    if markup.inline_keyboard[0][0].callback_data.startswith('product'):
        log.info('Выбирают товар')
        await call.message.edit_text("Выберите товар", reply_markup=markup)
        await call.answer()
    if markup.inline_keyboard[0][0].callback_data.startswith('category'):
        log.info('Выбирают подкатегорию')
        await call.message.edit_text("Cписок подкатегорий", reply_markup=markup)
        await call.answer()


async def select_quantity_product(call: CallbackQuery, callback_data: Product):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id,
                      product_id=callback_data.product_id)
    log.info(f"Выбрали товар")
    await query_db.update_order(chat_id=call.message.chat.id, product_id=callback_data.product_id)
    log.info("Выбирает количество товара")
    await call.message.edit_text("Выберите количество товара", reply_markup=getKeyboard_quantity_product())
    await call.answer()


async def update_quantity_product(call: CallbackQuery, callback_data: QuantityUpdate):
    quantity = callback_data.quantity
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id, quantity=quantity)
    log.info(f"Поменяли количество")
    await call.message.edit_reply_markup(reply_markup=getKeyboard_quantity_update(quantity))
    await call.answer()


async def create_order(call: CallbackQuery, bot: Bot):
    chat_id = call.message.chat.id
    log = logger.bind(name=call.message.chat.first_name, chat_id=chat_id)
    client_db = await query_db.get_client_info(chat_id=chat_id)
    order = await query_db.get_order_info(chat_id=chat_id)

    if not order:
        await call.message.delete()
        await call.message.answer(f'{texts.error_head}Не найдено заказа\nПопробуйте снова создать заказ.')
        await bot.send_message(chat_id, texts.menu, reply_markup=getKeyboard_start())
    if not client_db:
        await not_reg(call)
        return
    client_info = await oneC.get_client_info(client_db.phone_number)
    if not client_info:
        await not_reg(call)
        return
    response, answer = await utils.create_order(bot, chat_id=order.chat_id, first_name=order.first_name,
                                                paymentGateway=order.paymentGateway, paymentType=order.paymentType,
                                                product_id=order.product_id,
                                                price=order.price, quantity=order.quantity,
                                                currency=order.currency,
                                                currencyPrice=order.currencyPrice, client_name=order.client_name,
                                                client_phone=order.client_phone, client_mail=order.client_mail,
                                                shop=order.shop,
                                                seller_id=order.seller_id, sum_rub=order.sum_rub, sum=order.sum)
    if response.ok:
        if order.paymentType == '3':
            s_name, f_name, patronymic = order.client_name.split()
            textQR = (f'ST00012|Name={answer["ORG"]}'
                      f'|PersonalAcc={answer["BS"]}|BankName={answer["Bank"]}'
                      f'|BIC={answer["BIC"]}|CorrespAcc={answer["KBS"]}|PayeeINN={answer["ORGINN"]}'
                      f'|KPP={answer["ORGKPP"]}|LastName={s_name}|FirstName={f_name}|MiddleName={patronymic}'
                      f'|Purpose=Оплата заказа №{answer["Nomer"]} от {answer["Date"]}'
                      f'|Sum={round(Decimal(order.sum_rub) * 100)}')
            qr_path = await generateQR(textQR, order.paymentType, answer['Nomer'])
            log.info(f"Заказ под номером '{answer['Nomer']}' успешно создан")
            text = await texts.qr(answer['Nomer'], order.sum, chat_id, order.sum_rub)
            await call.message.delete()
            await bot.send_photo(chat_id, FSInputFile(qr_path), caption=text, parse_mode='HTML')
            await query_db.delete_order(chat_id=chat_id)
        elif order.paymentType == '2':
            textQR = answer['Ref']
            qr_path = await generateQR(textQR, order.paymentType, answer['Nomer'])
            log.info(f"Заказ под номером '{answer['Nomer']}' успешно создан")
            text = await texts.qr(answer['Nomer'], order.sum, chat_id, order.sum_rub)
            await call.message.delete()
            await bot.send_photo(chat_id, FSInputFile(qr_path), caption=text, parse_mode='HTML')
            await query_db.delete_order(chat_id=chat_id)
        else:
            log.info(f"Заказ под номером '{answer['Nomer']}' успешно создан")
            await call.message.delete()
            text = await texts.qr(answer['Nomer'], order.sum, chat_id, order.sum_rub)
            await bot.send_message(chat_id, f"<b><u>Заказ успешно создан</u></b>\n{text}", parse_mode='HTML')
            await query_db.delete_order(chat_id=chat_id)
    else:
        await call.message.answer(
            f"{texts.error_head}Сервер недоступен, его код ответа '{response.status}'\nПопробуйте создать заказ снова.")
        log.info(f"Сервер недоступен, его код ответа '{response.status}'")

    await bot.send_message(chat_id, texts.menu, reply_markup=getKeyboard_start(), parse_mode='HTML')
