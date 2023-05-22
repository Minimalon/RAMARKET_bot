from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import _
from core.oneC import utils
from core.oneC.api import Api
from core.utils.callbackdata import *

oneC = Api()


def getKeyboard_start(language=None):
    keyboard = InlineKeyboardBuilder()
    if language:
        keyboard.button(text=_('Заказ', locale=language), callback_data='startOrder')
        keyboard.button(text=_('Личный кабинет', locale=language), callback_data='profile')
        keyboard.button(text=_('История заказов', locale=language), callback_data='historyOrders')
    else:
        keyboard.button(text=_('Заказ'), callback_data='startOrder')
        keyboard.button(text=_('Личный кабинет'), callback_data='profile')
        keyboard.button(text=_('История заказов'), callback_data='historyOrders')
    keyboard.adjust(2, 1)
    return keyboard.as_markup()


def getKeyboard_profile():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=_('Главное меню'), callback_data='menu')
    # keyboard.button(text=_('Изменить язык'), callback_data='сhange_language')
    keyboard.adjust(1)
    return keyboard.as_markup()


def getKeyboard_change_language():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='Русский', callback_data=ChangeLanguage(language='ru'))
    keyboard.button(text='English', callback_data=ChangeLanguage(language='en'))
    keyboard.button(text='Türk', callback_data=ChangeLanguage(language='tr'))
    keyboard.adjust(1)
    return keyboard.as_markup()


def getKeyboard_selectCurrency():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="$", callback_data=Currency(currency='USD'))
    keyboard.button(text="₽", callback_data=Currency(currency='RUB'))
    keyboard.adjust(2, repeat=True)
    return keyboard.as_markup()


def getKeyboard_selectShop(shops):
    keyboard = InlineKeyboardBuilder()
    for shop in shops:
        keyboard.button(text=shop['Магазин'], callback_data=Shop(shop=str(shop['idМагазин']), currency=shop['Валюта'],
                                                                 price=str(shop['ВалютаКурс'])))
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
        keyboard.button(text=paytype['Наименование'],
                        callback_data=ChildPaymentGateway(id=paytype['Id'], idParent=paytype['IdParent'],
                                                          type=paytype['Type']))
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


async def getKeyboard_select_Child_PaymentGateway(Id: str, IdParent: str):
    keyboard = InlineKeyboardBuilder()
    groups = await utils.get_child_paymentWay(Id)
    if groups:
        for paytype in await utils.get_child_paymentWay(Id):
            keyboard.button(text=paytype['Наименование'],
                            callback_data=ChildPaymentGateway(id=paytype['Id'], idParent=paytype['IdParent'],
                                                              type=paytype['Type']))
    else:
        return getKeyboard_ProductStart()
    if Id != '':
        keyboard.button(text=_("<<< Назад"), callback_data=ChildPaymentGateway(id=IdParent, idParent='', type=''))
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
    for group in await utils.get_child_groups("1002592"):
        keyboard.button(text=group['Наименование'],
                        callback_data=Category(parent_id=group['idGroup'], id=group['id']))
    keyboard.button(text=_("<<< Назад"), callback_data='prevPage_catalog')
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


async def getKeyboard_products_or_categories(id: str, parent_id: str):
    keyboard = InlineKeyboardBuilder()

    products = await utils.get_tovar_by_group(id)
    if products:
        for product in products:
            keyboard.button(text=product['Наименование'], callback_data=Product(product_id=product['Id']))
        keyboard.button(text=_("<<< Назад"), callback_data=Category(id=parent_id, parent_id=id))
        keyboard.adjust(1, repeat=True)
        return keyboard.as_markup()

    groups = await utils.get_child_groups(id)
    if groups:
        for group in groups:
            text = group['Наименование']
            keyboard.button(text=text, callback_data=Category(parent_id=group['idGroup'], id=group['id']))
        if id != "1002592":
            keyboard.button(text=_("<<< Назад"), callback_data=Category(id=parent_id, parent_id=id))
        else:
            keyboard.button(text=_("<<< Назад"), callback_data='prevPage_catalog')
        keyboard.adjust(1, repeat=True)
        return keyboard.as_markup()

    if not groups and not products:
        raise ValueError


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


def getKeyboard_createOrder():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=_("Создать заказ"), callback_data='createOrder')
    keyboard.button(text=_("Главное меню"), callback_data='menu')
    keyboard.adjust(2)
    return keyboard.as_markup()
