import re
from aiogram.fsm.context import FSMContext

from core.utils import texts
from aiogram import Bot
from aiogram.types import Message, ReplyKeyboardRemove
from loguru import logger
from core.keyboards.inline import getKeyboard_start
from core.keyboards.reply import getKeyboard_registration
from core.database import query_db
from core.oneC.api import Api

oneC = Api()


async def get_start(message: Message, bot: Bot):
    client_phone = ''.join(re.findall(r'[0-9]*', message.contact.phone_number))
    log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id, client_phone=client_phone)
    client_info = await oneC.get_client_info(client_phone)
    if client_info:
        log.info("Есть в базе 1С")
        await query_db.update_client_info(chat_id=str(message.chat.id), phone_number=client_phone,
                                          first_name=message.contact.first_name, last_name=message.contact.last_name,
                                          user_id=str(message.contact.user_id))
        await bot.send_message(message.chat.id, 'Регистрация успешно пройдена', reply_markup=ReplyKeyboardRemove())
        await message.answer(texts.menu, reply_markup=getKeyboard_start(), parse_mode='HTML')
    else:
        log.error("Нету в базе 1С")
        text = f'Ваш сотовый "{client_phone}" не зарегистрирован в системе\n' \
               f'Уточните вопрос и попробуйте снова'
        await message.answer(text, reply_markup=getKeyboard_registration(), parse_mode='HTML')


async def check_registration(message: Message):
    log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id)
    log.info("/start")
    client_info = await query_db.get_client_info(chat_id=message.chat.id)
    if client_info:
        await message.answer(texts.menu, reply_markup=getKeyboard_start(), parse_mode='HTML')
    else:
        log.error("Нету в базе 1С")
        text = f'Вы зашли впервые, нажмите кнопку Регистрация'
        await message.answer(text, reply_markup=getKeyboard_registration(), parse_mode='HTML')


async def cancel(message: Message, state: FSMContext):
    chat_id = message.chat.id
    await state.clear()
    order = await query_db.get_order_info(chat_id=chat_id)
    if order:
        await query_db.delete_order(chat_id=chat_id)
        await message.answer(texts.menu, reply_markup=getKeyboard_start(), parse_mode='HTML')
    else:
        await message.answer(f"{texts.error_head}Не найдено текущего заказа", reply_markup=getKeyboard_start(),
                             parse_mode='HTML')
