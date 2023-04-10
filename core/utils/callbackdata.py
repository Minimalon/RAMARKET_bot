from aiogram.filters.callback_data import CallbackData


class Shop(CallbackData, prefix='shop'):
    shop: str


class ChildPaymentGateway(CallbackData, prefix='childPaymentGateway'):
    id: str
    idParent: str
    type: str


class PaymentGateway(CallbackData, prefix='paymentGateway'):
    id: str


class Category(CallbackData, prefix='category'):
    id: str
    parent_id: str


class Product(CallbackData, prefix='product'):
    product_id: str


class QuantityProduct(CallbackData, prefix='quantityProduct'):
    quantity: int


class QuantityUpdate(CallbackData, prefix='quantityInc'):
    quantity: int

