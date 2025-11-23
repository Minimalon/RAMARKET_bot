from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from core.oneC.models import User, UserShop, Payment
from core.utils.currencyes_cb import get_price_valute_by_one


class Product(BaseModel):
    id: str = Field(alias='Id')
    name: str = Field(alias='Наименование')
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
    symbol: str = Field(default='')

    def get_currency_symbol(self, currency_name: str = 'USD') -> str | None:
        currency_symbols = {
            'RUB': '₽',
            'USD': '$',
            'USDT': '$',
            'USDV': '$',
            'EUR': '€',
            'TRY': '₺',
            'AED': 'د.إ',
            'GBP': '£',
            'JPY': '¥',
            'CNY': '¥',
            'INR': '₹',
            'KZT': '₸',
            'UAH': '₴',
            'BYN': 'Br',
            'BRL': 'R$',
            'CAD': '$',
            'CHF': 'CHF',
            'CLP': '$',
            'COP': '$',
            'CRC': '₡',
            'CUP': '₱',
            'DOP': 'RD$',
            'EGP': '£',
            'GTQ': 'Q',
            'HNL': 'L',
            'ISK': 'kr',
            'KGS': 'лв',
            'MXN': '$',
            'MYR': 'RM',
            'NOK': 'kr',
            'PEN': 'S/',
            'PHP': '₱',
            'PKR': '₨',
            'PLN': 'zł',
            'PYG': '₲',
            'SEK': 'kr',
            'SVC': '$',
            'THB': '฿',
            'TWD': 'NT$',
            'UYU': '$U',
            'VEF': 'Bs F',
            'ZAR': 'R'
        }
        return currency_symbols.get(currency_name)

    @model_validator(mode='after')
    def get_currencySymbol(self):
        self.symbol = self.get_currency_symbol(self.name)
        return self

    async def correct_currency_price(self):
        self.price = await get_price_valute_by_one(self.name)
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
    order_id: str = Field(default='', title='Номер заказа в 1С')
    tg_user: TelegramUser
    rezident: str = Field(title="Страна покупателя")
    shop: UserShop | None = Field(default=None)
    currency: CurrencyOrder | None = Field(default=None)
    payment: Payment | None = Field(default=None)
    cart: list[Product] = Field(default=[], title='Корзина')
    sum_usd: Decimal = Field(default=0, decimal_places=2, title='Сумма заказа в долларах')
    sum_rub: Decimal = Field(default=0, decimal_places=0, title='Сумма заказа в рублях')
    sum_try: Decimal = Field(default=0, decimal_places=2, title='Сумма заказа в турецкких лирах')
    sum_kzt: Decimal = Field(default=0, decimal_places=0, title='Сумма заказа в тенге')
    sum_eur: Decimal = Field(default=0, decimal_places=0, title='Сумма заказа в евро')
    sum_usdt: Decimal = Field(default=0, decimal_places=0, title='Сумма заказа в евро')
    tax_sum_usd: Decimal = Field(default=0, decimal_places=2, title='Сумма заказа в долларах c комиссией')
    tax_sum_eur: Decimal = Field(default=0, decimal_places=2, title='Сумма заказа в евро c комиссией')
    tax_sum_usdt: Decimal = Field(default=0, decimal_places=2, title='Сумма заказа в евро c комиссией')
    tax_sum_rub: Decimal = Field(default=0, decimal_places=0, title='Сумма заказа в рублях c комиссией')
    tax_sum_try: Decimal = Field(default=0, decimal_places=0, title='Сумма заказа в турецкких лирах c комиссией')
    tax_sum_kzt: Decimal = Field(default=0, decimal_places=0, title='Сумма заказа в тенге c комиссией')
    client_name: str | None = Field(default=None)
    client_phone: str | None = Field(default=None)
    client_mail: str | None = Field(default=None)
    tax: float = Field(default=0)

    async def correct_order_sums(self):
        if len(self.cart) > 0:
            self.sum_usd = Decimal(0)
            self.sum_rub = Decimal(0)
            self.sum_try = Decimal(0)
            self.sum_kzt = Decimal(0)
            self.sum_eur = Decimal(0)
            self.sum_usdt = Decimal(0)

            if self.rezident == 'Казахстан':
                for product in self.cart:
                    self.sum_kzt += (product.price * self.currency.price) * product.quantity
                    self.sum_usd += product.price * product.quantity
                self.sum_rub += self.sum_usd * await get_price_valute_by_one('USD')
            elif self.shop.currency == 'TRY':
                if self.currency.name == 'RUB':
                    for product in self.cart:
                        self.sum_rub += product.price * product.quantity
                        self.sum_try += (product.price * product.quantity) / self.currency.price
                    self.sum_usd += self.sum_rub / await get_price_valute_by_one('USD')
                elif self.currency.name == 'TRY':
                    for product in self.cart:
                        self.sum_rub += (product.price * self.currency.price) * product.quantity
                        self.sum_try += product.price * product.quantity
                    self.sum_usd += self.sum_rub / await get_price_valute_by_one('USD')
                elif self.currency.name == 'USDT':
                    for product in self.cart:
                        self.sum_rub += (product.price * self.currency.price) * product.quantity
                        self.sum_usdt += product.price * product.quantity
                    self.sum_usd += self.sum_rub / await get_price_valute_by_one('USD')
            else:
                if self.currency.name == 'RUB':
                    for product in self.cart:
                        self.sum_rub += product.price * product.quantity
                        self.sum_usd += (product.price * product.quantity) / self.currency.price
                elif self.currency.name == 'USD':
                    for product in self.cart:
                        self.sum_rub += (product.price * self.currency.price) * product.quantity
                        self.sum_usd += product.price * product.quantity
                elif self.currency.name == 'USDV':
                    for product in self.cart:
                        self.sum_rub += (product.price * self.currency.price) * product.quantity
                        self.sum_usd += product.price * product.quantity
                elif self.currency.name == 'EUR':
                    for product in self.cart:
                        self.sum_rub += (product.price * self.currency.price) * product.quantity
                        self.sum_eur += product.price * product.quantity
                elif self.currency.name == 'USDT':
                    for product in self.cart:
                        self.sum_rub += (product.price * self.currency.price) * product.quantity
                        self.sum_usdt += product.price * product.quantity

        if self.tax > 0:
            self.tax_sum_usd = Decimal(round(self.sum_usd * Decimal(self.tax + 1), 2))
            self.tax_sum_eur = Decimal(round(self.sum_usd * Decimal(self.tax + 1), 2))
            self.tax_sum_usdt = Decimal(round(self.sum_usd * Decimal(self.tax + 1), 2))
            self.tax_sum_rub = Decimal(round(self.sum_rub * Decimal(self.tax + 1), 0))
            self.tax_sum_try = Decimal(round(self.sum_try * Decimal(self.tax + 1), 2))
            self.tax_sum_kzt = Decimal(round(self.sum_kzt * Decimal(self.tax + 1), 0))

        self.sum_usd = Decimal(round(self.sum_usd, 2))
        self.sum_rub = Decimal(round(self.sum_rub, 0))
        self.sum_try = Decimal(round(self.sum_try, 2))
        self.sum_kzt = Decimal(round(self.sum_kzt, 0))
        self.sum_eur = Decimal(round(self.sum_eur, 0))
        self.sum_usdt = Decimal(round(self.sum_usdt, 0))
        return self

    async def convert_currency_from_usd_to_kzt(self, currency_name: str = 'KZT'):
        new_price = await get_price_valute_by_one(currency_name)
        for product in self.cart:
            product.price = round((product.price * self.currency.price) / new_price, 0)
        self.currency = CurrencyOrder(
            name=currency_name,
            price=new_price
        )
        return self

    def create_1c_order(self) -> dict:
        order = {
            "TypeR": "Doc",
            "Order_id": None,  # Если указывать номер заказа, то заказ будет не создаваться, а изменяться
            "Data": None,  # Если указали Order_id, нужно также указать дату заказа в формате 02.01.2024 12:28:00
            "Tax": str(round(self.tax * 100, 0)),
            "Sklad": str(self.shop.id),
            "rezident": self.rezident,
            "KursPrice": str(self.currency.price),
            "Valuta": str(self.currency.name),
            "SO": str(self.payment.id),
            "Sotr": str(self.user.id),
            "Klient": str(self.client_name),
            "Telefon": str(self.client_phone),
            "Email": str(self.client_mail),
            "Itemc": [{"Tov": str(p.id), "Kol": str(p.quantity), "Cost": str(p.price), 'Sum': str(p.price * p.quantity)}
                      for p in self.cart]
        }
        return order

class FastOrderModel(BaseModel):
    user: User
    tg_user: TelegramUser
    rezident: str = Field(title="None")
    shop: UserShop | None = Field(default=None)
    currency: CurrencyOrder | None = Field(default=None)
    sum: Decimal = Field(default=0, decimal_places=2, title='Сумма заказа')

    def create_order_text(self) -> str:
        return (
            f'Быстрая продажа создана ✅\n\n'
            f'Магазин: {self.shop.name}\n'
            f'Валюта: {self.currency.name}\n'
            f'Сумма: {self.sum}\n'
        )

if __name__ == '__main__':
    a = Decimal(1.123)
    print(str(a))
