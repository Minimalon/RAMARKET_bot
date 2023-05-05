from core.database import query_db

error_head = f"➖➖➖➖➖🚨ОШИБКА🚨➖➖➖➖➖\n"
error_needOnlyDigits = error_head + ("Номер должен состоят максимум из 11 цифр\n"
                                     "Почта должна содержать знак <u><b>@</b></u>\n"
                                     "<b>Попробуйте снова.</b>")
error_fakeContact = f'{error_head}Ты отправил <u><b>не свой</b></u> контакт'

menu = (f'<u><b>Заказ</b></u> - Оформить заказ покупателю\n\n'
        f'<u><b>Личный кабинет</b></u> - Личные регистрационные данные\n\n'
        f'<u><b>История заказов</b></u> - Получить Excel файл с историями заказов')

zero_shops = "На вас не прикреплено ни одного магазина\nУточните вопрос и попробуйте снова"
select_payment = 'Выберите способ оплаты'
enter_phone = "Введите сотовый или почту клиента"


async def createOrder(**kwargs):
    if kwargs["client_phone"]:
        mail_or_phone = kwargs["client_phone"]
        message = "Сотовый"
    else:
        mail_or_phone = kwargs["client_mail"]
        message = "Почта"
    text = f'ℹ️ <b>Информация о заказе:</b>\n' \
           f'➖➖➖➖➖➖➖➖➖➖➖\n' \
           f'<b>ФИО клиента</b>: <code>{kwargs["client_name"]}</code>\n' \
           f'<b>{message} клиента</b>: <code>{mail_or_phone}</code>\n' \
           f'<b>Название магазина</b>: <code>{kwargs["shop_name"]}</code>\n' \
           f'<b>Тип оплаты</b>: <code>{kwargs["payment_name"]}</code>\n' \
           f'<b>Курс валюты</b>: <code>{kwargs["currencyPrice"]}</code>\n' \
           f'<b>Название товара</b>: <code>{kwargs["product_name"]}</code>\n' \
           f'<b>Цена товара</b>: <code>{kwargs["price"]} {kwargs["currency_symbol"]}</code>\n' \
           f'<b>Количество</b>: <code>{kwargs["quantity"]}</code>\n'
    if kwargs['currency'] == 'USD':
        text += f'<b>Итого</b>: <code>{kwargs["sum_usd"]} {kwargs["currency_symbol"]} / {kwargs["sum_rub"]} руб</code>'
    elif kwargs['currency'] == 'RUB':
        text += f'<b>Итого</b>: <code>{kwargs["sum_rub"]} {kwargs["currency_symbol"]} / {kwargs["sum_usd"]} $</code>'
    return text


async def qr(order_id, sum, chat_id, sum_rub):
    currency_name = await query_db.get_currency_name(chat_id=chat_id)
    text = (f"<b>Заказ под номером:</b> <code>{order_id}</code>\n"
            f"<b>На сумму:</b> <code>{sum} {currency_name} / {sum_rub} руб</code>")
    return text
