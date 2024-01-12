from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from core.utils import texts
from core.utils.states import StateEnterArticle
import core.database.query_db as query_db
from loguru import logger
from core.oneC import utils
from core.keyboards import inline
from config import _

async def error_message(message: Message, exception, state: FSMContext):
    text = f"{texts.error_head}{exception}"
    await message.answer(text)
    await state.set_state(StateEnterArticle.ERROR)


async def get_article(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(_("Введите ID товара"))
    await state.set_state(StateEnterArticle.GET_ARTICLE)


async def check_article(message: Message, state: FSMContext):
    try:
        article = message.text
        if not message.text.isdigit():
            await message.answer(texts.error_article_not_decimal)
            return

        tovar = await utils.get_tovar_by_ID(article)
        if not tovar:
            await message.answer('{text}'.format(text=texts.error_article_not_found(article)))
            return

        await state.update_data(product_id=article, name=message.chat.first_name)
        log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id, product_id=article)
        log.info("Ввели артикуль")
        await message.answer(_("Выберите количество товара"), reply_markup=inline.getKeyboard_quantity_product())
        await state.clear()
    except Exception as ex:
        logger.exception(ex)
        await error_message(message, ex, state)
