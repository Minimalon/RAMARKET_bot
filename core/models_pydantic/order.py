from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from core.oneC.models import User, UserShop, Payment
from core.utils.currencyes_cb import get_price_valute_by_one


class Product(BaseModel):
    name: str = Field(alias='Наименование')
    id: str = Field(alias='Id')
    group_name: str = Field(alias='NameGroup')
    group_id: str = Field(alias='idGroup')
    price: Decimal = Field(decimal_places=2, default=0)
    quantity: int = Field(default=0)


class ProductGroup(BaseModel):
    name: str = Field(alias='Наименование')
    id: str
    parent_name: str = Field(alias='NameParent')
    group_id: str = Field(alias='idGroup')


class CurrencyOrder(BaseModel):
    name: str
    price: Decimal = Field(decimal_places=4)
    symbol: str = Field(default='$')

    @model_validator(mode='after')
    def get_currencySymbol(self):
        currency_symbols = {
            'RUB': '₽',
            'USD': '$',
            'EUR': '€',
            'TRY': '₺',
            'AED': 'د.إ',
        }
        self.symbol = currency_symbols[self.name]
        return self


class TelegramUser(BaseModel):
    user_id: int
    chat_id: int
    is_bot: bool
    first_name: str
    last_name: str | None
    username: str | None
    language_code: str | None


class Order(BaseModel):
    user: User
    tg_user: TelegramUser
    shop: UserShop | None = Field(default=None)
    currency: CurrencyOrder | None = Field(default=None)
    payment: Payment | None = Field(default=None)
    cart: list[Product] = Field(default=[], title='Корзина')
    sum_usd: Decimal = Field(default=0, decimal_places=2, title='Сумма заказа в долларах')
    sum_rub: Decimal = Field(default=0, decimal_places=2, title='Сумма заказа в рублях')
    sum_try: Decimal = Field(default=0, decimal_places=2, title='Сумма заказа в турецкких лирах')
    client_name: str | None = Field(default=None)
    client_phone: str | None = Field(default=None)
    client_mail: str | None = Field(default=None)

    async def correct_order_sums(self):
        if len(self.cart) > 0:
            self.sum_usd = Decimal(0)
            self.sum_rub = Decimal(0)
            self.sum_try = Decimal(0)

            if self.currency.name == 'RUB':
                for product in self.cart:
                    self.sum_rub += product.price * product.quantity
                    self.sum_usd += (product.price * product.quantity) / self.currency.price
            elif self.currency.name == 'USD':
                for product in self.cart:
                    self.sum_rub += (product.price * self.currency.price) * product.quantity
                    self.sum_usd += product.price * product.quantity
            elif self.currency.name == 'TRY':
                for product in self.cart:
                    self.sum_rub += (product.price * self.currency.price) * product.quantity
                    self.sum_try += product.price * product.quantity
                self.sum_usd += self.sum_rub / await get_price_valute_by_one('USD')
        self.sum_usd = Decimal(round(self.sum_usd, 2))
        self.sum_rub = Decimal(round(self.sum_rub, 2))
        self.sum_try = Decimal(round(self.sum_try, 2))
        return self

    def create_1c_order(self) -> dict:
        order = {
            "TypeR": "Doc",
            "Sklad": self.shop.id,
            "KursPrice": self.currency.price,
            "SO": self.payment.id,
            "Sotr": self.user.id,
            "Klient": self.client_name,
            "Telefon": self.client_phone,
            "Email": self.client_mail,
            "Itemc": [{"Tov": p.id, "Kol": p.quantity, "Cost": p.price, 'Sum': p.price * p.quantity} for p in self.cart]
        }
        return order
