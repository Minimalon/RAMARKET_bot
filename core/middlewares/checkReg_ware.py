from typing import Callable, Awaitable, Dict, Any

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from loguru import logger

from core.database import query_db as queryDB
from core.handlers.basic import get_start
from core.keyboards.reply import getKeyboard_registration
from core.loggers.make_loggers import bot_log
from core.oneC import utils as oneC
from core.utils import texts


async def checkClientIN1c(phone):
    client_1c = await oneC.get_employeeInfo(phone)
    if not client_1c:
        return False
    elif client_1c['Администратор'] == "Нет":
        return False
    else:
        return True


async def checkRegMessage(message: Message) -> bool:
    client_db = await queryDB.get_client_info(chat_id=message.chat.id)
    if client_db is None:
        bot_log.debug("Нету в базе данных")
        try:
            if message.contact is not None:
                client_phone = texts.phone(message.contact.phone_number)
                if message.contact.user_id == message.from_user.id:
                    bot_log.info("Отправил свой контанкт")
                    if not await checkClientIN1c(client_phone):
                        bot_log.error("Не зарегистрирован в 1с")
                        await message.answer(texts.phoneNotReg(client_phone), reply_markup=getKeyboard_registration())
                        return False

                    await queryDB.update_client_info(chat_id=str(message.chat.id), phone_number=client_phone,
                                                     first_name=message.contact.first_name,
                                                     last_name=message.contact.last_name,
                                                     user_id=str(message.contact.user_id))
                    await message.answer(texts.succes_registration, reply_markup=ReplyKeyboardRemove())
                    bot_log.success(texts.succes_registration)
                    await get_start(message)
                    return True
                else:
                    bot_log.error("Отправил чужой сотовый, когда его нету в базе данных")
                    await message.answer(f'{texts.error_head}{texts.need_reg}', reply_markup=getKeyboard_registration())
                    return False
            else:
                bot_log.debug("Отправил не свой контакт")
                await message.answer(f'{texts.error_head}{texts.need_reg}', reply_markup=getKeyboard_registration())
                return False
        except AttributeError:
            await message.answer(f'{texts.error_head}{texts.need_reg}', reply_markup=getKeyboard_registration())
            return False
        except Exception as ex:
            bot_log.exception(ex)
            await message.answer(f'{texts.error_head}{texts.need_reg}', reply_markup=getKeyboard_registration())
    elif not await checkClientIN1c(client_db.phone_number):
        bot_log.error("Не зарегестрирован в 1с")
        # Нужно удалить из БД так, как нету в 1С или...... не надо удалять
        await message.answer(texts.phoneNotReg(client_db.phone_number), reply_markup=getKeyboard_registration())
        return False
    return True


async def checkRegCallback(call: CallbackQuery) -> bool:
    client_db = await queryDB.get_client_info(chat_id=call.message.chat.id)
    if client_db is None:
        bot_log.debug("Нету в базе данных")
        await call.message.answer(texts.need_reg, reply_markup=getKeyboard_registration())
        return False

    if not await checkClientIN1c(client_db.phone_number):
        # Нужно удалить из БД так, как нету в 1С или...... не надо удалять
        bot_log.error("Не зарегестрирован в 1с")
        await call.message.answer(texts.phoneNotReg(client_db.phone_number), reply_markup=getKeyboard_registration())
        return False
    return True


class CheckRegistrationMessageMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: dict[str, Any],
    ) -> Any:
        if await checkRegMessage(event):
            bot_log.info(f'Отправил сообщение "{event.text}"')
            return await handler(event, data)


class CheckRegistrationCallbackMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
            event: CallbackQuery,
            data: dict[str, Any],
    ) -> Any:
        if await checkRegCallback(event):
            return await handler(event, data)
