import re

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from loguru import logger

from config import _
from core.database import query_db
from core.keyboards.inline import getKeyboard_start
from core.keyboards.reply import getKeyboard_registration
from core.oneC import utils
from core.oneC.api import Api
from core.utils import texts

oneC = Api()


async def get_start(message: Message):
    client_phone = ''.join(re.findall(r'[0-9]*', message.contact.phone_number))
    log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id, client_phone=client_phone)
    oneC_user = await utils.get_user_info(phone=client_phone)
    client_info = await oneC.get_client_info(client_phone)
    if client_info:
        log.info("Есть в базе 1С")
        await query_db.update_client_info(chat_id=str(message.chat.id), phone_number=client_phone,
                                          first_name=message.contact.first_name, last_name=message.contact.last_name,
                                          user_id=str(message.contact.user_id))
        await message.answer(_('Регистрация успешно пройдена'), reply_markup=ReplyKeyboardRemove())
        await message.answer("{menu}".format(menu=texts.menu), reply_markup=getKeyboard_start(pravoRKO=oneC_user.pravoRKO))
    else:
        log.error("Нету в базе 1С")
        text = _(
            'Ваш сотовый {client_phone} не зарегистрирован в системе\n'f'Уточните вопрос и попробуйте снова') \
            .format(client_phone=client_phone)
        await message.answer(text, reply_markup=getKeyboard_registration())


async def check_registration(message: Message, state: FSMContext):
    log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id)
    log.info("/start")
    client_info = await query_db.get_client_info(chat_id=message.chat.id)
    oneC_user = await utils.get_user_info(phone=client_info.phone_number)
    await state.clear()
    if client_info:
        await message.answer("{menu}".format(menu=texts.menu), reply_markup=getKeyboard_start(pravoRKO=oneC_user.pravoRKO))
    else:
        log.error("Нету в базе 1С")
        await message.answer(_('Вы зашли впервые, нажмите кнопку Регистрация'), reply_markup=getKeyboard_registration())

