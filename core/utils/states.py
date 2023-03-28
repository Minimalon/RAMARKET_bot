from aiogram.fsm.state import State, StatesGroup


class StateCreateOrder(StatesGroup):
    GET_PRICE = State()
    GET_CLIENT_NAME = State()
    GET_CLIENT_PHONE = State()
    CREATE_ORDER = State()
    ERROR = State()


class StateCurrency(StatesGroup):
    GET_PRICE = State()


class StateEnterArticle(StatesGroup):
    GET_ARTICLE = State()
    ERROR = State()
