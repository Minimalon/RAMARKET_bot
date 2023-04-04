from core.database import query_db

menu = (f'<u><b>Заказ</b></u> - Оформить заказ покупателю\n\n'
        f'<u><b>Личный кабинет</b></u> - Личные регистрационные данные\n\n'
        f'<u><b>История заказов</b></u> - Получить Excel файл с историями заказов')

zero_shops = "На вас не прикреплено ни одного магазина\nУточните вопрос и попробуйте снова"
async def qr(answer_json, chat_id):
    text = (f"<b>Заказ под номером:</b> <code>{answer_json['Nomer']}</code>\n"
            f"<b>На сумму:</b> <code>{answer_json['Sum']} {await query_db.get_currency_name(chat_id=chat_id)}</code>")
    return text
