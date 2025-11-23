from aiogram.fsm.state import State, StatesGroup


class StateCreateOrder(StatesGroup):
    SELECT_QUANTITY = State()
    GET_PRICE = State()
    GET_CLIENT_NAME = State()
    GET_CLIENT_PHONE_OR_MAIL = State()
    CREATE_ORDER = State()
    ERROR = State()


class StateCurrency(StatesGroup):
    GET_PRICE = State()


class StateEnterArticle(StatesGroup):
    GET_ARTICLE = State()
    ERROR = State()

class StateWithdraw(StatesGroup):
    select_shop = State()
    select_currency = State()
    show_info = State()
    enter_sum = State()

class FastOrderState(StatesGroup):
    rezident = State()
    shop = State()
    currency = State()
    sum = State()
