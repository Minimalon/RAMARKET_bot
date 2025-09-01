#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-
import asyncio
import os

import aiogram.exceptions
from aiogram import Dispatcher, F
from aiogram.filters import Command, ExceptionTypeFilter
from aiogram.fsm.storage.redis import RedisStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pydantic import ValidationError

import config
from core.cron.google_stats import update_google_sheets
from core.filters.iscontact import IsTrueContact
from core.handlers import contact
from core.handlers import errors_handlers
from core.handlers.basic import get_start, check_registration
from core.handlers.callback import *
from core.handlers.states import enterArticle, CurrencyValue, createOrder, choiseShop
from core.loggers.make_loggers import create_loggers
from core.middlewares.checkReg_ware import CheckRegistrationMessageMiddleware, CheckRegistrationCallbackMiddleware
from core.middlewares.language_middleware import ACLMiddleware
from core.middlewares.logger_ware import CallBackMiddleware, MessageMiddleware
from core.utils.callbackdata import *
from core.utils.commands import get_commands
from core.utils.states import StateCreateOrder, StateCurrency, StateEnterArticle


@logger.catch()
async def start():
    await create_loggers()
    bot = Bot(token=config.token, parse_mode='HTML')
    # if not config.develope_mode:
    #     await bot.send_message(5263751490, 'Я Запустился!')
    await get_commands(bot)
    await init_models()

    storage = RedisStorage.from_url(config.redisStorage)
    dp = Dispatcher(storage=storage)

    # CRON
    scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
    # scheduler.add_job(update_google_sheets, trigger='interval', hours=3, kwargs={'path': os.path.join(config.dir_path, 'core', 'cron', 'pythonapp.json')})
    scheduler.add_job(update_google_sheets, trigger='interval', minutes=5, kwargs={'path': os.path.join(config.dir_path, 'core', 'cron', 'pythonapp.json')})
    scheduler.start()

    # Errors handlers
    # dp.errors.register(errors_handlers.tg_duble_error, ExceptionTypeFilter(aiogram.exceptions.TelegramBadRequest))
    dp.errors.register(errors_handlers.error_valueError, ExceptionTypeFilter(ValueError))
    dp.errors.register(errors_handlers.error_validationError, ExceptionTypeFilter(ValidationError))
    dp.errors.register(errors_handlers.error_total, ExceptionTypeFilter(Exception))

    # Middlewares
    ## Определение языка
    dp.update.middleware(ACLMiddleware(config.i18n))
    ## Логирование
    dp.callback_query.middleware(CallBackMiddleware())
    dp.message.middleware(MessageMiddleware())
    ## Проверка регистрации
    # dp.message.middleware(CheckRegistrationMessageMiddleware())
    # dp.callback_query.middleware(CheckRegistrationCallbackMiddleware())


    # Команды
    dp.message.register(check_registration, Command(commands=['start']))
    dp.message.register(test_perezaliv_rub, Command(commands=['test_perevizaliv_rub']))
    dp.message.register(test_perezaliv_try, Command(commands=['test_perevizaliv_try']))
    dp.message.register(perezaliv_try, Command(commands=['perevizaliv_try']))
    dp.message.register(perezaliv_rub, Command(commands=['perevizaliv_rub']))

    # Главное меню
    dp.callback_query.register(menu, F.data == 'menu')
    dp.callback_query.register(profile, F.data == 'profile')
    dp.callback_query.register(select_change_language, F.data == 'сhange_language')
    dp.callback_query.register(change_language, ChangeLanguage.filter())
    dp.callback_query.register(choiseShop.rezident, F.data == 'startOrder')
    dp.callback_query.register(history_orders, F.data == 'historyOrders')

    # Регистрация контакта
    dp.message.register(contact.get_true_contact, F.contact, IsTrueContact())
    dp.message.register(contact.get_fake_contact, F.contact)

    # История заказов
    dp.callback_query.register(select_historyOrders_days, HistoryOrderDays.filter())

    # Выдача наличных
    dp.callback_query.register(start_withdraw, F.data == 'withdraw_cash')
    dp.callback_query.register(withdraw_select_shop, StateWithdraw.select_shop, Shop.filter())
    dp.callback_query.register(withdraw_select_currency, StateWithdraw.select_currency, Currency.filter())
    dp.message.register(withdraw_enter_sum, StateWithdraw.enter_sum)
    dp.callback_query.register(withdraw_confirm, F.data == 'confirm_withdraw', StateWithdraw.show_info)

    # Создание заказа
    dp.callback_query.register(choiseShop.check_shops, CountryRezident.filter())
    dp.callback_query.register(choiseShop.choise_currency, Shop.filter())
    dp.callback_query.register(choiseShop.choise_currency_price, Currency.filter())
    dp.callback_query.register(selectMainPaymentGateway, F.data == 'currencyContinue')
    dp.callback_query.register(CurrencyValue.get_CurrencyPrice, F.data == 'currencyNewValue')
    dp.callback_query.register(selectChildPaymentGateway, ChildPaymentGateway.filter())
    dp.callback_query.register(show_catalog, F.data == 'catalog')
    dp.callback_query.register(enterArticle.get_article, F.data == 'enter_article')
    dp.callback_query.register(select_prev_page_catalog, F.data == 'prevPage_catalog')
    dp.callback_query.register(show_child_categories, Category.filter())
    dp.callback_query.register(select_quantity_product, Tovar.filter())
    dp.callback_query.register(update_quantity_product, QuantityUpdate.filter())
    dp.callback_query.register(createOrder.get_price, QuantityProduct.filter())
    dp.callback_query.register(show_catalog, F.data == 'add_product')
    dp.callback_query.register(createOrder.select_tax, F.data == 'continue_order')
    dp.callback_query.register(createOrder.enter_client_name, Taxes.filter())

    # Удаление заказа
    dp.callback_query.register(delete_order, DeleteOrder.filter())

    # dp.callback_query.register(createOrder.get_client_name_CALLBACK, F.data == 'currentPrice')
    # dp.callback_query.register(createOrder.get_price, F.data == 'newPrice')

    # STATES CREATE ORDER
    dp.message.register(createOrder.check_price, StateCreateOrder.GET_PRICE)
    dp.message.register(createOrder.check_client_name, StateCreateOrder.GET_CLIENT_NAME)
    dp.message.register(createOrder.check_client_phone_or_mail, StateCreateOrder.GET_CLIENT_PHONE_OR_MAIL)
    dp.message.register(createOrder.create_order, StateCreateOrder.CREATE_ORDER)
    dp.message.register(get_start, StateCreateOrder.ERROR)
    dp.callback_query.register(create_order, F.data == 'createOrder')

    # STATES CURRENCY
    dp.message.register(CurrencyValue.check_CurrencyPrice, StateCurrency.GET_PRICE)

    # STATES ARTICLE
    dp.message.register(enterArticle.check_article, StateEnterArticle.GET_ARTICLE)
    dp.message.register(get_start, StateEnterArticle.ERROR)


    try:
        await dp.start_polling(bot)
    except aiogram.exceptions.TelegramNetworkError:
        dp.callback_query.register(get_start)
    except Exception as e:
        logger.exception(e)
    finally:
        # if not config.develope_mode:
        #     await bot.send_message(5263751490, 'Я Остановился!!!!')
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(start())
