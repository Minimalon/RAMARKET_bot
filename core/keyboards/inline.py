from aiogram.utils.keyboard import InlineKeyboardBuilder
from core.utils.callbackdata import *
from core.insales import utils
from core.oneC.api import Api
from core.oneC import utils

oneC = Api()


def getKeyboard_start():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='Заказ', callback_data='startOrder')
    keyboard.button(text='Личный кабинет', callback_data='profile')
    keyboard.button(text='История заказов', callback_data='historyOrders')
    keyboard.adjust(2, 1)
    return keyboard.as_markup()


def getKeyboard_profile():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='Главное меню', callback_data='menu')
    keyboard.adjust(1)
    return keyboard.as_markup()


def getKeyboard_selectShop(shops):
    keyboard = InlineKeyboardBuilder()
    for shop in shops:
        keyboard.button(text=shop['Магазин'], callback_data=Shop(id=str(shop['idМагазин'])))
    return keyboard.as_markup()


def getKeyboard_selectPriceCurrency():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='Продолжить', callback_data="currencyContinue")
    keyboard.button(text='Изменить курс', callback_data='currencyNewValue')
    return keyboard.as_markup()


async def getKeyboard_select_Main_PaymentGateway():
    keyboard = InlineKeyboardBuilder()
    for paytype in await utils.get_main_paymentWay():
        keyboard.button(text=paytype['Наименование'],
                        callback_data=ChildPaymentGateway(id=paytype['Id'], idParent=paytype['IdParent']))
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


async def getKeyboard_select_Child_PaymentGateway(Id: str, IdParent: str):
    keyboard = InlineKeyboardBuilder()
    groups = await utils.get_child_paymentWay(Id)
    if groups:
        for paytype in await utils.get_child_paymentWay(Id):
            keyboard.button(text=paytype['Наименование'],
                            callback_data=ChildPaymentGateway(id=paytype['Id'], idParent=paytype['IdParent']))
    else:
        return getKeyboard_ProductStart()
    if Id != '':
        keyboard.button(text="<<< Назад", callback_data=ChildPaymentGateway(id=IdParent, idParent=''))
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


def getKeyboard_ProductStart():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Ввести ID товара", callback_data='enter_article')
    keyboard.button(text="Каталог", callback_data='catalog')
    keyboard.adjust(2, repeat=True)
    return keyboard.as_markup()


async def getKeyboard_catalog():
    keyboard = InlineKeyboardBuilder()
    for group in await utils.get_child_groups("1002592"):
        keyboard.button(text=group['Наименование'],
                        callback_data=Category(parent_id=group['idGroup'], id=group['id']))
    keyboard.button(text="<<< Назад", callback_data='prevPage_catalog')
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


async def getKeyboard_products_or_categories(id: str, parent_id: str):
    keyboard = InlineKeyboardBuilder()

    products = await utils.get_tovar_by_group(id)
    if products:
        for product in products:
            keyboard.button(text=product['Наименование'], callback_data=Product(product_id=product['Id']))
        keyboard.button(text="<<< Назад", callback_data=Category(id=parent_id, parent_id=id))
        keyboard.adjust(1, repeat=True)
        return keyboard.as_markup()

    groups = await utils.get_child_groups(id)
    if groups:
        for group in groups:
            text = group['Наименование']
            keyboard.button(text=text, callback_data=Category(parent_id=group['idGroup'], id=group['id']))
        if id != "1002592":
            keyboard.button(text="<<< Назад", callback_data=Category(id=parent_id, parent_id=id))
        else:
            keyboard.button(text="<<< Назад", callback_data='prevPage_catalog')
        keyboard.adjust(1, repeat=True)
        return keyboard.as_markup()

    if not groups and not products:
        raise ValueError


def getKeyboard_product_info():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Оставить текущую цену", callback_data='currentPrice')
    keyboard.button(text="Изменить цену", callback_data='newPrice')
    return keyboard.as_markup()


def getKeyboard_quantity_product():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="1", callback_data='None')
    keyboard.button(text="+", callback_data=QuantityUpdate(quantity=2))
    keyboard.button(text="Продолжить", callback_data=QuantityProduct(quantity=1))
    keyboard.adjust(2, 1)
    return keyboard.as_markup()


def getKeyboard_quantity_update(quantity):
    keyboard = InlineKeyboardBuilder()
    if quantity == 1:
        keyboard.button(text=f"{quantity}", callback_data='None')
        keyboard.button(text="+", callback_data=QuantityUpdate(quantity=quantity + 1))
        keyboard.button(text="Продолжить", callback_data=QuantityProduct(quantity=quantity))
        keyboard.adjust(2, 1)
    elif quantity > 1:
        keyboard.button(text="-", callback_data=QuantityUpdate(quantity=quantity - 1))
        keyboard.button(text=f"{quantity}", callback_data='None')
        keyboard.button(text="+", callback_data=QuantityUpdate(quantity=quantity + 1))
        keyboard.button(text="Продолжить", callback_data=QuantityProduct(quantity=quantity))
        keyboard.adjust(3, 1)
    return keyboard.as_markup()


def getKeyboard_createOrder():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Создать заказ", callback_data='createOrder')
    keyboard.button(text="Главное меню", callback_data='menu')
    keyboard.adjust(2)
    return keyboard.as_markup()
