from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.i18n import gettext as _


def getKeyboard_registration():
    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text=_('Регистрация'), request_contact=True)
    keyboard.adjust(1)
    return keyboard.as_markup(one_time_keyboard=True)
