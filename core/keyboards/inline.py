import os
from datetime import datetime

from aiogram.utils.keyboard import InlineKeyboardBuilder

import config
from config import _
from core.models_pydantic.order import ProductGroup, Order
from core.oneC import utils
from core.oneC.api import Api
from core.oneC.models import UserShop, Payment, User
from core.utils.callbackdata import *

oneC = Api()


def getKeyboard_start(language=None, pravoRKO: bool = False):
    keyboard = InlineKeyboardBuilder()
    if language:
        keyboard.button(text=_('Заказ', locale=language), callback_data='startOrder')
        keyboard.button(text=_('Личный кабинет', locale=language), callback_data='profile')
        keyboard.button(text=_('История заказов', locale=language), callback_data='historyOrders')
        if pravoRKO:
            keyboard.button(text=_('Выдача наличных', locale=language), callback_data='withdraw_cash')
    else:
        keyboard.button(text=_('Заказ'), callback_data='startOrder')
        keyboard.button(text=_('Личный кабинет'), callback_data='profile')
        keyboard.button(text=_('История заказов'), callback_data='historyOrders')
        if pravoRKO:
            keyboard.button(text=_('Выдача наличных'), callback_data='withdraw_cash')
    keyboard.adjust(2, 1)
    return keyboard.as_markup()


def getKeyboard_profile():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=_('Главное меню'), callback_data='menu')
    keyboard.button(text=_('Изменить язык'), callback_data='сhange_language')
    keyboard.adjust(1)
    return keyboard.as_markup()


def getKeyboard_change_language():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='Русский', callback_data=ChangeLanguage(language='ru'))
    keyboard.button(text='English', callback_data=ChangeLanguage(language='en'))
    keyboard.button(text='Türk', callback_data=ChangeLanguage(language='tr'))
    keyboard.adjust(1)
    return keyboard.as_markup()


def kb_rezident():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='Россия', callback_data=CountryRezident(rezident='Россия'))
    keyboard.button(text='Казахстан', callback_data=CountryRezident(rezident='Казахстан'))
    keyboard.button(text='Турция', callback_data=CountryRezident(rezident='Турция'))
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


async def getKeyboard_selectCurrency(order: Order):
    keyboard = InlineKeyboardBuilder()
    if order.shop.currency == 'TRY':
        keyboard.button(text='TRY', callback_data=Currency(name='TRY'))
        keyboard.button(text='RUB', callback_data=Currency(name='RUB'))
    elif order.shop.currency == 'EUR':
        keyboard.button(text='EUR', callback_data=Currency(name='EUR'))
    else:
        if order.rezident == 'Казахстан':
            keyboard.button(text='USD', callback_data=Currency(name='USD'))
        else:
            keyboard.button(text='RUB', callback_data=Currency(name='RUB'))
    keyboard.button(text='USDT', callback_data=Currency(name='USDT'))
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


def getKeyboard_selectShop(shops: list[UserShop]):
    keyboard = InlineKeyboardBuilder()
    for shop in shops:
        keyboard.button(text=shop.name, callback_data=Shop(id=shop.id))
    keyboard.adjust(2, repeat=True)
    return keyboard.as_markup()


def getKeyboard_selectPriceCurrency():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=_('Продолжить'), callback_data="currencyContinue")
    keyboard.button(text=_('Изменить курс'), callback_data='currencyNewValue')
    return keyboard.as_markup()


async def getKeyboard_select_Main_PaymentGateway():
    keyboard = InlineKeyboardBuilder()
    for paytype in await utils.get_main_paymentWay():
        keyboard.button(text=paytype.name,
                        callback_data=ChildPaymentGateway(id=paytype.id,
                                                          idParent=paytype.parent_id,
                                                          type=paytype.type))
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


async def getKeyboard_select_Child_PaymentGateway(pay: Payment):
    keyboard = InlineKeyboardBuilder()
    if pay is None:
        groups = await utils.get_child_paymentWay('')
    else:
        groups = await utils.get_child_paymentWay(pay.id)
    if groups:
        for paytype in groups:
            keyboard.button(text=paytype.name,
                            callback_data=ChildPaymentGateway(id=paytype.id,
                                                              idParent=paytype.parent_id,
                                                              type=paytype.type))
    else:
        return getKeyboard_ProductStart()
    if pay is not None:
        keyboard.button(text=_("<<< Назад"), callback_data=ChildPaymentGateway(id='', idParent='', type=''))
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


def getKeyboard_ProductStart():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=_("Ввести ID товара"), callback_data='enter_article')
    keyboard.button(text=_("Каталог"), callback_data='catalog')
    keyboard.adjust(2, repeat=True)
    return keyboard.as_markup()


