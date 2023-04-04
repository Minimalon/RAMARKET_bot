#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-

import asyncio
import os
from core.handlers.basic import get_start, check_registration
from core.handlers.callback import *
from core.utils.callbackdata import *
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from core.utils.states import StateCreateOrder, StateCurrency, StateEnterArticle
from core.handlers.states import enterArticle, CurrencyValue, createOrder, choiseShop
from core.utils.commands import get_commands



@logger.catch()
async def start():
    if not os.path.exists(os.path.join(config.dir_path, 'logs')):
        os.makedirs(os.path.join(config.dir_path, 'logs'))
    logger.add(os.path.join(config.dir_path, 'logs', 'debug.log'),
               format="{time:MMMM D, YYYY > HH:mm:ss} | {level} | {message} | {extra}", )

    bot = Bot(token=config.token)
    await get_commands(bot)

    dp = Dispatcher()

    dp.message.register(check_registration, Command(commands=['start']))
    dp.callback_query.register(menu, F.data == 'menu')
    dp.callback_query.register(profile, F.data == 'profile')
    dp.callback_query.register(create_order, F.data == 'createOrder')
    dp.callback_query.register(history_orders, F.data == 'historyOrders')

    dp.message.register(get_start, F.contact)
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

    # dp.callback_query.register(createOrder.get_client_name_CALLBACK, F.data == 'currentPrice')
    # dp.callback_query.register(createOrder.get_price, F.data == 'newPrice')

    # STATES CREATE ORDER
    dp.message.register(createOrder.check_price, StateCreateOrder.GET_PRICE)
    dp.message.register(createOrder.check_client_name, StateCreateOrder.GET_CLIENT_NAME)
    dp.message.register(createOrder.check_client_phone, StateCreateOrder.GET_CLIENT_PHONE)
    dp.message.register(createOrder.create_order, StateCreateOrder.CREATE_ORDER)
    dp.message.register(get_start, StateCreateOrder.ERROR)

    # STATES CURRENCY
    dp.message.register(CurrencyValue.check_CurrencyPrice, StateCurrency.GET_PRICE)

    # STATES ARTICLE
    dp.message.register(enterArticle.check_article, StateEnterArticle.GET_ARTICLE)
    dp.message.register(get_start, StateEnterArticle.ERROR)

    # STATES CHOISE SHOP
    dp.callback_query.register(choiseShop.check_shops, F.data == 'startOrder')
    dp.callback_query.register(choiseShop.choise_currency_price_Shop, Shop.filter())

    # ERRORS handlers
    # dp.errors.register(error_notFound_products_and_categories)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(start())
