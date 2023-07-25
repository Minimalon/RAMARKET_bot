from decimal import Decimal

from config import __, _

# region ERRORS
error_head = __("➖➖🚨ОШИБКА🚨➖➖\n")
error_fakeContact = __(f'{error_head}Ты отправил <u><b>не свой</b></u> контакт')
error_cancel = __("{error_head}Не найдено текущего заказа").format(error_head=error_head)
error_price_double_comma = __("{error_head}Вы написали больше одной запятой\nПример как надо: <b>10.12</b>").format(
    error_head=error_head)

error_price_not_decimal = __(
    "{error_head}Цена содержит не нужные символы\nПопробуйте снова\nПример как надо: <u><b>10.12</b></u>").format(
    error_head=error_head)

error_article_not_decimal = __("{error_head}Разрешено вводить только цифры\nПопробуйте снова").format(
    error_head=error_head)

error_not_found_order = __("{error_head}Не найдено заказа\nПопробуйте снова создать заказ.").format(
    error_head=error_head)


def error_full_name(name):
    return __(
        "{error_head}ФИО состоит из 3 слов, а ваше состоит из {count} слов\n<b>Попробуйте снова.</b>").format(
        error_head=error_head, count=len(name.split()))


def error_article_not_found(article):
    return __.format(
        error_head=error_head)


def error_server(response):
    return __("{error_head}Сервер недоступен, его код ответа '{response}'\nПопробуйте создать заказ снова.").format(error_head=error_head, response=response.status)


# endregion

menu = __('<u><b>Заказ</b></u> - Оформить заказ покупателю\n'
          '<u><b>Личный кабинет</b></u> - Личные регистрационные данные\n'
          '<u><b>История заказов</b></u> - Получить Excel файл с историями заказов')


def menu_new_language(language='ru'):
    return __('<u><b>Заказ</b></u> - Оформить заказ покупателю\n'
              '<u><b>Личный кабинет</b></u> - Личные регистрационные данные\n'
              '<u><b>История заказов</b></u> - Получить Excel файл с историями заказов', locale=language)


def cart(cart_bot):
    text = ''
    total_sum_usd = 0
    total_sum_rub = 0
    for index, product in enumerate(cart_bot, 1):
        text += _('ℹ️<b>Товар №{index}:</b>\n'
                  '      <b>Название товара</b>: <code>{product_name}</code>\n'
                  '      <b>Цена товара</b>: <code>{price} {currency_symbol}</code>\n'
                  '      <b>Количество</b>: <code>{quantity}</code>\n'). \
            format(index=index, product_name=product['product_name'], quantity=product['quantity'], price=product['price'], currency_symbol=product['currency_symbol'])
        total_sum_rub += Decimal(product['sum_rub'])
        total_sum_usd += Decimal(product['sum_usd'])
    text += _('<b>Общая сумма</b>: <code>{sum_usd} $ / {sum_rub} ₽</code>'). \
        format(sum_usd=Decimal(total_sum_usd).quantize(Decimal('1')), sum_rub=Decimal(total_sum_rub).quantize(Decimal('1')))
    return text


async def createOrder(order):
    if order["client_phone"]:
        mail_or_phone = order["client_phone"]
        message = __("Сотовый")
    else:
        mail_or_phone = order["client_mail"]
        message = __("Почта")
    cart_bot = order['cart_bot']
    text = __('ℹ️ <b>Информация о заказе:</b>\n'
              '➖➖➖➖➖➖➖➖➖➖➖\n'
              '<b>ФИО клиента</b>: <code>{client_name}</code>\n'
              '<b>{message} клиента</b>: <code>{mail_or_phone}</code>\n'
              '<b>Название магазина</b>: <code>{shop_name}</code>\n'
              '<b>Тип оплаты</b>: <code>{payment_name}</code>\n'
              '<b>Курс валюты</b>: <code>{currencyPrice}</code>\n'). \
        format(client_name=order["client_name"], message=message, mail_or_phone=mail_or_phone,
               shop_name=order["shop_name"], payment_name=order["payment_name"], currencyPrice=order["currencyPrice"])

    text += cart(cart_bot)
    return text


async def qr(order_id, sum_usd, sum_rub):
    text = __("<b>Заказ под номером:</b> <code>{order_id}</code>\n"
              "<b>На сумму:</b> <code>{sum_usd} $ / {sum_rub} ₽</code>"). \
        format(order_id=order_id, sum_usd=sum_usd, sum_rub=sum_rub)
    return text