async def getKeyboard_catalog():
    keyboard = InlineKeyboardBuilder()
    for pg in await utils.get_child_groups("1002592"):
        keyboard.button(text=pg.name,
                        callback_data=Category(parent_id=pg.group_id,
                                               id=pg.id))
    keyboard.button(text=_("<<< Назад"), callback_data='prevPage_catalog')
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


async def getKeyboard_products_or_categories(pg: ProductGroup):
    keyboard = InlineKeyboardBuilder()

    products = await utils.get_tovar_by_group(pg.id)
    if products:
        for product in products:
            keyboard.button(text=product.name, callback_data=Tovar(product_id=product.id))
        keyboard.button(text=_("<<< Назад"), callback_data=Category(id=pg.group_id, parent_id=pg.id))
    groups = await utils.get_child_groups(pg.id)
    if groups:
        for pg in groups:
            keyboard.button(text=pg.name, callback_data=Category(parent_id=pg.group_id, id=pg.id))
        if pg.group_id != "1002592":
            keyboard.button(text=_("<<< Назад"), callback_data=Category(id=pg.group_id, parent_id=pg.id))
        else:
            keyboard.button(text=_("<<< Назад"), callback_data='prevPage_catalog')
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


def getKeyboard_product_info():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=_("Оставить текущую цену"), callback_data='currentPrice')
    keyboard.button(text=_("Изменить цену"), callback_data='newPrice')
    return keyboard.as_markup()


def getKeyboard_quantity_product():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="1", callback_data='None')
    keyboard.button(text="+", callback_data=QuantityUpdate(quantity=2))
    keyboard.button(text=_("Продолжить"), callback_data=QuantityProduct(quantity=1))
    keyboard.adjust(2, 1)
    return keyboard.as_markup()


def getKeyboard_quantity_update(quantity):
    keyboard = InlineKeyboardBuilder()
    if quantity == 1:
        keyboard.button(text=f"{quantity}", callback_data='None')
        keyboard.button(text="+", callback_data=QuantityUpdate(quantity=quantity + 1))
        keyboard.button(text=_("Продолжить"), callback_data=QuantityProduct(quantity=quantity))
        keyboard.adjust(2, 1)
    elif quantity > 1:
        keyboard.button(text="-", callback_data=QuantityUpdate(quantity=quantity - 1))
        keyboard.button(text=f"{quantity}", callback_data='None')
        keyboard.button(text="+", callback_data=QuantityUpdate(quantity=quantity + 1))
        keyboard.button(text=_("Продолжить"), callback_data=QuantityProduct(quantity=quantity))
        keyboard.adjust(3, 1)
    return keyboard.as_markup()


def getKeyboard_cart():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=_("Продолжить"), callback_data='continue_order')
    keyboard.button(text=_("Добавить товар"), callback_data='add_product')
    keyboard.adjust(2)
    return keyboard.as_markup()


def kb_taxes():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='0 %', callback_data=Taxes(tax=0))
    keyboard.button(text='2 %', callback_data=Taxes(tax=0.02))
    keyboard.button(text='3 %', callback_data=Taxes(tax=0.03))
    keyboard.button(text='5 %', callback_data=Taxes(tax=0.05))
    keyboard.button(text='6 %', callback_data=Taxes(tax=0.06))
    keyboard.button(text='8 %', callback_data=Taxes(tax=0.08))
    keyboard.button(text='10 %', callback_data=Taxes(tax=0.10))
    keyboard.button(text='15 %', callback_data=Taxes(tax=0.15))
    keyboard.button(text='17 %', callback_data=Taxes(tax=0.17))
    keyboard.button(text='18 %', callback_data=Taxes(tax=0.18))
    keyboard.button(text='20 %', callback_data=Taxes(tax=0.20))
    keyboard.button(text='23 %', callback_data=Taxes(tax=0.23))
    keyboard.adjust(1)
    return keyboard.as_markup()


def getKeyboard_createOrder():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=_("Создать заказ"), callback_data='createOrder')
    keyboard.button(text=_("Главное меню"), callback_data='menu')
    keyboard.adjust(2)
    return keyboard.as_markup()


def getKeyboard_delete_order(order_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=_("Удалить заказ"),
                    callback_data=DeleteOrder(order_id=order_id, date=datetime.now().strftime('%Y%m%d%H%M')))
    keyboard.adjust(1)
    return keyboard.as_markup()

def kb_demo_currency(user: User):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='USD', callback_data=Currency(name='USD'))
    keyboard.button(text='RUB', callback_data=Currency(name='RUB'))
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()

def kb_withdraw():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='Выдать наличные✅', callback_data='confirm_withdraw')
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()

def kb_historyOrders_by_days():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='За вчерашний день', callback_data=HistoryOrderDays(days=-1))
    keyboard.button(text='Сегодня', callback_data=HistoryOrderDays(days=0))
    keyboard.button(text='3 дня', callback_data=HistoryOrderDays(days=3))
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()