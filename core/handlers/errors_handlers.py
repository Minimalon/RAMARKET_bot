from aiogram.types import ErrorEvent

from core.loggers.make_loggers import bot_log
from core.utils import texts


async def error_valueError(event: ErrorEvent):
    bot_log.error(event.exception)
    bot_log.exception(event.exception)
    if event.update.message is not None:
        await event.update.message.answer(texts.error_head + str(event.exception))
    else:
        await event.update.callback_query.message.answer(texts.error_head + str(event.exception))


async def error_validationError(event: ErrorEvent):
    errors = event.exception.errors()
    for error in errors:
        bot_log.error(str(error))
        if event.update.message is not None:
            await event.update.message.answer(texts.error_head + error['msg'])
        else:
            await event.update.callback_query.message.answer(texts.error_head + error['msg'])


async def tg_duble_error(event: ErrorEvent):
    await event.update.callback_query.answer('Вы дважды нажали на кнопку')
    return


async def error_total(event: ErrorEvent):
    bot_log.exception(event.exception)
    if event.update.message is not None:
        await event.update.message.answer(texts.error_head + str(event.exception))
    else:
        await event.update.callback_query.message.answer(texts.error_head + str(event.exception))
