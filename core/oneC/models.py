import enum
import json
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator


class Shop(BaseModel):
    """С запроса АПИ, где список всех магазинов"""

    def __init__(self, **data):
        if type(data["ВалютаКурс"]) == str:
            data["ВалютаКурс"] = data["ВалютаКурс"].replace(",", ".")
        super().__init__(**data)

    id: str = None
    name: str = Field(alias='Наименование')
    org: str = Field(alias='Org')
    currency: str = Field(alias='Валюта')
    currencyPrice: float = Field(alias='ВалютаКурс')
    city: str = Field(alias='Город')
    city_code: str = Field(alias='КодГород')
    country: str = Field(alias='Страна')
    country_code: str = Field(alias='КодСтраны')
    dogovor: str = Field(alias='Договор')
    dogovorID: str = Field(alias='ДоговорID')


class UserShop(BaseModel):
    def __init__(self, **data):
        if type(data["ВалютаКурс"]) == str:
            data["ВалютаКурс"] = data["ВалютаКурс"].replace(",", ".")
        super().__init__(**data)

    name: str = Field(alias='Магазин')
    id: str = Field(alias='idМагазин')
    currency: str = Field(alias='Валюта')
    currencySymbol: str = Field(default='$')
    currencyPrice: Decimal = Field(alias='ВалютаКурс', decimal_places=4)
    city: str = Field(alias='Город')
    city_code: str = Field(alias='КодГород')
    country: str = Field(alias='Страна')
    country_code: str = Field(alias='КодСтраны')

    @model_validator(mode='after')
    def get_currencySymbol(self):
        currency_symbols = {
            'RUB': '₽',
            'USD': '$',
            'USDV': '$',
            'EUR': '€',
            'TRY': '₺',
            'AED': 'د.إ',
        }
        self.currencySymbol = currency_symbols[self.currency]
        return self


class User(BaseModel):
    """GetUP"""

    id: str
    name: str = Field(alias='Наименование')
    admin: bool = Field(alias='Администратор')
    shops: list[UserShop] = Field(alias='Магазины')

    @field_validator('admin', mode='before')
    def check_admin(cls, v: str):
        if v == 'Да':
            return True
        else:
            return False


class Payment(BaseModel):
    id: str | None = Field(alias='Id')
    name: str = Field(alias='Наименование')
    parent_id: str = Field(alias='IdParent')
    parent_name: str = Field(alias='NameParent')
    type: str = Field(alias='Type')


class BankOrder(BaseModel):
    ORG: str = Field(alias='ORG')
    PersonalAcc: str = Field(alias='BS')
    BankName: str = Field(alias='Bank')
    BIC: str = Field(alias='BIC')
    CorrespAcc: str = Field(alias='KBS')
    PayeeINN: str = Field(alias='ORGINN')
    ORGKPP: str = Field(alias='KPP', default=None)
    Nomer: str = Field(alias='Nomer')
    Date: str = Field(alias='Date')
    Sum: str = Field(alias='Sum', default=None)
    LastName: str = Field(alias='LastName', default=None)
    FirstName: str = Field(alias='FirstName', default=None)
    MiddleName: str = Field(alias='MiddleName', default=None)

    def create_order(self):
        text = 'ST00012'
        if self.ORG:
            text += f'|Name={self.ORG}'
        if self.PersonalAcc:
            text += f'|PersonalAcc={self.PersonalAcc}'
        if self.BankName:
            text += f'|BankName={self.BankName}'
        if self.BIC:
            text += f'|BIC={self.BIC}'
        if self.CorrespAcc:
            text += f'|CorrespAcc={self.CorrespAcc}'
        if self.PayeeINN:
            text += f'|PayeeINN={self.PayeeINN}'
        if self.ORGKPP:
            text += f'|KPP={self.ORGKPP}'
        if self.Nomer and self.Date:
            text += f'|Purpose=Оплата заказа №{self.Nomer} от {self.Date}'
        if self.ORGKPP:
            text += f'|Name={self.ORG}'
        text += f'|LastName={self.LastName}|FirstName={self.FirstName}|MiddleName={self.MiddleName}'
        text += f'|Sum={self.Sum}'
        return text

    def add_sum(self, sum: str):
        self.Sum = sum

    def add_fio(self, fio: str):
        s_name, f_name, patronymic = fio.split()
        self.FirstName = s_name
        self.LastName = f_name
        self.MiddleName = patronymic


if __name__ == '__main__':
    a = json.dumps(json.loads(
        r"""{"ORG": "Общество с ограниченной ответственностью \"РА ФИНАНС\"",
        "ORGINN": "1655389654",
        "ORGKPP": "165501001",
        "BS": "40702810210000478716",
        "Bank": "АО \"Тинькофф Банк\"",
        "BIC": "044525974",
        "KBS": "30101810145250000974",
        "Sum": "913",
        "Nomer": "РА00-000659",
        "Date": "22.12.2023 15:06:11"}"""
    ))
    print(a)
    b = BankOrder.model_validate_json(a)
    print(b)
