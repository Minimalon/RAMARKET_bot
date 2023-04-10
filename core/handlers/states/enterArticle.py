from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from core.utils import texts
from core.utils.states import StateEnterArticle
import core.database.query_db as query_db
from loguru import logger
from core.oneC import utils
from core.keyboards import inline


async def error_message(message: Message, exception, state: FSMContext):
    text = f"{texts.error_head}{exception}"
    await message.answer(text)
    await state.set_state(StateEnterArticle.ERROR)


async def get_article(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Введите ID товара")
    await call.answer()
    await state.set_state(StateEnterArticle.GET_ARTICLE)


async def check_article(message: Message, state: FSMContext):
    try:
        article = message.text
        if not message.text.isdigit():
            text = f"{texts.error_head}Разрешено вводить только цифры\nПопробуйте снова"
            await message.answer(text, parse_mode='HTML')
            return

        tovar = await utils.get_tovar_by_ID(article)
        if not tovar:
            text = f"{texts.error_head}С данным ID '{article}' ничего не найдено\nПопробуйте снова"
            await message.answer(text, parse_mode='HTML')
            return

        await query_db.update_order(chat_id=message.chat.id, product_id=article)
        log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id, product_id=article)
        log.info("Ввели артикуль")
        await message.answer("Выберите количество товара", reply_markup=inline.getKeyboard_quantity_product())
        await state.clear()
    except Exception as ex:
        logger.exception(ex)
        await error_message(message, ex, state)
