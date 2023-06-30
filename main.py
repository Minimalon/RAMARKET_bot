#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-
import asyncio
import os

import aiogram.exceptions
from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.storage.redis import RedisStorage
from loguru import logger

from core.filters.iscontact import IsTrueContact
from core.handlers import contact
from core.handlers.basic import get_start, check_registration
from core.handlers.callback import *
from core.handlers.states import enterArticle, CurrencyValue, createOrder, choiseShop
from core.middlewares.language_middleware import ACLMiddleware
from core.utils.callbackdata import *
from core.utils.commands import get_commands
from core.utils.states import StateCreateOrder, StateCurrency, StateEnterArticle


@logger.catch()
async def start():
    if not os.path.exists(os.path.join(config.dir_path, 'logs')):
        os.makedirs(os.path.join(config.dir_path, 'logs'))
    logger.add(os.path.join(config.dir_path, 'logs', 'debug.log'),
               format="{time} | {level} | {name}:{function}:{line} | {message} | {extra}", )

    bot = Bot(token=config.token, parse_mode='HTML')
    await bot.send_message(5263751490, 'Я Запустился!')
    await get_commands(bot)
    await init_models()
    storage = RedisStorage.from_url(config.redisStorage)
    dp = Dispatcher(storage=storage)

    # middleware для определения языка
    dp.update.middleware(ACLMiddleware(config.i18n))

    # Команды
    dp.message.register(check_registration, Command(commands=['start']))

    # Главное меню
    dp.callback_query.register(menu, F.data == 'menu')
    dp.callback_query.register(profile, F.data == 'profile')
    dp.callback_query.register(select_change_language, F.data == 'сhange_language')
    dp.callback_query.register(change_language, ChangeLanguage.filter())
    dp.callback_query.register(create_order, F.data == 'createOrder')
    dp.callback_query.register(history_orders, F.data == 'historyOrders')

    # Регистрация контакта
    dp.message.register(contact.get_true_contact, F.contact, IsTrueContact())
    dp.message.register(contact.get_fake_contact, F.contact)

    # Создание заказа
    dp.callback_query.register(selectMainPaymentGateway, F.data == 'currencyContinue')
    dp.callback_query.register(CurrencyValue.get_CurrencyPrice, F.data == 'currencyNewValue')
    dp.callback_query.register(selectChildPaymentGateway, ChildPaymentGateway.filter())
    dp.callback_query.register(select_input_method_Product, PaymentGateway.filter())
    dp.callback_query.register(show_catalog, F.data == 'catalog')
    dp.callback_query.register(enterArticle.get_article, F.data == 'enter_article')
    dp.callback_query.register(select_prev_page_catalog, F.data == 'prevPage_catalog')
    dp.callback_query.register(show_childcategories, Category.filter())
    dp.callback_query.register(select_quantity_product, Product.filter())
    dp.callback_query.register(update_quantity_product, QuantityUpdate.filter())
    dp.callback_query.register(createOrder.get_price, QuantityProduct.filter())
    dp.callback_query.register(show_catalog, F.data == 'add_product')
    dp.callback_query.register(createOrder.enter_client_name, F.data == 'continue_order')

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

    # STATES CURRENCY
    dp.message.register(CurrencyValue.check_CurrencyPrice, StateCurrency.GET_PRICE)

    # STATES ARTICLE
    dp.message.register(enterArticle.check_article, StateEnterArticle.GET_ARTICLE)
    dp.message.register(get_start, StateEnterArticle.ERROR)

    # STATES CHOISE SHOP
    dp.callback_query.register(choiseShop.check_shops, F.data == 'startOrder')
    dp.callback_query.register(choiseShop.choise_currency, Shop.filter())
    dp.callback_query.register(choiseShop.choise_currency_price, Currency.filter())

    try:
        await dp.start_polling(bot)
    except aiogram.exceptions.TelegramNetworkError:
        dp.callback_query.register(get_start)
    except Exception as e:
        logger.exception(e)
    finally:
        await bot.send_message(5263751490, 'Я Остановился!!!!')
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(start())
