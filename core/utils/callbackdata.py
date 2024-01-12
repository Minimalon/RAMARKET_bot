from aiogram.filters.callback_data import CallbackData


class Currency(CallbackData, prefix='currency'):
    name: str


class Shop(CallbackData, prefix='shop'):
    id: str


class ChildPaymentGateway(CallbackData, prefix='childPaymentGateway'):
    id: str
    idParent: str
    type: str


class Category(CallbackData, prefix='category'):
    id: str
    parent_id: str


class Tovar(CallbackData, prefix='product'):
    product_id: str


class QuantityProduct(CallbackData, prefix='quantityProduct'):
    quantity: int


class QuantityUpdate(CallbackData, prefix='quantityInc'):
    quantity: int


class ChangeLanguage(CallbackData, prefix='select_language'):
    language: str


class DeleteOrder(CallbackData, prefix='del_ord'):
    order_id: str
    date: str
